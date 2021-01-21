import numpy as np
import datetime
from dateutil import tz
import copy
from .create_qvp import create_qvp_data


def createQVP(
    dirMdvDate,
    start_time,
    end_time,
    fields,
    desired_angle=15.0,
    time_zone="Africa/Kigali",
):
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

    out = list()
    for time in seqTime:
        qvp = create_qvp_data(dirMdvDate, None, time, fields, desired_angle, time_zone)
        if bool(qvp):
            out = out + [qvp]

    return out


def qvpTable(qvp):
    tab = list()
    for q in qvp:
        dat = copy.copy(q["data"])
        fields = list(dat.keys())
        for field in fields:
            tmp = dat[field].filled(-9999)
            dat[field] = tmp

        for j in range(len(q["height"])):
            x = {
                "time": q["time"],
                "elevation_angle": q["elevation"],
                "height": q["height"][j],
            }
            for field in fields:
                x[field] = dat[field][j]

            tab = tab + [x]

    return tab


def qvpMeshgrid(qvp):
    time = [q["time"] for q in qvp]
    time = [datetime.datetime.strptime(x, "%Y%m%d%H%M%S") for x in time]
    time = np.array(time)

    Z = qvp[0]["height"]
    dat = copy.copy(qvp[0]["data"])
    fields = list(dat.keys())
    for field in fields:
        dat[field] = dat[field].filled(-9999.0)

    for tt in range(1, len(qvp)):
        Z = np.column_stack((Z, qvp[tt]["height"]))
        tmp = copy.copy(qvp[tt]["data"])
        for field in fields:
            tmp[field] = tmp[field].filled(-9999.0)
            dat[field] = np.column_stack((dat[field], tmp[field]))

    for field in fields:
        dat[field] = np.ma.masked_where(dat[field] == -9999.0, dat[field])

    T, _ = np.meshgrid(time, Z[:, 0])
    Z = Z / 1000

    out = {"time": T, "height": Z}
    for field in fields:
        out[field] = dat[field]

    return out
