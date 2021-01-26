from .radargrid_extract import extract_grid_data


def extractRadarGrid(
    dirMdvDate,
    start_time,
    end_time,
    fields,
    points,
    levels=-1,
    padxyz=[0, 0, 0],
    fun_sp="mean",
    time_zone="Africa/Kigali",
):
    """
    Extract radar Cartesian data over a given points.

    Parameters
    ----------
    dirMdvDate: string
        full path to the folders containing the folders dates of the mdv files
    start_time: string
        The start time same time zone as "time_zone", format "YYYY-mm-dd HH:MM"
    end_time: string
        The end time same time zone as "time_zone", format "YYYY-mm-dd HH:MM"
    fields: list
        List of the fields to extract
    points: list of dictionary
        A list of the dictionary of the points to extract, format
        [{"id": "id_point1", "longitude": value_lon, "latitude": value_lat}, {...}, ...]
    levels: integer or list of integer
        A list of the index of altitudes to be extracted in integer, or -1 to extract all available altitude
    padxyz: list
        list of the padding in number of grid to apply to each point to extract with order  [longitude, latitude, altitude].
        Default [0, 0, 0], no padding applied
    fun_sp: string
        Function to be used for the padding. Options: "mean", "median", "max", "min"
    time_zone: string
        The time zone of "start_time", "end_time" and the output extracted data.
        Options: "Africa/Kigali" or "UTC". Default "Africa/Kigali"

    Returns
    -------
    Return a dictionary of
        points: the original points used to extract the data
        date: list of dates of the extracted data
        altitude: list of the altitudes of the extracted data
        data: dictionary of the fields in the form of 3d list
             dimension: (len(date) x len(altitude) x len(points))
    """

    return extract_grid_data(
        dirMDV=dirMdvDate,
        source=None,
        start_time=start_time,
        end_time=end_time,
        fields=fields,
        points=points,
        levels=levels,
        padxyz=padxyz,
        fun_sp=fun_sp,
        time_zone=time_zone,
    )


def gridExtractedTable(x):
    """
    Convert to table extracted radar Cartesian data.

    Parameters
    ----------
    x: dictionary
        Output from extractRadarGrid
    Returns
    -------
    A list of dictionaries
    """
    var = list(x['data'].keys())

    out = list()
    for p in range(len(x['coords'])):
        for e in range(len(x['altitude'])):
            for d in range(len(x['date'])):
                pt = x['coords'][p]
                tab = {'id': pt['id'],
                    'longitude': pt['longitude'],
                    'latitude': pt['latitude'],
                    'dates': x['date'][d],
                    'altitude': x['altitude'][e]
                 }
                for v in var:
                    tab[v] = x['data'][v][d][e][p]
                out = out + [tab]

    return out
