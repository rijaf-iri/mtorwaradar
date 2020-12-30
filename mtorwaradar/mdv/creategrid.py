import pyart

def create_grid_from_radar(radar, field_names = ['DBZ_F'],
                           grid_shape = (35, 800, 800),
                           z_lim = (0., 17000.),
                           y_lim = (-199750., 199750.),
                           x_lim = (-199750., 199750.),
                           gridding_algo = 'map_gates_to_grid',
                           map_roi = False,
                           weighting_function = 'Nearest',
                           roi_func = 'constant',
                           constant_roi = 710,
                           **kwargs):
    """
    constant_roi: float
        Radius of influence parameter in meter. Default 500 * sqrt(2) ~ 707
    """

    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.exclude_transition()
    for field in field_names:
        gatefilter.exclude_invalid(field)

    grid_origin_alt = 0
    grid_limits = (z_lim, y_lim, x_lim)
    grid = pyart.map.grid_from_radars(radar, gatefilters = gatefilter, fields = field_names,
                                      grid_shape = grid_shape, grid_limits = grid_limits,
                                      grid_origin_alt = grid_origin_alt,
                                      gridding_algo = gridding_algo, map_roi = map_roi,
                                      weighting_function = weighting_function,
                                      roi_func = roi_func, constant_roi = constant_roi,
                                      **kwargs)
    return grid
