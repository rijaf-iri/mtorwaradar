import os
import numpy as np
import datetime
from dateutil import tz
import pyart

from .radargrid_data import *
from ..util.utilities import rFloatVector_to_npmDarray

import rpy2.robjects as robjects
import rpy2.robjects.vectors as rvect
from rpy2.robjects.packages import importr

mtrwdata = importr("mtorwdata")


def extract_grid_data(
    dirMDV,
    source,
    start_time,
    end_time,
    fields,
    points,
    levels=-1,
    padxyz=[0, 0, 0],
    fun_sp="mean",
    time_zone="Africa/Kigali",
):
    """
    Extract radar Cartesian data over a given points.

    Parameters
    ----------
    dirMDV: string
        full path to the directory "mdv" (1) or the folders containing the folders dates of the mdv files (2)
    source: string
        a partial path of the directory containing the folders dates of the mdv files for (1) or None for (2)
    start_time: string
        The start time same time zone as "time_zone", format "YYYY-mm-dd HH:MM"
    end_time: string
        The end time same time zone as "time_zone", format "YYYY-mm-dd HH:MM"
    fields: list
        List of the fields to extract
    points: list of dictionary
        A list of the dictionary of the points to extract, format
        [{"id": "id_point1", "longitude": value_lon, "latitude": value_lat}, {...}, ...]
    levels: integer or list of integer
        A list of the index of altitudes to be extracted in integer, or -1 to extract all available altitude
    padxyz: list
        list of the padding to apply to each point to extract with order  [longitude, latitude, altitude].
        Default [0, 0, 0], no padding applied
    fun_sp: string
        Function to be used for the padding. Options: "mean", "median", "max", "min"
    time_zone: string
        The time zone of "start_time", "end_time" and the output extracted data.
        Options: "Africa/Kigali" or "UTC". Default "Africa/Kigali"

    Returns
    -------
    Return a dictionary of
        points: the original points used to extract the data
        date: list of dates of the extracted data
        altitude: list of the altitudes of the extracted data
        data: dictionary of the fields in the form of 3d list
             dimension: (len(date) x len(altitude) x len(points))
    """

    if source is None:
        dirDate = dirMDV
    else:
        dirDate = os.path.join(dirMDV, source)

    if type(fields) is not list:
        fields = [fields]

    start = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    start = start.replace(tzinfo=tz.gettz(time_zone))
    end = end.replace(tzinfo=tz.gettz(time_zone))
    time_range = end - start
    nb_seconds = time_range.days * 86400 + time_range.seconds + 300
    seqTime = [start + datetime.timedelta(seconds=x) for x in range(0, nb_seconds, 300)]

    if time_zone != "UTC":
        seqTime = [x.astimezone(tz.gettz("UTC")) for x in seqTime]

    seqTime = [x.strftime("%Y-%m-%d-%H-%M") for x in seqTime]

    grid0 = None
    for time in seqTime:
        grid0 = readRadarGrid(dirDate, time)
        if grid0 is not None:
            break

    if grid0 is None:
        return {}

    fields = [f for f in fields if f in list(grid0.fields.keys())]
    if len(fields) == 0:
        return {}

    if type(levels) is not list:
        if levels == -1:
            levels = list(range(grid0.nz))
        else:
            levels = [levels]

    max_nz = grid0.nz - 1
    if max(levels) > max_nz:
        levels = [l for l in levels if not l > max_nz]

    if len(levels) == 0:
        return {}

    lon, lat = pyart.core.cartesian_to_geographic(
        grid0.x["data"], grid0.y["data"], grid0.get_projparams()
    )
    alt = grid0.z["data"]

    r_coords = rvect.ListVector(
        {
            "lon": robjects.FloatVector(lon),
            "lat": robjects.FloatVector(lat),
            "alt": robjects.FloatVector(alt),
        }
    )

    r_points = robjects.DataFrame(points[0])
    for pt in points[1:]:
        r_points = r_points.rbind(robjects.DataFrame(pt))

    r_padxyz = robjects.FloatVector(padxyz)
    r_levels = robjects.FloatVector(levels)

    npt = len(points)
    nlev = len(levels)

    ext_data = dict()
    ext_data["coords"] = points
    ext_data["altitude"] = alt[levels].tolist()
    ext_data["date"] = list()
    ext_data["data"] = dict()
    for field in fields:
        ext_data["data"][field] = list()

    for time in seqTime:
        grid = readRadarGrid(dirDate, time, fields)
        if grid is None:
            continue

        r_data = dict()
        for field in fields:
            xdat = grid.fields[field]["data"]
            xdat = xdat.filled(np.nan)
            r_data[field] = robjects.FloatVector(xdat.flatten())

        r_data = rvect.ListVector(r_data)

        out = mtrwdata.extract_3DGridData(
            r_coords, r_data, r_points, r_levels, r_padxyz, fun_sp
        )
        out = dict(zip(out.names, out))

        for field in fields:
            xdat = out[field]
            xdat = rFloatVector_to_npmDarray(xdat, (npt, nlev))
            xdat = xdat.transpose()
            xdat = np.ma.masked_invalid(xdat)
            xdat = xdat.filled(-9999).tolist()
            ext_data["data"][field] = ext_data["data"][field] + [xdat]

        temps = radarCartTimeInfo(grid, time_zone)
        ext_data["date"] = ext_data["date"] + [temps["format"]]

    return ext_data
