from .radarpolar_extract import extract_polar_data


def extractRadarPolar(
    dirMdvDate,
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
    dirMdvDate: string
        full path to the folders containing the folders dates of the mdv files
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

    if pia is not None:
        if pia["method"] == "kdp":
            pia_pars = {"gamma": 0.8}
            if "pars" in pia:
                if "gamma" in pia["pars"]:
                    pia_pars["gamma"] = pia["pars"]["gamma"]
        else:
            pia_pars = {
                "a_max": 0.0002,
                "a_min": 0,
                "n_a": 10,
                "b_max": 0.7,
                "b_min": 0.65,
                "n_b": 6,
                "sector_thr": 10,
                "constraints": "none",
            }

            if "pars" in pia:
                if "constraints" in pia["pars"]:
                    pia_pars["constraints"] = pia["pars"]["constraints"]

                    if pia["pars"]["constraints"] == "dbz":
                        if "constraint_args_dbz" in pia["pars"]:
                            pia_pars["constraint_args_dbz"] = pia["pars"][
                                "constraint_args_dbz"
                            ]
                        else:
                            pia_pars["constraint_args_dbz"] = 60

                    if pia["pars"]["constraints"] == "pia":
                        if "constraint_args_pia" in pia["pars"]:
                            pia_pars["constraint_args_pia"] = pia["pars"][
                                "constraint_args_pia"
                            ]
                        else:
                            pia_pars["constraint_args_pia"] = 20

                    if pia["pars"]["constraints"] == "both":
                        if "constraint_args_dbz" in pia["pars"]:
                            pia_pars["constraint_args_dbz"] = pia["pars"][
                                "constraint_args_dbz"
                            ]
                        else:
                            pia_pars["constraint_args_dbz"] = 60

                        if "constraint_args_pia" in pia["pars"]:
                            pia_pars["constraint_args_pia"] = pia["pars"][
                                "constraint_args_pia"
                            ]
                        else:
                            pia_pars["constraint_args_pia"] = 20

                d_name = [
                    "a_max",
                    "a_min",
                    "n_a",
                    "b_max",
                    "b_min",
                    "n_b",
                    "sector_thr",
                ]
                p_name = list(pia["pars"].keys())
                inm = [x in d_name for x in pia["pars"]]
                if any(inm):
                    p_name = [i for (i, v) in zip(p_name, inm) if v]
                    for n in p_name:
                        pia_pars[n] = pia["pars"][n]

        pia["pars"] = pia_pars

    #######
    if filter is not None:
        if filter["method"] == "median_filter_censor":
            filter_pars = {
                "median_filter_len": 5,
                "minsize_seq": 3,
                "censor_field": "RHOHV",
                "censor_thres": 0.8,
            }
        elif filter["method"] == "median_filter":
            filter_pars = {"median_filter_len": 5, "minsize_seq": 3}
        else:
            filter_pars = {"window_len": 5, "window": "hanning"}

        ##
        d_name = list(filter_pars.keys())
        if "pars" in filter:
            f_name = list(filter["pars"].keys())
            inm = [x in d_name for x in f_name]
            if any(inm):
                f_name1 = [i for (i, v) in zip(f_name, inm) if v]
                for n in f_name1:
                    filter_pars[n] = filter["pars"][n]

            if filter["method"] == "median_filter_censor":
                if "censor_field" in f_name:
                    if "censor_thres" not in f_name:
                        if filter["pars"]["censor_field"] == "RHOHV":
                            filter_pars["censor_thres"] = 0.8
                        elif filter["pars"]["censor_field"] == "NCP":
                            filter_pars["censor_thres"] = 0.5
                        else:
                            filter_pars["censor_thres"] = 3

        ##
        filter["pars"] = filter_pars

    #######

    return extract_polar_data(
        dirMDV=dirMdvDate,
        source=None,
        start_time=start_time,
        end_time=end_time,
        fields=fields,
        points=points,
        sweeps=sweeps,
        pia=pia,
        dbz_fields=dbz_fields,
        filter=filter,
        filter_fields=filter_fields,
        apply_cmd=apply_cmd,
        time_zone=time_zone,
    )
