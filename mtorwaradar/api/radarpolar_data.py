import os
import numpy as np
import datetime
from dateutil import tz
from ..util.radarDateTime import mdv_end_time_file, polar_mdv_last_time
from ..mdv.readmdv import radarPolar
from ..util.filter import apply_filter
from ..util.pia import calculate_pia_dict_args


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
    if mdvtime is None:
        return None

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


def getFieldsPiaFilterCmd(pars_pia, pars_filter, apply_cmd):
    fields = []
    if bool(pars_pia):
        if pars_pia["method"] == "kdp":
            fields = fields + ["KDP_F"]
        else:
            fields = fields + ["DBZ_F"]

    if bool(pars_filter):
        if pars_filter["method"] == "median_filter_censor":
            fields = fields + [pars_filter["pars"]["censor_field"] + "_F"]

    if apply_cmd:
        fields = fields + ["CMD_FLAG"]

    fields = list(dict.fromkeys(fields))

    return fields


def applyFilter(radar, pars_filter, filter_fields):
    """
    pars_filter = {
                'method': 'median_filter_censor',
                'pars': {
                        # .....
                    }
            }
    """
    if pars_filter["method"] == "median_filter_censor":
        pars_filter["pars"]["censor_field"] = pars_filter["pars"]["censor_field"] + "_F"

    for field in filter_fields:
        radar.fields[field]["data"] = apply_filter(
            radar, pars_filter["method"], field, **pars_filter["pars"]
        )

    return radar


def correctAttenuation(radar, pars_pia, dbz_fields):
    """
    pars_pia = {
                'method': 'dbz',
                'pars': {
                        # .....
                    }
            }
    """
    pia_args = {}
    pia_args["use_pia"] = True
    pia_args["pia_field"] = pars_pia["method"]
    pia_args[pars_pia["method"]] = pars_pia["pars"]

    ## for pia using KDP, kdp_field = 'KDP_F'
    for field in dbz_fields:
        pia = calculate_pia_dict_args(radar, pia_args, dbz_field = field)
        radar.fields[field]["data"] = radar.fields[field]["data"] + pia

    return radar


def applyCMD(radar, fields):
    cmd_mask = radar.fields["CMD_FLAG"]["data"] == 1

    for field in fields:
        radar.fields[field]["data"] = np.ma.masked_where(
            cmd_mask, radar.fields[field]["data"]
        )

    return radar
