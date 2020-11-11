import inspect
import numpy as np
import copy
from ..util.utilities import do_call, str2numeric_dict_args
from ..util.pia import calculate_pia_dict_args
from ..util.filter import *
from .rain_rate import *

def rate_zh(radar, dbz_field = 'DBZ_F',
            coef = {'alpha': 0.017, 'beta': 0.714, 'invCoef': True},
            dbz_thres = {'min_dbz': 20, 'max_dbz': 60}, 
            pia = None, filter_dbz = None):
    dbz = apply_filter_dict_args(radar, dbz_field, filter_dbz)
    if dbz is None:
        dbz = radar.fields[dbz_field]['data']

    res_pia = calculate_pia_dict_args(radar, pia)
    if res_pia is not None:
        dbz = dbz + res_pia

    dbz = np.ma.masked_invalid(dbz)

    dbz_thres = str2numeric_dict_args(dbz_thres)
    dbz[dbz > dbz_thres['max_dbz']] = dbz_thres['max_dbz']
    dbz = np.ma.masked_where(dbz < dbz_thres['min_dbz'], dbz)

    coef = dict((k, float(v) if type(v) is str else v) for k, v in coef.items())
    rt = do_call(rr_zh, args = [dbz], kwargs = coef)
    rt = np.ma.masked_where(rt < 0.1, rt)
    rt = _create_rain_rate_field(radar, rt)

    return rt

def rate_zpoly(radar, dbz_field = 'DBZ_F',
               dbz_thres = {'min_dbz': 20, 'max_dbz': 60}, 
               pia = None, filter_dbz = None):
    dbz = apply_filter_dict_args(radar, dbz_field, filter_dbz)
    if dbz is None:
        dbz = radar.fields[dbz_field]['data']

    res_pia = calculate_pia_dict_args(radar, pia)
    if res_pia is not None:
        dbz = dbz + res_pia

    dbz = np.ma.masked_invalid(dbz)

    dbz_thres = str2numeric_dict_args(dbz_thres)
    dbz[dbz > dbz_thres['max_dbz']] = dbz_thres['max_dbz']
    dbz = np.ma.masked_where(dbz < dbz_thres['min_dbz'], dbz)

    rt = rr_zpoly(dbz)
    rt = np.ma.masked_where(rt < 0.1, rt)
    rt = _create_rain_rate_field(radar, rt)

    return rt

def rate_z_zdr(radar, dbz_field = 'DBZ_F', zdr_field = 'ZDR_F',
               coef = {'alpha': 0.00786, 'beta_zh': 0.967, 'beta_zdr': -4.98},
               dbz_thres = {'min_dbz': 20, 'max_dbz': 60},
               pia = None, filter_dbz = None, filter_zdr = None):
    dbz = apply_filter_dict_args(radar, dbz_field, filter_dbz)
    if dbz is None:
        dbz = radar.fields[dbz_field]['data']

    zdr = apply_filter_dict_args(radar, zdr_field, filter_zdr)
    if zdr is None:
        zdr = radar.fields[zdr_field]['data']

    res_pia = calculate_pia_dict_args(radar, pia)
    if res_pia is not None:
        dbz = dbz + res_pia

    dbz = np.ma.masked_invalid(dbz)
    zdr = np.ma.masked_invalid(zdr)

    dbz_thres = str2numeric_dict_args(dbz_thres)
    dbz[dbz > dbz_thres['max_dbz']] = dbz_thres['max_dbz']
    dbz = np.ma.masked_where(dbz < dbz_thres['min_dbz'], dbz)

    coef = dict((k, float(v) if type(v) is str else v) for k, v in coef.items())
    rt = do_call(rr_z_zdr, args = [dbz, zdr], kwargs = coef)
    # rt = np.ma.masked_where(rt < 0.1, rt)
    # rt = np.ma.masked_where(rt > 600., rt)
    rt[rt > 600.] = 600.
    rt = _create_rain_rate_field(radar, rt)

    return rt

def rate_kdp(radar, kdp_field = 'KDP_F',
             coef = {'alpha': 53.3, 'beta': 0.669},
             filter_kdp = None):
    kdp = apply_filter_dict_args(radar, kdp_field, filter_kdp)
    if kdp is None:
        kdp = radar.fields[kdp_field]['data']

    kdp = np.ma.masked_invalid(kdp)

    coef = dict((k, float(v) if type(v) is str else v) for k, v in coef.items())
    rt = do_call(rr_kdp, args = [kdp], kwargs = coef)
    rt = np.ma.masked_where(rt < 0.1, rt)
    rt = _create_rain_rate_field(radar, rt)

    return rt

def rate_kdp_zdr(radar, kdp_field = 'KDP_F', zdr_field = 'ZDR_F',
                 coef = {'alpha': 192, 'beta_kdp': 0.946, 'beta_zdr': -3.45},
                 filter_kdp = None, filter_zdr = None):
    kdp = apply_filter_dict_args(radar, kdp_field, filter_kdp)
    if kdp is None:
        kdp = radar.fields[kdp_field]['data']

    zdr = apply_filter_dict_args(radar, zdr_field, filter_zdr)
    if zdr is None:
        zdr = radar.fields[zdr_field]['data']

    kdp = np.ma.masked_invalid(kdp)
    zdr = np.ma.masked_invalid(zdr)

    coef = dict((k, float(v) if type(v) is str else v) for k, v in coef.items())
    rt = do_call(rr_kdp_zdr, args = [kdp, zdr], kwargs = coef)
    rt = np.ma.masked_where(rt < 0.1, rt)
    rt = _create_rain_rate_field(radar, rt)

    return rt

#######

def _create_rain_rate_field(radar, rain_rate):
    rt = copy.copy(radar)
    rt.fields = {}
    rt_dict = {
        'units': 'mm/hr',
        'standard_name': 'radar_estimated_rain_rate',
        'long_name': 'Radar estimated rain rate',
        'coordinates': 'elevation azimuth range',
        '_FillValue': rain_rate.fill_value,
        'data': rain_rate
    }
    rt.add_field('rain_rate', rt_dict, replace_existing = True)

    return rt
