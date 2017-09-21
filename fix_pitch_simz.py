#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
One-off script to fix residual mismatches in cmd_states pitch and SIM-Z.  These
are largely due to SCS107 runs with a dense set of replans that are not exactly
captured in the timeline loads.

This script uses telemetry to repair the errant command states.  The result is still
not perfect but mostly good.  The last fix is 2007:153.

# Fetch comparison telemetry
fetch --start 2002:010 --stop 2009:001:00:00:00 --dt 600 --outfile tlm2002_2008.dat \
      --time-format secs aopcadmd cobsrqid tscpos aosares1 point_suncentang

"""

import Ska.Table
import Ska.DBI
import Chandra.cmd_states as cmd_states

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--dbi",
                      default='sqlite',
                      help="Database interface (sqlite|sybase)")
    parser.add_option("--server",
                      default='db_base.db3',
                      help="DBI server (<filename>|sybase)")
    
    (opt, args) = parser.parse_args()
    return (opt, args)

def main():
    import numpy as np
    from scipy.signal import medfilt

    opt, args = get_options()

    if 'tlm' not in globals():
        print 'Reading telemetry'
        tlm = Ska.Table.read_ascii_table('t/tlm2002_2008.dat', delimiters=[','])

    db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server)

    datestart = '2002:010:00:00:00' 
    datestop = '2009:001:00:00:00'

    if 'states' not in globals():
        print 'Getting states'
        states = db.fetchall("""SELECT * from cmd_states
                                WHERE datestart > '%s'
                                AND datestop < '%s'""" % (datestart, datestop))
        ok = (tlm.date > states[0].tstart) & (tlm.date < states[-1].tstop)
        tlm = tlm[ok]
        state_vals = cmd_states.interpolate_states(states, tlm.date)

    simdiff = medfilt(tlm.tscpos - state_vals.simpos, 5)
    bad = abs(simdiff) > 5000.
    bad_state_idxs = np.unique(np.searchsorted(states.tstop, tlm[bad].date))
    for bad_state in states[bad_state_idxs]:
        ok = (tlm.date >= bad_state.tstart) & (tlm.date <= bad_state.tstop)
        simpos = np.median(tlm[ok].tscpos)
        cmd = "UPDATE cmd_states SET simpos=%d WHERE datestart='%s'" % (simpos, bad_state.datestart)
        print cmd
        db.execute(cmd)

    pitchdiff = medfilt(tlm.aosares1 - state_vals.pitch, 9)
    bad = abs(pitchdiff) > 5.
    bad_state_idxs = np.unique(np.searchsorted(states.tstop, tlm[bad].date))
    for bad_state in states[bad_state_idxs]:
        ok = (tlm.date >= bad_state.tstart) & (tlm.date <= bad_state.tstop)
        pitch = np.median(tlm[ok].aosares1)
        cmd = "UPDATE cmd_states SET pitch=%f WHERE datestart='%s'" % (pitch, bad_state.datestart)
        print cmd
        db.execute(cmd)

    db.commit()

if __name__ == '__main__':
    main()
    
