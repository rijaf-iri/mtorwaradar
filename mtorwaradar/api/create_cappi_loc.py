import os
import numpy as np
import datetime
from dateutil import tz
from netCDF4 import Dataset as ncdf
from .create_cappi import create_cappi_data


def createCAPPI(
    dirMdvDate,
    dirOUT,
    start_time,
    end_time,
    fields,
    cappi={
        "method": "composite_altitude",
        "pars": {"fun": "maximum", "min_alt": 1.7, "max_alt": 15},
    },
    apply_cmd=False,
    pia=None,
    dbz_fields=None,
    filter=None,
    filter_fields=None,
    time_zone="Africa/Kigali",
):
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
    if cappi["method"] == "composite_altitude":
        cappi_pars = {"fun": "maximum", "min_alt": 1.7, "max_alt": 15}
    else:
        cappi_pars = {"alt": 4.5}

    if "pars" in cappi:
        if cappi["method"] == "composite_altitude":
            d_name = list(cappi_pars.keys())
            c_name = list(cappi["pars"].keys())
            inm = [x in d_name for x in c_name]

            if any(inm):
                c_name = [i for (i, v) in zip(c_name, inm) if v]
                for n in c_name:
                    cappi_pars[n] = cappi["pars"][n]
        else:
            if "alt" not in cappi["pars"]:
                cappi_pars["alt"] = 4.5

    cappi["pars"] = cappi_pars

    #######
    if type(fields) is not list:
        fields = [fields]

    if dbz_fields is not None:
        if type(dbz_fields) is not list:
            dbz_fields = [dbz_fields]

    if filter_fields is not None:
        if type(filter_fields) is not list:
            filter_fields = [filter_fields]

    #######

    pars = {
        "cappi": cappi,
        "fields": fields,
        "apply_cmd": apply_cmd,
        "pia": pia,
        "dbz_fields": dbz_fields,
        "filter": filter,
        "filter_fields": filter_fields,
        "time_zone": time_zone,
    }

    #######

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

    #######

    for time in seqTime:
        don = create_cappi_data(dirMdvDate, None, time, pars)

        if not bool(don):
            print("No data, time:" + time + time_zone)
            continue

        # open a netCDF file to write
        out_ncfile = os.path.join(dirOUT, "cappi_" + don["time"]["format"] + ".nc")
        ncout = ncdf(out_ncfile, mode="w", format="NETCDF4")

        # define axis size
        ncout.createDimension("time", 1)
        ncout.createDimension("lat", len(don["lat"]))
        ncout.createDimension("lon", len(don["lon"]))

        # create time axis
        time = ncout.createVariable("time", np.float64, ("time",))
        time.long_name = "time"
        time.units = don["time"]["unit"]
        time.calendar = "standard"
        time.axis = "T"
        time[:] = don["time"]["value"]

        # create latitude axis
        lat = ncout.createVariable("lat", np.float32, ("lat"))
        lat.standard_name = "latitude"
        lat.long_name = "Latitude"
        lat.units = "degrees_north"
        lat.axis = "Y"
        lat[:] = don["lat"]

        # create longitude axis
        lon = ncout.createVariable("lon", np.float32, ("lon"))
        lon.standard_name = "longitude"
        lon.long_name = "Longitude"
        lon.units = "degrees_east"
        lon.axis = "X"
        lon[:] = don["lon"]

        # create variable
        for field in fields:
            var_field = ncout.createVariable(
                field,
                np.float32,
                ("time", "lat", "lon"),
                zlib=True,
                complevel=6,
            )
            var_field.long_name = field
            var_field.units = ""
            var_field.missing_value = -999.0
            vars_d = don["data"][field]
            var_field[0, :, :] = vars_d.filled(fill_value=-999.0)

        # global attributes
        ncout.description = "Constant Altitude Plan Position Indicator"
        ncout.close()

        print(
            "Creating CAPPI, time: "
            + don["time"]["format"]
            + " "
            + time_zone
            + " done."
        )
