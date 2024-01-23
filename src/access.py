from pydantic import BaseModel, Field

from __init__ import Access, CoverageResult, Demand
from .coverage import get_coverage_of_flight
from .angels import calculate_demands_angels

SENSOR_CAPABILITIES = {"range_in_m": 12_000}
COVERAGE_THRESHOLD = 75.0  # percentage


class Params(BaseModel):
    azimuth: float = Field(le=360, ge=0)
    elevation: float = Field(le=90, ge=-90)
    coverage_percentage: float = Field(le=100, ge=0)
    coverage_leftover: list[tuple[float, float]]


class Access1(BaseModel):
    demand_id: str
    flight_id: str
    start: str
    end: str
    params: Params


"""
{"demand_id" : demand_id, "coverage_start": TIME, "coverage_end": TIME, "params": {coverage_percentage, coverage_leftover}}
could be two same demands with 2 accesses, I need to do calculation that in case the access is not breaking(time following)
so make it like the same access, we will need to apply the same calculation to the angels_match function as well.
"""


class DemandCoverage(TypedDict):
    coverage_percent: float
    coverage_intersection: list[tuple[float, float]]
    coverage_leftover: list[tuple[float, float]]


def coverage_match(demand: Demand, coverage: CoverageResult):
    """
    :param demand:
    :param coverage:
    :return:
    """
    result = {}

    for timestamp in coverage:
        if coverage[timestamp][demand.id]["coverage_percent"] > COVERAGE_THRESHOLD:
            pass


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
    angels_result = [
        (calculate_demands_angels(point, demands), timestamp) for point, timestamp in flight_route
    ]

    for demand in demands:
        matching_coverage_with_demand = coverage_match(demand, coverage_result)
        matching_coverage_with_demand = angels_match(demand, angels_result)
        if matching_coverage_with_demand["found"] and matching_coverage_with_demand["found "]:
            pass
