# from eQ_rw import *
import os
import numpy as np
from eQ_rw import ids, Log, ReadStation, isnumber, error_dic, cat_format, dist_km
from textwrap import wrap
from datetime import datetime as dt


"""
===========================================
Velest module by @eqhalauwet
==========================================

Python module for reading velest output, ploting and exporting to GMT input.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. Read velest mainprint to see adjustmet hypocenter, velocity model, and RMS every iteration
2. Read cnv file modified to python 3 from pyvelest code (https://github.com/saeedsltm/PyVelest)  

Logs:

2017-Sep: Added _check_header line to automatic check data format from few Seiscomp3 version (see Notes).
2019-Oct: Major change: store readed data in dictionary format.
2020-May: Correction: select phase only without 'X' residual (unused phase on routine processing).
2020-Jul: Major change added Run_Velest() and Run_VelestSet() to run Velest recursively
2020-Jul: RunVelestSet() added recursive routine to adjust input velocity layer if velest is hang (solution not stable)

"""


def cnvpar_format(data_dic, evt_key, ifx='0'):

    lat = data_dic['lat']
    lon = data_dic['lon']
    depth = data_dic['dep']

    if lat < 0:
        lintang = abs(lat)
        lintang = ('%.4f' % lintang).zfill(7) + 'S'
    else:
        lintang = ('%.4f' % lat).zfill(7) + 'N'

    if lon < 0:
        bujur = abs(lon)
        bujur = ('%.4f' % bujur).zfill(8) + 'W'
    else:
        bujur = ('%.4f' % lon).zfill(8) + 'E'

    err_tim, err_lon, err_lat, err_dep, err_mag = error_dic(data_dic)

    # err_hz = ('%.2f' % mt.sqrt(err_lat ** 2 + err_lon ** 2))

    _parameters = (
        f"{str(evt_key.year)[-2:]:2}{int(evt_key.month):2}{int(evt_key.day):2} "
        f"{int(evt_key.hour):2}{int(evt_key.minute):2} {(evt_key.second + evt_key.microsecond * 1e-6):5.2f} "
        f"{lintang} {bujur} {depth:6.2f} {data_dic['mag']:6.2f}    "
        f"{round(data_dic['gap']):3} {float(ifx):4.1f} {data_dic['rms']:4.2f} "
        f"{err_tim:5.2f} {err_lon:5.2f} {err_lat:5.2f} {float(err_dep):5.2f} {float(err_mag):5.2f}")

    return _parameters


def ReadCNV(inpcnv='finalhypo.cnv'):

    # inpcnv = 'D:\project\\relokasi\\velest33\output\\finalhypo.cnv'
    cnv_dic = {}

    with open(inpcnv) as f:

        for l in f:

            if l.strip():

                chk_hdr = [h.isdigit() or h == ' ' for h in l[0:5]]

                if all(chk_hdr):

                    yer = int('%004d' % float(l[0:2]))
                    if 80 <= yer <= 99:
                        yer += 1900
                    else:
                        yer += 2000
                    mon = int('%01d' % float(l[2:4]))
                    day = int('%1d' % float(l[4:6]))
                    H = int('%1d' % float(l[7:9]))
                    M = int('%1d' % float(l[9:11]))
                    sec = float(l[12:17])
                    msec = int((sec - int(sec)) * 1e6)
                    sec = int(sec)

                    if sec >= 60:
                        sec = sec - 60
                        M += 1
                    if M >= 60:
                        M = M - 60
                        H += 1
                    if H >= 24:
                        H = H - 24
                        day += 1
                    if yer == 0:
                        yer = 1900

                    try:

                        ot = dt(yer, mon, day, H, M, sec, msec)

                    except ValueError:

                        print('+++ ==> Error encounterd on the following line:\n', l)

                    lat = float(l[18:26].strip()[:-1])
                    strlat = l[25:26].strip()
                    if strlat == 'S':  # added by eQ - June 2020
                        lat = -lat
                    lon = float(l[27:36].strip()[:-1])
                    strlon = l[35:36].strip()
                    if strlon == 'W':  # added by eQ - June 2020
                        lon = -lon
                    dpt = float(l[37:43].strip())
                    mag = float(l[45:50].strip())
                    gap = float(l[54:57].strip())
                    rms = float(l[62:67].strip())
                    ifx = 'NaN'
                    errtim = 'NaN'
                    errlon = 'NaN'
                    errlat = 'NaN'
                    errmag = 'Nan'
                    errv = 'NaN'
                    nevt = 'NaN'

                    if len(l) > 100:  # added parameter on eQ's velest converter

                        # print("\neQ's cnv extended catalog\n")
                        ifx = 0.0
                        errtim = float(l[67:73].strip())
                        errlon = float(l[73:79].strip())
                        errlat = float(l[79:85].strip())
                        errv = l[85:91].strip()
                        errmag = l[91:97].strip()
                        nevt = int(l[97:104].strip())

                    eqid = ot

                    cnv_dic[eqid] = {'nevt': nevt,
                                     'lat': lat,
                                     'lon': lon,
                                     'dep': dpt,
                                     'mag': mag,
                                     'gap': gap,
                                     'rms': rms,
                                     'errt': errtim,
                                     'erlon': errlon,
                                     'erlat': errlat,
                                     'errv': errv,
                                     'ermag': errmag,
                                     'ifx': ifx,
                                     'arr': {'sta': [],
                                             'pha': [],
                                             'wth': [],
                                             'del': []}
                                     }

                elif not all(chk_hdr):

                    cc = 0

                    for _ in range(6):

                        try:

                            cnv_dic[eqid]['arr']['sta'].append(l[0 + cc:4 + cc].strip())
                            cnv_dic[eqid]['arr']['pha'].append(l[4 + cc:5 + cc].strip())
                            cnv_dic[eqid]['arr']['wth'].append(int(l[5 + cc:6 + cc].strip()))
                            cnv_dic[eqid]['arr']['del'].append(float(l[7 + cc:12 + cc]))

                        except ValueError:

                            pass

                        cc += 12  # length of each phase info

                    # cnv_dic[eqid]['arr']['sta'] = filter(None, cnv_dic[eqid]['arr']['sta'])
                    # cnv_dic[eqid]['arr']['pha'] = filter(None, cnv_dic[eqid]['arr']['pha'])
                    # cnv_dic[eqid]['arr']['del'] = filter(None, cnv_dic[eqid]['arr']['del'])

    return cnv_dic


