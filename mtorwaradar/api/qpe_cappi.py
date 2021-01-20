import numpy as np
from .radarpolar_qpe import *
from .radarpolar_data import *
from ..qpe.create_cappi import create_cappi_grid
from ..qpe import rain_rate
from ..util.utilities import do_call


def compute_cappi_qpe(dirDate, time, pars):
    """
    Compute QPE

    Compute the precipitation rate and accumulation for 5 minutes

    Parameters
    ----------
    dirDate: string
        full path to the directory of the folders (in the form of date yyyymmdd) containing the MDV files
    time: string
        the approximate time of the mdv file to use, format "yyyy-mm-dd-HH-MM"
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
    fields = getFieldsToUseQPE(pars)
    radar = readRadarPolar(dirDate, time, fields)
    if radar is None:
        return {}

    if bool(pars["filter"]):
        radar = applyFilterQPE(radar, pars["filter"])

    if bool(pars["pia"]):
        if pars["qpe"]["method"] in ["RATE_Z", "RATE_ZPOLY", "RATE_Z_ZDR"]:
            radar = correctAttenuationQPE(radar, pars["pia"])

    if pars["apply_cmd"]:
        radar = applyCMDQPE(radar)

    rlon, rlat, data = createCAPPIQPE(radar, pars["cappi"])
    rtime = radarPolarTimeInfo(radar, pars["time_zone"])

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
            "unit": "mm",
            "data": precip_accumul,
        },
    }

    return qpe


def createCAPPIQPE(radar, pars_cappi):
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

