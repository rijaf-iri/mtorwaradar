
from ..mdv.creategrid import create_grid_from_radar
from ..mdv.projdata import grid_coordsGeo

def create_cappi_grid(radar, fields = ['DBZ_F'],
                      cappi = 'one_altitude', param_cappi = 4.5):
    """
    Create pseudo CAPPI (Constant Altitude Plan Position Indicator)
    radar:
        pyart radar polar object
    fields: list
        list of fields to be used to compute the qpe
    cappi: string
        Method used to create the CAPPI, available options
        'one_altitude':
        'alt_maximum':
        'alt_average':
        'alt_median':
        'ppi_ranges':
    param_cappi:
        Parameters to be used to compute the CAPPI
        'one_altitude': float
            Value of the altitude at which the CAPPI will be created
        'alt_maximum', 'alt_average' and 'alt_median': dictionary
            A dictionary with keys 'min_alt' and 'max_alt' representing
            the minimum and maximum of the altitude to be used to create the CAPPI
            example: {'min_alt': 1.7, 'max_alt': 15.}
        'ppi_ranges': list
        List of lists containing the elevation angle and the start range
        [[elevation angle (in degree), start range (in km)], .....]

    Returns:
        lon: 1d numpy array
        lat: 1d numpy array
        data: dictionary of the fields containing the data, 2d numpy masked ndarray 
    """
    if cappi == 'ppi_ranges':
        grid_shape = (1, 800, 800)
        z_lim = (param_cappi * 1000., param_cappi * 1000.)
        constant_roi = 3000.
        grid = create_grid_from_radar(radar, fields,
                                      grid_shape = grid_shape,
                                      z_lim = z_lim,
                                      constant_roi = constant_roi)
        lon, lat = grid_coordsGeo(grid)

        data = dict()
        for field in fields:
          data[field] = grid.fields[field]['data']  
    elif cappi == 'one_altitude':
        grid_shape = (1, 800, 800)
        z_lim = (param_cappi * 1000., param_cappi * 1000.)
        constant_roi = 3000.
        grid = create_grid_from_radar(radar, fields,
                                      grid_shape = grid_shape,
                                      z_lim = z_lim,
                                      constant_roi = constant_roi)
        lon, lat = grid_coordsGeo(grid)

        data = dict()
        for field in fields:
          data[field] = grid.fields[field]['data']  
    else:
        lev = np.arange(param_cappi['min_alt'] * 1000,
                        param_cappi['max_alt'] * 1000, 500)
        grid_shape = (len(lev), 800, 800)
        z_lim = (lev[0], lev[len(lev) - 1])
        constant_roi = 1500.
        grid = create_grid_from_radar(radar, fields,
                                      grid_shape = grid_shape,
                                      z_lim = z_lim,
                                      constant_roi = constant_roi)
        lon, lat = grid_coordsGeo(grid)

        data = dict()
        for field in fields:
            if cappi == 'alt_maximum':
                foo = np.amax
            if cappi == 'alt_average':
                foo = np.nanmean
            if cappi == 'alt_median':
                foo = np.nanmedian
            
            data[field] = foo(grid.fields[field]['data'], axis = 0)

    return lon, lat, data
