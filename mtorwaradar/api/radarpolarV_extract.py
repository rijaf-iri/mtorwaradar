import os
import numpy as np
import datetime
from dateutil import tz
import pyart

from .radarpolar_data import *
from ..util.utilities import rFloatVector_to_npmDarray

import rpy2.robjects as robjects
import rpy2.robjects.vectors as rvect
from rpy2.robjects.packages import importr

mtrwdata = importr("mtorwdata")


def extract_polar_vertical(
    dirMDV,
    source,
    start_time,
    end_time,
    fields,
    points,
    padxy=[0, 0],
    fun_sp="mean",
    heights=None,
    apply_cmd=False,
    pia=None,
    dbz_fields=None,
    filter=None,
    filter_fields=None,
    time_zone="Africa/Kigali",
):
    if source is None:
        dirDate = dirMDV
    else:
        dirDate = os.path.join(dirMDV, source)

    if type(fields) is not list:
        fields = [fields]

    #####

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

    #####
    radar0 = None
    for time in seqTime:
        radar0 = readRadarPolar(dirDate, time)
        if radar0 is not None:
            break

    if radar0 is None:
        return {}

    fields = [f for f in fields if f in list(radar0.fields.keys())]
    if len(fields) == 0:
        return {}

    #######
    x_r = radar0.gate_x["data"]
    y_r = radar0.gate_y["data"]
    z_r = radar0.gate_z["data"]

    projparams = radar0.projection.copy()
    projparams["lon_0"] = radar0.longitude["data"][0]
    projparams["lat_0"] = radar0.latitude["data"][0]
    # lon_r, lat_r = pyart.core.cartesian_to_geographic(x_r, y_r, projparams)

    r_coords = rvect.ListVector(
        {
            "x": robjects.FloatVector(x_r.flatten()),
            "y": robjects.FloatVector(y_r.flatten()),
            "z": robjects.FloatVector(z_r.flatten()),
            # "lon": robjects.FloatVector(lon_r.flatten()),
            # "lat": robjects.FloatVector(lat_r.flatten()),
        }
    )

    #######

    if heights is None:
        heights = [0, 10000, 500]
    r_heights = np.arange(heights[0], heights[1] + 0.001, heights[2])

    r_x = np.arange(0, x_r.max() + 0.001, 500)
    r_x = np.concatenate((-1 * np.flip(r_x[1:]), r_x))
    r_y = np.arange(0, y_r.max() + 0.001, 500)
    r_y = np.concatenate((-1 * np.flip(r_y[1:]), r_y))
    r_x, r_y = np.meshgrid(r_x, r_y)
    r_lon, r_lat = pyart.core.cartesian_to_geographic(r_x, r_y, projparams)

    r_interp = rvect.ListVector(
        {
            "x": robjects.FloatVector(r_x[0, :]),
            "y": robjects.FloatVector(r_y[:, 0]),
            "z": robjects.FloatVector(r_heights),
            "lon": robjects.FloatVector(r_lon[0, :]),
            "lat": robjects.FloatVector(r_lat[:, 0]),
        }
    )

    #######

    r_points = robjects.DataFrame(points[0])
    for pt in points[1:]:
        r_points = r_points.rbind(robjects.DataFrame(pt))

    r_padxy = robjects.FloatVector(padxy)

    #####

    fields_pars = getFieldsPiaFilterCmd(pia, filter, apply_cmd)
    fields_read = fields + fields_pars
    fields_read = list(dict.fromkeys(fields_read))

    #####

    npt = len(points)
    nlev = len(r_heights)

    ext_data = dict()
    ext_data["coords"] = points
    ext_data["height"] = r_heights.tolist()
    ext_data["date"] = list()
    ext_data["data"] = dict()
    for field in fields:
        ext_data["data"][field] = list()

    #####

    for time in seqTime:
        radar = readRadarPolar(dirDate, time, fields_read)
        if radar is None:
            continue

        if bool(filter) & bool(filter_fields):
            radar = applyFilter(radar, filter, filter_fields)

        if bool(pia) & bool(dbz_fields):
            radar = correctAttenuation(radar, pia, dbz_fields)

        if apply_cmd:
            radar = applyCMD(radar, fields)

        #####
        r_data = dict()
        for field in fields:
            xdat = radar.fields[field]["data"]
            xdat = xdat.filled(np.nan)
            r_data[field] = robjects.FloatVector(xdat.flatten())

        r_data = rvect.ListVector(r_data)

        out = mtrwdata.extract_3DPolarData(
            r_coords, r_data, r_interp, r_points, r_padxy, fun_sp
        )

        out = dict(zip(out.names, out))

        for field in fields:
            xdat = out[field]
            xdat = rFloatVector_to_npmDarray(xdat, (npt, nlev))
            xdat = xdat.transpose()
            xdat = np.ma.masked_invalid(xdat)
            xdat = xdat.filled(-9999).tolist()
            ext_data["data"][field] = ext_data["data"][field] + [xdat]

        temps = radarPolarTimeInfo(radar, time_zone)
        ext_data["date"] = ext_data["date"] + [temps["format"]]

    return ext_data
