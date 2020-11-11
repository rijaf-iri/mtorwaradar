import numpy as np
import pyart
import cartopy

def polar_projData(radar, sweep, field):
    sweep_slice = radar.get_slice(sweep)
    data = radar.fields[field]['data'][sweep_slice]
    lat, lon, alt = radar.get_gate_lat_lon_alt(sweep, filter_transitions = True)

    return lon, lat, data

def polar_projDataCRS(radar, sweep, field):
    sweep_slice = radar.get_slice(sweep)
    data = radar.fields[field]['data'][sweep_slice]
    x, y, z = radar.get_gate_x_y_z(sweep, filter_transitions = True)

    projection = cartopy.crs.epsg(3857)
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection.proj4_params)
    lon = lon + radar.longitude['data'][0]
    lat = lat + radar.latitude['data'][0]

    return lon, lat, data, projection

##########

# def polar_projDataCRS(radar, sweep, field):
#     display = pyart.graph.RadarMapDisplay(radar)
#     data = display._get_data(field, sweep, mask_tuple = None,
#                              filter_transitions = True, gatefilter = None)
#     x, y = display._get_x_y(sweep, edges = True, filter_transitions = True)

#     projection = cartopy.crs.epsg(3857)
#     lon, lat = pyart.core.cartesian_to_geographic(x * 1000, y * 1000, projection.proj4_params)
#     lon = lon + radar.longitude['data'][0]
#     lat = lat + radar.latitude['data'][0]

#     return lon, lat, data, projection

##########

def polar_projData3d(radar, field):
    lon, lat, z = polar_coordsGeo3d(radar)
    alt = radar.altitude['data'][0] + z
    data = radar.fields[field]['data']

    return lon, lat, alt, data

def polar_projDataCRS3d(radar, field):
    lon, lat, z, projection = polar_coordsGeoCRS3d(radar)
    alt = radar.altitude['data'][0] + z
    data = radar.fields[field]['data']

    return lon, lat, alt, data, projection

def cart_projData(grid, level, field):
    lon, lat = grid_coordsGeo(grid)
    lon, lat = np.meshgrid(lon, lat)
    data = grid.fields[field]['data'][level, :, :]

    return lon, lat, data

def cart_projDataCRS(grid, level, field):
    lon, lat, projection = grid_coordsGeoCRS(grid)
    lon, lat = np.meshgrid(lon, lat)
    data = grid.fields[field]['data'][level, :, :]

    return lon, lat, data, projection

def cart_projData3d(grid, field):
    lon, lat, z = grid_coordsGeo3d(grid)
    elv, lat, lon = np.meshgrid(z, lat, lon, indexing = 'ij')
    # alt = round(grid.origin_altitude['data'][0], 1) + elv
    alt = elv
    data = grid.fields[field]['data']

    return lon, lat, alt, data

def cart_projDataCRS3d(grid, field):
    lon, lat, z, projection = grid_coordsGeoCRS3d(grid)
    elv, lat, lon = np.meshgrid(z, lat, lon, indexing = 'ij')
    # alt = round(grid.origin_altitude['data'][0], 1) + elv
    alt = elv
    data = grid.fields[field]['data']

    return lon, lat, alt, data, projection

def cart_xyzData(grid, field):
    z, y, x = np.meshgrid(grid.z['data'],
                          grid.y['data'],
                          grid.x['data'],
                          indexing = 'ij')
    data = grid.fields[field]['data']

    return x, y, z, data

############################

def polar_coordsGeo3d(radar):
    x = radar.gate_x['data']
    y = radar.gate_y['data']
    z = radar.gate_z['data']

    projparams = radar.projection.copy()
    projparams['lon_0'] = radar.longitude['data'][0]
    projparams['lat_0'] = radar.latitude['data'][0]
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projparams)

    return lon, lat, z

def polar_coordsGeoCRS3d(radar):
    x = radar.gate_x['data']
    y = radar.gate_y['data']
    z = radar.gate_z['data']

    projection = cartopy.crs.epsg(3857)
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection.proj4_params)
    lon = lon + radar.longitude['data'][0]
    lat = lat + radar.latitude['data'][0]

    return lon, lat, z, projection

def grid_coordsGeo(grid):
    x = grid.x['data']
    y = grid.y['data']

    projection = grid.get_projparams()
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection)

    return lon, lat

def grid_coordsGeoCRS(grid):
    x = grid.x['data']
    y = grid.y['data']

    projection = cartopy.crs.epsg(3857)
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection.proj4_params)
    lon = lon + grid.origin_longitude['data'][0]
    lat = lat + grid.origin_latitude['data'][0]

    return lon, lat, projection

def grid_coordsGeo3d(grid):
    x = grid.x['data']
    y = grid.y['data']
    z = grid.z['data']

    projection = grid.get_projparams()
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection)

    return lon, lat, z

def grid_coordsGeoCRS3d(grid):
    x = grid.x['data']
    y = grid.y['data']
    z = grid.z['data']

    projection = cartopy.crs.epsg(3857)
    lon, lat = pyart.core.cartesian_to_geographic(x, y, projection.proj4_params)
    lon = lon + grid.origin_longitude['data'][0]
    lat = lat + grid.origin_latitude['data'][0]

    return lon, lat, z, projection

