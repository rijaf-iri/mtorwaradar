import numpy as np
import pyart

def polar_xsec_data(radar, field, azimuth):
    azimuth = float(azimuth)
    azimuths = [azimuth, (azimuth + 180) % 360]

    unq_swp = _unique_sweeps_by_elevation_angle(radar)
    radar = radar.extract_sweeps(unq_swp)

    xsect = pyart.util.cross_section_ppi(radar, target_azimuths = azimuths, az_tol = 0.05)
    display = pyart.graph.RadarDisplay(xsect)

    sec_data = []
    for sweep in range(0, 2):
        data = display._get_data(field, sweep, mask_tuple = None,
                                 filter_transitions = True, gatefilter = None)
        x, y, z = display._get_x_y_z(sweep, edges = True, filter_transitions = True)
        sweep_slice = display._radar.get_slice(sweep)
        az_mean = np.abs(np.mean(display._radar.azimuth['data'][sweep_slice]))

        if 89.5 <= az_mean <= 90.0:
            R = np.sqrt(x ** 2 + y ** 2) * np.sign(x)
        else:
            R = np.sqrt(x ** 2 + y ** 2) * np.sign(y)

        if sweep == 0:
            if (R >= 0).all():
                R = -R
                print(sweep)
        else:
            if (R <= 0).all():
                R = -R
                print(sweep)

        sec_data.append([R, z, data])

    data = {'x0': sec_data[0][0], 'z0': sec_data[0][1], 'data0': sec_data[0][2],
            'x1': sec_data[1][0], 'z1': sec_data[1][1], 'data1': sec_data[1][2]}

    return data

############################
# https://github.com/ARM-DOE/pyart/issues/718

def _get_vcp(radar):
    """ Return a list of elevation angles representative of each sweep.
    These are the median of the elevation angles in each sweep, which are
    more likely to be identical than the mean due to change of elevation angle
    at the beginning and end of each sweep.
    """
    vcp = [np.median(el_this_sweep) for el_this_sweep in radar.iter_elevation()]
    return np.asarray(vcp, dtype=radar.elevation['data'].dtype)

def _unique_sweeps_by_elevation_angle(radar, tol=0.05):
    """ Returns the sweep indices that correspond to unique
    elevation angles, for use in extract_sweeps.
    
    The default is a tolerance of 0.05 deg. 
    """
    vcp = _get_vcp(radar)
    close_enough = (vcp/tol).astype('int32')
    unq_el, unq_el_idx = np.unique(close_enough, return_index=True)
    return unq_el_idx
