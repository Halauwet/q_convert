import os
from eQ_rw import ids, isnumber, dist_km, ReadStation
from datetime import datetime as dt
from datetime import timedelta as td

"""
===========================================
earthquake katalog reader by @eqhalauwet
==========================================

Python module for reading BMKG arrival data files.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. ReadBMKG (now oldReadBMKG) is fuction to read list_detail_2 format from old PGN format (2008-mid 2016), 
   new PGN format (2016-present), PGR IX Seiscomp3 2008 format (2009-mid 2019) and 2017 format (mid 2019-present).
2. The new ReadBMKG read from almost all BMKG arrival format.
3. Can extract only parameter, or with phase data (phase=True), or with magnitudo (maglist=True)
   and option to calculate distance in km (distkm=True).
4. distkm read station data from file "input/bmkg_station.dat" with format ("Station" "Latitude" "Longitude")
5. data error depth and error mag on dict[ot]['err'] using string format (not float) 
   to give flag fixed depth and fixed mag (-0.0)
6. data amp on 'magnitudo list' (dict[ot]['mls']) using string format to accept "N/A" value which exist in data 

Logs:

2017-Sep: Added _check_header line to automatic check data format from few Seiscomp3 version (see Notes).
2019-Oct: Major change: store readed data in dictionary format.
2020-May: Correction: select phase only without "X" residual (unused phase on routine processing).
2020-Jul: New Routine for ReadBMKG data using buffer read to handle huge data ("old" ReadBMKG renamed to oldReadBMKG).
2020-Jul: Added option to only get parameter, with phase data (phase=True), with magnitudo (maglist=True)
          and option to calculate distance in km (distkm=True) (see Notes).
"""

