import os
import numpy as np
import datetime
from dateutil import tz
from ..util.radarDateTime import mdv_end_time_file, polar_mdv_last_time
from ..mdv.readmdv import radarPolar
from ..util.filter import apply_filter
from ..util.pia import calculate_pia_dict_args
from ..qpe.create_cappi import create_cappi_grid
from ..qpe import rain_rate
from ..util.utilities import do_call


def computeCAPPIQPE(dirDate, pars):
    """
    Compute QPE

    Compute the precipitation rate and accumulation for 5 minutes

    Parameters
    ----------
    dirDate: string
        full path to the directory of the folders (in the form of date yyyymmdd) containing the MDV files
    pars: dictionary
        dictionary of the arguments

    Returns
    -------
    qpe: dictionary
        lon: 1d array longitude
        lat: 1d array latitude
        time: dictionary with keys: format, value, unit
        qpe: dictionary of the precipitation rate and accumulation over 5 minutes
    """
    fields = getFieldsToUse(pars)
    radar = readRadarPolar(dirDate, pars['time'], fields)
    if radar is None:
        return {}

    if bool(pars["filter"]):
        radar = applyFilter(radar, pars["filter"])

    if bool(pars["filter"]):
        if pars["qpe"]["method"] in ["RATE_Z", "RATE_ZPOLY", "RATE_Z_ZDR"]:
            radar = correctAttenuation(radar, pars["pia"])

    if pars["apply_cmd"]:
        radar = applyCMD(radar)

    rlon, rlat, data = createCAPPI(radar, pars["cappi"])
    rtime = ncoutTimeInfo(radar)

    if pars["qpe"]["method"] in ["RATE_Z", "RATE_ZPOLY", "RATE_Z_ZDR"]:
        data = maskDBZthres(data, pars["dbz_thres"])

    qpe = computeQPE(data, pars["qpe"])

    return {"lon": rlon, "lat": rlat, "time": rtime, "qpe": qpe}


def computeQPE(data, pars_qpe):
    """
    data = {
        'DBZ_F': 'numpy masked_array',
        'ZDR_F': 'numpy masked_array'
    }
    ###
    pars_qpe = {
                'method': 'RATE_Z',
                'pars': {
                        'alpha': 300,
                        'beta': 1.4,
                        'invCoef': False
                    }
                }
    """
    if pars_qpe["method"] == "RATE_Z":
        fun = rain_rate.rr_zh
        args = [data["DBZ_F"]]

    if pars_qpe["method"] == "RATE_ZPOLY":
        fun = rain_rate.rr_zpoly
        args = [data["DBZ_F"]]
        pars_qpe["pars"] = {}

    if pars_qpe["method"] == "RATE_Z_ZDR":
        fun = rain_rate.rr_z_zdr
        args = [data["DBZ_F"], data["ZDR_F"]]

    if pars_qpe["method"] == "RATE_KDP":
        fun = rain_rate.rr_kdp
        args = [data["KDP_F"]]

    if pars_qpe["method"] == "RATE_KDP_ZDR":
        fun = rain_rate.rr_kdp_zdr
        args = [data["KDP_F"], data["ZDR_F"]]

    kwargs = pars_qpe["pars"]

    precip_rate = do_call(fun, args=args, kwargs=kwargs)
    precip_accumul = precip_rate * 300.0 / 3600.0

    qpe = {
        "rate": {
            "name": "rate",
            "long_name": "Precipitation rate",
            "unit": "mm/hr",
            "data": precip_rate,
        },
        "precip": {
            "name": "precip",
            "long_name": "Precipitation accumulation",
            "unit": "mm/hr",
            "data": precip_accumul,
        },
    }

    return qpe


def createCAPPI(radar, pars_cappi):
    """
    pars_cappi = {
                'method': 'ppi_ranges',
                'pars': {
                        'alt': 4.5
                    }
                }
    """
    fields_r = list(radar.fields.keys())
    fields_q = ["DBZ_F", "ZDR_F", "KDP_F"]
    fields_u = list(set(fields_r) & set(fields_q))

    method = pars_cappi["method"]

    if method == "composite_altitude":
        param_cappi = pars_cappi["pars"]
    else:
        param_cappi = pars_cappi["pars"]["alt"]

    return create_cappi_grid(radar, fields_u, method, param_cappi)


