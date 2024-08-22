import pickle
from eQ_rw import q_filter, map_area
from bmkg_rw import ReadBMKG
from nordic_rw import WriteNordic
from check_outliers import check_outliers
from datetime import datetime as dt

"""
===========================================
earthquake katalog converter by @eqhalauwet
==========================================

Python script for convert BMKG arrival data to nordic format.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. It is read bmkg arrival data using "ReadBMKG" module then convert to nordic format.
2. Data can be filtered of area and quality parameter (gap, rms, min phase, etc).
3. Output in nordic .out format, and additional catalog list and arrival.

Logs:

2018-Sep: Added filter option.
2020-May: Change file input type from obj to list, so that it can import from several files.
2020-May: Add filter phase routine

"""
fileinput = ['D:/BMKG/Katalog/Arrival PGN/list_detail_2010.txt'] #,
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2009.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2010.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2011.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2012.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2013.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2014.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2015.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2016.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2017.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2018.txt',
#              'D:/BMKG/Katalog/Arrival PGN/list_detail_2019.txt']

bmkgdata, ids = ReadBMKG(fileinput)
save_dic = True  # Save filtered dictionary or not?

output = 'output/nordic.out'
out_log = 'output/log.txt'
out_dic = 'dict_data/ambon_data(2008-2019).pkl'
# save_dic = False  # True/False

# pkl_file = open(out_dic, "rb")
# bmkgdata = pickle.load(pkl_file)
# ids = '__earthquake data converter by eQ Halauwet__\n\n'

filter_flag = True  # True/False

# FILTER PARAMETER

# Filter phase
lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI',
             'BANI', 'NLAI', 'BSMI', 'OBMI']

# Filter area
ulat = -2.5
blat = -4.5
llon = 127
rlon = 130.5

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
mode = 'manual'
max_rms = 2
max_gap = 250
max_spatial_err = 10
min_P = 6
min_S = 0
max_depth = 60
rem_fixd = False
min_time = dt(1970, 1, 3)  # (year, month, day)
max_time = dt(2019, 9, 24)  # (year, month, day)

filt_dic = {'min_tim': min_time,
            'max_tim': max_time,
            'area': {'top': ulat,
                     'bot': blat,
                     'left': llon,
                     'right': rlon
                     },
            'max_dep': max_depth,
            'rm_fixd': rem_fixd,
            'max_rms': max_rms,
            'max_gap': max_gap,
            'max_err': max_spatial_err,
            'mode': mode,
            'phase': {'lst_pha': lst_phase,
                      'min_P': min_P,
                      'min_S': min_S}
            }

filtered_data = q_filter(bmkgdata, filt_dic, inptype='BMKG', prob_flag=False)

WriteNordic(inp=bmkgdata, filt=filt_dic, out=output, out_log=out_log,
            inptype='BMKG', filt_flag=filter_flag, prob_flag=False)

map_area(filt_dic['area'])

check_outliers(arrival_file='output/arrival.dat', std_error=4)

if save_dic:
    nldic = open(out_dic, 'wb')
    pickle.dump(bmkgdata, nldic)
    nldic.close()
