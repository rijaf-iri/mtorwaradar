import numpy as np
import rpy2.robjects as robjects

def do_call(what, args = None, kwargs = None):
    if args is None and kwargs is not None:
        return what(**kwargs)
    elif args is not None and kwargs is None:
        return what(*args)
    else:
        return what(*args, **kwargs)

########

# args = dict((k, v if v.isalpha() else int(v) if v.isdigit() else float(v)) for k, v in args.items())

def str2numeric_dict_args(args):
    for key in args:
        val = args[key]
        if type(val) is str:
            if not val.isalpha():
                val = int(val) if val.isdigit() else float(val)
        args[key] = val

    return args

########

def npmDarray_to_rFloatVector(arr):
    x_1d = arr.transpose().reshape(arr.size)

    return robjects.FloatVector(x_1d)

def rFloatVector_to_npmDarray(vec, shape):
    # shape: tuple
    dim = robjects.IntVector(shape)
    arr = robjects.r.array(vec, dim)

    return np.array(arr)

########

def uv_to_wind(u, v):
    ws = np.sqrt(u**2 + v**2)
    wd = np.rad2deg(np.arctan2(u, v)) + np.where(ws < 1e-14, 0, 180)

    return ws, wd

def wind_to_uv(ws, wd):
    d_rad = np.deg2rad(wd)
    u = -ws * np.sin(d_rad)
    v = -ws * np.cos(d_rad)

    return u, v

########

def pretty(low, high, n):
    range = _nicenumber(high - low, False)
    d = _nicenumber(range / (n - 1), True)
    miny = np.floor(low / d) * d
    maxy = np.ceil (high / d) * d
 
    return np.arange(miny, maxy + 0.5 * d, d)

## from https://stackoverflow.com/a/44396692
def _nicenumber(x, round):
    exp = np.floor(np.log10(x))
    f   = x / 10**exp

    if round:
        if f < 1.5:
            nf = 1.
        elif f < 3.:
            nf = 2.
        elif f < 7.:
            nf = 5.
        else:
            nf = 10.
    else:
        if f <= 1.:
            nf = 1.
        elif f <= 2.:
            nf = 2.
        elif f <= 5.:
            nf = 5.
        else:
            nf = 10.

    return nf * 10.**exp