def ReadSta(inpsta='bmkg_station.dat'):

    # inpsta = 'bmkg_station.dat'
    sta_dic = {}

    with open(inpsta) as f:

        for l in f:

            if l.strip():

                chk_hdr = [h == '(' for h in l[0:1]]

                if not all(chk_hdr):

                    sta = l[0:4].strip()
                    lat = float(l[4:12].strip()[:-1])
                    strlat = l[11:12].strip()
                    if strlat == 'S':  # editted by eQ June 2020
                        lat = -lat
                    lon = float(l[13:22].strip()[:-1])
                    strlon = l[21:22].strip()
                    if strlon == 'W':
                        lon = -lon
                    elev = float(l[23:27].strip())
                    inn = int(l[28:29].strip())
                    icc = int(l[29:33].strip())
                    p_dly = float(l[33:39].strip())
                    s_dly = float(l[40:46].strip())
                    imod = int(l[47:50].strip())

                    sta_dic[sta] = {'lat': lat,
                                    'lon': lon,
                                    'elv': elev,
                                    'in': inn,
                                    'icc': icc,
                                    'p_dly': p_dly,
                                    's_dly': s_dly,
                                    'imod': imod
                                    }
    return sta_dic


def ReadMod(inpmod='velout.mod'):

    mod_dic = {}

    hint = 'VELOCITY MODEL'
    flag = False

    with open(inpmod) as f:

        for l in f:

            if hint in l:
                flag = True
                vmod = l.split()[3][:1]
                mod_dic[vmod] = {'vel': [],
                                 'dep': [],
                                 'damp': []
                                 }

            if flag and len(l.split()) < 2 or flag and not l.strip():
                flag = False

            if flag:
                v, d, vd = map(float, (l.split()[0:3]))
                mod_dic[vmod]['vel'].append(v)
                mod_dic[vmod]['dep'].append(d)
                mod_dic[vmod]['damp'].append(vd)

    return mod_dic


