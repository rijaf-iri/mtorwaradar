import numpy as np
import datetime
from dateutil import tz
# import matplotlib.pyplot as plt
from .create_qvp import create_qvp_data


def createQVP(
    dirMdvDate,
    start_time,
    end_time,
    fields,
    desired_angle=15.,
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
        out = out + [qvp]

    return out

def qvpTable(qpv):
    tab = list()
    for q in qvp:
        dat = q['data']
        fields = list(dat.keys())
        for field in fields:
            dat[field] = dat[field].filled(-9999)

        for j in range(len(q["height"])):
            x = {
                "time": q["time"],
                "elevation_angle": q['elevation'],
                "height": q["height"][j]
            }
            for field in fields:
                x[field] = dat[field][j]

            tab = tab + [x]

    return tab

