import math as mt
from eQ_rw import *
from datetime import datetime as dt

"""
rewrite ReadNLLoc and Write

"""
# fileinput = ['D:/project/python/pycharm/geoQ/q_modul/converter/Ambon2.hyp']
# mag_cat = 'D:/project/python/pycharm/geoQ/q_modul/converter/output/nlloc_mag.dat'

def ReadNLLoc(fileinput='data', mag_cat='nlloc_mag.dat'):

    baris = []
    dsec = 40
    nloc_event = 0
    for f in fileinput:
        file = open(f, 'r')
        baris += file.readlines()
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
    # print(f'\nelimcat: {n_elim_cat}\n')
    nlloc_dic = {}
    i = 0
    ev = 0
    lat_gau = 0
    lon_gau = 0
    dep_gau = 0
    gap = 0
    rms = 0
    err_time = 0
    err_lat = 0
    err_lon = 0
    err_v = 0
    elim_cat = 0
    elim_event = []
    while i < len(baris):
        # if len(baris[i]) > 0 and baris[i][0] == 'SEARCH':
        if len(baris[i]) > 0 and baris[i][0] == 'GEOGRAPHIC':
            ev += 1
            arr_sta = []
            arr_pha = []
            arr_dis = []
            arr_azi = []
            arr_del = []
            arr_res = []
            arr_wt = []
            mod = baris[i-2][1]
            tahun = baris[i][2]
            bulan = baris[i][3].zfill(2)
            tanggal = baris[i][4].zfill(2)
            jam = baris[i][5].zfill(2)
            menit = baris[i][6].zfill(2)
            detik = ('%.6f' % float(baris[i][7])).zfill(7)
            sec = int(float(detik))
            msec = int(float('%.6f' % (float(detik) - sec)) * 1e6)
            ot = dt(int(tahun), int(bulan), int(tanggal), int(jam), int(menit), sec, msec)
            lintang = float('%.6f' % float(baris[i][9]))
            bujur = float('%.6f' % float(baris[i][11]))
            depth = float('%.6f' % float(baris[i][13]))
            # get magnitudo from bmkg catalog
            mag = 'Nan'
            mag_type = 'Unk'
            err_mag = 'Nan'
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
            if mag == 'Nan':
                print(f'Event {ev} magnitude not found on catalog. '
                      f'Check OT time deviation or number of eliminated catalog!')
            j = 0
            while j < 1:
                i += 1
                if len(baris[i]) > 0 and baris[i][0] == 'QUALITY':
                    rms = float('%.3f' % float(baris[i][8]))
                    gap = float(baris[i][12])
                elif len(baris[i]) > 0 and baris[i][0] == 'STATISTICS':
                    err_lon = mt.sqrt(float('%.4f' % float(baris[i][8])))
                    err_lat = mt.sqrt(float('%.4f' % float(baris[i][14])))
                    err_v = mt.sqrt(float('%.4f' % float(baris[i][18])))
                elif len(baris[i]) > 0 and baris[i][0] == 'STAT_GEOG':
                    lat_gau = float('%.6f' % float(baris[i][2]))
                    lon_gau = float('%.6f' % float(baris[i][4]))
                    dep_gau = float('%.6f' % float(baris[i][6]))
                elif len(baris[i]) > 0 and baris[i][0] == 'QML_OriginQuality':
                    pha_count = int(baris[i][4])
                    err_time = float(baris[i][12])
                    # elif len(baris[i]) > 0 and baris[i][0] == 'DIFFERENTIAL':
                    i += 4
                    # j += 1
                elif len(baris[i]) > 0 and baris[i][0] == 'PHASE':
                    i += 1
                    for i in range(i, i + pha_count):
                        try:
                            idSta = baris[i][0]
                            phase = baris[i][4]
                            jam_arr = baris[i][7][0:2]
                            menit_arr = baris[i][7][2:4]
                            detik_arr = '%.4f' % float(baris[i][8])
                            sec = int(float(detik_arr))
                            msec = int(float('%.4f' % (float(detik_arr) - sec)) * 1e6)
                            at = dt(int(tahun), int(bulan), int(tanggal), int(jam_arr), int(menit_arr), sec, msec)
                            deltatime = float('%.4f' % (at.timestamp() - ot.timestamp()))
                            if deltatime < 0:
                                if int(jam_arr) == 0 and int(menit_arr) < 25:
                                    deltatime = float('%.4f' % (deltatime + 86400))
                                    if deltatime > 1000:
                                        print(f'\nThere is ilogical phase on event {ev}')
                                        deltatime = 0
                            res = baris[i][17]
                            wt = baris[i][18]
                            dis = baris[i][22]
                            azi = baris[i][23]
                            if not isnumber(dis) or not isnumber(azi) or not isnumber(res):
                                print(f'Potential data error line {i}')
                            arr_sta.append(idSta)
                            arr_pha.append(phase)
                            arr_dis.append(dis)
                            arr_azi.append(azi)
                            arr_del.append(deltatime)
                            arr_res.append(res)
                            arr_wt.append(wt)
                        except:
                            print(f'Potential data error line {i}')
                elif len(baris[i]) > 0 and baris[i][0] == 'END_PHASE':
                    j += 1
            # i += 1
            nlloc_dic[ot] = {'yea': tahun,
                             'mon': bulan,
                             'dat': tanggal,
                             'hou': jam,
                             'min': menit,
                             'sec': detik,
                             'lat': lintang,
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
                                     'wt': arr_wt}
                             }
        i += 1
    print(f'Eliminated events on BMKG catalog {elim_event}')
    return nlloc_dic, ids, elim_event


