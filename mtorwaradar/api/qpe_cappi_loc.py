import os
import numpy as np
import datetime
from dateutil import tz
from netCDF4 import Dataset as ncdf
from .qpe_cappi import compute_cappi_qpe


def computeCAPPIQPE(
    dirMdvDate,
    dirOUT,
    start_time,
    end_time,
    cappi={
        "method": "composite_altitude",
        "pars": {"fun": "maximum", "min_alt": 1.7, "max_alt": 15},
    },
    qpe={"method": "RATE_Z", "pars": {"alpha": 300, "beta": 1.4, "invCoef": False}},
    dbz_thres={"min": 20, "max": 65},
    apply_cmd=True,
    pia=None,
    filter=None,
    time_zone="Africa/Kigali",
):
    #######
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
    if qpe["method"] == "RATE_Z":
        qpe_pars = {"alpha": 300, "beta": 1.4, "invCoef": False}
    elif qpe["method"] == "RATE_Z_ZDR":
        qpe_pars = {"alpha": 0.00786, "beta_zh": 0.967, "beta_zdr": -4.98}
    elif qpe["method"] == "RATE_KDP":
        qpe_pars = {"alpha": 53.3, "beta": 0.669}
    elif qpe["method"] == "RATE_KDP_ZDR":
        qpe_pars = {"alpha": 192, "beta_kdp": 0.946, "beta_zdr": -3.45}
    else:
        qpe_pars = None

    if "pars" in qpe:
        if qpe["method"] == "RATE_ZPOLY":
            qpe_pars = None
        else:
            d_name = list(qpe_pars.keys())
            q_name = list(qpe["pars"].keys())
            inm = [x in d_name for x in q_name]

            if any(inm):
                q_name = [i for (i, v) in zip(q_name, inm) if v]
                for n in q_name:
                    qpe_pars[n] = qpe["pars"][n]

    qpe["pars"] = qpe_pars

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

    for time in seqTime:
        pars = {
            "cappi": cappi,
            "qpe": qpe,
            "dbz_thres": dbz_thres,
            "pia": pia,
            "filter": filter,
            "apply_cmd": apply_cmd,
            "time_zone": time_zone,
        }

        data = compute_cappi_qpe(dirMdvDate, time, pars)
        if not bool(data):
            print("No data, time:" + time + time_zone)
            continue

        # open a netCDF file to write
        out_ncfile = os.path.join(dirOUT, "precip_" + data["time"]["format"] + ".nc")
        ncout = ncdf(out_ncfile, mode="w", format="NETCDF4")

        # define axis size
        ncout.createDimension("time", 1)
        ncout.createDimension("lat", len(data["lat"]))
        ncout.createDimension("lon", len(data["lon"]))

        # create time axis
        time = ncout.createVariable("time", np.float64, ("time",))
        time.long_name = "time"
        time.units = data["time"]["unit"]
        time.calendar = "standard"
        time.axis = "T"
        time[:] = data["time"]["value"]

        # create latitude axis
        lat = ncout.createVariable("lat", np.float32, ("lat"))
        lat.standard_name = "latitude"
        lat.long_name = "Latitude"
        lat.units = "degrees_north"
        lat.axis = "Y"
        lat[:] = data["lat"]

        # create longitude axis
        lon = ncout.createVariable("lon", np.float32, ("lon"))
        lon.standard_name = "longitude"
        lon.long_name = "Longitude"
        lon.units = "degrees_east"
        lon.axis = "X"
        lon[:] = data["lon"]

        # create variable
        rate = ncout.createVariable(
            data["qpe"]["rate"]["name"],
            np.float32,
            ("time", "lat", "lon"),
            zlib=True,
            complevel=6,
        )
        rate.long_name = data["qpe"]["rate"]["long_name"]
        rate.units = data["qpe"]["rate"]["unit"]
        rr_rate = data["qpe"]["rate"]["data"]
        rate[0, :, :] = rr_rate.filled(fill_value=0.0)

        precip = ncout.createVariable(
            data["qpe"]["precip"]["name"],
            np.float32,
            ("time", "lat", "lon"),
            zlib=True,
            complevel=6,
        )
        precip.long_name = data["qpe"]["precip"]["long_name"]
        precip.units = data["qpe"]["precip"]["unit"]
        rr_precip = data["qpe"]["precip"]["data"]
        precip[0, :, :] = rr_precip.filled(fill_value=0.0)

        # global attributes
        ncout.description = "Quantitative Precipitation Estimation"
        ncout.close()

        print(
            "Computing QPE, time: "
            + data["time"]["format"]
            + " "
            + time_zone
            + " done."
        )
