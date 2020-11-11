import numpy as np
import pyart
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

from ..util.utilities import npmDarray_to_rFloatVector, rFloatVector_to_npmDarray

mtrwdata = importr('mtorwdata')

def cart_xsec_data(grid, field, points, res = 500):
    """
    grid: radar grid
    points: [[start_alt, start_lon], [end_lat, end_lon]]
    res: resolution of the input data (in meter)
    """
    xr = grid.y['data']
    yr = grid.y['data']
    zr = grid.z['data']
    data = grid.fields[field]['data']

    projection = grid.get_projparams()
    lon, lat = pyart.core.cartesian_to_geographic(xr, yr, projection)

    xr, yr = np.meshgrid(xr, yr)
    lon, lat = np.meshgrid(lon, lat)

    #####
    dist1 = (lon - points[0][1])**2 + (lat - points[0][0])**2
    ix1, iy1 = np.where(dist1 == dist1.min())
    xpt1 = xr[ix1, iy1]
    ypt1 = yr[ix1, iy1]

    dist2 = (lon - points[1][1])**2 + (lat - points[1][0])**2
    ix2, iy2 = np.where(dist2 == dist2.min())
    xpt2 = xr[ix2, iy2]
    ypt2 = yr[ix2, iy2]

    dy = ypt1 - ypt2
    dx = xpt1 - xpt2
    slp = dy/dx
    intr = ypt1 - slp * xpt1

    dst = np.sqrt(dx**2 + dy**2)
    nbx = int(dst/res)

    xmin = min(xpt1, xpt2)
    xmax = max(xpt1, xpt2)

    #####
    ix, iy = np.where(abs(yr - slp * xr - intr) <= res)
    ii = np.logical_and(xr[ix, iy] >= xmin, xr[ix, iy] <= xmax)
    ix = ix[ii]
    iy = iy[ii]

    v = data[:, ix, iy]
    v = np.ma.filled(v, np.nan)
    x, z = np.meshgrid(xr[ix, iy], zr)
    y, z = np.meshgrid(yr[ix, iy], zr)

    x = npmDarray_to_rFloatVector(x)
    y = npmDarray_to_rFloatVector(y)
    z = npmDarray_to_rFloatVector(z)
    v = npmDarray_to_rFloatVector(v)

    #####
    x_g = np.linspace(xmin, xmax, nbx)
    x_g = x_g.flatten()
    y_g = intr + slp * x_g

    dst = np.sqrt((x_g - x_g[0])**2 + (y_g - y_g[0])**2)
    dst = np.round(dst, 2)
    dst, zh = np.meshgrid(dst, zr)
    dst = dst/1000.
    zh = zh/1000.

    x_g, z_g = np.meshgrid(x_g, zr)
    y_g, z_g = np.meshgrid(y_g, zr)

    x_g = npmDarray_to_rFloatVector(x_g)
    y_g = npmDarray_to_rFloatVector(y_g)
    z_g = npmDarray_to_rFloatVector(z_g)

    #####
    v_out = mtrwdata.interp3d_xsec(x, y, z, v, x_g, y_g, z_g)
    v_out = rFloatVector_to_npmDarray(v_out, dst.shape)
    v_out = np.ma.masked_where(np.isnan(v_out), v_out)

    if xpt1 > xpt2:
        v_out = np.flip(v_out, axis = 1)

    data = {'x': dst, 'z': zh, 'data': v_out}

    return data
