import inspect
import wradlib as wlb
from .utilities import do_call, str2numeric_dict_args

def calculate_pia_dict_args(radar, pia = None,
                            dbz_field = 'DBZ_F',
                            kdp_field = 'KDP_F'):
    if pia is not None:
        if pia['use_pia']:
            if pia['pia_field'] in pia.keys():
                pia_args = pia[pia['pia_field']]
                pia_args = str2numeric_dict_args(pia_args)

                if pia['pia_field'] == 'dbz':
                    args_constr = [k for k in pia_args.keys() if 'constraint' in k]
                    if len(args_constr) > 0:
                        args_pia = [k for k in pia_args.keys() if k not in args_constr]
                        args_constr, pia_args = map(lambda keys: {x: pia_args[x] for x in keys}, [args_constr, args_pia])

                        if args_constr['constraints'] == 'both':
                            pia_args['constraints'] = [wlb.atten.constraint_dbz, wlb.atten.constraint_pia]
                            pia_args['constraint_args'] = [[args_constr['constraint_args_dbz']], [args_constr['constraint_args_pia']]]
                        elif args_constr['constraints'] == 'dbz':
                            pia_args['constraints'] = [wlb.atten.constraint_dbz]
                            pia_args['constraint_args'] = [[args_constr['constraint_args_dbz']]]
                        elif args_constr['constraints'] == 'pia':
                            pia_args['constraints'] = [wlb.atten.constraint_pia]
                            pia_args['constraint_args'] = [[args_constr['constraint_args_pia']]]
                        else:
                            pia_args['constraints'] = None
                            pia_args['constraint_args'] = None

                    pia_args['dbz_field'] = dbz_field
                else:
                    pia_args['kdp_field'] = kdp_field

                pia_args['pia_field'] = pia['pia_field']

                return calculate_pia(radar, **pia_args)
            else:
                return correct_attenuation(radar, pia_field = pia['pia_field'])
        else:
            return None
    else:
        return None

# args_dbz = ['a_max', 'a_min', 'n_a', 'b_max', 'b_min', 'n_b', 'sector_thr',
#             'constraint_args_dbz', 'constraint_args_pia']
# num_dbz = [float, float, int, float, float, int, int, float, float]
# for k in range(len(args_dbz)):
#     pia_args[args_dbz[k]] = num_dbz[k](pia_args[args_dbz[k]])

def calculate_pia(radar, **kwargs):
    args1 = inspect.getfullargspec(correct_attenuation).args[1:]
    args2 = inspect.getfullargspec(wlb.atten.correct_attenuation_constrained).args[1:]
    args3 = inspect.getfullargspec(wlb.atten.pia_from_kdp).args[1:]
    pia_args = args1 + args2 + args3

    pia_kwargs = dict((key, kwargs[key]) for key in pia_args if key in kwargs)
    pia = do_call(correct_attenuation, args = [radar], kwargs = pia_kwargs)

    return pia

def correct_attenuation(radar, pia_field = 'dbz', dbz_field = 'DBZ_F',
                        kdp_field = 'KDP_F', **kwargs):
    # path-integrated attenuation
    # pia_field: 'dbz' or 'kdp'
    dr = radar.range['meters_between_gates']/1000

    if pia_field == 'dbz':
        dbz = radar.fields[dbz_field]['data']
        pia_fun = wlb.atten.correct_attenuation_constrained
        pia_args = inspect.getfullargspec(pia_fun).args[1:]
        pia_kwargs = dict((key, kwargs[key]) for key in pia_args if key in kwargs)
        if not 'gate_length' in kwargs:
            pia_kwargs['gate_length'] = dr
        pia = do_call(pia_fun, args = [dbz], kwargs = pia_kwargs)

    if pia_field == 'kdp':
        kdp = radar.fields[kdp_field]['data']
        pia_fun = wlb.atten.pia_from_kdp
        pia_args = inspect.getfullargspec(pia_fun).args[1:]
        pia_kwargs = dict((key, kwargs[key]) for key in pia_args if key in kwargs)
        if not 'dr' in kwargs:
            pia_kwargs['dr'] = dr
        pia = do_call(pia_fun, args = [kdp], kwargs = pia_kwargs)

    return pia
