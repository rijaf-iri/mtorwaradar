import pyart
import numpy as np
import copy

import rpy2.robjects as robjects
import rpy2.robjects.vectors as rvect
from rpy2.robjects.packages import importr

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

from ..mdv.creategrid import create_grid_from_radar
from ..mdv.projdata import grid_coordsGeo, polar_coordsGeo3d
from ..util.utilities import rFloatVector_to_npmDarray

mtrwdata = importr("mtorwdata")


def create_cappi_grid(radar, fields=["DBZ_F"], cappi="one_altitude", param_cappi=4.5):
    """
    Create CAPPI (Constant Altitude Plan Position Indicator)
    radar:
        pyart radar polar object
    fields: list
        list of fields to be used to compute the qpe
    cappi: string
        Method used to create the CAPPI, available options are
        'one_altitude': create CAPPI by interpolating the radar polar at a given altitude
        'composite_altitude': create CAPPI by computing the maximum, average or median
                              between 2 given altitudes after converting the radar polar to a regular grid
        'ppi_ranges': create a pseudo CAPPI at a given altitude by using each elevation angle
                      at a particular distance from the radar
    param_cappi:
        Parameters to be used to compute the CAPPI
        'one_altitude': float
            Value of the altitude at which the CAPPI will be created
        'composite_altitude': dictionary
            A dictionary with keys 'fun', 'min_alt' and 'max_alt' representing the function,
            the minimum and maximum of the altitude (in km) to be used to create the CAPPI.
            The available options for 'fun' are: 'maximum', 'average' and 'median'.
            Example: param_cappi={'fun': 'maximum', 'min_alt': 1.7, 'max_alt': 15.}
        'ppi_ranges': float
            Value of the altitude at which the pseudo CAPPI will be created

    Returns: lon, lat, data
        lon: 1d numpy array
        lat: 1d numpy array
        data: dictionary of the fields containing the data, 2d numpy masked ndarray
    """
    if cappi == "ppi_ranges":
        lon, lat, data = ppi_ranges_cappi_data(radar, param_cappi, fields)
    elif cappi == "one_altitude":
        grid_shape = (1, 800, 800)
        z_lim = (param_cappi * 1000.0, param_cappi * 1000.0)
        constant_roi = 3000.0
        grid = create_grid_from_radar(
            radar, fields, grid_shape=grid_shape, z_lim=z_lim, constant_roi=constant_roi
        )
        lon, lat = grid_coordsGeo(grid)

        data = dict()
        for field in fields:
            data[field] = grid.fields[field]["data"][0, :, :]
    else:
        lev = np.arange(
            param_cappi["min_alt"] * 1000, param_cappi["max_alt"] * 1000, 500
        )
        grid_shape = (len(lev), 800, 800)
        z_lim = (lev[0], lev[len(lev) - 1])
        constant_roi = 1500.0
        grid = create_grid_from_radar(
            radar, fields, grid_shape=grid_shape, z_lim=z_lim, constant_roi=constant_roi
        )
        lon, lat = grid_coordsGeo(grid)

        data = dict()
        for field in fields:
            if param_cappi["fun"] == "maximum":
                fun = np.amax
            elif param_cappi["fun"] == "average":
                fun = np.nanmean
            elif param_cappi["fun"] == "median":
                fun = np.nanmedian
            else:
                fun = np.amax

            data[field] = fun(grid.fields[field]["data"], axis=0)

    return lon, lat, data


