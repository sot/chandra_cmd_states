# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Compare states values to telemetry.

# Fetch telemetry
fetch --start 2008:001 --stop 2008:365 --dt 300 --outfile tlm2008.dat \
       --time-format secs aopcadmd cobsrqid tscpos aosares1 point_suncentang
fetch --start 2003:001 --stop 2003:365 --dt 300 --outfile tlm2003.dat \
      --time-format secs aopcadmd cobsrqid tscpos aosares1 point_suncentang
"""
import logging
import Ska.Table
import Ska.DBI
import Chandra.cmd_states as cmd_states
from Ska.Matplotlib import plot_cxctime, pointpair
from Chandra.Time import DateTime
from scipy.signal import medfilt

# Configure logging to emit msgs to stdout
logging.basicConfig(level=10,
                    format='%(message)s',
                    stream=sys.stdout)

year = 2003

if 'tlm' not in globals():
    print 'Reading telemetry'
    tlm = Ska.Table.read_ascii_table('t/tlm%d.dat' % year)  # or ','

# db = Ska.DBI.DBI(dbi='sqlite', server='db_base.db3')
db = Ska.DBI.DBI(dbi='sybase')

datestart = '%d:365' % (year-1)
datestop = '%d:001' % (year+1)

if 'states' not in globals():
    print 'Getting states'
    states = db.fetchall("""SELECT * from cmd_states
                            WHERE datestop > '%s'
                            AND datestart < '%s'""" % (datestart, datestop))
    state_vals = cmd_states.interpolate_states(states, tlm.date)


diff = medfilt(tlm.aosares1 - state_vals.pitch, 9)
figure(1, figsize=(5.5,4))
clf()
plot_cxctime(tlm.date, diff, fmt='.-b')
title('AOSARES1 - states.pitch (%d)' % year)
ylabel('degrees')
savefig('t/cmp_pitch_%d.png' % year)

figure(2, figsize=(5.5,4))
clf()
hist(diff, bins=50, log=True)
title('AOSARES1 - states.pitch (%d)' % year)
xlabel('degrees')
savefig('t/cmp_hist_pitch_%d.png' % year)

if 0:  # for debug
    figure(5, figsize=(5.5,4))
    clf()
    plot_cxctime(tlm.date, tlm.aosares1, fmt='-b')
    plot_cxctime(tlm.date, state_vals.pitch, fmt='-r')
    title('AOSARES1 and states.pitch')
    ylabel('degrees')


diff = medfilt(tlm.tscpos - state_vals.simpos, 5)
figure(3, figsize=(5.5,4))
clf()
plot_cxctime(tlm.date, diff, fmt='.-b')
title('tlm.TSCPOS - states.simpos (%d)' % year)
ylabel('steps')
savefig('t/cmp_simz_%d.png' % year)

figure(4, figsize=(5.5,4))
clf()
hist(diff, bins=50, log=True)
title('tlm.TSCPOS and states.simpos (%d)' % year)
ylabel('steps')
savefig('t/cmp_hist_simz_%d.png' % year)



diff = medfilt(tlm.cobsrqid - state_vals.obsid, 9)
figure(5, figsize=(5.5,4))
clf()
plot_cxctime(tlm.date, diff, fmt='.-b')
title('tlm.cobsrqid - state_vals.obsid (%d)' % year)
ylabel('steps')
savefig('t/cmp_obsid_%d.png' % year)

figure(6, figsize=(5.5,4))
clf()
hist(diff, bins=50, log=True)
title('tlm.cobsrqid - state_vals.obsid (%d)' % year)
ylabel('steps')
savefig('t/cmp_hist_obsid_%d.png' % year)