def ReadBMKG(inp=None, phase=True, maglist=False, distkm=False):
    """
    :param inp: BMKG arrival format (list_detail2)
    :type inp: list filename
    :param phase: option read phase data (sts arrival) or not
    :param maglist: option read magnitudo data (sts mag) or not
    :param distkm: calculate distance in km (need sts_data file)
    """

    flag_ori = False
    flag_mag = False
    flag_pha = False
    flag_mlst = False

    bmkg_dic = {}

    # if distkm:
    sts_data = os.path.join(os.path.dirname(__file__), 'input', 'bmkg_station_new.dat')
    sts_dic = ReadStation(sts_data)

    i = 0
    ev = 0
    for file in inp:

        with open(file, "r", -1) as f:

            for l in f:

                i += 1

                if 'Origin:' in l and len(l.split()) < 4:
                    ev += 1
                    flag_ori = True
                    continue

                if 'Network magnitudes:' in l and len(l.split()) < 4:
                    flag_mag = True
                    continue

                if phase and 'Phase arrivals:' in l and len(l.split()) < 4:
                    sta = []
                    net = []
                    dis = []
                    azi = []
                    pha = []
                    dtm = []
                    res = []
                    wth = []
                    pha_dic = {}
                    flag_pha = True
                    continue

                if maglist and 'Station magnitudes:' in l and len(l.split()) < 4:
                    sta = []
                    net = []
                    dis = []
                    azi = []
                    typ = []
                    val = []
                    res = []
                    amp = []
                    mag_dic = {}
                    flag_mlst = True
                    continue

                if flag_ori:

                    if flag_ori and not l.strip():
                        flag_ori = False
                        continue

                    if 'Date' in l:
                        tahun, bulan, tanggal = map(int, l.split()[1].split('-')[0:3])
                        continue

                    if 'Time' in l:
                        jam, menit = map(int, l.split()[1].split(':')[0:2])
                        detik = float(l.split()[1].split(':')[2])
                        sec = int(detik)
                        msec = round((detik - sec) * 1e6)

                        if '+/-' in l:
                            err_tim = float(l.split()[3])

                        try:
                            ot = dt(tahun, bulan, tanggal, jam, menit, sec, msec)
                        except ValueError:
                            print(f'Error encountered on event {ev} data-line {i}\n')
                        continue

                    if 'Latitude' in l:
                        lintang = float(l.split()[1])
                        if '+/-' in l:
                            err_lat = float(l.split()[4])
                        continue

                    if 'Longitude' in l:
                        bujur = float(l.split()[1])
                        if '+/-' in l:
                            err_lon = float(l.split()[4])
                        continue

                    if 'Depth' in l:
                        depth = float(l.split()[1])
                        if '+/-' in l:
                            err_dep = l.split()[4]
                        else:
                            err_dep = '-0.0'
                        continue

                    if 'manual' in l:
                        mod = l.split()[1]
                    elif 'automatic' in l:
                        mod = l.split()[1]

                    if 'RMS' in l:
                        rms = float(l.split()[2])
                        continue

                    if 'gap' in l:
                        gap = float(l.split()[2])
                        continue

                if flag_mag:

                    if 'preferred' in l:
                        mag = float(l.split()[1])
                        mag_type = l.split()[0]
                        if '+/-' in l:
                            err_mag = l.split()[3]
                        else:
                            err_mag = '-0.0'

                        bmkg_dic[ot] = {'lat': lintang,
                                        'lon': bujur,
                                        'dep': depth,
                                        'mag': mag,
                                        'typ': mag_type,
                                        'gap': gap,
                                        'rms': rms,
                                        'mod': mod,
                                        'err': {'e_tim': err_tim,
                                                'e_lat': err_lat,
                                                'e_lon': err_lon,
                                                'e_dep': err_dep,
                                                'e_mag': err_mag}}

                        flag_mag = False
                        continue

                if flag_pha:

                    if flag_pha and not l.strip():
                        pha_dic[ot] = {'arr': {'sta': sta,
                                               'net': net,
                                               'dis': dis,
                                               'azi': azi,
                                               'pha': pha,
                                               'del': dtm,
                                               'res': res,
                                               'wth': wth}}

                        bmkg_dic[ot].update(pha_dic[ot])

                        flag_pha = False
                        continue

                    if '##' not in l and isnumber(l.split()[6]) and 'X' not in l.split()[7]:

                        if distkm:
                            dist, az1, az2 = dist_km(lintang, bujur, l.split()[0], sts_dic)
                            if az2 is None:
                                print(f'Enter station coordinate on {sts_data} to calculate the distance\n')
                                continue
                        else:
                            dist = float(l.split()[2])

                        jam2, menit = map(int, l.split()[5].split(':')[0:2])
                        detik = float((l.split())[5].split(':')[2])
                        sec = int(detik)
                        msec = round((detik - sec) * 1e6)

                        try:
                            at = dt(tahun, bulan, tanggal, jam2, menit, sec, msec)
                            if jam2 < jam:
                                at = at + td(days=1)
                            deltatime = float('%.2f' % (at.timestamp() - ot.timestamp()))
                        except ValueError:
                            print(f'Error encountered on event {ev} data-line {i}\n')

                        sta.append(l.split()[0])
                        net.append(l.split()[1])
                        dis.append(dist)
                        azi.append(float(l.split()[3]))
                        pha.append(l.split()[4])
                        dtm.append(deltatime)
                        res.append(float(l.split()[6]))
                        wth.append(l.split()[8])

                if flag_mlst:

                    if flag_mlst and not l.strip():
                        mag_dic[ot] = {'mls': {'sta': sta,
                                               'net': net,
                                               'dis': dis,
                                               'azi': azi,
                                               'typ': typ,
                                               'val': val,
                                               'res': res,
                                               'amp': amp}}

                        bmkg_dic[ot].update(mag_dic[ot])

                        flag_mlst = False
                        continue

                    if isnumber(l.split()[2]) and isnumber(l.split()[3]) and isnumber(l.split()[5]) and \
                            isnumber(l.split()[6]) and isnumber(l.split()[7]):

                        if distkm:
                            dist, az1, az2 = dist_km(lintang, bujur, l.split()[0], sts_dic)
                            if az2 is None:
                                print(f'Enter station coordinate on {sts_data} to calculate the distance\n')
                                continue
                        else:
                            dist = float(l.split()[2])

                        sta.append(l.split()[0])
                        net.append(l.split()[1])
                        dis.append(dist)
                        azi.append(int(l.split()[3]))
                        typ.append(l.split()[4])
                        val.append(float(l.split()[5]))
                        res.append(float(l.split()[6]))
                        amp.append(l.split()[7])

    return bmkg_dic, ids
