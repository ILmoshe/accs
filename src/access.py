import arrow

from . import Access, CoverageResult, Demand, Point
from .angels import calculate_demands_angels
from .coverage import get_coverage_of_flight

SENSOR_CAPABILITIES = {"range_in_m": 12_000}
COVERAGE_THRESHOLD = 60.0  # percentage


def same_access(before_timestamp: str, now_timestamp: str, time_range_in_sec: float) -> bool:
    before_time = arrow.get(before_timestamp)
    now_time = arrow.get(now_timestamp)

    time_difference = (now_time - before_time).total_seconds()

    return (
        abs(time_difference - time_range_in_sec) < 0.000001
    )  # Using a small epsilon for floating-point comparison


def is_angle_access(demand: Demand, angle_result):
    azimuth = angle_result[demand.id]["azimuth"]["valid"]
    elevation = angle_result[demand.id]["elevation"]["valid"]
    if azimuth is not None and elevation is not None:
        return azimuth, elevation
    return False


def access_match(
    flight_id, demand: Demand, coverage: CoverageResult, angels_result, flight_threshold_in_sec: float = 60
):
    """
    For now, we are not adding the 'params' because it will make it much complicated.
    The angles make it complicated for following access too. we will just put the first one
    :param flight_id:
    :param demand:
    :param coverage:
    :param angels_result
    :param flight_threshold_in_sec:
    :return:
    """
    result = []

    for timestamp in coverage:
        is_covering = coverage[timestamp][demand.id]["coverage_percent"] > COVERAGE_THRESHOLD
        angle = is_angle_access(demand, angels_result[timestamp])
        if is_covering and bool(angle):
            access_coverage_before = result[-1] if len(result) >= 1 else False
            following_access = access_coverage_before is not False and same_access(
                access_coverage_before.start, timestamp, flight_threshold_in_sec
            )
            if following_access:
                # TODO: add angles params etc
                access_coverage_before.end = timestamp
            else:
                coverage_access = Access(
                    **{
                        "flight_id": flight_id,
                        "demand_id": demand.id,
                        "start": timestamp,
                        "end": timestamp,
                        "params": {
                            "azimuth": angle[0],
                            "elevation": angle[1],
                        },
                    }
                )
                result.append(coverage_access)
    return result


def get_accesses(
    flight_id: str,
    flight_route: tuple[tuple[float, float], str],
    demands: list[Demand],
) -> list[Access]:
    coverage_result: CoverageResult = get_coverage_of_flight(
        flight_route,
        demands,
        SENSOR_CAPABILITIES["range_in_m"],
    )
    angels_result = {
        timestamp: calculate_demands_angels(Point(lat=point[0], long=point[1]), demands)
        for point, timestamp in flight_route
    }

    list_of_accesses = []
    for demand in demands:
        accesses_for_demand = access_match(flight_id, demand, coverage_result, angels_result)
        if len(accesses_for_demand):
            list_of_accesses.append(*accesses_for_demand)

    return list_of_accesses
