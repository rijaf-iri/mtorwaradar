import os
from pyart.core.transforms import antenna_to_cartesian
from .radarpolar_data import readRadarPolar, radarPolarTimeInfo


def create_qvp_data(dirMDV, source, time, fields, desired_angle, time_zone):
    if source is None:
        dirDate = dirMDV
    else:
        dirDate = os.path.join(dirMDV, source)

    radar = readRadarPolar(dirDate, time, fields)
    if radar is None:
        return {}

    index = abs(radar.fixed_angle["data"] - desired_angle).argmin()
    radar_range = radar.range["data"] / 1000.0
    radar_angle = radar.fixed_angle["data"][index]
    _, _, height = antenna_to_cartesian(radar_range, 0.0, radar_angle)

    data = dict()
    for field in fields:
        data[field] = radar.get_field(index, field).mean(axis=0)

    infoT = radarPolarTimeInfo(radar, time_zone)

    return {
        "time": infoT["format"],
        "elevation": radar_angle,
        "height": height,
        "data": data,
    }
