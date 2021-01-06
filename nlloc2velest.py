import os
import pickle
from datetime import datetime as dt
from eQ_rw import q_filter, map_area
from nlloc_rw import ReadNLLoc
from velest_rw import WriteVelest
from check_outliers import check_outliers

"""
===========================================
earthquake katalog converter by @eqhalauwet
==========================================

Python script for convert NLLoc dictionary to velest.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. It is read NLLoc LocSum.hyp using "ReadNLLoc" module then convert to velest format.
2. Data can be filtered of area and quality parameter (gap, rms, min phase, etc).
3. Output in velest .cnv format (phase P & S), and additional catalog list and arrival.

Logs:

2018-Sep: Added filter option.
2020-May: Change file input type from obj to list, so that it can import from several files.
2020-May: Add filter phase routine

"""
fileinput = 'D:/q_repo/q_nlloc/loc/q_loc.hyp'
mag_cat = 'D:/q_repo/q_convert/output/nlloc_mag.dat'  # output from bmkg2nlloc
nllocdata, ids, elim_event = ReadNLLoc(fileinput, mag_cat)
# save_dic = True  # Save filtered dictionary or not?

if not os.path.exists('output'):
    os.makedirs('output')
if not os.path.exists('dict_data'):
    os.makedirs('dict_data')

output_p = os.path.join('output', 'phase_P.cnv')
output_s = os.path.join('output', 'phase_S.cnv')
output_arr = os.path.join('output', 'arrival.dat')
output_cat = os.path.join('output', 'catalog.dat')
out_log = os.path.join('output', 'log.txt')
out_geo = os.path.join('output', 'sts_geometry.txt')
out_dic = os.path.join('dict_data', 'NLLdic_Ambon-3_corr.pkl')

# pkl_file = open(out_dic, "rb")
# nllocdata = pickle.load(pkl_file)
# ids = '__earthquake data converter by eQ Halauwet__\n\n'
# elim_event = []
save_dic = False  # Save filtered dictionary or not?

probs_flag = False  # For nlloc input: True = using Gausian expectation (GAU), False = using nll Min Likelihood (ML)
filter_flag = False  # Using filter parameter or not

# FILTER PARAMETER
# Filter area
min_time = dt(1970, 1, 3)  # (year, month, day)
max_time = dt(2019, 12, 31)  # (year, month, day)
ulat = -1.5
blat = -5.5
llon = 126
rlon = 131.5
max_depth = 60

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
rem_fixd = True
max_rms = 2
max_gap = 360
max_spatial_err = 100
mode = ''

# Filter phase
lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI', 'BANI', 'NLAI', 'BSMI', 'OBMI']
min_P = 5
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

filtered_data = q_filter(nllocdata, filt_dic, inptype='nlloc', prob_flag=True)

WriteVelest(inp=filtered_data, area=filt_dic['area'], out_p=output_p, out_s=output_s, out_arr=output_arr,
            out_cat=output_cat, out_geom=out_geo, out_log=out_log)

map_area(filt_dic['area'])

check_outliers(arrival_file=output_arr, std_error=4, plot_flag=True)

if save_dic:
    nldic = open(out_dic, 'wb')
    pickle.dump(nllocdata, nldic)
    nldic.close()
