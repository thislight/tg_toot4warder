from dataclasses import dataclass
import datetime
import arrow

TimeCost = float

@dataclass
class MeasurementData(object):
    time: arrow.Arrow
    responded: bool
    success: bool
    time_cost: TimeCost

class RemoteMeasurement(object):
    def __init__(self, maxitems: int) -> None:
        self.item_limits = maxitems
        self.data: list[MeasurementData] = []
        super().__init__()

def push_data(rmeasurement: RemoteMeasurement, data: MeasurementData) -> None:
    rmeasurement.data.append(data)
    while len(rmeasurement.data) > rmeasurement.item_limits:
        rmeasurement.data.pop()

def maintains(rmeasurement: RemoteMeasurement) -> None:
    rmeasurement.data.sort(key= lambda d: d.time)

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

_MaxTimeCostMeasurementData = MeasurementData
_MinTimeCostMeasurementData = MeasurementData
_MaxTimeCost = float
_MinTimeCost = float

def maxmin_time_cost_data(rmeasurement: RemoteMeasurement) -> tuple[_MaxTimeCostMeasurementData, _MinTimeCostMeasurementData]:
    max_cost = max(rmeasurement.data, key=lambda d: d.time_cost)
    min_cost = min(rmeasurement.data, key=lambda d:d.time_cost)
    return max_cost, min_cost

def maxmin_time_cost(rmeasurement: RemoteMeasurement) -> tuple[_MaxTimeCost, _MinTimeCost]:
    max_cost_d, min_cost_d = maxmin_time_cost_data(rmeasurement)
    return max_cost_d.time_cost, min_cost_d.time_cost
