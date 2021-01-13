import os
import numpy as np
import datetime
from dateutil import tz
from .radarpolar_data import *


def extract_polar_data(
    dirMDV,
    source,
    start_time,
    end_time,
    fields,
    points,
    sweeps=-1,
    pia=None,
    dbz_fields=None,
    filter=None,
    filter_fields=None,
    apply_cmd=False,
    time_zone="Africa/Kigali",
):
    """
    Extract radar polar data over a given points.

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
    sweeps: integer or list of integer
        A list of the elevation angles to be extracted in integer, or -1 to extract all available elevation angles
    pia: dictionary or None
        Dictionary of the method and parameters to use to perform an attenuation correction
        for the reflectivity fields before extraction.
        Default None, no attenuation correction performed.
    dbz_fields: list or None
        List of reflectivity fields to correct the attenuation. Must be in "fields". Default None
    filter: dictionary
        Dictionary of the method and parameters to use to filter the fields before extraction.
        Default None, no filter applied.
    filter_fields: list or None
        List of fields in which the filter will be applied. Must be in "fields". Default None
    apply_cmd: boolean
        Apply clutter mitigation decision to the fields. Default False
    time_zone: string
        The time zone of "start_time", "end_time" and the output extracted data.
        Options: "Africa/Kigali" or "UTC". Default "Africa/Kigali"

    Returns
    -------
    Return a dictionary of
        points: the original points used to extract the data
        date: list of dates of the extracted data
        elevation_angle: list of the elevation angles of the extracted data
        data: dictionary of longitude, latitude, altitude and the fields in the form of 3d list
             dimension: (len(date) x len(elevation_angle) x len(points))
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

    #####
    radar0 = None
    for time in seqTime:
        radar0 = readRadarPolar(dirDate, time, None)
        if radar0 is not None:
            break

    if radar0 is None:
        return {}

    if type(sweeps) is not list:
        if sweeps == -1:
            sweeps = list(range(radar0.nsweeps))
        else:
            sweeps = [sweeps]

    ext_data = dict()
    ext_data["coords"] = points
    ext_data["elevation_angle"] = radar0.fixed_angle["data"][sweeps].tolist()
    ext_data["date"] = list()
    ext_data["data"] = dict()
    ext_data["data"]["longitude"] = list()
    ext_data["data"]["latitude"] = list()
    ext_data["data"]["altitude"] = list()
    for field in fields:
        ext_data["data"][field] = list()

    fields_pars = getFieldsPiaFilterCmd(pia, filter, apply_cmd)
    fields_read = fields + fields_pars
    fields_read = list(dict.fromkeys(fields_read))

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

        fill_fields = dict()
        for field in fields:
            v_field = radar.fields[field]["data"]
            fill_fields[field] = v_field.filled(np.nan)

        s_lon = list()
        s_lat = list()
        s_alt = list()
        s_fields = dict()
        for field in fields:
            s_fields[field] = list()

        for swp in sweeps:
            sweep_slice = radar.get_slice(swp)
            lat, lon, alt = radar.get_gate_lat_lon_alt(swp, filter_transitions=True)

            p_lon = list()
            p_lat = list()
            p_alt = list()
            p_fields = dict()
            for field in fields:
                p_fields[field] = list()

            for pxy in points:
                ixy = (
                    np.square(lon - pxy["longitude"]) + np.square(lat - pxy["latitude"])
                ).argmin()
                p_lon = p_lon + [lon.flatten()[ixy]]
                p_lat = p_lat + [lat.flatten()[ixy]]
                p_alt = p_alt + [alt.flatten()[ixy]]
                for field in fields:
                    v_field = fill_fields[field].flatten()[ixy]
                    p_fields[field] = p_fields[field] + [v_field]

            s_lon = s_lon + [p_lon]
            s_lat = s_lat + [p_lat]
            s_alt = s_alt + [p_alt]
            for field in fields:
                s_fields[field] = s_fields[field] + [p_fields[field]]

        ext_data["data"]["longitude"] = ext_data["data"]["longitude"] + [s_lon]
        ext_data["data"]["latitude"] = ext_data["data"]["latitude"] + [s_lat]
        ext_data["data"]["altitude"] = ext_data["data"]["altitude"] + [s_alt]
        for field in fields:
            ext_data["data"][field] = ext_data["data"][field] + [s_fields[field]]

        temps = radarPolarTimeInfo(radar, time_zone)
        ext_data["date"] = ext_data["date"] + [temps["format"]]

    return ext_data