def WriteNLLoc(inp, inp_mag=None, filt=None, out_nlloc='phase.obs', out_log='log.txt', out_arr='arrival.dat',
               out_cat='catalog.dat', out_geom='sts_geometry.dat', inptype='BMKG',
               filt_flag=False, prob_flag=False, elim_event=None):

    nlloc = open(out_nlloc, 'w')
    nll_mag = open(inp_mag, 'w')

    cat = open(out_cat, 'w')
    cat.write('ev_num Y M D    h:m:s       lon      lat   dep  mag    time_val             '
              'time_str          +/- ot   lon  lat  dep  mag mtype rms gap phnum\n')

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
    tSP: float = 0
    bobot = '0'
    IFX = '0'
    mag = 0
    maxdep = 0
    maxgap = 0
    maxrms = 0
    minpha = 100
    maxpha = 0
    minS = 100
    maxS = 0

    sts_data = os.path.join(os.path.dirname(__file__), 'input', 'bmkg_station.dat')
    sts_dic = ReadStation(sts_data)

    event = 0
    err_num = 0
    for evt in sorted(bmkgdata):
        d = bmkgdata[evt]

        lat = d['lat']
        lon = d['lon']
        depth = d['dep']

        if len(lst_phase) > 0:
            index_P = [i for i, x in enumerate(d['arr']['pha']) if x == 'P']
            index_S = [i for i, x in enumerate(d['arr']['pha']) if x == 'S']
            sts_P = [d['arr']['sta'][i] for i in index_P]
            sts_S = [d['arr']['sta'][i] for i in index_S]
            sel_stP = [sts_P[i] for i, x in enumerate(sts_P) if x in lst_phase]
            sel_stS = [sts_S[i] for i, x in enumerate(sts_S) if x in lst_phase]
            ct_P = len(sel_stP)
            ct_S = len(sel_stS)
        else:
            ct_P = d['arr']['pha'].count('P')
            ct_S = d['arr']['pha'].count('S')
        if min_time <= evt <= max_time and \
                ulat >= lat >= blat and \
                llon <= lon <= rlon and \
                depth <= max_depth and \
                d['mod'] == mode and \
                d['rms'] <= max_rms and \
                d['gap'] <= max_gap and \
                ct_P >= min_P:  # and ct_S >= min_S:  # evt <= dt(2019,9,24) and \ d['dep'] <= max_depth and \
            # ambon_data[evt] = d

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

            p = bmkgdata[evt]['arr']
            for i in range(len(p['sta'])):
                if len(p['sta'][i]) > 4:
                    idSta = p['sta'][i][:4]
                else:
                    idSta = p['sta'][i]
                phase = p['pha'][i]
                deltatime = p['del'][i]
                if deltatime < 0 or deltatime > 200:
                    _err_pha += f' phase {phase} stasiun {idSta} event no. {event}\n'
                    err_num += 1
                res = p['res'][i]
                phase = phase[:1]

                try:
                    sta_lon = sts_dic[p['sta'][i]]['lon']
                    sta_lat = sts_dic[p['sta'][i]]['lat']
                    dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
                    dis = np.round(dis / 1000, decimals=3)
                except KeyError:
                    print(f'Station {idSta} not found in the station list!\n'
                          f'Enter station coordinate on {sts_data} to calculate the distance')
                    continue

                if phase == 'P' and idSta in lst_phase:

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

                if phase == 'S' and idSta in lst_phase:
                    sta_S = idSta
                    res_S = res
                    tS = deltatime
                    num_s = num_s + 1

                if sta_S == sta_P and idSta in lst_phase:
                    arr_s = evt + td(seconds=tS)
                    tSP = arr_s.timestamp() - arr_p.timestamp()
                    _NLLocPha += f"       {np.round(arr_p.second + arr_p.microsecond / 1e6 + tSP, decimals=2):05.2f} " \
                                 f"{phase} 1"

                    _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                             f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')

            _NLLocPha += '\n\n'
            P_pha = num_p
            S_pha = num_s
            cat.write(str(event) + ' ' + _catalog + ' ' + str(len(p['sta'])) + '\n')
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
        # else:
        # print('Filtered events: ' + str(evt))

    nlloc.close()
    cat.close()
    arr.close()
    nll_mag.close()
