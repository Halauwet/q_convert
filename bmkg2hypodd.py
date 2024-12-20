import os
import pickle
from eQ_rw import q_filter, map_area
from bmkg_rw import ReadBMKG
from hypodd_rw import WriteHypoDD
from datetime import datetime as dt
from check_outliers import check_outliers

"""
===========================================
earthquake katalog converter by @eqhalauwet
==========================================

Python script for convert BMKG arrival data to HypoDD.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. It is read bmkg arrival data using "ReadBMKG" then convert to velest format.
2. Data can be filtered of area and quality parameter (gap, rms, min phase, etc).
3. Output in velest .dat format (phase P & S), and additional catalog list and arrival.

Logs:

2018-Sep: Added filter option.
2020-May: Change file input type from obj to list, so that it can import from several files.
2020-May: Add filter phase routine
D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN
"""
fileinput = ['D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2008.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2009.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2010.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2011.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2012.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2013.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2014.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2015.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2016.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2017.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2018.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2019.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2020.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2021.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2022.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2023.txt',
             'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGN/list_detail_2024.txt']

# fileinput = ['D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2013.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2014.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2015.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2016.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2017.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2018.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2019_sc3.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2019_sc4.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2020.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2021.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2022.txt',
#              'D:/Documents/BMKG/Data AAI/Katalog Gempa/Arrival PGR IX/list_detail2_2023.txt']
bmkgdata, ids = ReadBMKG(fileinput)
# save_dic = True  # Save filtered dictionary or not?

if not os.path.exists('output'):
    os.makedirs('output')
if not os.path.exists('dict_data'):
    os.makedirs('dict_data')

out_root = 'output'
output = os.path.join(out_root, 'phase.dat')
output_arr = os.path.join(out_root, 'arrival.dat')
output_cat = os.path.join(out_root, 'catalog.dat')
out_log = os.path.join(out_root, 'log.txt')
out_geo = os.path.join(out_root, 'sts_geometry.dat')
out_dic = os.path.join('dict_data', 'thesis_2009-2020.pkl')

# pkl_file = open(out_dic, "rb")
# bmkgdata = pickle.load(pkl_file)
# ids = '__earthquake data converter by eQ Halauwet__\n\n'
save_dic = False  # True/False

# FILTER PARAMETER
# Filter temporal and spatial
min_time = dt(2008, 1, 1)  # (year, month, day)
max_time = dt(2025, 12, 31)  # (year, month, day)
ulat = 15
blat = -18
llon = 85
rlon = 150
max_depth = 750

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
rem_fixd = False
max_rms = 2.5
max_gap = 200
max_spatial_err = 40
mode = 'manual'

# Filter phase
lst_phase = []  # ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI', 'BANI', 'NLAI', 'BSMI', 'OBMI']
min_P = 0
min_S = 0

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

WriteHypoDD(inp=filtered_data, area=filt_dic['area'], out=output, out_arr=output_arr,
            out_cat=output_cat, out_geom=out_geo, out_log=out_log)

map_area(filt_dic['area'], out_dir=out_root, max_dep=max_depth)

check_outliers(arrival_file=output_arr, out_dir=out_root, std_error=4, max_dep=max_depth,plot_flag=True)

if save_dic:
    nldic = open(out_dic, 'wb')
    pickle.dump(filtered_data, nldic)
    nldic.close()
