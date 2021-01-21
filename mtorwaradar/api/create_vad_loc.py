import numpy as np
import datetime
from dateutil import tz
import matplotlib.pyplot as plt
from .create_vad import create_vad_data


def createVAD(
    dirMdvDate,
    start_time,
    end_time,
    heights=None,
    vel_field="VEL_F",
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

    #######
    if heights is None:
        heights = [0, 10000, 100]
    z_want = np.arange(heights[0], heights[1], heights[2])

    out = list()
    for time in seqTime:
        vad = create_vad_data(dirMdvDate, None, time, z_want, vel_field, time_zone)
        out = out + [vad]

    return out


def vadTable(vad):
    tab = list()
    for v in vad:
        for j in range(len(v["height"])):
            x = {
                "time": v["time"],
                "height": v["height"][j],
                "speed": v["speed"][j],
                "direction": v["direction"][j],
                "u_wind": v["u_wind"][j],
                "v_wind": v["v_wind"][j],
            }
            tab = tab + [x]

    return tab


def vadProfile(vad, index_time, sample=None):
    u = vad[index_time]["u_wind"]
    v = vad[index_time]["v_wind"]
    z = vad[index_time]["height"] / 1000
    time = vad[index_time]["time"]
    time = datetime.datetime.strptime(time, "%Y%m%d%H%M%S")
    time = time.strftime("%Y-%m-%d %H:%M:%S")

    if sample is None:
        step = 1
    else:
        step = sample

    iz = np.arange(0, len(z), step)
    xb, yb = np.meshgrid(0, z[iz])
    ub = u[iz]
    vb = v[iz]

    fig, ax = plt.subplots()
    plt.grid(True)

    ax.plot(u, z, label="U Wind")
    ax.plot(v, z, label="V Wind")

    ax.axvline(0, color="k")
    ax.legend(loc=2)

    ax.barbs(xb, yb, ub, vb)

    plt.title("Velocity Azimuth Display " + time, fontsize=12)
    plt.xlabel("Wind Speed (m/s)")
    plt.ylabel("Heights (km)")

    return fig, ax


def vadBarb(vad, sample=None):
    time = [v["time"] for v in vad]
    time = [datetime.datetime.strptime(x, "%Y%m%d%H%M%S") for x in time]
    time = np.array(time)

    Z = vad[0]["height"]
    U = vad[0]["u_wind"]
    V = vad[0]["v_wind"]

    if sample is None:
        step = 1
    else:
        step = sample

    iz = np.arange(0, len(Z), step)

    Z = Z[iz]
    U = U[iz]
    V = V[iz]
    for tt in range(1, len(vad)):
        # Z = np.vstack((Z, vad[tt]['height'][iz]))
        # U = np.vstack((U, vad[tt]['u_wind'][iz]))
        # V = np.vstack((V, vad[tt]['v_wind'][iz]))
        Z = np.column_stack((Z, vad[tt]["height"][iz]))
        U = np.column_stack((U, vad[tt]["u_wind"][iz]))
        V = np.column_stack((V, vad[tt]["v_wind"][iz]))

    T, _ = np.meshgrid(time, Z[:, 0])

    Z = Z / 1000

    fig, ax = plt.subplots()
    ax.barbs(T, Z, U, V)
    plt.xlabel("Time")
    plt.ylabel("Heights (km)")

    return fig, ax


def vadQuiver(vad, sample=None, color=False):
    time = [v["time"] for v in vad]
    time = [datetime.datetime.strptime(x, "%Y%m%d%H%M%S") for x in time]
    time = np.array(time)

    Z = vad[0]["height"]
    U = vad[0]["u_wind"]
    V = vad[0]["v_wind"]

    if sample is None:
        step = 1
    else:
        step = sample

    iz = np.arange(0, len(Z), step)

    Z = Z[iz]
    U = U[iz]
    V = V[iz]
    for tt in range(1, len(vad)):
        Z = np.column_stack((Z, vad[tt]["height"][iz]))
        U = np.column_stack((U, vad[tt]["u_wind"][iz]))
        V = np.column_stack((V, vad[tt]["v_wind"][iz]))

    T, _ = np.meshgrid(time, Z[:, 0])

    Z = Z / 1000

    fig, ax = plt.subplots()
    if color:
        M = np.hypot(U, V)
        qui = ax.quiver(T, Z, U, V, M)
    else:
        qui = ax.quiver(T, Z, U, V)

    plt.quiverkey(
        qui,
        X=0.9,
        Y=1.05,
        U=1,
        label="1 m/s",
        labelpos="E",
        fontproperties={"weight": "bold"},
    )
    plt.xlabel("Time")
    plt.ylabel("Heights (km)")

    return fig, ax, qui