def ReadMainVelest(inpmain='mainprint.out'):
    iter_dic = {}
    init_dic = {}
    final_dic = {}

    with open(inpmain) as f:
        hint_invel = 'layer    vel '
        hint_inxyz = 'eq    origin-time'
        hint_avres = 'Events with  '

        hint_itvel = 'Velocity model   1'
        hint_itxyz = 'eq       ot     x'
        hint_stcor = 'Adjusted station'

        hint_fnxyz = 'date    origin   '
        hint_sstat = 'sta phase nobs'
        hint_rstat = 'nlay   top ..... bottom'
        hint_sres = 'Stn#  Stn     RES'

        flag_invel = False
        flag_inxyz = False
        flag_avres = False

        flag_itvel = False
        flag_itxyz = False
        flag_stcor = False

        flag_fnxyz = False
        flag_sstat = False
        flag_rstat = False
        flag_sres = False

        flag_input = False
        flag_itinit = False
        flag_itfnal = False
        flag_itdone = False
        flag_itnext = False
        flag_itstop = False

        flag_invsts = False
        i = 0
        for l in f:
            i += 1
            # print(i)

            # Iteration phase
            if 'INPUT - M O D E L' in l:
                flag_input = True
            if '--------------------------------------------------------------------------------' in l:
                if itt_num == 0:
                    flag_input = False
                    flag_itinit = True
                else:
                    flag_itnext = True
                flag_itdone = False
            if 'ITERATION no' in l:
                itt_num = int(l.split()[2])
                continue
            if 'iteration done' in l:
                flag_itdone = True
                continue
            if 'final solution' in l:
                flag_itnext = True
                flag_itfnal = True
                flag_itdone = False
            if 'End of program' in l:
                flag_itstop = True

            if flag_input:
                if hint_invel in l:
                    itt_num = 0
                    flag_invel = True
                    vel = []
                    damp = []
                    dep = []
                    stn = []
                    obs = []
                    continue
                if flag_invel and not l.strip():
                    flag_invel = False
                    continue
                if flag_invel and hint_invel not in l:
                    v, d, vd = map(float, (l.split()[1:4]))
                    vel.append(v)
                    dep.append(d)
                    damp.append(vd)
                    continue

                if hint_inxyz in l:
                    flag_inxyz = True
                    ev_num = []
                    origin = []
                    lat = []
                    lon = []
                    dp = []
                    x = []
                    y = []
                    z = []
                    mag = []
                    ifx = []
                    nobs = []
                    continue
                if flag_inxyz and not l.strip():
                    flag_inxyz = False
                    continue
                if flag_inxyz and hint_inxyz not in l:
                    thn, bln, tgl = map(int, wrap(l.split()[1], 2))
                    if thn < 90:
                        thn = 2000 + thn
                    elif thn >= 90:
                        thn = 1900 + thn
                    jam, mnt = map(int, wrap(l.split()[2], 2))
                    dtk, mdtk = map(int, l.split()[3].split('.'))
                    if dtk >= 60:
                        dtk = dtk - 60
                        mnt += 1
                    if mnt >= 60:
                        mnt = mnt - 60
                        jam += 1
                    if jam >= 24:
                        jam = jam - 24
                        tgl += 1
                    ev_num.append(int(l[0:4]))
                    origin.append(dt(thn, bln, tgl, jam, mnt, dtk, int(mdtk * 1e4)))
                    lin = float(l[22:30])
                    if l[30:31] == 'S':
                        lin = -lin
                    lat.append(lin)
                    buj = float(l[31:40])
                    if l[40:41] == 'W':
                        buj = -buj
                    lon.append(buj)
                    dp.append(float(l[41:48]))
                    x.append(float(l[48:55]))
                    y.append(float(l[55:62]))
                    z.append(float(l[62:69]))
                    mag.append(float(l[69:74]))
                    ifx.append(int(l[74:76]))
                    nobs.append(int(l[76:80]))
                    continue

                if 'readings for ' in l:
                    stn.append(l.split()[3])
                    obs.append(int(l.split()[5]))
                    continue

            if flag_itdone:
                if hint_itvel in l:
                    flag_itvel = True
                    vel = []
                    dvel = []
                    dep = []
                    continue
                if flag_itvel and not l.strip():
                    flag_itvel = False
                    continue
                if flag_itvel and hint_itvel not in l:
                    v, dv, d = map(float, (l.split()[0:3]))
                    vel.append(v)
                    dvel.append(dv)
                    dep.append(d)
                    continue

                if hint_itxyz in l:
                    flag_itxyz = True
                    ev_num = []
                    ot = []
                    x = []
                    y = []
                    z = []
                    rms = []
                    avres = []
                    dot = []
                    dx = []
                    dy = []
                    dz = []
                    continue
                if flag_itxyz and not l.strip():
                    flag_itxyz = False
                    continue
                if flag_itxyz and hint_itxyz not in l:
                    if isnumber(l[0:5]):
                        ev_num.append(int(l[0:5]))
                        ot.append(float(l[5:15]))
                        x.append(float(l[15:22]))
                        y.append(float(l[22:29]))
                        z.append(float(l[29:36]))
                        rms.append(float(l[36:43]))
                        avres.append(float(l[43:50]))
                        dot.append(float(l[50:59]))
                        dx.append(float(l[59:66]))
                        dy.append(float(l[66:73]))
                        dz.append(float(l[73:80]))
                    continue

                if 'A V E R A G E   of ADJUSTMENTS' in l:
                    av_adj_ot = float(l[50:59])
                    av_adj_x = float(l[59:66])
                    av_adj_y = float(l[66:73])
                    av_adj_z = float(l[73:80])
                    continue
                if 'A V E R A G E   of ABSOLUTE ADJUSTMENTS' in l:
                    abs_adj_ot = float(l[50:59])
                    abs_adj_x = float(l[59:66])
                    abs_adj_y = float(l[66:73])
                    abs_adj_z = float(l[73:80])
                    continue

                if 'Step length damping' in l:
                    used_damping = float(l.split()[4])
                    continue
                elif 'NO step length damping applied' in l:
                    used_damping = l.split()[0]
                    continue

                if hint_stcor in l:
                    flag_stcor = True
                    st_cor_dic = {}
                    stn = []
                    ptcor = []
                    dpcor = []
                    next(f)
                    i += 1
                    continue
                if flag_stcor and not l.strip():
                    st_cor_dic['itr_' + str(itt_num)] = {'st_cor': {'sta': stn,
                                                                    'ptcor': ptcor,
                                                                    'dpcor': dpcor}}
                    flag_invsts = True
                    flag_stcor = False
                    continue
                if flag_stcor and hint_stcor not in l:
                    lcol = l.split()
                    if len(lcol) > 13:
                        stn.append(lcol[0])
                        stn.append(lcol[3])
                        stn.append(lcol[6])
                        stn.append(lcol[9])
                        stn.append(lcol[12])
                        ptcor.append(float(lcol[1]))
                        ptcor.append(float(lcol[4]))
                        ptcor.append(float(lcol[7]))
                        ptcor.append(float(lcol[10]))
                        ptcor.append(float(lcol[13]))
                        dpcor.append(float(lcol[2]))
                        dpcor.append(float(lcol[5]))
                        dpcor.append(float(lcol[8]))
                        dpcor.append(float(lcol[11]))
                        dpcor.append(float(lcol[14]))
                    elif len(lcol) > 10:
                        stn.append(lcol[0])
                        stn.append(lcol[3])
                        stn.append(lcol[6])
                        stn.append(lcol[9])
                        ptcor.append(float(lcol[1]))
                        ptcor.append(float(lcol[4]))
                        ptcor.append(float(lcol[7]))
                        ptcor.append(float(lcol[10]))
                        dpcor.append(float(lcol[2]))
                        dpcor.append(float(lcol[5]))
                        dpcor.append(float(lcol[8]))
                        dpcor.append(float(lcol[11]))
                    elif len(lcol) > 7:
                        stn.append(lcol[0])
                        stn.append(lcol[3])
                        stn.append(lcol[6])
                        ptcor.append(float(lcol[1]))
                        ptcor.append(float(lcol[4]))
                        ptcor.append(float(lcol[7]))
                        dpcor.append(float(lcol[2]))
                        dpcor.append(float(lcol[5]))
                        dpcor.append(float(lcol[8]))
                    elif len(lcol) > 4:
                        stn.append(lcol[0])
                        stn.append(lcol[3])
                        ptcor.append(float(lcol[1]))
                        ptcor.append(float(lcol[4]))
                        dpcor.append(float(lcol[2]))
                        dpcor.append(float(lcol[5]))
                    elif len(lcol) > 1:
                        stn.append(lcol[0])
                        ptcor.append(float(lcol[1]))
                        dpcor.append(float(lcol[2]))
                    continue

            if flag_itfnal:
                if hint_fnxyz in l:
                    flag_fnxyz = True
                    ev_num = []
                    origin = []
                    lat = []
                    lon = []
                    dp = []
                    mag = []
                    nobs = []
                    rms = []
                    x = []
                    y = []
                    z = []
                    continue
                if flag_fnxyz and not l.strip():
                    flag_fnxyz = False
                    continue
                if flag_fnxyz and hint_fnxyz not in l:
                    thn, bln, tgl = map(int, wrap(l.split()[1], 2))
                    if thn < 90:
                        thn = 2000 + thn
                    elif thn >= 90:
                        thn = 1900 + thn
                    jam, mnt = map(int, wrap(l.split()[2], 2))
                    dtk, mdtk = map(int, l.split()[3].split('.'))
                    if dtk >= 60:
                        dtk = dtk - 60
                        mnt += 1
                    if mnt >= 60:
                        mnt = mnt - 60
                        jam += 1
                    if jam >= 24:
                        jam = jam - 24
                        tgl += 1
                    ev_num.append(int(l[0:4]))
                    origin.append(dt(thn, bln, tgl, jam, mnt, dtk, int(mdtk * 1e4)))
                    lin = float(l[22:30])
                    if l[30:31] == 'S':
                        lin = -lin
                    lat.append(lin)
                    buj = float(l[31:40])
                    if l[40:41] == 'W':
                        buj = -buj
                    lon.append(buj)
                    dp.append(float(l[41:48]))
                    mag.append(float(l[48:53]))
                    nobs.append(int(l[53:57]))
                    rms.append(float(l[57:63]))
                    x.append(float(l[63:71]))
                    y.append(float(l[71:78]))
                    z.append(float(l[78:85]))
                    continue

                if hint_sstat in l:
                    flag_sstat = True
                    sta = []
                    pha = []
                    obs = []
                    avres = []
                    avwres = []
                    std = []
                    wsum = []
                    delay = []
                    next(f)
                    i += 1
                    continue
                if flag_sstat and not l.strip():
                    flag_sstat = False
                    continue
                if flag_sstat and hint_sstat not in l:
                    sta.append(l[0:5].strip())
                    pha.append(l[5:9].strip())
                    obs.append(int(l[9:13]))
                    avres.append(float(l[13:21]))
                    avwres.append(float(l[21:29]))
                    std.append(float(l[29:37]))
                    wsum.append(float(l[37:46]))
                    delay.append(float(l[46:54]))
                    continue

                if hint_rstat in l:
                    flag_rstat = True
                    lay = 0
                    nlay = []
                    top = []
                    bot = []
                    vel = []
                    nhyp = []
                    nref = []
                    reflen = []
                    nhit = []
                    av_rayxy = []
                    av_rayz = []
                    rflx = []
                    next(f)
                    i += 1
                    continue
                if flag_rstat and not l.strip():
                    flag_rstat = False
                    continue
                if flag_rstat and hint_rstat not in l:
                    lcol = l.split()
                    lay += 1
                    if len(l) > 77:
                        if isnumber(lcol[0]):
                            nlay.append(int(lcol[0]))
                        else:
                            nlay.append(lay)
                        top.append(float(l[5:13]))
                        bot.append(float(l[16:22]))
                        vel.append(float(l[27:33]))
                        nhyp.append(int(l[38:43]))
                        nref.append(int(l[43:48]))
                        reflen.append(float(l[48:54]))
                        nhit.append(int(l[54:60]))
                        av_rayxy.append(float(l[60:66]))
                        av_rayz.append(float(l[66:72]))
                        rflx.append(int(l[72:78]))
                    else:
                        if isnumber(lcol[0]):
                            nlay.append(int(lcol[0]))
                        else:
                            nlay.append(lay)
                        top.append(float(l[5:13]))
                        bot.append(float(l[5:13]))
                        vel.append(float(l[27:33]))
                        nhyp.append(int(l[38:43]))
                        nref.append(int(l[43:48]))
                        reflen.append(float(l[48:54]))
                        nhit.append(int(l[54:60]))
                        av_rayxy.append(float(l[60:66]))
                        av_rayz.append(float(l[66:72]))
                        rflx.append(0)
                    continue

                if hint_sres in l:
                    flag_sres = True
                    nstn = []
                    stn = []
                    res = []
                    nres = []
                    res1 = []
                    nres1 = []
                    res2 = []
                    nres2 = []
                    res3 = []
                    nres3 = []
                    res4 = []
                    nres4 = []
                    continue
                if flag_sres and not l.strip():
                    flag_sres = False
                    continue
                if flag_sres and len(l) > 77 and hint_sres not in l:
                    nstn.append(int(l[0:4]))
                    stn.append(l[4:11].strip())
                    res.append(float(l[11:19]))
                    nres.append(int(l[20:24]))
                    res1.append(float(l[25:32]))
                    nres1.append(int(l[33:37]))
                    res2.append(float(l[38:45]))
                    nres2.append(int(l[46:50]))
                    res3.append(float(l[51:58]))
                    nres3.append(int(l[59:63]))
                    res4.append(float(l[64:71]))
                    nres4.append(int(l[72:76]))

                if 'Total nr of events' in l:
                    nevt = int(l.split()[5])
                    next(f)
                    i += 1
                    continue
                if 'Total nr of refracted' in l:
                    nrfr = int(l.split()[6])
                    continue
                if 'Total nr of reflected' in l:
                    nrfl = int(l.split()[6])
                    continue
                if 'Total nr of   other' in l:
                    noth = int(l.split()[6])
                    next(f)
                    i += 1
                    continue
                if 'Total nr of    all' in l:
                    nall = int(l.split()[6])
                    next(f)
                    i += 1
                    continue

                if 'Straight and direct rays' in l:
                    if isnumber(l[29:36]):
                        err_drc = float(l[29:36])
                    else:
                        err_drc = l[29:36]
                    continue
                if 'Refracted           rays' in l:
                    if isnumber(l[29:36]):
                        err_rfr = float(l[29:36])
                    else:
                        err_rfr = l[29:36]
                    continue
                if 'Reflected           rays' in l:
                    if isnumber(l[29:36]):
                        err_rfl = float(l[29:36])
                    else:
                        err_rfl = l[29:36]
                    next(f)
                    i += 1
                    continue
                if 'Average horizontal ray length' in l:
                    av_hlen = float(l[32:39])
                    continue
                if 'Average  vertical  ray length' in l:
                    av_vlen = float(l[32:39])
                    continue
                if 'GAPs were between' in l:
                    min_gap = int(l[19:22])
                    max_gap = int(l[27:30])
                    continue
                if '(average GAP was' in l:
                    avr_gap = int(l[22:26])
                    continue

            if hint_avres in l:
                flag_avres = True
                high_avres = 0
                ev_hres = []
                ev_avres = []
                ev_obs = []
                next(f)
                i += 1
                continue
            if flag_avres and not l.strip():
                flag_avres = False
                continue
            if flag_avres and 'Event#' in l:
                high_avres += 1
                ev_hres.append(int(l[7:11]))
                ev_avres.append(float(l[37:43]))
                ev_obs.append(int(l[50:53]))
                continue

            if 'DATVAR=' in l:
                datvar = float(l[8:20])
                sq_res = float(l[40:54])
                rms_res = float(l[68:])
                next(f)
                i += 1
                continue
            if 'straight and direct ray' in l:
                drc_rays = int(l[0:7])
                abs_res_drc = float(l[33:43])
                mres_drc = float(l[44:53])
                continue
            if 'refracted           rays' in l:
                rfr_rays = int(l[0:7])
                abs_res_rfr = float(l[33:43])
                mres_rfr = float(l[44:53])
                continue
            if 'reflected           rays' in l:
                rfl_rays = int(l[0:7])
                abs_res_rfl = float(l[33:43])
                mres_rfl = float(l[44:53])
                next(f)
                i += 1
                continue
            if 'ALL                 RAYS' in l:
                all_rays = int(l[0:7])
                abs_res_all = float(l[33:43])
                mres_all = float(l[44:53])
                diff_rays = float(l[54:-2])
                continue

            if flag_itinit:
                init_dic = {'datvar': datvar,
                            'sqr_res': sq_res,
                            'rms_res': rms_res,
                            'num_highres': high_avres,
                            'evt_highres': {'event': ev_hres,
                                            'avres': ev_avres,
                                            'nobs': ev_obs
                                            },
                            'rays': {'direct': {'num': drc_rays,
                                                'abs_res': abs_res_drc,
                                                'm_res': mres_drc},
                                     'refraction': {'num': rfr_rays,
                                                    'abs_res': abs_res_rfr,
                                                    'm_res': mres_rfr},
                                     'reflection': {'num': rfl_rays,
                                                    'abs_res': abs_res_rfl,
                                                    'm_res': mres_rfl},
                                     'all': {'num': all_rays,
                                             'abs_res': abs_res_all,
                                             'm_res': mres_all,
                                             'diff': diff_rays}
                                     },
                            'event': {'num': ev_num,
                                      'origin': origin,
                                      'lat': lat,
                                      'lon': lon,
                                      'dep': dp,
                                      'x': x,
                                      'y': y,
                                      'z': z,
                                      'mag': mag,
                                      'ifx': ifx,
                                      'nobs': nobs},
                            'vel_mod': {'vel': vel,
                                        'dep': dep,
                                        'damp': damp},
                            'readings': {'sta': stn,
                                         'num': obs}
                            }
                flag_itinit = False
            if flag_itnext:
                iter_dic['itr_' + str(itt_num)] = {'datvar': datvar,
                                                   'sqr_res': sq_res,
                                                   'rms_res': rms_res,
                                                   'num_highres': high_avres,
                                                   'evt_highres': {'event': ev_hres,
                                                                   'avres': ev_avres,
                                                                   'nobs': ev_obs
                                                                   },
                                                   'rays': {'direct': {'num': drc_rays,
                                                                       'abs_res': abs_res_drc,
                                                                       'm_res': mres_drc},
                                                            'refraction': {'num': rfr_rays,
                                                                           'abs_res': abs_res_rfr,
                                                                           'm_res': mres_rfr},
                                                            'reflection': {'num': rfl_rays,
                                                                           'abs_res': abs_res_rfl,
                                                                           'm_res': mres_rfl},
                                                            'all': {'num': all_rays,
                                                                    'abs_res': abs_res_all,
                                                                    'm_res': mres_all,
                                                                    'diff': diff_rays}
                                                            },
                                                   'event': {'num': ev_num,
                                                             'ot': ot,
                                                             'x': x,
                                                             'y': y,
                                                             'z': z,
                                                             'rms': rms,
                                                             'avres': avres,
                                                             'dot': dot,
                                                             'dx': dx,
                                                             'dy': dy,
                                                             'dz': dz},
                                                   'adjustment': {'avr': {'ot': av_adj_ot,
                                                                          'x': av_adj_x,
                                                                          'y': av_adj_y,
                                                                          'z': av_adj_z},
                                                                  'abs': {'ot': abs_adj_ot,
                                                                          'x': abs_adj_x,
                                                                          'y': abs_adj_y,
                                                                          'z': abs_adj_z}
                                                                  },
                                                   'vel_mod': {'vel': vel,
                                                               'dvel': dvel,
                                                               'dep': dep,
                                                               'damp': used_damping}
                                                   }

                if flag_invsts:
                    iter_dic['itr_' + str(itt_num)].update(st_cor_dic['itr_' + str(itt_num)])
                    flag_invsts = False
                flag_itnext = False
            if flag_itstop:
                final_dic = {'nevent': nevt,
                             'nrfrray': nrfr,
                             'nrflray': nrfl,
                             'nothray': noth,
                             'nallray': nall,
                             'event': {'num': ev_num,
                                       'origin': origin,
                                       'lat': lat,
                                       'lon': lon,
                                       'dep': dp,
                                       'x': x,
                                       'y': y,
                                       'z': z,
                                       'mag': mag,
                                       'rms': rms,
                                       'nobs': nobs},
                             'stn_stat': {'stn': sta,
                                          'pha': pha,
                                          'nobs': obs,
                                          'avres': avres,
                                          'avwres': avwres,
                                          'std': std,
                                          'wsum': wsum,
                                          'delay': delay},
                             'ray_stat': {'nlay': nlay,
                                          'top': top,
                                          'bot': bot,
                                          'vel': vel,
                                          'nhyp': nhyp,
                                          'nheadwv': nref,
                                          'lenrfr': reflen,
                                          'nraypass': nhit,
                                          'avrayh': av_rayxy,
                                          'avrayv': av_rayz,
                                          'nrfl': rflx},
                             'avr_err': {'drc': err_drc,
                                         'rfr': err_rfr,
                                         'rfl': err_rfl},
                             'ray_len': {'horizontal': av_hlen,
                                         'vertical': av_vlen},
                             'gap': {'min': min_gap,
                                     'max': max_gap,
                                     'avr': avr_gap},
                             'res_quadrn': {'stnum': nstn,
                                            'stn': stn,
                                            'res': res,
                                            'nres': nres,
                                            'res_q1': res1,
                                            'nres_q1': nres1,
                                            'res_q2': res2,
                                            'nres_q2': nres2,
                                            'res_q3': res3,
                                            'nres_q3': nres3,
                                            'res_q4': res4,
                                            'nres_q4': nres4}
                             }
                flag_itstop = False
    return iter_dic, init_dic, final_dic, ids


