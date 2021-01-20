import os
import numpy as np

from .radarpolar_data import *
from ..qpe.create_cappi import create_cappi_grid


def create_cappi_data(dirMDV, source, time, pars):
    if source is None:
        dirDate = dirMDV
    else:
        dirDate = os.path.join(dirMDV, source)

    fields_pars = getFieldsPiaFilterCmd(pars["pia"], pars["filter"], pars["apply_cmd"])
    fields_read = pars["fields"] + fields_pars

    if pars["dbz_fields"] is not None:
        fields_read = fields_read + pars["dbz_fields"]

    if pars["filter_fields"] is not None:
        fields_read = fields_read + pars["filter_fields"]

    fields_read = list(dict.fromkeys(fields_read))

    radar = readRadarPolar(dirDate, time, fields_read)
    if radar is None:
        return {}

    if bool(pars["filter"]) & bool(pars["filter_fields"]):
        radar = applyFilter(radar, pars["filter"], pars["filter_fields"])

    if bool(pars["pia"]) & bool(pars["dbz_fields"]):
        radar = correctAttenuation(radar, pars["pia"], pars["dbz_fields"])

    if pars["apply_cmd"]:
        radar = applyCMD(radar, pars["fields"])

    method = pars["cappi"]["method"]
    if method == "composite_altitude":
        param_cappi = pars["cappi"]["pars"]
    else:
        param_cappi = pars["cappi"]["pars"]["alt"]

    lon, lat, data = create_cappi_grid(radar, pars["fields"], method, param_cappi)

    rtime = radarPolarTimeInfo(radar, pars["time_zone"])

    return {"lon": lon, "lat": lat, "time": rtime, "data": data}
