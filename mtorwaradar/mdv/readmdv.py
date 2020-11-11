import numpy as np
import pyart

def radarPolar(filename, fields = 'all'):
    # fields
    # 'all': read all fields
    # None : only read metadata
    # list of fields or a str of one field: the fields to be read

    field_names = ['DBZ', 'DBZ_F', 'DBZVC', 'DBZVC_F', 'DBZHC', 'DBZHC_F',
                   'VEL', 'VEL_F', 'ZDR', 'ZDR_F', 'NCP', 'NCP_F',
                   'SNR', 'SNR_F', 'SNRHC', 'SNRHC_F', 'SNRVC', 'SNRVC_F',
                   'DBMHC', 'DBMVC', 'WIDTH', 'WIDTH_F', 'PHIDP', 'PHIDP_F',
                   'RHOHV', 'RHOHV_F', 'KDP', 'KDP_F', 'CMD_FLAG']

    if fields is not None:
        if fields == 'all':
            fields_excl = None
        else:
            if not isinstance(fields, list):
                fields = [fields]
            fields_excl = [x for x in field_names if x not in fields]
    else:
        fields_excl = field_names

    radar = pyart.io.read_mdv(filename,
                              exclude_fields = fields_excl,
                              file_field_names = True,
                              delay_field_loading = True)
    return radar

def radarPolarDerived(filename, fields = 'all'):
    # fields
    # 'all': read all fields
    # None : only read metadata
    # list of fields or a str of one field: the fields to be read

    field_names = ['RATE_ZH', 'RATE_Z_ZDR', 'RATE_KDP', 'RATE_KDP_ZDR',
                   'RATE_HYBRID', 'RATE_PID', 'PID']

    if fields is not None:
        if fields == 'all':
            fields_excl = None
        else:
            if not isinstance(fields, list):
                fields = [fields]
            fields_excl = [x for x in field_names if x not in fields]
    else:
        fields_excl = field_names

    radar = pyart.io.read_mdv(filename,
                              exclude_fields = fields_excl,
                              file_field_names = True,
                              delay_field_loading = True)
    return radar

def radarCart(filename, fields = 'all'):
    # fields
    # 'all': read all fields
    # None : only read metadata
    # list of fields or a str of one field: the fields to be read

    field_names = ['DBZ', 'DBZ_F', 'DBZHC_F', 'DBZVC_F',
                   'NCP', 'CLUT', 'VEL', 'VEL_F']

    if fields is not None:
        if fields == 'all':
            fields_excl = None
        else:
            if not isinstance(fields, list):
                fields = [fields]
            fields_excl = [x for x in field_names if x not in fields]
    else:
        fields_excl = field_names

    grid = pyart.io.read_grid_mdv(filename,
                                  exclude_fields = fields_excl,
                                  file_field_names = True,
                                  delay_field_loading = True)
    return grid

def radarGrid(filename, fields = 'all'):
    mdv = pyart.io.mdv_common.MdvFile(pyart.io.common.prepare_for_read(filename))
    field_names = mdv.fields

    if fields is not None:
        if fields == 'all':
            fields_excl = None
        else:
            if not isinstance(fields, list):
                fields = [fields]
            fields_excl = [x for x in field_names if x not in fields]
    else:
        fields_excl = field_names

    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        grid = pyart.io.read_grid_mdv(filename,
                                      exclude_fields = fields_excl,
                                      file_field_names = True,
                                      delay_field_loading = True)
    return grid

def grid_data(filename):
    grid = pyart.io.read_grid_mdv(filename,
                                  file_field_names = True,
                                  delay_field_loading = True)
    return grid

def grid_data1(filename):
    import warnings
    with warnings.catch_warnings():
        # warnings.simplefilter("ignore")
        warnings.filterwarnings("ignore")
        grid = pyart.io.read_grid_mdv(filename,
                                      file_field_names = True,
                                      delay_field_loading = True)
    return grid
