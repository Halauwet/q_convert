import os
import math as mt
from eQ_rw import ids, Log, ReadStation, isnumber, error_dic, cat_format, dist_km
from datetime import datetime as dt
from datetime import timedelta as td


"""
===========================================
HypoDD module by @eqhalauwet
==========================================

Python module for writting HypoDD phase file, ploting and exporting to GMT input.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. Write hypoDD phase file

Logs:

2020-Agu: WriteHypoDD

"""


def WriteHypoDD(inp, area, out='phase.dat', out_arr='arrival.dat', out_cat='catalog.dat',
                out_geom='sts_geometry.dat', out_log='log.txt', elim_event=None):
    """
    :param inp: dictionary data (q_format)
    :param area: dictionary area parameter from filter dictionary
    :param out: output hypodd phase file
    :param out_arr: output file for arrival data (q_format) input for q_plot
    :param out_cat: output file for extended catalog data (q_format) input for q_plot
    :param out_geom: output file for geometry station (distance & azimuth) (q_format) input for q_plot
    :param out_log: output log file
    :param elim_event: list of eliminated event (check with catalog BMKG output bmkg2nlloc)
    """

    sts_data = os.path.join(os.path.dirname(__file__), 'input', 'bmkg_station.dat')
    sts_dic = ReadStation(sts_data)

    pha = open(out, 'w')

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
        mag = d['mag']
        rms = d['rms']
        gap = d['gap']

        event += 1
        
        err_tim, err_lon, err_lat, err_dep, err_mag = error_dic(d)

        err_hz = mt.sqrt(err_lat ** 2 + err_lon ** 2)
        
        _parameters = (
            f"# {str(evt.year):4} {int(evt.month):2} {int(evt.day):2} "
            f"{int(evt.hour):2} {int(evt.minute):2} {(evt.second + evt.microsecond * 1e-6):5.2f} "
            f"{lat:6.2f}   {lon:7.2f}   {depth:6.1f} {mag:4.1f} "
            f"{float(err_hz):5.2f} {float(err_dep):5.2f} {rms:7.3f}")

        _catalog = cat_format(d, evt, sts_data, sts_dic)

        num_p = 0
        num_s = 0
        sta_P = 'P'
        sta_S = 'S'
        _arr = ''
        _pha = ''

        p = inp[evt]['arr']
        for i in range(len(p['sta'])):

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
                _pha += f"{idSta.rjust(5)}    {deltatime:8.2f}   {float(bobot):5.3f}   {phase}\n"

            if phase == 'S':
                sta_S = idSta
                res_S = res
                tS = deltatime
                num_s = num_s + 1
                _pha += f"{idSta.rjust(5)}    {deltatime:8.2f}   {float(bobot):5.3f}   {phase}\n"

            if sta_S == sta_P:
                arr_s = evt + td(seconds=tS)
                tSP = arr_s.timestamp() - arr_p.timestamp()
                _arr += (f'{event:<6} {idSta:4} {tP:8.3f} {tS:8.3f} {tSP:8.3f} {float(res_P):5.2f} '
                         f'{float(res_S):5.2f} {depth:6.2f} {mag:.2f} {dis:8.3f}\n')

        P_pha = num_p
        S_pha = num_s
        pha.write(f"{_parameters}    {event:6}\n{_pha}")
        cat.write(f"{event:<6} {_catalog} {len(p['sta']):3}\n")

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

    pha.close()
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

    Log(inp=par_dic, out=out, log=out_log)