def ppi_ranges_cappi_data(radar, alt_cappi, fields):
    """
    Create pseudo CAPPI from each elevation angle
    radar:
        pyart radar polar object
    alt_cappi: float
        Value of the altitude at which the CAPPI will be created
    fields: list
        list of fields to be used to compute the qpe

    Returns: lon, lat, data
        lon: 1d numpy array
        lat: 1d numpy array
        data: dictionary of the fields containing the data, 2d numpy masked ndarray
    """
    rg = radar.range["data"] / 1000
    azimuth0 = np.arange(0, radar.nrays, 360)
    fill_value = radar.fields[fields[0]]["data"].fill_value

    start = azimuth0
    end = np.append(azimuth0[np.arange(1, len(azimuth0))], radar.nrays)
    pcappi = ppi_ranges_cappi(radar, alt_cappi)
    lon, lat, z = polar_coordsGeo3d(radar)

    mat = copy.copy(lon)
    mat = mat[slice(start[0], end[0])]
    mat[:] = np.nan
    xlon = copy.copy(mat)
    ylat = copy.copy(mat)
    data = dict()
    for field in fields:
        data[field] = copy.copy(mat)

    for j in np.arange(len(azimuth0)):
        ix = slice(start[j], end[j])
        xlo = lon[ix]
        xla = lat[ix]
        xdat = dict()
        for field in fields:
            xdat[field] = radar.fields[field]["data"][ix]

        if j == 0:
            ixR = np.where(rg >= pcappi[j][0])
        elif j == len(azimuth0) - 1:
            ixR = np.where(rg <= pcappi[j - 1][0])
        else:
            ixR = np.where((rg <= pcappi[j - 1][0]) & (rg >= pcappi[j][0]))

        xlon[:, ixR] = xlo[:, ixR]
        ylat[:, ixR] = xla[:, ixR]
        for field in fields:
            fill_val = xdat[field].fill_value
            data[field][:, ixR] = xdat[field][:, ixR]
            xx = data[field]
            data[field] = np.ma.masked_where(xx == fill_val, xx)

    for field in fields:
        data[field] = np.ma.masked_invalid(data[field])

    ########
    xgrd = np.linspace(-199750.0, 199750.0, 800)
    ygrd = np.linspace(-199750.0, 199750.0, 800)
    projection = {
        "proj": "pyart_aeqd",
        "lon_0": radar.longitude["data"][0],
        "lat_0": radar.latitude["data"][0],
    }
    lon, lat = pyart.core.cartesian_to_geographic(xgrd, ygrd, projection)
    nx = len(lon)
    ny = len(lat)

    g_lon = robjects.FloatVector(lon)
    g_lat = robjects.FloatVector(lat)

    x_lon = robjects.FloatVector(xlon.flatten())
    y_lat = robjects.FloatVector(ylat.flatten())
    x_data = dict()

    for field in fields:
        xdat = data[field]
        xdat = xdat.filled(np.nan)
        x_data[field] = robjects.FloatVector(xdat.flatten())

    x_data = rvect.ListVector(x_data)

    ########
    out = mtrwdata.interp_ppi_ranges_cappi(x_lon, y_lat, x_data, g_lon, g_lat)
    out = dict(zip(out.names, out))
    out_data = dict()
    for field in fields:
        xdat = out[field]
        xdat = rFloatVector_to_npmDarray(xdat, (nx, ny))
        xdat = xdat.transpose()
        xdat = np.ma.masked_invalid(xdat)
        xdat.fill_value = fill_value
        out_data[field] = xdat

    return lon, lat, out_data


