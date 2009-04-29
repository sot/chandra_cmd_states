#
# Fetch telemetry
# fetch --start 2008:001 --stop 2008:365 --dt 300 --outfile tlm2008.dat --time-format secs aopcadmd cobsrqid tscpos aosares1 point_suncentang
# fetch --start 2003:001 --stop 2003:365 --dt 300 --outfile tlm2003.dat --time-format secs aopcadmd cobsrqid tscpos aosares1 point_suncentang
# 
import logging
import Ska.Table
import Ska.DBI
import cmd_states
from Ska.Matplotlib import plot_cxctime, pointpair
from Chandra.Time import DateTime

# Configure logging to emit msgs to stdout
logging.basicConfig(level=10,
                    format='%(message)s',
                    stream=sys.stdout)

if 'tlm' not in globals():
    tlm = Ska.Table.read_ascii_table('tlm2008.dat', delimiters=[' '])  # or ','

db = Ska.DBI.DBI(dbi='sqlite', server='db2008.db3')

datestart = '2007:365'
datestop = '2009:001'

if 'states' not in globals():
    states = db.fetchall("""SELECT * from cmd_states
                            WHERE datestop > '%s'
                            AND datestart < '%s'""" % (datestart, datestop))
    state_vals = cmd_states.interpolate_states(states, tlm.date)

# ok = (states.tstart > min(tlm.date)) & (states.tstop < max(tlm.date))
# pitches = Ska.Numpy.interpolate(tlm.aosares1, tlm.date, states[ok].tstart)

figure(1, figsize=(5.5,4))
clf()
plot_cxctime(tlm.date, tlm.aosares1 - state_vals.pitch, fmt='.-b')
title('AOSARES1 - states.pitch')
ylabel('degrees')
savefig('cmp_pitch_2008.png')

figure(2, figsize=(5.5,4))
clf()
hist(tlm.aosares1 - state_vals.pitch, bins=50, log=True)
title('AOSARES1 - states.pitch')
xlabel('degrees')
savefig('cmp_hist_pitch_2008.png')