def maskDBZthres(data, dbz_thres):
    """
    dbz_thres = {'min': 20, 'max': 65}
    """
    dbz = data["DBZ_F"]
    dbz = np.ma.masked_invalid(dbz)
    dbz = np.ma.masked_where(dbz < dbz_thres["min"], dbz)
    dbz = dbz.filled(-999.0)
    dbz[dbz > dbz_thres["max"]] = dbz_thres["max"]
    dbz = np.ma.masked_where(dbz == -999.0, dbz)
    data["DBZ_F"] = dbz

    return data


def getFieldsToUse(pars):
    """
    pars = {
        'qpe': {
                'method': 'RATE_Z'
              },
        'pia': {
                   'method': 'dbz'
               },
        'filter': {
                    'method': 'median_filter_censor',
                    'pars': {
                                'censor_field': "NCP"
                            }
                  },
        'apply_cmd': True
    }
    """
    if pars["qpe"]["method"] in ["RATE_Z", "RATE_ZPOLY"]:
        fields = ["DBZ_F"]
    elif pars["qpe"]["method"] == "RATE_Z_ZDR":
        fields = ["DBZ_F", "ZDR_F"]
    elif pars["qpe"]["method"] == "RATE_KDP":
        fields = ["KDP_F"]
    elif pars["qpe"]["method"] == "RATE_KDP_ZDR":
        fields = ["KDP_F", "ZDR_F"]
    else:
        fields = ["DBZ_F", "ZDR_F", "KDP_F", "RHOHV_F", "NCP_F", "SNR_F"]

    if bool(pars["pia"]):
        if pars["pia"]["method"] == "kdp":
            fields = fields + ["KDP_F"]
        else:
            fields = fields + ["DBZ_F"]

    if bool(pars["filter"]):
        if pars["filter"]["method"] == "median_filter_censor":
            fields = fields + [pars["filter"]["pars"]["censor_field"] + "_F"]

    if pars["apply_cmd"]:
        fields = fields + ["CMD_FLAG"]

    fields = list(dict.fromkeys(fields))

    return fields


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


def applyFilter(radar, pars_filter):
    """
    pars_filter = {
                'method': 'median_filter_censor',
                'pars': {
                        # .....
                    }
            }
    """
    fields_r = list(radar.fields.keys())
    fields_q = ["DBZ_F", "ZDR_F", "KDP_F"]
    fields_u = list(set(fields_r) & set(fields_q))

    if pars_filter["method"] == "median_filter_censor":
        pars_filter["pars"]["censor_field"] = pars_filter["pars"]["censor_field"] + "_F"

    for field in fields_u:
        radar.fields[field]["data"] = apply_filter(
            radar, pars_filter["method"], field, **pars_filter["pars"]
        )

    return radar


def correctAttenuation(radar, pars_pia):
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

    pia = calculate_pia_dict_args(radar, pia_args)
    radar.fields["DBZ_F"]["data"] = radar.fields["DBZ_F"]["data"] + pia

    return radar


def applyCMD(radar):
    cmd_mask = radar.fields["CMD_FLAG"]["data"] == 1

    fields_r = list(radar.fields.keys())
    fields_q = ["DBZ_F", "ZDR_F", "KDP_F"]
    fields_u = list(set(fields_r) & set(fields_q))

    for field in fields_u:
        radar.fields[field]["data"] = np.ma.masked_where(
            cmd_mask, radar.fields[field]["data"]
        )

    return radar


def ncoutTimeInfo(radar):
    last_scan_time = polar_mdv_last_time(radar)
    last_scan_time = datetime.datetime.strptime(last_scan_time, "%Y-%m-%d %H:%M:%S UTC")
    last_scan_time = last_scan_time.replace(tzinfo=tz.gettz("UTC"))
    last_scan_time = last_scan_time.astimezone(tz.gettz("Africa/Kigali"))
    time_format = last_scan_time.strftime("%Y%m%d%H%M%S")
    time_numeric = last_scan_time.timestamp()
    time_unit = "seconds since 1970-01-01 00:00:00"

    return {"format": time_format, "value": time_numeric, "unit": time_unit}
