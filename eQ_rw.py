import os
import sys
import utm
import math as mt
import numpy as np
import pandas as pd
from pyproj import Proj
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

    # if mode == '':
    #     if inptype == 'bmkg' or inptype == 'BMKG':
    #         mode = 'manual'
    #     else:
    #         mode = 'OCTREE'

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

        if fromdate <= evt <= todate and \
                ulat >= lat >= blat and \
                llon <= lon <= rlon and \
                depth <= max_depth and \
                evt_data['rms'] <= max_rms and \
                evt_data['gap'] <= max_gap and \
                evt_data['err']['e_lat'] <= max_spatial_err and \
                evt_data['err']['e_lon'] <= max_spatial_err and \
                float(evt_data['err']['e_dep']) <= max_spatial_err and \
                ct_P >= min_P and ct_S >= min_S:

            if rem_fixd:
                if evt_data['err']['e_dep'] != '-0.0':
                    pass
                else:
                    continue

            if mode == '' or mode is None:
                pass
            else:
                if evt_data['mod'] == mode:
                    pass
                else:
                    continue

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
                log1 = (f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on each event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"{err_num} potentially error phase (TT > 200), see log.txt\n\n"
                        f"All the outputs are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

                log2 = (f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on each event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"{err_num} potentially phase error (TT > 200):\n{_err_pha}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All the outputs are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
            else:
                log1 = (f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on each event {maxS}\n\n"
                        f"{err_num} potential phase error (TT > 200), see log.txt\n\n"
                        f"All the outputs are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

                log2 = (f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on each event {maxS}\n\n"
                        f"{err_num} potentially phase error (TT > 200):\n{_err_pha}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All the outputs are on 'output' folder: "
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")

        else:

            if len(_err_sta) > 0:
                log1 =(f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on event {maxS}\n\n"
                        f"Renamed station:\n{_err_sta}\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All the outputs are on 'output' folder:"
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
                log2 = log1
            else:
                log1 = (f"Converts {event} events in the areas: lat({ulat} - {blat}) & lon({llon} - {rlon}):\n "
                        f"max depth {maxdep} km\n max RMS {maxrms} secs\n max gap {maxgap} deg\n "
                        f"min P-phase on each event {minpha}\n max P-phase on each event {maxpha}\n "
                        f"min S-phase on each event {minS}\n max S-phase on event {maxS}\n\n"
                        f"Eliminated events on BMKG Catalog:\n {elim_event}\n\n"
                        f"All the outputs are on 'output' folder:"
                        f"'{out}', 'catalog.dat' and wadati 'arrival.dat'")
                log2 = log1

    else:

        log1 = f'Tidak ada data yang berhasil dikonvert!\nPeriksa data atau parameter filter\n\n{_err_pha}'
        log2 = log1

    print('\n' + ids + log1)
    file = open(log, 'w')
    file.write(ids + log2)
    file.close()


def ReadStation(inpsta='input/bmkg_station_new.dat', delimiter=","):
    sta_dic = {}

    df = pd.read_csv(inpsta, skipinitialspace=True, delimiter=delimiter, dtype={"loc": str})
    df = df.fillna('')

    for i, r in df.iterrows():
        sta_dic[str(r['sta'])] = {'net': str(r['net']),
                                  'loc': str(r['loc']),
                                  'cha': str(r['ch']),
                                  'lat': r['lat'],
                                  'lon': r['lon']}

    # #Old stations format
    # with open(inpsta) as f:
    #
    #     for l in f:
    #
    #         if l.strip():
    #
    #             chk_hdr = isnumber(l.split()[1])
    #
    #             if chk_hdr:
    #                 sta = l.split()[0]
    #                 lat, lon = map(float, (l.split()[1:3]))
    #
    #                 sta_dic[sta] = {'lat': lat,
    #                                 'lon': lon
    #                                 }
    return sta_dic


def calculate_interval(max_range, max_interval=10, default=20):
    allowed_intervals = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]

    for interval in allowed_intervals:
        if max_range / interval <= max_interval:
            return interval

    return default


def calculate_height(jm_width, r_bounds):
    """
    Calculate the height of a GMT Mercator plot.

    Parameters:
    min_lon (float): Minimum longitude of the region.
    max_lon (float): Maximum longitude of the region.
    min_lat (float): Minimum latitude of the region.
    max_lat (float): Maximum latitude of the region.
    map_width_cm (float): Width of the map in centimeters.

    Returns:
    float: Height of the map in centimeters.
    """

    min_lon, max_lon, min_lat, max_lat = r_bounds

    # Calculate the mid-latitude
    mid_lat = (min_lat + max_lat) / 2

    # Calculate the differences
    delta_lon = max_lon - min_lon
    delta_lat = max_lat - min_lat

    # Calculate the aspect ratio
    aspect_ratio = delta_lat / (delta_lon * mt.cos(mt.radians(mid_lat)))

    # Calculate the height
    map_height_cm = jm_width * aspect_ratio

    return map_height_cm


def map_area(inp_area, out_dir='output', max_dep=100):
    T = inp_area['top'] + 1.5
    B = inp_area['bot'] - 1
    L = inp_area['left'] - 1
    R = inp_area['right'] + 1

    utm_zone = utm.from_latlon(np.mean([B, T]), np.mean([L, R]))[2]
    p = Proj(proj='utm', zone=utm_zone, ellps='WGS84')  # use kwargs

    [Xx_min, X_max], [Yy_min, Y_max] = p([L, R], [B, T])
    lon_dist = X_max - Xx_min
    lat_dist = Y_max - Yy_min

    interval_dep = calculate_interval(abs(max_dep), 5)
    interval_map = int(max(calculate_interval(abs(T-B), 10), calculate_interval(abs(R-L), 10)))
    interval_inset = int(max(calculate_interval(abs(T-B), 6), calculate_interval(abs(R-L), 6)))

    J = 20
    # J = 13 * lon_dist / lat_dist
    # J = np.ceil((R-L) / (T-B) * 130)/10

    # r_bounds = (-180, 180, -60, 60)  # xmin, xmax, ymin, ymax
    # jm_width = 20  # Width of the map in cm (-JM<width>)

    # height = calculate_height(jm_width, r_bounds)

    JY = calculate_height(J, (L, R, B, T))

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(os.path.join(out_dir, 'inc')):
        os.makedirs(os.path.join(out_dir, 'inc'))

    bat = open(os.path.join(out_dir, 'inc', 'area.bat'), 'w')
    bat.write(f'set tlat={T}\n')
    bat.write(f'set blat={B}\n')
    bat.write(f'set rlon={R}\n')
    bat.write(f'set llon={L}\n')
    bat.write(f'set J={J}\n')
    bat.write(f'set JY={JY+0.1}\n')
    bat.write(f'set Jdep={JY/2.7}\n\n')
    bat.write(f'set DX={(J-5)/2}\n')
    bat.write(f'set DX2={(J-5)}\n\n')
    bat.write(f'set DY={(J-5)}\n\n')
    bat.write(f'set maxZ={max_dep}\n\n')

    bat.write(f'set itvD={int(interval_dep)}\n')
    bat.write(f'set itvL={interval_map}\n')
    bat.write(f'set itvLf={interval_map/2}\n')
    bat.write(f'set itvLi={interval_inset}\n')

    if R - L < 2:
        ll_inset = L - (1.6 * (R - L))
        rl_inset = R + (1.6 * (R - L))
        bl_inset = B - (1.3 * (T - B))
        tl_inset = T + (1.3 * (T - B))
    elif R - L < 5:
        ll_inset = L - (1.3 * (R - L))
        rl_inset = R + (1.3 * (R - L))
        bl_inset = B - (1 * (T - B))
        tl_inset = T + (1 * (T - B))
    elif R - L < 8:
        ll_inset = L - (0.9 * (R - L))
        rl_inset = R + (0.9 * (R - L))
        bl_inset = B - (0.7 * (T - B))
        tl_inset = T + (0.7 * (T - B))
    else:
        ll_inset = L - (0.7 * (R - L))
        rl_inset = R + (0.7 * (R - L))
        bl_inset = B - (1 / 3 * (T - B))
        tl_inset = T + (1 / 3 * (T - B))

    Rx = float(R - ((R - L) / 8))
    Ry1 = float(T - ((T - B) / 15))
    Ry2 = float(T - ((T - B) / 5))
    if R - L < 2:
        skala = 50
    else:
        skala = mt.floor((R - L) / 2) * 50

    bat.write(f'set R=%llon%/%rlon%/%blat%/%tlat%\n')
    bat.write(f'set R_inset={ll_inset}/{rl_inset}/{bl_inset}/{tl_inset}\n\n')
    bat.write(f'set coast=pscoast -JM{J} -R%R% -Ggray -Dh -K -X1.6 -Y6.5\n')
    bat.write(f'set basemap=psbasemap -JM{J} -R%R% -Tdg{Rx}/{Ry1}+w1.2+f1+jTC -Lg{Rx}/{Ry2}+c-1+w{skala}k+l+ab+jTC '
              f'--FONT_ANNOT_PRIMARY=11 --FONT_LABEL=14 --MAP_FRAME_TYPE=plain -O -K\n')
    bat.close()


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
        print(f'Station {sts} was not found in the station list!')

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
        if len(data_dic['arr']['dis']) == 0:
            dis = '0.0'
        else:
            dis = data_dic['arr']['dis'][0]
        mode = data_dic['mod']
    else:
        mag_typ = 'M'
        dis = '0.0'
        mode = 'nomode'

    nearsta = ""
    if len(data_dic['arr']['sta']) != 0:
        nearsta = data_dic['arr']['sta'][0]
        dist, az1, az2 = dist_km(lat, lon, nearsta, sts_dic)
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
        f"{data_dic['rms']:6.3f} {round(data_dic['gap']):3} {nearsta:9} {float(dis):8.3f} {mode:6}")

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
