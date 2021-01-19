import os
import datetime
from dateutil import tz

from ..util.radarDateTime import mdv_end_time_file, grid_mdv_time
from ..mdv.readmdv import radarGrid


def readRadarGrid(dirRadar, time, fields="all"):
    mdvtime = mdv_end_time_file(dirRadar, time)
    if mdvtime is None:
        return None

    mdvfile = os.path.join(dirRadar, mdvtime[0], mdvtime[1] + ".mdv")
    grid = radarGrid(mdvfile, fields)
    return grid


def radarCartTimeInfo(grid, time_zone):
    last_scan_time = grid_mdv_time(grid)
    last_scan_time = datetime.datetime.strptime(last_scan_time, "%Y-%m-%d %H:%M:%S UTC")
    last_scan_time = last_scan_time.replace(tzinfo=tz.gettz("UTC"))
    if time_zone != "UTC":
        last_scan_time = last_scan_time.astimezone(tz.gettz(time_zone))
    time_format = last_scan_time.strftime("%Y%m%d%H%M%S")
    time_numeric = last_scan_time.timestamp()
    time_unit = "seconds since 1970-01-01 00:00:00"

    return {"format": time_format, "value": time_numeric, "unit": time_unit}
