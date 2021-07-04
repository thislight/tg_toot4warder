from dataclasses import dataclass, field
import datetime
from typing import Optional, cast, Dict, Tuple, List
import arrow

TimeCost = float


@dataclass
class MeasurementData(object):
    time: arrow.Arrow
    responded: bool
    success: bool
    time_cost: TimeCost
    error_type: Optional[str] = None


class RemoteMeasurement(object):
    def __init__(self, maxitems: int) -> None:
        self.item_limits = maxitems
        self.data: List[MeasurementData] = []
        super().__init__()


def push_data(rmeasurement: RemoteMeasurement, data: MeasurementData) -> None:
    rmeasurement.data.append(data)
    while len(rmeasurement.data) > rmeasurement.item_limits:
        rmeasurement.data.pop(0)


def maintains(rmeasurement: RemoteMeasurement) -> None:
    rmeasurement.data.sort(key=lambda d: d.time)
    while len(rmeasurement.data) > rmeasurement.item_limits:
        rmeasurement.data.pop(0)


def time_range_start(rmeasurement: RemoteMeasurement) -> arrow.Arrow:
    return rmeasurement.data[0].time


def time_range_end(rmeasurement: RemoteMeasurement) -> arrow.Arrow:
    return rmeasurement.data[-1].time


def time_delta(rmeasurement: RemoteMeasurement) -> datetime.timedelta:
    return time_range_end(rmeasurement) - time_range_start(rmeasurement)


def total_responded_possibility(rmeasurement: RemoteMeasurement) -> float:
    total_data_n = len(rmeasurement.data)
    responded_n = sum([1 for d in rmeasurement.data if d.responded])
    return responded_n / total_data_n


def total_success_possibility(rmeasurement: RemoteMeasurement) -> float:
    total_data_n = len(rmeasurement.data)
    success_n = sum([1 for d in rmeasurement.data if d.success])
    return success_n / total_data_n


def average_time_cost(rmeasurement: RemoteMeasurement) -> float:
    total_data_n = len(rmeasurement.data)
    total_cost = sum([d.time_cost for d in rmeasurement.data])
    return total_cost / total_data_n


def group_by_error_type(
    rmeas: RemoteMeasurement,
) -> Dict[Optional[str], List[MeasurementData]]:
    d: Dict[Optional[str], List[MeasurementData]] = dict()
    for x in rmeas.data:
        if not d.get(x.error_type):
            d[x.error_type] = []
        d[x.error_type].append(x)
    return d


def error_happened_times(rmeas: RemoteMeasurement) -> Dict[str, int]:
    groups = group_by_error_type(rmeas)
    countings: Dict[str, int] = dict()
    for k in groups:
        if k:
            countings[k] = len(groups[k])
    return countings


def the_most_happened_error_type(rmeas: RemoteMeasurement) -> Optional[Tuple[str, int]]:
    countings = error_happened_times(rmeas)
    kvpair_list = list(countings.items())
    if not kvpair_list:
        return None
    kvpair_list.sort(key=lambda kvp: kvp[1], reverse=True)
    return kvpair_list[0]


def error_rate_of_type(rmeas: RemoteMeasurement, errt: str) -> Optional[float]:
    countings = error_happened_times(rmeas)
    error_data_list = countings.get(errt, None)
    if not error_data_list:
        return None
    return error_data_list / len(rmeas.data)


_MaxTimeCostMeasurementData = MeasurementData
_MinTimeCostMeasurementData = MeasurementData
_MaxTimeCost = float
_MinTimeCost = float


def maxmin_time_cost_data(
    rmeasurement: RemoteMeasurement,
) -> Tuple[_MaxTimeCostMeasurementData, _MinTimeCostMeasurementData]:
    max_cost = max(rmeasurement.data, key=lambda d: d.time_cost)
    min_cost = min(rmeasurement.data, key=lambda d: d.time_cost)
    return max_cost, min_cost


def maxmin_time_cost(
    rmeasurement: RemoteMeasurement,
) -> Tuple[_MaxTimeCost, _MinTimeCost]:
    max_cost_d, min_cost_d = maxmin_time_cost_data(rmeasurement)
    return max_cost_d.time_cost, min_cost_d.time_cost


@dataclass
class MeasurementSnapshot(object):
    time_start: arrow.Arrow
    time_end: arrow.Arrow
    time_delta: datetime.timedelta
    responded_rate: float
    success_rate: float
    average_time_cost: float
    max_time_cost: float
    min_time_cost: float
    the_most_happened_error_type: Optional[str]
    the_most_happened_error_rate: Optional[float]
    generated_at: arrow.Arrow = field(default_factory=lambda: arrow.get())


def capture_measurement(rmeas: RemoteMeasurement) -> MeasurementSnapshot:
    max_time_cost, min_time_cost = maxmin_time_cost(rmeas)
    the_most_happened_error_result = the_most_happened_error_type(rmeas)
    if the_most_happened_error_result:
        the_most_happened_error: Optional[str] = the_most_happened_error_result[0]
    else:
        the_most_happened_error = None
    the_most_happened_error_rate = (
        error_rate_of_type(rmeas, cast(str, the_most_happened_error))
        if the_most_happened_error
        else None
    )
    return MeasurementSnapshot(
        time_start=time_range_start(rmeas),
        time_end=time_range_end(rmeas),
        time_delta=time_delta(rmeas),
        responded_rate=total_responded_possibility(rmeas),
        success_rate=total_success_possibility(rmeas),
        average_time_cost=average_time_cost(rmeas),
        max_time_cost=max_time_cost,
        min_time_cost=min_time_cost,
        the_most_happened_error_type=the_most_happened_error,
        the_most_happened_error_rate=the_most_happened_error_rate,
    )
