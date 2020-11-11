
import numpy as np
import re
# import matplotlib as mpl

from .colorlist import _make_color_dict

########

def get_ColorScale(ckeyfile):
    with open(ckeyfile) as cf:
        ckey = [l.strip(' ') for l in cf]
        ckey = [x.rstrip('\n') for x in ckey if not x.startswith('#')]
        ckey = [x for x in ckey if x != '']
        ckey = [';'.join(x.split()) for x in ckey]
        ckey = [x.split(';') for x in ckey]
        ckey = [x for x in ckey if len(x) > 2]
        ck = []
        for x in ckey:
            c = []
            for y in x:
                if y.startswith('!'):
                    break
                else:
                    c = c + [y]
            ck = ck + [c]
        ckey = [x if len(x) == 3 else x[0:2] + [' '.join([x[i] for i in range(2, len(x))])] for x in ck]

    breaks = [x[0] for x in ckey[1:]]
    pattern = re.compile('\.')
    precFloat = [not pattern.search(x) == None for x in breaks]
    if any(precFloat):
        breaks = [float(x) for x in breaks]
    else:
        breaks = [int(x) for x in breaks]

    kol_ext = [ckey[0][2], ckey[len(ckey) - 1][2]]
    kol_ext = [x.lower() for x in kol_ext]
    kol = [x[2] for x in ckey[1:-1]]
    kol = [x.lower() for x in kol]

    kol_dict = _make_color_dict()
    kol_dict = dict((key.lower(), value) for (key, value) in kol_dict.items())

    colors_ext = []
    for k in kol_ext:
        if not k.startswith('#'):
            if k in list(kol_dict.keys()):
                k = kol_dict[k]
        colors_ext = colors_ext + [k]

    colors = []
    for k in kol:
        if not k.startswith('#'):
            if k in list(kol_dict.keys()):
                k = kol_dict[k]
        colors = colors + [k]

    return breaks, colors, colors_ext

def format_ColorScale(breaks, colors, colors_ext):
    kol = [None] * (len(colors) + 2)

    # for j in range(len(kol)):
    #     if j == 0:
    #         kol[j] = mpl.colors.to_hex(colors_ext[0])
    #     elif j == len(kol) - 1:
    #         kol[j] = mpl.colors.to_hex(colors_ext[1])
    #     else:
    #         kol[j] = mpl.colors.to_hex(colors[j - 1])

    for j in range(len(kol)):
        if j == 0:
            kol[j] = colors_ext[0]
        elif j == len(kol) - 1:
            kol[j] = colors_ext[1]
        else:
            kol[j] = colors[j - 1]

    kol.reverse()
    breaks = [str(x) for x in breaks]
    breaks.reverse()

    return {'labels': breaks, 'colors': kol}
