import math
import sys
import pickle
from eQ_rw import *
from datetime import datetime as dt
from datetime import timedelta as td
from bmkg_rw import ReadBMKG
sys.path.append('/mnt/d/q_repo/q_modul')
sys.path.append('D:/q_repo/q_modul')
from check_outliers import *

"""
===========================================
earthquake katalog converter by @eqhalauwet
==========================================

Python script for convert BMKG arrival data to NLLoc input (Hypo71 phase format).

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. It is read bmkg arrival data using "ReadBMKG" module then convert to Hypo71 phase format.
2. Data can be filtered of area and quality parameter (gap, rms, min phase, etc).
3. Output in Hypo71 phase format and additional catalog list and arrival.

Logs:

2018-Sep: Added filter parameter.
2020-May: Change file input type from obj to list, so that it can import from several files.
2020-May: Add filter phase routine
2020-Jun: Add output to NLLoc phase

"""
fileinput = ['D:/BMKG/Katalog/Arrival PGN/list_detail_2008.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2009.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2010.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2011.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2012.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2013.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2014.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2015.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2016.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2017.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2018.txt',
             'D:/BMKG/Katalog/Arrival PGN/list_detail_2019.txt']

bmkgdata, ids = ReadBMKG(fileinput)

# pkl_file = open("dict_data/ambon_data(2008-2019).pkl", "rb")
# bmkgdata = pickle.load(pkl_file)
# ids = '__earthquake data converter by eQ Halauwet__\n\n'

# ambon_data = {}

output_nlloc = 'output/phase.obs'

Use_filter = 'Y'  # Y/N
# ___________________________________________________________
# Filter phase
lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI',
             'BANI', 'NLAI', 'BSMI', 'OBMI']  # if not using filter phase, set to: []
# Filter area
ulat = -2.5
blat = -4.5
llon = 127
rlon = 130.5
max_depth = 60

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
mode = 'manual'
max_rms = 2
max_gap = 360
min_P = 5
# min_S = 4
# rem_fixd = False
min_time = dt(2009, 1, 1)  # (year, month, day)
max_time = dt(2019, 12, 31)  # (year, month, day)

# convert all data
if Use_filter == 'N' or Use_filter == 'n':
    lst_phase = []
    llon = -180; rlon = 180; blat = -90; ulat = 90
    max_depth = 800; max_gap = 360; max_rms = 10.0
    min_P = 0; min_S = 0; mode = 'manual'
    max_time = dt(9999, 1, 1)

nlloc = open(output_nlloc, 'w')
nll_mag = open('output/nlloc_mag.dat', 'w')

cat = open('output/catalog.dat', 'w')
cat.write('ev_num Y M D    h:m:s       lon      lat   dep  mag    time_val             '
          'time_str          +/- ot   lon  lat  dep  mag mtype rms gap phnum\n')

arr = open('output/arrival.dat', 'w')
arr.write('ev_num pha      tp       ts      ts-p  res_p res_s  depth  mag    dis\n')

sts_gmtry = open('output/sts_geometry.dat', 'w')
sts_gmtry.write('ev_num sts    dist    azi1    azi2\n')

# List var
_err_pha = ''
res_P: float = 0; res_S: float = 0
tS: float = 0; tP: float = 0; tSP: float = 0
bobot = '0'; IFX = '0'; mag = 0
maxdep = 0; maxgap = 0; maxrms = 0
minpha = 100; maxpha = 0
minS = 100; maxS = 0

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
            d['err']['e_dep'] != '-0.0' and \
            ct_P >= min_P:  # and ct_S >= min_S:  # evt <= dt(2019,9,24) and \ d['dep'] <= max_depth and \
        # ambon_data[evt] = d

        event += 1
        time_sec = evt.timestamp()
        nll_mag.write(f"{event:<6} {time_sec} {d['mag']:4.2f} {d['typ']:6} {float(d['err']['e_mag']):5.2f} {evt}\n")
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
                _NLLocPha += f"       {np.round(arr_p.second + arr_p.microsecond/1e6 + tSP, decimals=2):05.2f} " \
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
if event > 0:
    if err_num > 0:
        log1 = (f'Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n '
                f'maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n '
                f'minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n '
                f'minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n'
                f'{err_num} potential phase error, see log.txt\n\nAll output are on "output" folder: '
                f'velest "phase.cnv", "catalog.dat" and wadati "arrival.dat"')
        log2 = (f'Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n '
                f'maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n '
                f'minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n '
                f'minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n'
                f'{err_num} potential phase error:\n{_err_pha}\nAll output are on "output" folder: '
                f'velest "phase.cnv", "catalog.dat" and wadati "arrival.dat"')
    else:
        log1 = (f'Mengkonversi {event} events dalam area: lintang({ulat} - {blat}) & bujur({llon} - {rlon}):\n '
                f'maksimum kedalaman {maxdep} km\n maksimum RMS {maxrms} sec\n maksimum gap {maxgap} deg\n '
                f'minimum phase P tiap event {minpha}\n maksimum phase P tiap event {maxpha}\n '
                f'minimum phase S tiap event {minS}\n maksimum phase S tiap event {maxS}\n\n'
                'All output are on "output" folder: velest "phase.cnv", "catalog.dat" and wadati "arrival.dat"')
        log2 = log1
else:
    log1 = f'Tidak ada data yang berhasil dikonvert!\nPeriksa data atau parameter filter\n\n{_err_pha}'
    log2 = log1
print('\n' + ids + log1)
file = open('output/log.txt', 'w')
file.write(ids + log2)
file.close()

check_outliers(arrival_file='output/arrival.dat', std_error=4, plot_flag=True)
