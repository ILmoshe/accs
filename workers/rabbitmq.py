import asyncio
import datetime
import json
from copy import deepcopy

import aio_pika
import asyncpg
from shapely import LineString, Polygon

from src import Flight, Sensor
from src.logic import create_case_for_flight_path


async def insert_sensor(conn, sensor_data):
    # Check if the sensor already exists
    existing_sensor = await conn.fetchrow("SELECT id FROM sensor WHERE id = $1", sensor_data["name"])
    if existing_sensor is None:
        # Insert the new sensor
        await conn.execute(
            """
            INSERT INTO sensor (id, focal_length_mm, height_mm, image_width_px, width_mm)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
        """,
            sensor_data["name"],
            sensor_data["focal_length_mm"],
            sensor_data["height_mm"],
            sensor_data["image_width_px"],
            sensor_data["width_mm"],
        )
        print(f"Sensor {sensor_data['name']} inserted.")
    else:
        print(f"Sensor {sensor_data['name']} already exists.")


async def insert_flight(conn, flight_data):
    path = LineString(flight_data["path"]).wkt
    # Insert flight data
    await conn.execute(
        """
        INSERT INTO flight (id, path, camera_azimuth, camera_elevation_start, camera_elevation_end, height_meters, speed_km_h, sensor_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (id) DO NOTHING
    """,
        flight_data["id"],
        path,
        int(flight_data["camera_azimuth"]),
        int(flight_data["camera_elevation_start"]),
        int(flight_data["camera_elevation_end"]),
        int(flight_data["height_meters"]),
        int(flight_data["speed_km_h"]),
        flight_data["sensor_id"],
    )


async def create_tables(conn: asyncpg.Connection):
    # Create the 'sensor' table if it doesn't exist
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor (
            id VARCHAR PRIMARY KEY,
            focal_length_mm INT,
            height_mm INT,
            image_width_px INT,
            width_mm INT
        );
    """
    )

    # Create the 'flight' table if it doesn't exist
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS flight (
            id VARCHAR PRIMARY KEY,
            path GEOMETRY(LineString, 4326),
            camera_azimuth INT,
            camera_elevation_start INT,
            camera_elevation_end INT,
            height_meters INT,
            speed_km_h INT,
            sensor_id VARCHAR REFERENCES sensor(id)
        );
    """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fov (
        id SERIAL PRIMARY KEY,
        related_points GEOMETRY(LineString, 4326),
        flight_id VARCHAR REFERENCES flight(id),
        fov GEOMETRY(Polygon, 4326)
        );
    """
    )


async def update_fov_with_flight(
    conn: asyncpg.Connection, flight_id: str, fov: Polygon, related_points: LineString
):
    await conn.execute(
        """
            INSERT INTO fov (related_points, flight_id, fov)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO NOTHING
        """,
        related_points.wkt,
        flight_id,
        fov.wkt,
    )


def process_FOV_warper(conn: asyncpg.Connection, rubbish: aio_pika.abc.AbstractExchange):
    async def process_FOV(
        message: aio_pika.abc.AbstractIncomingMessage,
    ) -> None:
        async with message.process(ignore_processed=True):
            try:
                msg = json.loads(message.body.decode())
                flight_params = msg["flight"]
                coords = deepcopy(flight_params["path"]["feature"]["geometry"]["coordinates"])
                flight_params["path"] = coords

                sensor = Sensor(**msg["sensor"])
                await insert_sensor(conn, msg["sensor"])
                await insert_flight(conn, {**flight_params, "sensor_id": sensor.name})
                fligth = {**flight_params, "path_case": coords, "sensor": sensor}
                flight = Flight(**fligth)
                fovs = create_case_for_flight_path(flight)

                await asyncio.gather(
                    *[
                        update_fov_with_flight(
                            conn,
                            flight.id,
                            Polygon(fov["case_polygon"]),
                            LineString(list(fov["points"].values())),
                        )
                        for fov in fovs
                    ]
                )

                iso_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                payload = json.dumps({"flight_id": flight.id, "timestamp": iso_time})
                msg_response = aio_pika.Message(body=payload.encode())
                await rubbish.publish(msg_response, routing_key="fovResponse")

                await message.ack()

            except BaseException:
                await message.nack()

            await asyncio.sleep(1)

    return process_FOV


async def main() -> None:
    connection = await aio_pika.connect_robust(
        "amqps://nblmrhlt:LUkkf6MfMJ_W_TRaHU_CgEbm51QSiJfU@cow.rmq2.cloudamqp.com/nblmrhlt",
    )
    queue_constructRoute = "constructRoute"
    queue_fov_result = "fovResponse"
    conn_pool = await asyncpg.create_pool(
        user="postgres", password="changeme", database="accs", host="34.165.254.33"
    )
    await create_tables(conn_pool)

    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "myExchange", type=aio_pika.exchange.ExchangeType.DIRECT, durable=True
    )
    await channel.set_qos(prefetch_count=10)
    fov_result_queue = await channel.declare_queue(queue_fov_result, durable=True)
    constructFov_queue = await channel.declare_queue(queue_constructRoute, durable=True)
    await fov_result_queue.bind("myExchange")
    await constructFov_queue.bind("myExchange")
    await constructFov_queue.consume(process_FOV_warper(conn_pool, exchange))

    try:
        # Wait until terminate
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
