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
import Ska.DBI
import chandra_cmd_states as cmd_states
from Ska.Matplotlib import plot_cxctime, pointpair
from Chandra.Time import DateTime
from scipy.signal import medfilt
import numpy as np
from Ska.engarchive import fetch

# Configure logging to emit msgs to stdout
logging.basicConfig(level=10,
                    format='%(message)s',
                    stream=sys.stdout)

tlm = fetch.MSIDset(['4HPOSARO', '4LPOSARO'], '2009:010:12:00:00', '2010:210:12:00:00', stat='5min')

# db = Ska.DBI.DBI(dbi='sybase')

datestart = DateTime('2008:360:12:00:00').date
datestop = DateTime('2010:220:12:00:00').date

if 1 or 'states' not in globals():
    print 'Getting states'
    db = Ska.DBI.DBI(dbi='sqlite', server='db_base.db3')
    states = db.fetchall("""SELECT * from cmd_states
                            WHERE datestop > '%s'
                            AND datestart < '%s'""" % (datestart, datestop))
    state_vals_h = cmd_states.interpolate_states(states, tlm['4HPOSARO'].times)
    state_vals_l = cmd_states.interpolate_states(states, tlm['4LPOSARO'].times)

hetg_state_pos = np.where(state_vals_h['hetg'] == 'RETR', 78.0, 6.0)
letg_state_pos = np.where(state_vals_l['letg'] == 'RETR', 77.0, 6.0)

diff = medfilt(tlm['4HPOSARO'].vals - hetg_state_pos, 9)
figure(1, figsize=(5.5,4))
clf()
plot_cxctime(tlm['4HPOSARO'].times, diff, fmt='.-b')
title('4HPOSARO - states.hetg')
ylabel('degrees')
savefig('t/cmp_hetg.png')

figure(2, figsize=(5.5,4))
clf()
hist(diff, bins=50, log=True)
title('4HPOSARO - states.hetg')
xlabel('degrees')
savefig('t/cmp_hist_hetg.png')

diff = medfilt(tlm['4LPOSARO'].vals - letg_state_pos, 9)
figure(3, figsize=(5.5,4))
clf()
plot_cxctime(tlm['4LPOSARO'].times, diff, fmt='.-b')
title('4LPOSARO - states.letg')
ylabel('degrees')
savefig('t/cmp_letg.png')

figure(4, figsize=(5.5,4))
clf()
hist(diff, bins=50, log=True)
title('4LPOSARO - states.letg')
xlabel('degrees')
savefig('t/cmp_hist_letg.png')

