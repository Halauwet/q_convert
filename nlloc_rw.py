import os
import math as mt
import numpy as np
from eQ_rw import ids, isnumber, Log, ReadStation, cat_format, dist_km
from datetime import datetime as dt
from datetime import timedelta as td

"""
rewrite ReadNLLoc and Write

"""
# fileinput = 'D:/project/python/pycharm/geoQ/q_modul/converter/Ambon2.hyp'
# mag_cat = 'D:/project/python/pycharm/geoQ/q_modul/converter/output/nlloc_mag.dat'

def ReadNLLoc(fileinput='data.hyp', mag_cat='nlloc_mag.dat'):
    """
    :param fileinput: nlloc locsum.hyp file
    :param mag_cat: catalog magnitudo from bmkg2nlloc output (take magnitudo value from bmkg catalog
    if not calculate magnitudo directly on nlloc
    """

    dsec = 40
    nloc_event = 0

    # Crosscheck nlloc event and bmkg magnitudo catalog to detect eliminated event
    file = open(fileinput, 'r')
    baris = file.readlines()
    file.close()
    for i in range(len(baris)):
        baris[i] = baris[i].split()
        if len(baris[i]) > 0 and baris[i][0] == 'GEOGRAPHIC':
            nloc_event += 1
    cat = open(mag_cat, 'r')
    event = cat.readlines()
    for i in range(len(event)):
        event[i] = event[i].split()
    cat.close()
    n_elim_cat = len(event) - nloc_event

    flag_evt = False
    flag_pha = False
    flag_wrt = False

    nlloc_dic = {}
    i = 0
    ev = 0
    elim_cat = 0
    elim_event = []

    with open(fileinput, "r", -1) as f:

        for l in f:

            i += 1

            if 'Location completed.' in l:
                ev += 1
                flag_evt = True
                flag_wrt = False
                continue

            if flag_evt:

                if 'SEARCH' in l:
                    mod = l.split()[1]
                    continue

                if 'GEOGRAPHIC' in l:
                    tahun, bulan, tanggal, jam, menit = map(int, l.split()[2:7])
                    detik = float(l.split()[7])
                    sec = int(detik)
                    msec = round((detik - sec) * 1e6)

                    try:
                        ot = dt(tahun, bulan, tanggal, jam, menit, sec, msec)
                    except ValueError:
                        print(f'Error encountered on event {ev} data-line {i}\n')

                    lintang, bujur, depth = map(float, l.split()[9:14:2])

                    mag = 'NaN'
                    mag_type = 'Unk'
                    err_mag = 'NaN'
                    for j in range(n_elim_cat - elim_cat + 1):
                        if ev + j + elim_cat == int(event[ev - 1 + j + elim_cat][0]) and \
                                round(ot.timestamp()) in range(round(float(event[ev - 1 + j + elim_cat][1])) - dsec,
                                                               round(float(event[ev - 1 + j + elim_cat][1])) + dsec):
                            mag = float('%.2f' % float(event[ev - 1 + j + elim_cat][2]))
                            mag_type = event[ev - 1 + j + elim_cat][3]
                            err_mag = event[ev - 1 + j + elim_cat][4]
                            elim_cat += j
                            break
                        else:
                            elim_event.append(ev + j + elim_cat)
                            print(f'Eliminated, event no. {ev + j + elim_cat} on BMKG catalog')
                    if mag == 'NaN':
                        print(f'Event {ev} magnitude was not found on catalog. '
                              f'Check OT time deviation or number of eliminated catalog!')

                if 'QUALITY' in l:
                    rms = float(l.split()[8])
                    gap = float(l.split()[12])
                    continue

                if 'STATISTICS' in l:
                    err_lon = mt.sqrt(float(l.split()[8]))
                    err_lat = mt.sqrt(float(l.split()[14]))
                    err_v = mt.sqrt(float(l.split()[18]))
                    continue

                if 'STAT_GEOG' in l:
                    lat_gau, lon_gau, dep_gau = map(float, l.split()[2:7:2])
                    continue

                if 'QML_OriginQuality' in l:
                    # pha_count = int(l.split()[4])
                    err_time = float(l.split()[12])
                    continue

                if 'PHASE ID' in l:  # unused phased included
                    arr_sta = []
                    arr_pha = []
                    arr_dis = []
                    arr_azi = []
                    arr_del = []
                    arr_res = []
                    arr_wth = []
                    flag_pha = True
                    continue
                if flag_pha and 'END_PHASE' in l:
                    flag_pha = False
                    flag_evt = False
                    flag_wrt = True
                    continue
                if flag_pha and 'PHASE' not in l:
                    try:
                        jam_arr = int(l.split()[7][0:2])
                        menit_arr = int(l.split()[7][2:4])
                        detik_arr = float(l.split()[8])
                        sec = int(detik_arr)
                        msec = round((detik_arr - sec) * 1e6)
                        try:
                            at = dt(tahun, bulan, tanggal, jam_arr, menit_arr, sec, msec)
                            if at < ot:
                                at = at + td(days=1)
                            deltatime = float('%.4f' % (at.timestamp() - ot.timestamp()))
                        except ValueError:
                            print(f'Error encountered on event {ev} data-line {i}\n')

                        res = l.split()[17]
                        dis = l.split()[22]
                        azi = l.split()[23]
                        if not isnumber(dis) or not isnumber(azi) or not isnumber(res):
                            print(f'Potential data error line {i}')

                        arr_sta.append(l.split()[0])
                        arr_pha.append(l.split()[4])
                        arr_dis.append(float(dis))
                        arr_azi.append(int(float(azi)))
                        arr_del.append(deltatime)
                        arr_res.append(float(res))
                        arr_wth.append(l.split()[18])
                    except:
                        print(f'Potential data error line {i}')

            if flag_wrt:
                nlloc_dic[ot] = {'lat': lintang,
                                 'lon': bujur,
                                 'dep': depth,
                                 'lat_gau': lat_gau,
                                 'lon_gau': lon_gau,
                                 'dep_gau': dep_gau,
                                 'mag': mag,
                                 'typ': mag_type,
                                 'gap': gap,
                                 'rms': rms,
                                 'mod': mod,
                                 'err': {'e_tim': err_time,
                                         'e_lat': err_lat,
                                         'e_lon': err_lon,
                                         'e_dep': err_v,
                                         'e_mag': err_mag},
                                 'arr': {'sta': arr_sta,
                                         # 'net': [],
                                         'dis': arr_dis,
                                         'azi': arr_azi,
                                         'pha': arr_pha,
                                         'del': arr_del,
                                         'res': arr_res,
                                         'wth': arr_wth}
                                 }
                flag_wrt = False

    print(f'Eliminated events on BMKG catalog {elim_event}')
    return nlloc_dic, ids, elim_event


