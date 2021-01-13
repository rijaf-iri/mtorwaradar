import os
import numpy as np
import datetime
from dateutil import tz
from ..util.radarDateTime import mdv_end_time_file, polar_mdv_last_time
from ..mdv.readmdv import radarPolar


def readRadarPolar(dirRadar, time, fields="all"):
    """
    Read radar polar

    Parameters
    ----------
    dirRadar: string
        The full path to the folder containing the radar polar folders formed by date (yyyymmdd)
        Ex: /home/data/Projdir/mdv/radarPolar/ops1/sur
    time: string
        The approximation time to be read in the form "yyyy-mm-dd-HH-MM".
    fields: string or list
        The list of the fields to read or a value "all" to read all fields

    Returns
    -------
    radar: pyart radar polar object

    """
    mdvtime = mdv_end_time_file(dirRadar, time)
    mdvfile = os.path.join(dirRadar, mdvtime[0], mdvtime[1] + ".mdv")
    radar = radarPolar(mdvfile, fields)
    return radar


def radarPolarTimeInfo(radar, time_zone):
    last_scan_time = polar_mdv_last_time(radar)
    last_scan_time = datetime.datetime.strptime(last_scan_time, "%Y-%m-%d %H:%M:%S UTC")
    last_scan_time = last_scan_time.replace(tzinfo=tz.gettz("UTC"))
    if time_zone != "UTC":
        last_scan_time = last_scan_time.astimezone(tz.gettz(time_zone))
    time_format = last_scan_time.strftime("%Y%m%d%H%M%S")
    time_numeric = last_scan_time.timestamp()
    time_unit = "seconds since 1970-01-01 00:00:00"

    return {"format": time_format, "value": time_numeric, "unit": time_unit}
