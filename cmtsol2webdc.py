from obspy import UTCDateTime
# inp_file = 'input/cmtsol_thesis_1976.txt'
inp_file = 'input/cmtsol_thesis.txt'
out_file = 'webdc_thesis.dat'

ev = 1000
i = 0
pde_loc = True
flag_event = False
# webdc_cat = ''

webdc_file = open(out_file, 'w')

with open(inp_file, 'r', -1) as f:

    for l in f:

        # i += 1

        if 'PDE' in l and 'PDEW' not in l or 'MLI' in l and len(l.split()) > 6:
            ev += 1
            ida, Y, M, D, h, m, s, lat, lon, dep, m1, m2 = l.split()[0:12]
            # Y = int(Y[-4:])
            ot = UTCDateTime(int(Y), int(M), int(D), int(h), int(m), float(s))
            if pde_loc:
                flag_event = True
            continue

        if 'PDEW' in l and len(l.split()) > 6:
            ev += 1
            Y, M, D, h, m, s, lat, lon, dep, m1, m2 = l.split()[0:11]
            Y = int(Y[-4:])
            ot = UTCDateTime(Y, int(M), int(D), int(h), int(m), float(s))
            if pde_loc:
                flag_event = True
            continue

        if flag_event:
            if 'event name:' in l:
                id = l.split()[2]
                continue
            if 'latitude:' in l:
                lat = float(l.split()[1])
                continue
            if 'longitude:' in l:
                lon = float(l.split()[1])
                continue
            if 'depth:' in l:
                dep = float(l.split()[1])
                continue
            if 'time shift:' in l:
                t_shift = float(l.split()[2])
                ot = ot + t_shift
                continue

        if not l.strip():
            if float(m1) != 0:
                mag = float(m1)
            else:
                mag = float(m2)
            if flag_event:
                flag_event = False
            # webdc_cat += f'{ot};{lat:.2f};{lon:.2f};{dep:.1f};{mag:.1f};{ev};{id}\n'
            webdc_file.write(f'{ot.strftime("%Y-%m-%dT%H:%M:%S")};{lat:.2f};{lon:.2f};{dep:.1f};{mag:.1f};{ev};{id}\n')

webdc_file.close()
