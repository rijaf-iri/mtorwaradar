import os
import numpy as np
from ..util.radarDateTime import mdv_end_time_file
from ..mdv.readmdv import radarPolar

def radarPolarPrecipData(dirSource, time, params, cmdflag = True, cmdmask = "y"):
    """ 
    time: a string with format yyyy-mm-dd-HH-MM
    params is from json file: radarPolar_rate_user.json or radarPolar_rate_ops.json
    """
    mdvtime = mdv_end_time_file(dirSource, time)
    if mdvtime is None:
        return None

    mdvfile = os.path.join(dirSource, mdvtime[0], mdvtime[1] + ".mdv")

    if params['label'] in ['RATE_Z', 'RATE_ZPOLY']:
        fields = ['DBZ_F']
        if params['pia']['use_pia'] and params['pia']['pia_field'] == 'kdp':
            fields = fields + ['KDP_F']
        if params['filter_dbz']['use_filter'] and params['filter_dbz']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_dbz']['median_filter_censor']['censor_field'] + '_F']

        if params['label'] == 'RATE_Z':
            pars_coef = params['rate_coef']
            params.pop('rate_coef', None)

            pars_zh = {'invCoef': pars_coef['invCoef']}
            if pars_coef['invCoef']:
                pars_zh['alpha'] = pars_coef['alpha0']
                pars_zh['beta'] = pars_coef['beta0']
            else:
                pars_zh['alpha'] = pars_coef['alpha1']
                pars_zh['beta'] = pars_coef['beta1']

            params['rate_coef'] = pars_zh
    elif params['label'] == 'RATE_Z_ZDR':
        fields = ['DBZ_F', 'ZDR_F']
        if params['pia']['use_pia'] and params['pia']['pia_field'] == 'kdp':
            fields = fields + ['KDP_F']
        if params['filter_dbz']['use_filter'] and params['filter_dbz']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_dbz']['median_filter_censor']['censor_field'] + '_F']
        if params['filter_zdr']['use_filter'] and params['filter_zdr']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_zdr']['median_filter_censor']['censor_field'] + '_F']
    elif params['label'] == 'RATE_KDP':
        fields = ['KDP_F']
        if params['filter_kdp']['use_filter'] and params['filter_kdp']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_kdp']['median_filter_censor']['censor_field'] + '_F']
    elif params['label'] == 'RATE_KDP_ZDR':
        fields = ['KDP_F', 'ZDR_F']
        if params['filter_kdp']['use_filter'] and params['filter_kdp']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_kdp']['median_filter_censor']['censor_field'] + '_F']
        if params['filter_zdr']['use_filter'] and params['filter_zdr']['filter_fun'] == 'median_filter_censor':
            fields = fields + [params['filter_zdr']['median_filter_censor']['censor_field'] + '_F']
    else:
        fields = ['DBZ_F', 'ZDR_F', 'KDP_F', 'RHOHV_F', 'NCP_F', 'SNR_F']

    ## remove duplicate
    fields = list(dict.fromkeys(fields))

    ## Apply Clutter Mitigation Decision Flag
    if cmdflag:
        radar = radarPolar(mdvfile, ['CMD_FLAG'] + fields)

        CMDF = radar.fields['CMD_FLAG']['data']

        if cmdmask == "y":
            mask = CMDF == 1.
        else:
            mask = (CMDF == 1.).data

        for j in range(len(fields)):
            datF = radar.fields[fields[j]]['data']
            datF = np.ma.masked_where(mask, datF)
            radar.fields[fields[j]]['data'] = datF
    else:
        radar = radarPolar(mdvfile, fields)

    return radar