def ppi_ranges_cappi_plot(radar, alt_cappi, alt_max=7.5):
    """
    Plot pseudo CAPPI from each elevation angle
    radar:
        pyart radar polar object
    alt_cappi: float
        Value of the altitude at which the CAPPI will be created
    alt_max: float
        The maximum altitude to display on the plot

    Returns: figure, axes
        figure: figure object of type matplotlib.figure.Figure
        axes: axes object of type matplotlib.axes._subplots.AxesSubplot
    """
    pcappi = ppi_ranges_cappi(radar, alt_cappi)
    elv_angle = radar.fixed_angle["data"]
    rg = radar.range["data"] / 1000
    alt = (radar.gate_z["data"] + radar.altitude["data"]) / 1000

    yymax = np.repeat(alt_max, len(rg))
    azimuth0 = np.arange(0, radar.nrays, 360)

    ######
    fig, ax = plt.subplots()

    for j in azimuth0:
        plt.plot(rg, alt[j, :], color="gray", linestyle="solid", linewidth=1.5)

    for j in np.arange(len(azimuth0) - 1):
        if j == 0:
            ixR = np.where(rg >= pcappi[j][0])
        else:
            ixR = np.where((rg <= pcappi[j - 1][0]) & (rg >= pcappi[j][0]))

        yalt = alt[azimuth0[j], :][ixR]
        plt.plot(rg[ixR], yalt, color="black", linestyle="solid", linewidth=2)
        plt.plot(
            [pcappi[j][0], pcappi[j][0]],
            [pcappi[j][1], pcappi[j][2]],
            color="black",
            linestyle="solid",
            linewidth=2,
        )

        ixR = np.where(rg <= pcappi[len(azimuth0) - 2][0])
        yalt = alt[azimuth0[-1], :][ixR]
        plt.plot(rg[ixR], yalt, color="black", linestyle="solid", linewidth=2)

    for j in np.arange(len(azimuth0) - 1, 0, -1):
        txt = str(elv_angle[j]) + "°"
        yy = alt[azimuth0[j], :]
        idx = np.argwhere(np.diff(np.sign(yymax - yy))).flatten()
        ax.text(
            rg[idx],
            alt_max + 0.1,
            txt,
            rotation=90,
            fontsize=8,
            ha="center",
            va="bottom",
        )

    txt = str(elv_angle[0]) + "°"
    idx = len(rg) - 1
    ax.text(
        rg[idx],
        alt[0, :][idx] + 0.1,
        txt,
        rotation=90,
        fontsize=8,
        ha="center",
        va="bottom",
    )

    ax.set_ylim(0, alt_max)
    ax.axhline(y=alt_cappi, color="red", linestyle="dashed", linewidth=1.5)

    trans = transforms.blended_transform_factory(
        ax.get_yticklabels()[0].get_transform(), ax.transData
    )
    ax.text(
        0,
        alt_cappi,
        str(alt_cappi),
        color="red",
        transform=trans,
        ha="right",
        va="center",
    )

    plt.xlabel("Distance from radar (km)")
    plt.ylabel("Altitude (km)")
    plt.grid(True)

    return fig, ax


def ppi_ranges_cappi(radar, alt_cappi):
    """
    Create pseudo CAPPI from each elevation angle
    radar:
        pyart radar polar object
    alt_cappi: float
        Value of the altitude at which the CAPPI will be created

    Returns:
        List of lists containing the start range and start altitude for below elevation angle
        and end altitude for above elevation angle
        [
         [start range elev_angle_below (km),
          start altitude elev_angle_below (km),
          end altitude elev_angle_above (km)],
           .....
        ]
    """
    rg = radar.range["data"] / 1000
    alt = (radar.gate_z["data"] + radar.altitude["data"]) / 1000
    azimuth0 = np.arange(0, radar.nrays, 360)

    ycappi = np.repeat(alt_cappi, len(rg))

    param_cappi = [[]] * (len(azimuth0) - 1)

    for j in np.arange(len(azimuth0) - 1):
        yalt0 = alt[azimuth0[j], :]
        ix0 = np.argwhere(np.diff(np.sign(ycappi - yalt0))).flatten()
        yalt1 = alt[azimuth0[j + 1], :]
        ix1 = np.argwhere(np.diff(np.sign(ycappi - yalt1))).flatten()

        ixR = np.where((rg < rg[ix0]) & (rg > rg[ix1]))
        ixR = ixR[0]

        idRg = None
        for i in np.arange(len(ixR)):
            h0 = alt_cappi - yalt0[ixR[i]]
            h1 = yalt1[ixR[i]] - alt_cappi

            if (h0 - h1) < 0:
                idRg = ixR[i - 1]
                break

        param_cappi[j] = list([rg[idRg], yalt0[idRg], yalt1[idRg]])

    return param_cappi
