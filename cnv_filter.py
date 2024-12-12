import os
from eQ_rw import arr_filter, geometry_filter, map_area
from velest_rw import ReadCNV, CNV_Filter
from check_outliers import check_outliers
from datetime import datetime as dt

inp_cnv = 'D:/project/relokasi/Velest33/output/phase_Grad08_0.30_5.25.cnv'
inp_stt = 'D:/q_repo/ambon_data/02. No filter fixed depth/sts_geometry.dat'
inp_arr = 'D:/q_repo/ambon_data/02. No filter fixed depth/arrival.dat'

out_root = 'D:/q_repo/ambon_data/03. Relocated Single Event_Filter/Grad08_0.30_5.25'

output_stt = os.path.join(out_root, 'sts_geometry.dat')
output_arr = os.path.join(out_root, 'arrival.dat')
output_cat = os.path.join(out_root, 'catalog.dat')
out_cnv = os.path.join(out_root, 'phase_Grad08_0.30_5.25.cnv')
out_log = os.path.join(out_root, 'log.txt')

cnvdata = ReadCNV(inp_cnv)

# FILTER PARAMETER
# Filter area
min_time = dt(1970, 1, 3)  # (year, month, day)
max_time = dt(2019, 12, 31)  # (year, month, day)
ulat = -2.5
blat = -4.5
llon = 127
rlon = 130.5
max_depth = 60

# Filter kualitas data: batasan max azimuth_gap & rms_residual, min phase tiap event dan max jarak_sensor (degree)
rem_fixd = False
max_rms = 2
max_gap = 180
max_spatial_err = 100

# Filter phase
lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI', 'BANI', 'NLAI', 'BSMI', 'OBMI']
min_pha = 6

filt_dic = {'min_tim': min_time,
            'max_tim': max_time,
            'area': {'top': ulat,
                     'bot': blat,
                     'left': llon,
                     'right': rlon
                     },
            'max_dep': max_depth,
            'rem_fixd': rem_fixd,
            'max_rms': max_rms,
            'max_gap': max_gap,
            'max_err': max_spatial_err,
            'lst_pha': lst_phase,
            'min_pha': min_pha
            }

index_event = CNV_Filter(cnvdata, filt_dic, out_cnv, out_cat=output_cat, out_log=out_log)

arr_filter(inp_arr, out=output_arr, index=index_event)

geometry_filter(inp_stt, out=output_stt, index=index_event)

map_area(filt_dic['area'], out_dir=out_root, max_dep=max_depth)

check_outliers(arrival_file=output_arr, out_dir=out_root, std_error=4, plot_flag=False)
