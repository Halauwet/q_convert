import sys
from velest_rw import *
# from velest_rw import ReadCNV, CNV_Filter
# from eQ_rw import arr_filter, geometry_filter

sys.path.append('/mnt/d/q_repo/q_velest')
sys.path.append('D:/q_repo/q_velest')
# from Q_Velest import *

sys.path.append('/mnt/d/q_repo/q_modul')
sys.path.append('D:/q_repo/q_modul')
from check_outliers import *

inp_cnv = 'D:/q_repo/ambon_data/01. Filter fixed depth/recalc gap/recalculate_gap.cnv'
inp_stt = 'D:/q_repo/ambon_data/01. Filter fixed depth/sts_geometry.dat'
inp_arr = 'D:/q_repo/ambon_data/01. Filter fixed depth/arrival.dat'

output_stt = os.path.join('output', 'sts_geometry.dat')
output_arr = os.path.join('output', 'arrival.dat')
output_cat = os.path.join('output', 'catalog.dat')
out_cnv = os.path.join('output', 'phase.cnv')
out_log = os.path.join('output', 'log.txt')

cnvdata = ReadCNV(inp_cnv)

# FILTER PARAMETER
# Filter phase
lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI',
             'BANI', 'NLAI', 'BSMI', 'OBMI']

# Filter area
ulat = -2.5
blat = -4.5
llon = 127
rlon = 130.5
max_depth = 60

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
max_rms = 5
max_gap = 180
max_spatial_err = 100
min_pha = 5
# rem_fixd = True
min_time = dt(1970, 1, 3)  # (year, month, day)
max_time = dt(2019, 12, 31)  # (year, month, day)

filt_dic = {'lst_pha': lst_phase,
            'area': {'top': ulat,
                     'bot': blat,
                     'left': llon,
                     'right': rlon
                     },
            'max_dep': max_depth,
            'max_gap': max_gap,
            'max_rms': max_rms,
            'min_pha': min_pha,
            'max_err': max_spatial_err,
            # 'rem_fixd': rem_fixd,
            'min_tim': min_time,
            'max_tim': max_time
            }

index_event = CNV_Filter(cnvdata, filt_dic, out_cnv, out_cat=output_cat, out_log=out_log)

arr_filter(inp_arr, out=output_arr, index=index_event)

geometry_filter(inp_stt, out=output_stt, index=index_event)

check_outliers(arrival_file=output_arr, std_error=4, plot_flag=True)
