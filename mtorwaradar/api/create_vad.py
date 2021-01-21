import os
from pyart.retrieve import velocity_azimuth_display
from .radarpolar_data import readRadarPolar, radarPolarTimeInfo
from ..util.utilities import suppress_stdout


def create_vad_data(dirMDV, source, time, z_want, vel_field, time_zone):
    if source is None:
        dirDate = dirMDV
    else:
        dirDate = os.path.join(dirMDV, source)

    radar = readRadarPolar(dirDate, time, vel_field)
    if radar is None:
        return {}

    with suppress_stdout():
        vad = velocity_azimuth_display(radar, vel_field, z_want)

    infoT = radarPolarTimeInfo(radar, time_zone)

    return {
        "time": infoT["format"],
        "height": vad.height,
        "speed": vad.speed,
        "direction": vad.direction,
        "u_wind": vad.u_wind,
        "v_wind": vad.v_wind,
    }
