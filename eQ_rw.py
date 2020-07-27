import os
import sys
import numpy as np
from obspy_geodetics import gps2dist_azimuth

"""
===========================================
earthquake katalog reader by @eqhalauwet
==========================================

Python module for reading arrival data files.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. ReadBMKG() read list_detail_2 format from old PGN format (2008-mid 2016), new PGN format (2016-present)
PGR IX Seiscomp3 2008 format (2009-mid 2019) and 2017 format (mid 2019-present) to python dictionary.

2. ReadNLLoc() read NLLoc LocSum.hyp to python dictionary

3. WriteVelest() write eQ dictionary data to Velest.cnv 

Logs:

2017-Sep: Added _check_header line to automatic check data format from few Seiscomp3 version (see Notes).
2019-Oct: Major change: store readed data in dictionary format.
2020-May: Correction: select phase only without 'X' residual (unused phase on routine processing).
2020-Jun: Added function ReadNLLoc() to read NLLoc LocSum.hyp into python dictionary
2020-Jun: Added function WriteVelest() to write eQ dictionary data to Velest.cnv 


2020-Jul: Added function q_filter() to filter q_dictionary data
"""

ids = '__earthquake data converter by eQ Halauwet__\n\n'


def isnumber(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


def phase_filter(inp_data, used_station):
    """
    :param inp_data: dictionary data
    :param used_station: list of used station phase
    """
    for evt in sorted(inp_data):

        arrv = inp_data[evt]['arr']

        j = 0
        for i in range(len(arrv['del'])):

            if arrv['sta'][i-j] not in used_station:

                # print(f"delete phase {arrv['sta'][i-j]}")
                del arrv['sta'][i-j]
                del arrv['net'][i-j]
                del arrv['dis'][i-j]
                del arrv['azi'][i-j]
                del arrv['pha'][i-j]
                del arrv['del'][i-j]
                del arrv['res'][i-j]
                del arrv['wth'][i-j]

                j += 1

    return inp_data


def q_filter(inp_data, filt=None, inptype='BMKG', prob_flag=False):
    """
    :param inp_data: dictionary data
    :param filt: dictionary filter parameter
    :param inptype: input data from BMKG or NLLoc
    :param prob_flag: (if use NLLoc input) option to use Gausian expectation (GAU)
                      location or Minimum likelihood location
    """

    if filt is None:
        sys.exit('\nFilter flag is on, please give filter parameter\n')

    f = filt
    fromdate = f['min_tim']
    todate = f['max_tim']
    area = f['area']
    ulat = area['top']
    blat = area['bot']
    llon = area['left']
    rlon = area['right']
    max_depth = f['max_dep']
    rem_fixd = f['rm_fixd']
    max_rms = f['max_rms']
    max_gap = f['max_gap']
    max_spatial_err = f['max_err']
    mode = f['mode']
    lst_phase = f['phase']['lst_pha']
    min_P = f['phase']['min_P']
    min_S = f['phase']['min_S']

    if len(lst_phase) != 0:
        inp_data = phase_filter(inp_data, lst_phase)

    if mode == '':
        if inptype == 'bmkg' or inptype == 'BMKG':
            mode = 'manual'
        else:
            mode = 'OCTREE'

    filt_data = {}

    for evt in sorted(inp_data.keys()):

        evt_data = inp_data[evt]
        ct_P = evt_data['arr']['pha'].count('P')
        ct_S = evt_data['arr']['pha'].count('S')

        if inptype == 'bmkg' or inptype == 'BMKG':
            lat = evt_data['lat']
            lon = evt_data['lon']
            depth = evt_data['dep']
        elif inptype == 'nlloc' or inptype == 'NLLoc':
            if prob_flag:
                lat = evt_data['lat_gau']
                lon = evt_data['lon_gau']
                depth = evt_data['dep_gau']
            else:
                lat = evt_data['lat']
                lon = evt_data['lon']
                depth = evt_data['dep']
        else:
            sys.exit('\nCurently support input from "BMKG" list detail or "NLLoc" LocSum.hyp\n')

        if rem_fixd:
            if fromdate <= evt <= todate and \
                    ulat >= lat >= blat and \
                    llon <= lon <= rlon and \
                    depth <= max_depth and \
                    evt_data['mod'] == mode and \
                    evt_data['rms'] <= max_rms and \
                    evt_data['gap'] <= max_gap and \
                    evt_data['err']['e_lat'] <= max_spatial_err and \
                    evt_data['err']['e_lon'] <= max_spatial_err and \
                    float(evt_data['err']['e_dep']) <= max_spatial_err and \
                    ct_P >= min_P and ct_S >= min_S and \
                    evt_data['err']['e_dep'] != '-0.0':

                if inptype == 'nlloc' or inptype == 'NLLoc':
                    if prob_flag:
                        print('\nUsing NLLoc Gausian Expectation location\n')
                        inp_data[evt]['lon'] = inp_data[evt]['lon_gau']
                        inp_data[evt]['lat'] = inp_data[evt]['lat_gau']
                        inp_data[evt]['dep'] = inp_data[evt]['dep_gau']
                    del inp_data[evt]['lon_gau']
                    del inp_data[evt]['lat_gau']
                    del inp_data[evt]['dep_gau']

                filt_data[evt] = inp_data[evt]

        else:

            if fromdate <= evt <= todate and \
                    ulat >= lat >= blat and \
                    llon <= lon <= rlon and \
                    depth <= max_depth and \
                    evt_data['mod'] == mode and \
                    evt_data['rms'] <= max_rms and \
                    evt_data['gap'] <= max_gap and \
                    evt_data['err']['e_lat'] <= max_spatial_err and \
                    evt_data['err']['e_lon'] <= max_spatial_err and \
                    float(evt_data['err']['e_dep']) <= max_spatial_err and\
                    ct_P >= min_P and ct_S >= min_S:

                if inptype == 'nlloc' or inptype == 'NLLoc':
                    if prob_flag:
                        print('\nUsing NLLoc Gausian Expectation location\n')
                        inp_data[evt]['lon'] = inp_data[evt]['lon_gau']
                        inp_data[evt]['lat'] = inp_data[evt]['lat_gau']
                        inp_data[evt]['dep'] = inp_data[evt]['dep_gau']
                    del inp_data[evt]['lon_gau']
                    del inp_data[evt]['lat_gau']
                    del inp_data[evt]['dep_gau']

                filt_data[evt] = inp_data[evt]

    return filt_data


def Log(inp, out='phase', log='log.txt'):
    p = inp
    area = p['area']
    pha = p['phase']
    event = p['ev_num']
    err_num = pha['err_num']
    ulat = area['top']
    blat = area['bot']
    llon = area['left']
    rlon = area['right']
    maxdep = p['max_dep']
    maxrms = p['max_rms']
    maxgap = p['max_gap']
    minpha = p['min_p']
    maxpha = p['max_p']
    minS = p['min_s']
    maxS = p['max_s']
    _err_pha = pha['err_pha']
    _err_sta = p['err_sta']
    elim_event = p['elim_ev']

    if event > 0:
        if err_num > 0:
            if len(_err_sta) > 0:
                log1 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"{err_num} potential phase error (TT > 200), see log.txt\n\n"
                        f"All output are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

                log2 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"{err_num} potential phase error (TT > 200):\n{_err_pha}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All output are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
            else:
                log1 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"{err_num} potential phase error (TT > 200), see log.txt\n\n"
                        f"All output are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

                log2 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"{err_num} potential phase error (TT > 200):\n{_err_pha}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All output are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

        else:

            if len(_err_sta) > 0:
                log1 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All output are on 'output' folder:"
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
                log2 = log1
            else:
                log1 = (f"Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n "
                        f"maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n "
                        f"minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n "
                        f"minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All output are on 'output' folder:"
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
                log2 = log1

    else:

        log1 = f'Tidak ada data yang berhasil dikonvert!\nPeriksa data atau parameter filter\n\n{_err_pha}'
        log2 = log1

    print('\n' + ids + log1)
    file = open(log, 'w')
    file.write(ids + log2)
    file.close()


def ReadStation(inpsta='input/bmkg_station.dat'):
    sta_dic = {}

    with open(inpsta) as f:

        for l in f:

            if l.strip():

                chk_hdr = isnumber(l.split()[1])

                if chk_hdr:
                    sta = l.split()[0]
                    lat, lon = map(float, (l.split()[1:3]))

                    sta_dic[sta] = {'lat': lat,
                                    'lon': lon
                                    }
    return sta_dic


def dist_km(lat, lon, sts, sts_dic):

    dist = None
    az1 = None
    az2 = None

    try:
        sta_lon = sts_dic[sts]['lon']
        sta_lat = sts_dic[sts]['lat']
        dis, az1, az2 = gps2dist_azimuth(lat, lon, sta_lat, sta_lon)
        dist = np.round(dis / 1000, decimals=3)

    except KeyError:
        # template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        # message = template.format(type(ex).__name__, ex.args)
        print(f'Station {sts} not found in the station list!')

    return dist, az1, az2


def data_count(data_dic):

    jml_ev = 0
    jml_P = 0
    jml_S = 0

    for i in data_dic:
        jml_ev += 1
        jml_P += data_dic[i]['arr']['pha'].count('P')
        jml_S += data_dic[i]['arr']['pha'].count('S')

    print(f'jml event {jml_ev}, jml P = {jml_P},  jml S = {jml_S}')

    return jml_ev, jml_P, jml_S


def error_dic(data_dic):
    if 'err' in data_dic:
        # input bmkg/nllocdic
        err_tim = data_dic['err']['e_tim']
        err_lon = data_dic['err']['e_lon']
        err_lat = data_dic['err']['e_lat']
        err_dep = data_dic['err']['e_dep']
        err_mag = data_dic['err']['e_mag']

    else:
        # input cnvdic
        err_tim = data_dic['errt']
        err_lon = data_dic['erlon']
        err_lat = data_dic['erlat']
        err_dep = data_dic['errv']
        err_mag = data_dic['ermag']

    return err_tim, err_lon, err_lat, err_dep, err_mag


def cat_format(data_dic, evt_key, sts_data, sts_dic):
    lat = data_dic['lat']
    lon = data_dic['lon']
    depth = data_dic['dep']

    time_sec = evt_key.timestamp()
    displayed_time: str = evt_key.strftime('%d-%m-%Y %H:%M:%S UTC')

    err_tim, err_lon, err_lat, err_dep, err_mag = error_dic(data_dic)

    if 'err' in data_dic:
        mag_typ = data_dic['typ']
        dis = data_dic['arr']['dis'][0]
        mode = data_dic['mod']
    else:
        mag_typ = 'M'
        dis = '0.0'
        mode = 'nomode'

    dist, az1, az2 = dist_km(lat, lon, data_dic['arr']['sta'][0], sts_dic)
    if az2 is None:
        print(f'Enter station coordinate on {sts_data} to calculate the distance\n')
    else:
        dis = dist

    # err_hz = ('%.2f' % mt.sqrt(err_lat ** 2 + err_lon ** 2))

    _catalog = (
        f"{evt_key.year} {str(evt_key.month).zfill(2)} {str(evt_key.day).zfill(2)} {str(evt_key.hour).zfill(2)}:"
        f"{str(evt_key.minute).zfill(2)}:{('%.2f' % (evt_key.second + evt_key.microsecond * 1e-6)).zfill(5)} "
        f"{lon:8.4f} {lat:8.4f} {depth:6.2f} {data_dic['mag']:.2f} {time_sec:.3f} \"{displayed_time}\" +/- "
        f"{err_tim:5.2f} {err_lon:5.2f} {err_lat:5.2f} {float(err_dep):5.2f} {float(err_mag):5.2f} {mag_typ:6} "
        f"{data_dic['rms']:6.3f} {round(data_dic['gap']):3} {float(dis):8.3f} {mode:6}")

    return _catalog


def arr_filter(inp, out='arrival_filt.dat', index=None):
    if os.stat(inp).st_size == 0:
        sys.exit("Arrival data is empty\n")
    elif index is None or index == []:
        sys.exit("Give event number list to parameter 'index=' \n")

    arr_out = open(out, 'w')
    arr_out.write('ev_num pha      tp       ts      ts-p  res_p res_s  depth  mag    dis\n')

    with open(inp) as f:

        for l in f:

            if l.split()[0] in index:
                arr_out.write(l)

    arr_out.close()


def geometry_filter(inp, out='sts_geometry_filt.dat', index=None):
    if os.stat(inp).st_size == 0:
        sys.exit("Geometry data is empty\n")
    elif index is None or index == []:
        sys.exit("Give event number list to parameter 'index=' \n")

    stat_out = open(out, 'w')
    stat_out.write('ev_num sts    dist    azi1    azi2\n')

    with open(inp) as f:

        for l in f:

            if l.split()[0] in index:
                stat_out.write(l)

    stat_out.close()