def WriteNLLoc(inp, area, out_nlloc='phase.obs', out_mag='nlloc_mag.dat', out_arr='arrival.dat', out_cat='catalog.dat',
               out_geom='sts_geometry.dat', out_log='log.txt', elim_event=None):

    sts_data = os.path.join(os.path.dirname(__file__), 'input', 'bmkg_station_new.dat')
    sts_dic = ReadStation(sts_data)

    nlloc = open(out_nlloc, 'w')
    nll_mag = open(out_mag, 'w')

    cat = open(out_cat, 'w')
    cat.write('ev_num  Y   M  D    h:m:s       lon       lat     dep  mag    time_val           " time_str "        '
              '+/-   ot   lon   lat   dep   mag  mtype   rms   gap  nearsta mode   phnum\n')

    arr = open(out_arr, 'w')
    arr.write('ev_num pha      tp       ts      ts-p  res_p res_s  depth  mag    dis\n')

    sts_gmtry = open(out_geom, 'w')
    sts_gmtry.write('ev_num sts    dist    azi1    azi2\n')

    # List var
    _err_pha = ''
    res_P: float = 0
    res_S: float = 0
    tS: float = 0
    tP: float = 0
    bobot = '0'
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
        time_sec = evt.timestamp()
        nll_mag.write(
            f"{event:<6} {time_sec} {d['mag']:4.2f} {d['typ']:6} {float(d['err']['e_mag']):5.2f} {evt}\n")
        mag = d['mag']
        rms = d['rms']
        gap = d['gap']

        _catalog = cat_format(d, evt, sts_data, sts_dic)

        num_p = 0
        num_s = 0
        sta_P = 'P'
        sta_S = 'S'
        _arr = ''
        _NLLocPha = ''

        p = inp[evt]['arr']
        for i in range(len(p['sta'])):
            # if len(p['sta'][i]) > 4:
            #     idSta = p['sta'][i][:4]
            # else:
            idSta = p['sta'][i]

            if idSta == 'BANI':
                idSta = 'BNDI'

            phase = p['pha'][i]
            deltatime = p['del'][i]
            if deltatime < 0 or deltatime > 200:
                _err_pha += f' phase {phase} stasiun {idSta} event no. {event}\n'
                err_num += 1
            if deltatime > 1000:
                print(f'\nThere is ilogical phase on event {event}')
            res = p['res'][i]
            phase = phase[:1]

            dis, az1, az2 = dist_km(lat, lon, p['sta'][i], sts_dic)
            if az2 is None:
                print(f'Enter station coordinate on {sts_data} to calculate the distance\n')
                continue

            if phase == 'P':

                # Write geometry data to files (filter sts)
                if isnumber(az1):
                    sts_gmtry.write(f'{event:<6} {idSta:4} {dis:8.3f} {az1:7.3f} {az2:7.3f}\n')

                sta_P = idSta
                res_P = res
                tP = deltatime
                num_p += 1

                arr_p = evt + td(seconds=tP)
                if num_p == 1:
                    _NLLocPha += f"{idSta.ljust(4)} {phase} {bobot} {str(arr_p.year)[2:]}{arr_p.month:02d}" \
                                 f"{arr_p.day:02d}{arr_p.hour:02d}{arr_p.minute:02d}" \
                                 f"{arr_p.second + np.round(arr_p.microsecond / 1e6, decimals=2):05.2f}"
                else:
                    _NLLocPha += f"\n{idSta.ljust(4)} {phase} {bobot} {str(arr_p.year)[2:]}{arr_p.month:02d}" \
                                 f"{arr_p.day:02d}{arr_p.hour:02d}{arr_p.minute:02d}" \
                                 f"{arr_p.second + np.round(arr_p.microsecond / 1e6, decimals=2):05.2f}"

            if phase == 'S':
                sta_S = idSta
                res_S = res
                tS = deltatime
                num_s = num_s + 1

            if sta_S == sta_P:
                arr_s = evt + td(seconds=tS)
                tSP = arr_s.timestamp() - arr_p.timestamp()
                _NLLocPha += f"       {np.round(arr_p.second + arr_p.microsecond / 1e6 + tSP, decimals=2):05.2f} " \
                             f"{phase} 1"

                _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                         f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')

        _NLLocPha += '\n\n'
        P_pha = num_p
        S_pha = num_s
        cat.write(f"{event:<6} {_catalog} {len(p['sta']):3}\n")
        nlloc.write(_NLLocPha)

        if P_pha == 1:
            print(event)
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

    nlloc.close()
    nll_mag.close()
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
               'err_sta': [],
               'elim_ev': elim_event
               }

    Log(inp=par_dic, out=out_nlloc, log=out_log)
