import math as mt
from eQ_rw import *
from datetime import datetime as dt
from datetime import timedelta as td

"""
Belum include cat_format()

next: add Nordic_format()  

"""

def WriteNordic(inp, filt, out='nordic.out', out_log='log.txt', inptype='BMKG',
                filt_flag=False, prob_flag=False, elim_event=None):

    sts_data = os.path.join('input', 'bmkg_station.dat')
    sts = ReadStation(sts_data)

    if elim_event is None:
        elim_event = []
    _err_pha = ''
    _err_sta = ''
    sufx_pha = '4'
    res_P: float = 0
    res_S: float = 0
    tS: float = 0
    tP: float = 0
    # tSP: float = 0
    bobot = '0'
    IFX = '0'
    # mag = 0
    maxdep = 0
    maxgap = 0
    maxrms = 0
    minpha = 100
    maxpha = 0
    minS = 100
    maxS = 0

    f = filt
    area = f['area']
    if filt_flag:
        lst_phase = f['lst_pha']
        ulat = area['top']
        blat = area['bot']
        llon = area['left']
        rlon = area['right']
        mode = f['mode']
        max_rms = f['max_rms']
        max_gap = f['max_gap']
        min_P = f['min_P']
        min_S = f['min_S']
        max_spatial_err = f['max_err']
        max_depth = f['max_dep']
        rem_fixd = f['rem_fixd']
        min_time = f['min_tim']
        max_time = f['max_tim']
    else:
        # convert all data
        lst_phase = []
        llon = -180
        rlon = 180
        blat = -90
        ulat = 90
        max_depth = 800
        rem_fixd = False
        max_gap = 360
        max_rms = 10.0
        min_P = 4
        min_S = 0
        max_spatial_err = 10000
        min_time = dt(1970, 1, 3)
        max_time = dt(9999, 1, 1)
        if inptype == 'bmkg' or inptype == 'BMKG':
            mode = 'manual'
        else:
            mode = 'OCTREE'

    nordic_out = open(out, 'w')
    cat = open('output/catalog.dat', 'w')
    cat.write('ev_num Y M D    h:m:s       lon      lat   dep  mag    time_val           " time_str "'
              '        +/- ot   lon  lat  dep  mag mtype rms gap nearsta mode phnum\n')
    arr = open('output/arrival.dat', 'w')
    arr.write('ev_num pha tp ts ts-p res_p res_s depth mag dis\n')
    event = 0
    err_num = 0
    if inptype == 'nlloc' or inptype == 'NLLoc':
        if prob_flag:
            print('\nUsing NLLoc Gausian Expectation location')
        else:
            print('\nUsing NLLoc Maximum Likelihood location')
    for evt in sorted(inp):
        d = inp[evt]
        if inptype == 'bmkg' or inptype == 'BMKG':
            lat = d['lat']
            lon = d['lon']
            depth = d['dep']
        elif inptype == 'nlloc' or inptype == 'NLLoc':
            if prob_flag:
                lat = d['lat_gau']
                lon = d['lon_gau']
                depth = d['dep_gau']
            else:
                lat = d['lat']
                lon = d['lon']
                depth = d['dep']
        else:
            print('Curently support input from "BMKG" list detail or "NLLoc" LocSum.hyp')
            break
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
        if rem_fixd:
            if min_time <= evt <= max_time and \
                    ulat >= lat >= blat and \
                    llon <= lon <= rlon and \
                    depth <= max_depth and \
                    d['mod'] == mode and \
                    d['rms'] <= max_rms and \
                    d['gap'] <= max_gap and \
                    d['err']['e_lat'] <= max_spatial_err and d['err']['e_lon'] <= max_spatial_err and \
                    d['err']['e_dep'] != '-0.0' and \
                    ct_P >= min_P:  # and ct_S >= min_S
                # d['err']['e_dep'] <= max_spatial_err and \
                # mt.sqrt(d['err']['e_lat']**2 + d['err']['e_lon']**2) <= max_spatial_err and \
                event += 1
                time_sec = evt.timestamp()
                displayed_time: str = evt.strftime('%d-%m-%Y %H:%M:%S UTC')
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
                err_lat = d['err']['e_lat']
                err_lon = d['err']['e_lon']
                err_hz = ('%.2f' % mt.sqrt(err_lat ** 2 + err_lon ** 2))
                mag = d['mag']
                rms = d['rms']
                gap = d['gap']
                mtype = d['typ'][:2]
                mtype = mtype[1:]
                if mtype == '':
                    mtype = 'M'
                elif mtype == 'w':
                    mtype = 'W'
                elif mtype == 'b':
                    mtype = 'B'

                try:
                    sta_lon = sts[d['arr']['sta'][0]]['lon']
                    sta_lat = sts[d['arr']['sta'][0]]['lat']
                    dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
                    dis = np.round(dis / 1000, decimals=3)
                except:
                    print(f"Nearest station {d['arr']['sta'][0]} not found in the station list!\n"
                          f"Enter station coordinate on {sts_data} to calculate the distance")
                    dis = d['arr']['dis'][0]

                _parameters = (f" {d['yea']} {d['mon']}{d['dat']} {d['hou']}{d['min']} {float(d['sec']):4.1f}"
                               f" L {lat:7.3f} {lon:7.3f}{depth:5.1f} BMKG"
                               f"{ct_P:3d}{rms:4.1f}{mag:4.1f}{mtype}BMKG               1\n"
                               f" GAP={gap:3d}      {d['err']['e_tim']:6.2f}    {err_lat:6.1f}  {err_lon:6.1f}"
                               f"{float(d['err']['e_dep']):5.1f}       1E+01       1E+01       1E+01E\n")

                # _parameters = (f" {d['yea']} {d['mon']}{d['dat']} {d['hou']}{d['min']} {float(d['sec']):4.1f}"
                #                f" L {lat:7.3f} {lon:7.3f}{depth:5.1f} BMKG"
                #                f"{ct_P:3d}{rms:4.1f}                        1\n"
                #                f" GAP={gap:3d}      {d['err']['e_tim']:6.2f}    {err_lat:6.1f}  {err_lon:6.1f}"
                #                f"{float(d['err']['e_dep']):5.1f}\n")

                _catalog = (f"{d['yea']} {d['mon']} {d['dat']} {d['hou']}:{d['min']}:{d['sec']} "
                            f"{lon:.4f} {lat:.4f} {depth:.2f} {mag:.2f} {time_sec:.3f} \"{displayed_time}\" +/- "
                            f"{d['err']['e_tim']:.2f} {err_lon:.2f} {err_lat:.2f} {float(d['err']['e_dep']):.2f} "
                            f"{float(d['err']['e_mag'])} {d['typ']} {rms:.3f} {gap} {dis} {d['mod']}")

                num_p = 0
                num_s = 0
                num_pha = 0
                mul_p = 0
                mul_s = 0
                sta_P = 'P'
                sta_S = 'S'
                _arr = ''
                _PHASES = ' STAT SP IPHASW D HRMM SECON CODA AMPLIT PERI AZIMU VELO AIN AR TRES W  DIS CAZ7\n'
                # _P_phases = ''
                # _S_phases = ''
                p = inp[evt]['arr']
                for i in range(len(p['sta'])):
                    if len(p['sta'][i]) > 4:
                        idSta = p['sta'][i][:4]
                        _err_sta += f" station '{p['sta'][i]}' renamed to '{idSta}'\n"
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
                        sta_lon = sts[p['sta'][i]]['lon']
                        sta_lat = sts[p['sta'][i]]['lat']
                        dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
                        dis = np.round(dis/1000, decimals=3)
                    except:
                        print(f'Station {idSta} not found in the station list!\n'
                              f'Enter station coordinate on {sts_data} to calculate the distance')
                        continue

                    if len(lst_phase) > 0:
                        if idSta in lst_phase:
                            num_pha += 1
                            art = evt + td(seconds=deltatime)
                            # if num_pha > 6:
                            #     _PHASES += '\n'
                            #     num_pha = 1
                            _PHASES += (f" {idSta:4s}     {phase:1s}   {bobot:1s}   "
                                        f"{art.hour:02d}{art.minute:02d} {art.second + art.microsecond * 1e-6:5.2f}"
                                        f"                                   {float(res):5.1f}  "
                                        f"{float(p['dis'][i]):5.1f} {int(p['azi'][i]):3d}{sufx_pha}\n")
                            if phase == 'P' and idSta in lst_phase:
                                sta_P = idSta
                                res_P = res
                                tP = deltatime
                                num_p += 1
                                # if num_p > 6:
                                #     _P_phases += '\n'
                                #     num_p = 1
                                #     mul_p += 1
                                # _P_phases += idSta.rjust(4) + phase.rjust(1) +
                                # bobot.rjust(1) + ('%.2f' % deltatime).rjust(6)
                            if phase == 'S' and idSta in lst_phase:
                                sta_S = idSta
                                res_S = res
                                tS = deltatime
                                num_s = num_s + 1
                                # if num_s > 6:
                                #     _S_phases += '\n'
                                #     num_s = 1
                                #     mul_s += 1
                                # _S_phases += idSta.rjust(4) + phase.rjust(1) +
                                # bobot.rjust(1) + ('%.2f' % deltatime).rjust(6)
                            if sta_S == sta_P and idSta in lst_phase:
                                tSP = tS - tP
                                _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                                         f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')
                    else:
                        num_pha += 1
                        arrt = evt + td(seconds=deltatime)
                        _PHASES += (f" {idSta:4s}     {phase:1s}   {bobot:1s}   "
                                    f"{arrt.hour:02d}{arrt.minute:02d} {arrt.second + arrt.microsecond * 1e-6:5.2f}"
                                    f"                                   {float(res):5.1f}  "
                                    f"{float(p['dis'][i]):5.1f} {int(p['azi'][i]):3d}{sufx_pha}\n")
                        if phase == 'P':
                            sta_P = idSta
                            res_P = res
                            tP = deltatime
                            num_p += 1
                        if phase == 'S':
                            sta_S = idSta
                            res_S = res
                            tS = deltatime
                            num_s = num_s + 1
                        if sta_S == sta_P:
                            tSP = tS - tP
                            _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                                     f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')
                _PHASES += '\n'
                P_pha = mul_p * 6 + num_p
                S_pha = mul_s * 6 + num_s
                cat.write(str(event) + ' ' + _catalog + ' ' + str(len(p['sta'])) + '\n')
                nordic_out.write(_parameters + _PHASES)
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
        else:
            if min_time <= evt <= max_time and \
                    ulat >= lat >= blat and \
                    llon <= lon <= rlon and \
                    depth <= max_depth and \
                    d['mod'] == mode and \
                    d['rms'] <= max_rms and \
                    d['gap'] <= max_gap and \
                    d['err']['e_lat'] <= max_spatial_err and d['err']['e_lon'] <= max_spatial_err and \
                    ct_P >= min_P:  # and ct_S >= min_S
                # d['err']['e_dep'] <= max_spatial_err and \
                # mt.sqrt(d['err']['e_lat']**2 + d['err']['e_lon']**2) <= max_spatial_err and \
                event += 1
                time_sec = evt.timestamp()
                displayed_time: str = evt.strftime('%d-%m-%Y %H:%M:%S UTC')
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
                err_lat = d['err']['e_lat']
                err_lon = d['err']['e_lon']
                err_hz = ('%.2f' % mt.sqrt(err_lat ** 2 + err_lon ** 2))
                mag = d['mag']
                rms = d['rms']
                gap = d['gap']
                mtype = d['typ'][:2]
                mtype = mtype[1:]
                if mtype == '':
                    mtype = 'M'
                elif mtype == 'w':
                    mtype = 'W'
                elif mtype == 'b':
                    mtype = 'B'

                try:
                    sta_lon = sts[d['arr']['sta'][0]]['lon']
                    sta_lat = sts[d['arr']['sta'][0]]['lat']
                    dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
                    dis = np.round(dis / 1000, decimals=3)
                except:
                    print(f"Nearest station {d['arr']['sta'][0]} not found in the station list!\n"
                          f"Enter station coordinate on {sts_data} to calculate the distance")
                    dis = d['arr']['dis'][0]

                _parameters = (f" {d['yea']} {d['mon']}{d['dat']} {d['hou']}{d['min']} {float(d['sec']):4.1f}"
                               f" L {lat:7.3f} {lon:7.3f}{depth:5.1f} BMKG"
                               f"{ct_P:3d}{rms:4.1f}{mag:4.1f}{mtype}BMKG               1\n"
                               f" GAP={gap:3d}      {d['err']['e_tim']:6.2f}    {err_lat:6.1f}  {err_lon:6.1f}"
                               f"{float(d['err']['e_dep']):5.1f}       1E+01       1E+01       1E+01E\n")

                # _parameters = (f" {d['yea']} {d['mon']}{d['dat']} {d['hou']}{d['min']} {float(d['sec']):4.1f}"
                #                f" L {lat:7.3f} {lon:7.3f}{depth:5.1f} BMKG"
                #                f"{ct_P:3d}{rms:4.1f}                        1\n"
                #                f" GAP={gap:3d}      {d['err']['e_tim']:6.2f}    {err_lat:6.1f}  {err_lon:6.1f}"
                #                f"{float(d['err']['e_dep']):5.1f}\n")

                _catalog = (f"{d['yea']} {d['mon']} {d['dat']} {d['hou']}:{d['min']}:{d['sec']} "
                            f"{lon:.4f} {lat:.4f} {depth:.2f} {mag:.2f} {time_sec:.3f} \"{displayed_time}\" +/- "
                            f"{d['err']['e_tim']:.2f} {err_lon:.2f} {err_lat:.2f} {float(d['err']['e_dep']):.2f} "
                            f"{float(d['err']['e_mag'])} {d['typ']} {rms:.3f} {gap} {dis} {d['mod']}")
                num_p = 0
                num_s = 0
                num_pha = 0
                mul_p = 0
                mul_s = 0
                sta_P = 'P'
                sta_S = 'S'
                _arr = ''
                _PHASES = ' STAT SP IPHASW D HRMM SECON CODA AMPLIT PERI AZIMU VELO AIN AR TRES W  DIS CAZ7\n'
                # _P_phases = ''
                # _S_phases = ''
                p = inp[evt]['arr']
                for i in range(len(p['sta'])):
                    if len(p['sta'][i]) > 4:
                        idSta = p['sta'][i][:4]
                        _err_sta += f" station '{p['sta'][i]}' renamed to '{idSta}'\n"
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
                        sta_lon = sts[p['sta'][i]]['lon']
                        sta_lat = sts[p['sta'][i]]['lat']
                        dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
                        dis = np.round(dis/1000, decimals=3)
                    except:
                        print(f'Station {idSta} not found in the station list!\n'
                              f'Enter station coordinate on {sts_data} to calculate the distance')
                        continue

                    if len(lst_phase) > 0:
                        if idSta in lst_phase:
                            num_pha += 1
                            art = evt + td(seconds=deltatime)
                            # if num_pha > 6:
                            #     _PHASES += '\n'
                            #     num_pha = 1
                            _PHASES += (f" {idSta:4s}     {phase:1s}   {bobot:1s}   "
                                        f"{art.hour:02d}{art.minute:02d} {art.second + art.microsecond * 1e-6:5.2f}"
                                        f"                                   {float(res):5.1f}  "
                                        f"{float(p['dis'][i]):5.1f} {int(p['azi'][i]):3d}{sufx_pha}\n")
                            if phase == 'P' and idSta in lst_phase:
                                sta_P = idSta
                                res_P = res
                                tP = deltatime
                                num_p += 1
                                # if num_p > 6:
                                #     _P_phases += '\n'
                                #     num_p = 1
                                #     mul_p += 1
                                # _P_phases += idSta.rjust(4) + phase.rjust(1) +
                                # bobot.rjust(1) + ('%.2f' % deltatime).rjust(6)
                            if phase == 'S' and idSta in lst_phase:
                                sta_S = idSta
                                res_S = res
                                tS = deltatime
                                num_s = num_s + 1
                                # if num_s > 6:
                                #     _S_phases += '\n'
                                #     num_s = 1
                                #     mul_s += 1
                                # _S_phases += idSta.rjust(4) + phase.rjust(1) +
                                # bobot.rjust(1) + ('%.2f' % deltatime).rjust(6)
                            if sta_S == sta_P and idSta in lst_phase:
                                tSP = tS - tP
                                _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                                         f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')
                    else:
                        num_pha += 1
                        arrt = evt + td(seconds=deltatime)
                        _PHASES += (f" {idSta:4s}     {phase:1s}   {bobot:1s}   "
                                    f"{arrt.hour:02d}{arrt.minute:02d} {arrt.second + arrt.microsecond * 1e-6:5.2f}"
                                    f"                                   {float(res):5.1f}  "
                                    f"{float(p['dis'][i]):5.1f} {int(p['azi'][i]):3d}{sufx_pha}\n")
                        if phase == 'P':
                            sta_P = idSta
                            res_P = res
                            tP = deltatime
                            num_p += 1
                        if phase == 'S':
                            sta_S = idSta
                            res_S = res
                            tS = deltatime
                            num_s = num_s + 1
                        if sta_S == sta_P:
                            tSP = tS - tP
                            _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                                     f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')
                _PHASES += '\n'
                P_pha = mul_p * 6 + num_p
                S_pha = mul_s * 6 + num_s
                cat.write(str(event) + ' ' + _catalog + ' ' + str(len(p['sta'])) + '\n')
                nordic_out.write(_parameters + _PHASES)
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
    nordic_out.close()
    cat.close()
    arr.close()
    par_dic = {'ev_num': event,
               'area': filt['area'],
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
    Log(inp=par_dic, out=out, log=out_log)


