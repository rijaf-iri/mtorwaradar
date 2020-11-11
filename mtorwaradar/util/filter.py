import numpy as np
import inspect
from scipy import signal
import pyart
from .utilities import do_call, str2numeric_dict_args

def apply_filter_dict_args(radar, filter_field, filter_pars = None, censor_fieldF = True):
    if filter_pars is not None:
        if filter_pars['use_filter']:
            filter_fun = filter_pars['filter_fun']
            if filter_fun in filter_pars.keys():
                filter_args = filter_pars[filter_fun]
                filter_args = str2numeric_dict_args(filter_args)
                if filter_fun == 'median_filter_censor' and censor_fieldF:
                    filter_args['censor_field'] = filter_args['censor_field'] + '_F'

                return apply_filter(radar, filter_fun, filter_field, **filter_args)
            else:
                return apply_filter(radar, filter_fun, filter_field)
        else:
            return None
    else:
        return None

def apply_filter(radar, filter_fun, filter_field, **kwargs):
    dispatcher = { 
        'median_filter_censor' : median_filter_censor, 
        'median_filter' : median_filter,
        'smooth_trim': smooth_trim,
        'smooth_trim_scan': smooth_trim_scan
    }
    filter_args = inspect.getfullargspec(dispatcher[filter_fun]).args[2:]
    filter_kwargs = dict((key, kwargs[key]) for key in filter_args if key in kwargs)

    return do_call(dispatcher[filter_fun], args = [radar, filter_field], kwargs = filter_kwargs)

# DBZ, ZDR and LDR can be somewhat noisy gate-to-gate. This 
# section gives you the option of smoothing the fields in range by 
# applying a median filter.

# Option to filter a field with median filter.
# The filter is computed in range.

# Option to censor the output using set thresholds.
# Examples are SNR (Signal-to-noise), NCP (normalized coherent power)
# and  RHOHV (Cross correlation ratio). If the specified field at a gate is 
# lower than the threshold, all output fields will be set to missing 
# for that gate.
# NCP < 0.5, RHOHV < 0.8, SNR < 3

## pyart.retrieve.kdp_proc.filter_psidp
def median_filter_censor(radar, filter_field,
                         median_filter_len = 5, minsize_seq = 3,
                         censor_field = 'RHOHV_F', censor_thres = 0.7):
    filter_f = radar.fields[filter_field]['data']
    censor_f = radar.fields[censor_field]['data']

    # Initialize mask
    mask = np.ones(filter_f.shape) * False
    # Censoring
    mask += censor_f < censor_thres
    # Add filter_field mask
    mask += filter_f.mask

    field_filter = np.zeros(filter_f.shape)
    for i, row in enumerate(filter_f):
        # idx of last valid gate
        idx = np.where(~row.mask)[0]
        if len(idx):
            row = row[0:idx[-1] + 1]
            row_with_nan = np.ma.filled(row, np.nan)
            # To be sure to always have a left and right neighbour,
            # we need to pad the signal with NaN
            row_with_nan = np.pad(
                row_with_nan, (1, 1), 'constant',
                constant_values=(np.nan,))
            idx = np.where(np.isfinite(row_with_nan))[0]
            nan_left = idx[np.where(np.isnan(row_with_nan[idx - 1]))[0]]
            nan_right = idx[np.where(np.isnan(row_with_nan[idx + 1]))[0]]

            len_sub = nan_right - nan_left
            for j, l in enumerate(len_sub):
                if l < minsize_seq:
                    mask[i, nan_left[j] - 1:nan_right[j] + 1] = True

            # median filter
            row = signal.medfilt(row_with_nan, median_filter_len)
            field_filter[i, 0:len(row[1:-1])] = row[1:-1]

    field_filter = np.ma.masked_array(field_filter,
        mask = mask, fill_value = filter_f.fill_value)

    return field_filter

def median_filter(radar, filter_field, median_filter_len = 5, minsize_seq = 3):
    filter_f = radar.fields[filter_field]['data']
    mask = np.ones(filter_f.shape) * False
    mask += filter_f.mask

    field_filter = np.zeros(filter_f.shape)
    for i, row in enumerate(filter_f):
        idx = np.where(~row.mask)[0]
        if len(idx):
            row = row[0:idx[-1] + 1]
            row_with_nan = np.ma.filled(row, np.nan)
            row_with_nan = np.pad(
                row_with_nan, (1, 1), 'constant',
                constant_values=(np.nan,))
            idx = np.where(np.isfinite(row_with_nan))[0]
            nan_left = idx[np.where(np.isnan(row_with_nan[idx - 1]))[0]]
            nan_right = idx[np.where(np.isnan(row_with_nan[idx + 1]))[0]]

            len_sub = nan_right - nan_left
            for j, l in enumerate(len_sub):
                if l < minsize_seq:
                    mask[i, nan_left[j] - 1:nan_right[j] + 1] = True

            row = signal.medfilt(row_with_nan, median_filter_len)
            field_filter[i, 0:len(row[1:-1])] = row[1:-1]

    field_filter = np.ma.masked_array(field_filter,
        mask = mask, fill_value = filter_f.fill_value)

    return field_filter

def smooth_trim(radar, filter_field, window_len = 5, window = 'hanning'):
    field = radar.fields[filter_field]['data']
    field_nan = np.ma.filled(field, np.nan)
    field_smooth = np.zeros(field.shape)
    for i, row in enumerate(field_nan):
        smth = pyart.correct.phase_proc.smooth_and_trim(row, window_len, window)
        field_smooth[i, :] = smth

    field_smooth = np.ma.masked_invalid(field_smooth)
    field_smooth = np.ma.masked_array(field_smooth,
        mask = field.mask, fill_value = field.fill_value)

    return field_smooth

def smooth_trim_scan(radar, filter_field, window_len = 5, window = 'hanning'):
    field = radar.fields[filter_field]['data']
    field_nan = np.ma.filled(field, np.nan)
    field_smooth = pyart.correct.phase_proc.smooth_and_trim_scan(field_nan, window_len, window)

    field_smooth = np.ma.masked_invalid(field_smooth)
    field_smooth = np.ma.masked_array(field_smooth,
        mask = field.mask, fill_value = field.fill_value)

    return field_smooth
