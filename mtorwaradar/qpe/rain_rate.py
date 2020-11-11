import numpy as np
import copy

def rr_zh(dbz, alpha = 0.017, beta = 0.714, invCoef = True):
    fill_value = dbz.fill_value
    Z = np.ma.power(10., 0.1 * dbz)
    if(invCoef):
        rt = alpha * np.ma.power(Z, beta)
    else:
        rt = np.ma.power(Z / alpha, 1.0 / beta)

    rt.fill_value = fill_value
    return rt

def rr_zpoly(dbz):
    fill_value = dbz.fill_value
    X = dbz
    X2 = X * X
    X3 = X2 * X
    X4 = X3 * X
    poly = -2.3 + 0.17 * X -5.1e-3 * X2 + 9.8e-5 * X3 - 6e-7 * X4
    rt = np.ma.power(10., poly)

    rt.fill_value = fill_value
    return rt

def rr_z_zdr(dbz, zdr, alpha = 0.00786, beta_zh = 0.967, beta_zdr = -4.98):
    fill_value = dbz.fill_value
    Z = np.ma.power(10., 0.1 * dbz)
    rt = alpha * np.ma.power(Z, beta_zh) * np.ma.power(zdr, beta_zdr)
    # rt = alpha * np.ma.power(dbz, beta_zh) * np.ma.power(zdr, beta_zdr)

    rt.fill_value = fill_value
    return rt

def rr_kdp(kdp, alpha = 53.3, beta = 0.669):
    fill_value = kdp.fill_value
    # rt = np.sign(kdp) * alpha * np.ma.power(np.abs(kdp), beta)
    # rt = np.ma.masked_where(rt < 0, rt)
    kdp[kdp < 0] = 0.
    rt = alpha * np.ma.power(kdp, beta)

    rt.fill_value = fill_value
    return rt

def rr_kdp_zdr(kdp, zdr, alpha = 192, beta_kdp = 0.946, beta_zdr = -3.45):
    fill_value = kdp.fill_value
    # rt = np.sign(kdp) * alpha * np.ma.power(np.abs(kdp), beta_kdp) * np.ma.power(zdr, beta_zdr)
    # rt = np.ma.masked_where(rt < 0, rt)
    kdp[kdp < 0] = 0.
    rt = alpha * np.ma.power(kdp, beta_kdp) * np.ma.power(zdr, beta_zdr)

    rt.fill_value = fill_value
    return rt

def rr_hybrid(rt_zh, rt_z_zdr, rt_kdp, rt_kdp_zdr,
              hybrid_aa = 10, hybrid_bb = 50, hybrid_cc = 100):
    """
    PRECIP_RATE_HYBRID
    The HYBRID rate is a combination of the other rates.

    If RATE_ZH <= hybrid_aa, RATE_HYBRID = RATE_ZH
    Else if RATE_Z_ZDR <= hybrid_bb, RATE_HYBRID = RATE_Z_ZDR
    Else If RATE_Z_ZDR <= hybrid_cc, RATE_HYBRID = RATE_KDP_ZDR
    Else if RATE_Z_ZDR > hybrid_bb, RATE_HYBRID = RATE_KDP
    """
    fill_value = rt_zh.fill_value
    hybrid = copy.deepcopy(rt_zh)
    hybrid[np.logical_not(hybrid.mask)] = 0
    
    mask_aa = rt_zh <= hybrid_aa
    hybrid[mask_aa] = rt_zh[mask_aa]
    mask_bb = np.logical_and(rt_z_zdr <= hybrid_bb, np.logical_not(mask_aa))
    hybrid[mask_bb] = rt_z_zdr[mask_bb]
    mask_cc = np.logical_or(np.logical_not(mask_aa), np.logical_not(mask_bb))
    mask_cc = np.logical_and(rt_z_zdr <= hybrid_cc, np.logical_not(mask_cc))
    hybrid[mask_cc] = rt_kdp_zdr[mask_cc]
    mask_ee = np.logical_and(rt_z_zdr > hybrid_bb, np.logical_not(mask_cc))
    hybrid[mask_ee] = rt_kdp[mask_ee]

    hybrid.fill_value = fill_value
    return hybrid

