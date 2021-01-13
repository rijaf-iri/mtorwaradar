import numpy as np
from ..util.filter import apply_filter
from ..util.pia import calculate_pia_dict_args


def getFieldsToUseQPE(pars):
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


def applyFilterQPE(radar, pars_filter):
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


def correctAttenuationQPE(radar, pars_pia):
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


def applyCMDQPE(radar):
    cmd_mask = radar.fields["CMD_FLAG"]["data"] == 1

    fields_r = list(radar.fields.keys())
    fields_q = ["DBZ_F", "ZDR_F", "KDP_F"]
    fields_u = list(set(fields_r) & set(fields_q))

    for field in fields_u:
        radar.fields[field]["data"] = np.ma.masked_where(
            cmd_mask, radar.fields[field]["data"]
        )

    return radar