def ReadVelestVel(inpmain='mainprint.out'):
    with open(inpmain) as f:

        hint_itvel = ' Velocity model   1'
        flag_itvel = False
        flag_itdone = False

        for l in f:

            if 'ITERATION no' in l:
                itt_num = int(l.split()[2])
                flag_itdone = False
                continue
            if 'iteration done' in l:
                flag_itdone = True
                continue
            if 'final solution' in l:
                break

            if flag_itdone:
                if hint_itvel in l:
                    flag_itvel = True
                    vel = []
                    dep = []
                    damp = []
                    # dvel = []
                    continue
                if flag_itvel and not l.strip():
                    flag_itvel = False
                    continue
                if flag_itvel and hint_itvel not in l:
                    v, dv, d = map(float, (l.split()[0:3]))
                    vel.append(v)
                    dep.append(d)
                    damp.append(1)
                    # dvel.append(dv)

    return itt_num, vel, dep, damp


def ReadVelestVar(inpmain='mainprint.out'):
    model_var = []
    data_var = []

    with open(inpmain) as f:

        flag = False
        hint = ' Velocity model   1'

        for l in f:

            if hint in l:
                flag = True
                tmp = []

            if flag and not l.strip():
                model_var.append(np.linalg.norm(tmp) ** 2)
                flag = False

            if flag and hint not in l:
                tmp.append(float(l.split()[1]))

    with open(inpmain) as f:

        hint = 'DATVAR='

        for l in f:

            if hint in l:
                data_var.append(float(l.split()[1]))

    data_var.pop(0)

    return model_var, data_var


