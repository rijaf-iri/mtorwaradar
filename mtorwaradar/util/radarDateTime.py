
import datetime
import os
import re
from .utilities import ArgumentError

def get_mdv_time(radar):
    t_origin = radar.time['units'].split()
    t_origin = [x.strip() for x in t_origin]
    t_origin = [x for x in t_origin if x != '']
    t_origin = t_origin[-1]
    t_origin = datetime.datetime.strptime(t_origin, '%Y-%m-%dT%H:%M:%SZ')
    temps = [t_origin + datetime.timedelta(seconds = x) for x in radar.time['data']]

    return temps

def polar_mdv_last_time(radar):
    temps = get_mdv_time(radar)

    return temps[-1].strftime('%Y-%m-%d %H:%M:%S UTC')

def grid_mdv_time(grid):
    temps = get_mdv_time(grid)

    return temps[0].strftime('%Y-%m-%d %H:%M:%S UTC')

def mdv_nearest_time_file(dirMDV, time):
    t0 = datetime.datetime.strptime(time, '%Y-%m-%d-%H-%M')

    daty = []
    daty = daty + [t0 + datetime.timedelta(seconds = -5 * 60)]
    daty = daty + [t0]
    daty = daty + [t0 + datetime.timedelta(seconds = 5 * 60)]

    heure = [x.strftime("%Y%m%d%H") for x in daty]
    heure = list(set(heure))
    heure = [datetime.datetime.strptime(t, '%Y%m%d%H') for t in heure]

    jr = [x.strftime("%Y%m%d") for x in heure]
    hr = [x.strftime("%H") for x in heure]

    dt = []
    for i in range(len(jr)):
        d = jr[i]
        pattern = '^' + hr[i] + '.+\\.mdv$'
        ddir = os.path.join(dirMDV, d)
        if not os.path.isdir(ddir):
            continue
        ff = [os.path.splitext(d + f)[0] for f in os.listdir(ddir) if re.match(pattern, f)]
        dt = dt + ff

    if len(dt) == 0:
        return None

    dt = [datetime.datetime.strptime(t, '%Y%m%d%H%M%S') for t in dt]
    dt = [t for t in dt if daty[0] <= t <= daty[2]]

    if len(dt) == 0:
        return None

    tr = min(dt, key=lambda x: abs(x - t0))

    return [tr.strftime("%Y%m%d"), tr.strftime("%H%M%S")]

def mdv_end_time_file(dirMDV, time):
    t0 = datetime.datetime.strptime(time, '%Y-%m-%d-%H-%M')
    daty = [t0] + [t0 + datetime.timedelta(seconds = 5 * 60)]

    heure = [x.strftime("%Y%m%d%H") for x in daty]
    heure = list(set(heure))
    heure = [datetime.datetime.strptime(t, '%Y%m%d%H') for t in heure]

    jr = [x.strftime("%Y%m%d") for x in heure]
    hr = [x.strftime("%H") for x in heure]

    dt = []
    for i in range(len(jr)):
        d = jr[i]
        pattern = '^' + hr[i] + '.+\\.mdv$'
        ddir = os.path.join(dirMDV, d)
        if not os.path.isdir(ddir):
            continue
        ff = [os.path.splitext(d + f)[0] for f in os.listdir(ddir) if re.match(pattern, f)]
        dt = dt + ff

    if len(dt) == 0:
        return None

    dt = [datetime.datetime.strptime(t, '%Y%m%d%H%M%S') for t in dt]
    dt = [t for t in dt if t0 <= t <= daty[1]]

    if len(dt) == 0:
        return None

    dt.sort()
    tr = dt[0]

    return [tr.strftime("%Y%m%d"), tr.strftime("%H%M%S")]

def mdv_seq_times_files(dirMDV, start_time, end_time, times = "end"):
    t0 = datetime.datetime.strptime(start_time, '%Y-%m-%d-%H-%M')
    t1 = datetime.datetime.strptime(end_time, '%Y-%m-%d-%H-%M')

    time_range = t1 - t0
    nb_seconds = time_range.days * 86400 + time_range.seconds + 300
    time_list = [t0 + datetime.timedelta(seconds = x) for x in range(0, nb_seconds, 300)]
    time_list = [x.strftime('%Y-%m-%d-%H-%M') for x in time_list]

    if times == "end":
        foo = mdv_end_time_file
    elif times == "nearest":
        foo = mdv_nearest_time_file
    else:
        raise ArgumentError("'times' must be 'end' or 'nearest'")

    mdvdates = [foo(dirMDV, t) for t in time_list]
    mdvdates = [x for x in mdvdates if x]
    if len(mdvdates) == 0:
        mdvdates = None

    return mdvdates

def round_5minutes(time):
    mn = int(time.strftime('%M'))
    divm = mn % 5
    if divm != 0:
        mn = mn - divm
    daty = time.strftime('%Y-%m-%d-%H')
    daty = daty + '-' + str(mn)

    return datetime.datetime.strptime(daty, '%Y-%m-%d-%H-%M')
