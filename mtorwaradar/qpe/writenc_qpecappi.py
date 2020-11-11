
import numpy as np
import datetime
from ..mdv.projdata import grid_coordsGeo
from netCDF4 import Dataset as ncdf

def writenc_qpecappi(grid, timestamp, timeunits,
                     outncfile, miss_val = -999.):
    pr = np.amax(grid.fields['rain_rate']['data'], axis = 0)
    tot = pr * 300./3600.

    # add time dimension
    pr = pr[np.newaxis, :, :]
    tot = tot[np.newaxis, :, :]
    xlon, xlat = grid_coordsGeo(grid)

    # open a netCDF file to write
    ncout = ncdf(outncfile, mode = 'w', format = 'NETCDF4')

    # define axis size
    ncout.createDimension('time', 1)
    ncout.createDimension('lat', len(xlat))
    ncout.createDimension('lon', len(xlon))

    # create time axis
    time = ncout.createVariable('time', np.float64, ('time',))
    time.long_name = 'time'
    time.units = timeunits
    time.calendar = 'standard'
    time.axis = 'T'

    time[:] = timestamp

    # create latitude axis
    lat = ncout.createVariable('lat', np.float32, ('lat'))
    lat.standard_name = 'latitude'
    lat.long_name = 'latitude'
    lat.units = 'degrees_north'
    lat.axis = 'Y'

    lat[:] = xlat[:]

    # create longitude axis
    lon = ncout.createVariable('lon', np.float32, ('lon'))
    lon.standard_name = 'longitude'
    lon.long_name = 'longitude'
    lon.units = 'degrees_east'
    lon.axis = 'X'

    lon[:] = xlon[:]

    # create variable
    rate = ncout.createVariable('rate', np.float32, ('time', 'lat', 'lon'),
                                zlib = True, complevel = 6)
    rate.long_name = 'Precipitation rate'
    rate.units = 'mm/hr'
    rate.missing_value = miss_val

    pr = pr.filled(fill_value = miss_val)
    rate[:, :, :] = pr

    precip = ncout.createVariable('precip', np.float32, ('time', 'lat', 'lon'),
                                  zlib = True, complevel = 6)
    precip.long_name = 'Precipitation accumulation'
    precip.units = 'mm'
    precip.missing_value = miss_val

    tot = tot.filled(fill_value = miss_val)
    precip[:, :, :] = tot

    # global attributes
    ncout.description = 'Quantitative precipitation estimation using Z-R relationship'
    ncout.zr_alpha = 0.0396
    ncout.zr_beta = 0.679
    ncout.history = "Created " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ncout.close()

    return 0