def WriteVelest(inp, area, out_p='phase_P.cnv', out_s='phase_S.cnv', out_arr='arrival.dat', out_cat='catalog.dat',
                out_geom='sts_geometry.dat', out_log='log.txt', elim_event=None):
    """
    :param inp: dictionary data (q_format)
    :param area: dictionary area parameter from filter dictionary
    :param out_p: output file for phase P
    :param out_s: output file for phase S
    :param out_log: output log file
    :param out_arr: output file for arrival data (q_format) input for q_plot
    :param out_cat: output file for extended catalog data (q_format) input for q_plot
    :param out_geom: output file for geometry station (distance & azimuth) (q_format) input for q_plot
    :param elim_event: list of eliminated event (check with catalog BMKG output bmkg2nlloc)
    """

    sts_data = os.path.join(os.path.dirname(__file__), 'input', 'bmkg_station.dat')
    sts_dic = ReadStation(sts_data)

    # cnv = open('PHASE.cnv', 'w')
    cnv_p = open(out_p, 'w')
    cnv_s = open(out_s, 'w')

    cat = open(out_cat, 'w')
    cat.write('ev_num  Y   M  D    h:m:s       lon       lat     dep  mag    time_val           " time_str "        '
              '+/-   ot   lon   lat   dep   mag  mtype   rms   gap  nearsta mode   phnum\n')

    arr = open(out_arr, 'w')
    arr.write('ev_num pha      tp       ts      ts-p  res_p res_s  depth  mag    dis\n')

    sts_gmtry = open(out_geom, 'w')
    sts_gmtry.write('ev_num sts    dist    azi1    azi2\n')

    if elim_event is None:
        elim_event = []
    _err_pha = ''
    _err_sta = ''
    res_P: float = 0
    res_S: float = 0
    tS: float = 0
    tP: float = 0

    bobot = '0'
    IFX = '0'
    maxdep = 0
    maxgap = 0
    maxrms = 0
    minpha = 100
    maxpha = 0
    minS = 100
    maxS = 0

    event = 0
    err_num = 0

    for evt in sorted(inp):
        d = inp[evt]
        lat = d['lat']
        lon = d['lon']
        depth = d['dep']

        event += 1
        mag = d['mag']
        rms = d['rms']
        gap = d['gap']

        _catalog = cat_format(d, evt, sts_data, sts_dic)
        _parameters = cnvpar_format(d, evt, ifx=IFX)

        num_p = 0
        num_s = 0
        # num_pha = 0
        mul_p = 0
        mul_s = 0
        sta_P = 'P'
        sta_S = 'S'
        _arr = ''
        # _PHASES = ''
        _P_phases = ''
        _S_phases = ''

        p = inp[evt]['arr']
        for i in range(len(p['sta'])):
            if len(p['sta'][i]) > 4:
                idSta = p['sta'][i][:4]
                _err_sta += f" station '{p['sta'][i]}' renamed to '{idSta}'\n"
                # print(f"Station '{p['sta'][i]}' renamed to '{idSta}'")
            else:
                idSta = p['sta'][i]
            if idSta == 'BANI':
                idSta = 'BNDI'
            phase = p['pha'][i]
            deltatime = p['del'][i]
            if deltatime < 0 or deltatime > 200:
                _err_pha += f' phase {phase} stasiun {idSta} event no. {event}\n'
                err_num += 1
            res = p['res'][i]

            if p['del'][i] > 1000:
                print(f'\nThere is ilogical phase on event {event}')

            dis, az1, az2 = dist_km(lat, lon, p['sta'][i], sts_dic)
            if az2 is None:
                print(f'Enter station coordinate on {sts_data} to calculate the distance\n')
                continue

            # num_pha += 1
            # if num_pha > 6:
            #     _PHASES += '\n'
            #     num_pha = 1
            # _PHASES += idSta.rjust(4) + phase.rjust(1) + bobot.rjust(1) + ('%.2f' % deltatime).rjust(6)

            if phase == 'P':

                # Write geometry data to files (filter sts)
                if isnumber(az1):
                    sts_gmtry.write(f'{event:<6} {idSta:4} {dis:8.3f} {az1:7.3f} {az2:7.3f}\n')

                sta_P = idSta
                res_P = res
                tP = deltatime
                num_p += 1
                if num_p > 6:
                    _P_phases += '\n'
                    num_p = 1
                    mul_p += 1
                _P_phases += f"{idSta:>4}{phase:1}{bobot:1}{deltatime:6.2f}"

            if phase == 'S':
                sta_S = idSta
                res_S = res
                tS = deltatime
                num_s = num_s + 1
                if num_s > 6:
                    _S_phases += '\n'
                    num_s = 1
                    mul_s += 1
                _S_phases += f"{idSta:>4}{phase:1}{bobot:1}{deltatime:6.2f}"

            if sta_S == sta_P:
                tSP = tS - tP
                _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                         f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')

        _P_phases += '\n\n'
        _S_phases += '\n\n'
        # _PHASES += '\n\n'
        P_pha = mul_p * 6 + num_p
        S_pha = mul_s * 6 + num_s
        cat.write(f"{event:<6} {_catalog} {len(p['sta']):3}\n")
        # cnv.write(f"{_parameters}{event:6}\n{_PHASES}")
        cnv_p.write(f"{_parameters}{event:6}\n{_P_phases}")
        if S_pha > 0:
            cnv_s.write(f"{_parameters}{event:6}\n{_S_phases}")

        if P_pha == 1:
            print(f'event {event} only has 1 phase')
        if P_pha < minpha:
            minpha = P_pha
        if P_pha > maxpha:
            maxpha = P_pha
        if S_pha < minS:
            minS = S_pha
        if S_pha > maxS:
            maxS = S_pha
        if S_pha > 0:
            arr.write(_arr)
        if depth > maxdep:
            maxdep = depth
        if rms > maxrms:
            maxrms = rms
        if gap > maxgap:
            maxgap = gap

    # cnv.close()
    cnv_p.close()
    cnv_s.close()
    cat.close()
    arr.close()
    sts_gmtry.close()

    par_dic = {'ev_num': event,
               'area': area,
               'max_dep': maxdep,
               'max_rms': maxrms,
               'max_gap': maxgap,
               'min_p': minpha,
               'max_p': maxpha,
               'min_s': minS,
               'max_s': maxS,
               'phase': {'err_num': err_num,
                         'err_pha': _err_pha,
                         },
               'err_sta': _err_sta,
               'elim_ev': elim_event
               }

    Log(inp=par_dic, out=out_p, log=out_log)


