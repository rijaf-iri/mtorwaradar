
import pyart
import numpy as np

def echo_tops_array(data, alt, thres):
    """
    Compute echo tops from reflectivity data

    Echo top is derived from reflectivity data. It's an estimate of the highest altitude
    where the value of dBZ exceeds a specified threshold. 

    Parameters
    ----------
    data: array
        The DBZ field data. A 3D numpy masked array
        With shape (z, y, x)
    alt: list
        List of the altitude in km. Same length of the first dimension of data
    thres: float
        The DBZ threshold to be used

    Returns
    -------
    echo_tops: array
        A 2D numpy masked array containing the echo top. Units: km
    """

    arr_thres = data >= thres
    arr_index = np.empty(arr_thres.shape)
    arr_index[:]= -1

    for lev in range(arr_thres.shape[0]):
        arr_index[lev, arr_thres[lev, :, :]] = lev

    arr_index = np.ma.masked_where(arr_index == -1, arr_index)
    arr_mask = np.logical_and.reduce(arr_index.mask)
    index = np.argmax(arr_index, axis=0)

    lev = list(range(len(alt)))
    ix = np.digitize(index.ravel(), lev, right=True)
    echo_tops = alt[ix].reshape(index.shape)
    echo_tops = np.ma.masked_where(arr_mask, echo_tops)

    return echo_tops

def compute_echo_tops(grid, thres = [10., 15., 20.], field_name = "DBZ_F"):
    """
    Compute echo tops from reflectivity data

    Echo top is derived from reflectivity data. It's an estimate of the highest altitude
    where the value of dBZ exceeds a specified threshold. 

    Parameters
    ----------
    grid: Grid
        Grid with data which will be used to compute the echo tops.
        A pyart gridded radar data in Cartesian coordinate
    thres: list
        List of the DBZ thresholds to be used.
    field_name : str
        Name of the reflectivity to be used.

    Returns
    -------
    grid: Grid
        A gridded radar data in Cartesian coordinate containing the echo tops
    """

    x_crd = grid.x['data']
    y_crd = grid.y['data']
    grid_shape = (1, grid.ny, grid.nx)
    grid_limits = ((0, 0),
                   (y_crd.min(), y_crd.max()),
                   (x_crd.min(), x_crd.max()))
    grid_out = pyart.testing.make_empty_grid(grid_shape, grid_limits)

    grid_out.time = grid.time
    grid_out.origin_longitude = grid.origin_longitude
    grid_out.origin_latitude = grid.origin_latitude
    grid_out.origin_altitude = grid.origin_altitude

    alt = grid.z['data']/1000
    data = grid.fields[field_name]['data']

    for th in thres:
        echo_tops = echo_tops_array(data, alt, th)

        th_str = ('%f' % th).rstrip('0').rstrip('.')
        echo_dict = {
            'units': 'km',
            'standard_name': 'echo_tops',
            'long_name': 'Echo tops, Threshold ' + th_str + 'dBZ',
            '_FillValue': data.fill_value,
            'data': echo_tops.reshape(grid_shape)
        }
        echo_name = 'Tops' + th_str
        grid_out.add_field(echo_name, echo_dict, replace_existing = True)

    return grid_out


