import os
import json
import pyart
import copy
import datetime
from dateutil import tz

from ..util.radarDateTime import polar_mdv_last_time
from .writenc_qpecappi import writenc_qpecappi
from .precipCalc_polar import calculate_PrecipRate
from .precipRadar_polar import radarPolarPrecipData

def compute_qpecappi(start_time, end_time, dirSource, dirNCOUT,
                     pars_file, method = 'RATE_Z', cmdflag = True, cmdmask = "y",
                     grid_shape = (25, 800, 800), z_lim = (0., 12000.),
                     y_lim = (-199750., 199750.), x_lim = (-199750., 199750.)):
    t0 = datetime.datetime.strptime(start_time, '%Y-%m-%d-%H-%M')
    t1 = datetime.datetime.strptime(end_time, '%Y-%m-%d-%H-%M')
    time_range = t1 - t0
    nb_seconds = time_range.days * 86400 + time_range.seconds + 300
    time_list = [t0 + datetime.timedelta(seconds = x) for x in range(0, nb_seconds, 300)]
    time_list = [x.strftime('%Y-%m-%d-%H-%M') for x in time_list]

    params = readJSON_params(pars_file, method)

    for time in time_list:
        params_c = copy.deepcopy(params)
        radar = radarPolarPrecipData(dirSource, time, params_c, cmdflag, cmdmask)
        if radar is None:
            continue

        calculate_qpecappi(radar, dirNCOUT, params_c, grid_shape, z_lim, y_lim, x_lim)

    return 0

def calculate_qpecappi(radar, dirNCOUT, params, grid_shape, z_lim, y_lim, x_lim):
    """ 
    params is from json file: radarPolar_rate_user.json or radarPolar_rate_ops.json
    """
    prrate = calculate_PrecipRate(radar, params)
    grid_limits = (z_lim, y_lim, x_lim)
    grid = pyart.map.grid_from_radars(prrate, fields = ['rain_rate'],
                                      grid_shape = grid_shape, grid_limits = grid_limits,
                                      gridding_algo = 'map_gates_to_grid', map_roi = False,
                                      weighting_function = 'Nearest',
                                      roi_func = 'constant', constant_roi = 2000.)

    temps = polar_mdv_last_time(radar)
    temps = datetime.datetime.strptime(temps, '%Y-%m-%d %H:%M:%S UTC')
    temps = temps.replace(tzinfo = tz.gettz('UTC'))
    timef = temps.strftime('%Y%m%d%H%M%S')
    timed = temps.timestamp()
    timeu = 'seconds since 1970-01-01 00:00:00'
    outncfile = os.path.join(dirNCOUT, "qpe_" + timef + ".nc")

    writenc_qpecappi(grid, timed, timeu, outncfile)

def readJSON_params(pars_file, method):
    """
    pars_json_file: path to parameter file radarPolar_rate_ops.json
    method: one of 'RATE_Z', 'RATE_ZPOLY', 'RATE_Z_ZDR', 'RATE_KDP' or 'RATE_KDP_ZDR'
    """
    with open(pars_file) as json_file:
        pars = json.load(json_file)['fields']

    methods = [pars[i]['label'] for i in range(len(pars))]
    ix = methods.index(method)

    return pars[ix]