def CNV_Filter(inp, filt, out, pha='P', out_cat='catalog.dat', out_log='log.txt'):
    """
    :param inp: dictionary data (ReadCNV)
    :param filt: dictionary filter parameter
    :param out: output file name
    :param pha: phase type (P/S)
    :param out_cat: output file for extended catalog data (q_format) input for q_plot
    :param out_log: output log file

    """
    sts_data = os.path.join('input', 'bmkg_station.dat')
    sts_dic = ReadStation(sts_data)

    idx_event = []
    _err_pha = ''
    _err_sta = ''
    bobot = '0'
    IFX = '0'
    maxdep = 0
    maxgap = 0
    maxrms = 0
    minpha = 100
    maxpha = 0

    f = filt
    area = f['area']
    lst_phase = f['lst_pha']
    ulat = area['top']
    blat = area['bot']
    llon = area['left']
    rlon = area['right']
    max_depth = f['max_dep']
    max_rms = f['max_rms']
    max_gap = f['max_gap']
    min_pha = f['min_pha']
    min_time = f['min_tim']
    max_time = f['max_tim']
    # max_spatial_err = f['max_err']
    # rem_fixd = f['rm_fixd']

    cnv = open(out, 'w')
    cat = open(out_cat, 'w')
    cat.write('ev_num Y M D    h:m:s       lon      lat   dep  mag    time_val             '
              'time_str          +/- ot   lon  lat  dep  mag mtype rms gap phnum\n')

    evts = 0
    err_num = 0
    for evt in sorted(inp):
        d = inp[evt]
        lat = d['lat']
        lon = d['lon']
        depth = d['dep']

        if len(lst_phase) > 0:
            index_P = [i for i, x in enumerate(d['arr']['pha']) if x == pha]
            sts_P = [d['arr']['sta'][i] for i in index_P]
            sel_stP = [sts_P[i] for i, x in enumerate(sts_P) if x in lst_phase]
            ct_P = len(sel_stP)
        else:
            ct_P = d['arr']['pha'].count(pha)

        if min_time <= evt <= max_time and \
                ulat >= lat >= blat and \
                llon <= lon <= rlon and \
                depth <= max_depth and \
                d['rms'] <= max_rms and \
                d['gap'] <= max_gap and \
                ct_P >= min_pha:  # and ct_S >= min_S

            evts += 1
            event = int(d['nevt'])
            idx_event.append(str(event))

            # mag = d['mag']
            rms = d['rms']
            gap = d['gap']

            _catalog = cat_format(d, evt, sts_data, sts_dic)
            _parameters = cnvpar_format(d, evt, ifx=IFX)

            num_pha = 0
            mul_p = 0
            _P_phases = ''

            p = inp[evt]['arr']

            for i in range(len(p['del'])):

                if len(p['sta'][i]) > 4:
                    idSta = p['sta'][i][:4]
                    print(f"Station '{p['sta'][i]}' renamed to '{idSta}'")
                else:
                    idSta = p['sta'][i]

                phase = p['pha'][i]

                deltatime = p['del'][i]
                if deltatime < 0 or deltatime > 200:
                    _err_pha += f' phase {phase} stasiun {idSta} event no. {event}\n'
                    err_num += 1

                if d['arr']['del'][i] > 1000:
                    print(f'\nThere is ilogical phase on event {event}')

                if len(lst_phase) > 0:
                    if phase == pha and idSta in lst_phase:
                        num_pha += 1
                        if num_pha > 6:
                            _P_phases += '\n'
                            num_pha = 1
                            mul_p += 1
                        _P_phases += f"{idSta:>4}{phase:1}{bobot:1}{deltatime:6.2f}"
                else:
                    if phase == pha:
                        num_pha += 1
                        if num_pha > 6:
                            _P_phases += '\n'
                            num_pha = 1
                            mul_p += 1
                        _P_phases += f"{idSta:>4}{phase:1}{bobot:1}{deltatime:6.2f}"

            _P_phases += '\n\n'

            P_pha = mul_p * 6 + num_pha

            cat.write(f"{event:6} {_catalog} {len(p['del']):3}\n")

            cnv.write(f"{_parameters}{event:6}\n{_P_phases}")

            if P_pha == 1:
                print(event)
            if P_pha < minpha:
                minpha = P_pha
            if P_pha > maxpha:
                maxpha = P_pha
            if depth > maxdep:
                maxdep = depth
            if rms > maxrms:
                maxrms = rms
            if gap > maxgap:
                maxgap = gap

    cnv.close()
    cat.close()

    par_dic = {'ev_num': evts,
               'area': filt['area'],
               'max_dep': maxdep,
               'max_rms': maxrms,
               'max_gap': maxgap,
               'min_p': minpha,
               'max_p': maxpha,
               'min_s': 0,
               'max_s': 0,
               'phase': {'err_num': err_num,
                         'err_pha': _err_pha,
                         },
               'err_sta': _err_sta,
               'elim_ev': []
               }

    Log(inp=par_dic, out=out, log=out_log)

    return idx_event
