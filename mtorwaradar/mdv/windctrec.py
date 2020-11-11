import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

from .projdata import grid_coordsGeo
from ..util.utilities import npmDarray_to_rFloatVector, rFloatVector_to_npmDarray, uv_to_wind

mtrwdata = importr('mtorwdata')

def get_uv_ctrec(grid):
    lon, lat = grid_coordsGeo(grid)
    u_comp = grid.fields['U comp']['data'][0, :, :]
    v_comp = grid.fields['V comp']['data'][0, :, :]

    return lon, lat, u_comp, v_comp

def regrid_wind_ctrec(grid, res_x = 0.1, res_y = 0.1):
    """ 
    Original resolution 500 meter or 0.0044936 degree.
    res_x: resolution in degree decimal for x
    res_y: resolution in degree decimal for y
    """

    lon, lat, u_comp, v_comp = get_uv_ctrec(grid)
    fill_value = u_comp.fill_value
    u_comp = np.ma.filled(u_comp, np.nan)
    v_comp = np.ma.filled(v_comp, np.nan)

    x_d = robjects.FloatVector(lon)
    y_d = robjects.FloatVector(lat)
    u_d = npmDarray_to_rFloatVector(u_comp)
    v_d = npmDarray_to_rFloatVector(v_comp)

    nx = round(np.ptp(lon)/res_x)
    ny = round(np.ptp(lat)/res_y)
    lon_new = np.linspace(lon.min(), lon.max(), nx)
    lat_new = np.linspace(lat.min(), lat.max(), ny)

    x_g = robjects.FloatVector(lon_new)
    y_g = robjects.FloatVector(lat_new)

    u_out = mtrwdata.interp_surface_grid(x_d, y_d, u_d, x_g, y_g)
    v_out = mtrwdata.interp_surface_grid(x_d, y_d, v_d, x_g, y_g)

    u_out = rFloatVector_to_npmDarray(u_out, (nx, ny))
    v_out = rFloatVector_to_npmDarray(v_out, (nx, ny))

    u_out = np.ma.masked_where(np.isnan(u_out), u_out)
    v_out = np.ma.masked_where(np.isnan(v_out), v_out)
    u_out.fill_value = fill_value
    v_out.fill_value = fill_value

    x_m, y_m = np.meshgrid(lon_new, lat_new)

    return x_m, y_m, u_out, v_out

def get_wind_ctrec(grid, res_x = 0.1, res_y = 0.1):
    """ Original resolution 500 meter or 0.0044936 degree.
    res_x: resolution in degree decimal for x
    res_y: resolution in degree decimal for y
    """

    x, y, u, v = regrid_wind_ctrec(grid, res_x, res_y)
    ws, wd = uv_to_wind(u, v)

    s_v = ws.flatten().data
    d_v = wd.flatten().data

    msk1 = u.flatten().mask
    msk2 = v.flatten().mask
    msk3 = np.ma.masked_where(s_v < 0.1, s_v).mask
    ix = np.where(np.logical_not(msk1 | msk2 | msk3))
    if len(ix[0]) == 0:
        return None

    x_v = x.flatten()[ix]
    y_v = y.flatten()[ix]
    s_v = np.round(s_v[ix], 1)
    d_v = np.round(d_v[ix], 1)

    return np.column_stack((x_v, y_v, s_v, d_v))
