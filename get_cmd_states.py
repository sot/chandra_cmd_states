#!/usr/bin/env python
"""
Get the Chandra commanded states over a range of time as a space-delimited
ASCII table.

"""
import Ska.DBI
from Chandra.Time import DateTime
import sys
import Chandra.cmd_states
import numpy
import Ska.Numpy
from numpy.lib import recfunctions

STATE_VALS = """\
obsid power_cmd si_mode vid_board clocking fep_count ccd_count
simpos simfa_pos hetg letg
pcad_mode pitch ra dec roll q1 q2 q3 q4
trans_keys
"""

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--start",
                      help="Start date for update (default=stop-10 days)")
    parser.add_option("--stop",
                      help="Stop date for update (default=Now)")
    parser.add_option("--vals",
                      help="Comma-separated list of state values.  "
                      "Possible values are:\n" + STATE_VALS,)
    parser.add_option("--outfile",
                      help="Output file (default=stdout)")
    parser.add_option("--dbi",
                      default='sybase',
                      help="Database interface (default=sybase)")
    parser.add_option("--server",
                      default='sybase',
                      help="DBI server (default=sybase)")

    (opt, args) = parser.parse_args()
    return (opt, args)

def main():
    opt, args = get_options()

    allowed_state_vals = STATE_VALS.split()
    if opt.vals is None:
        state_vals = allowed_state_vals
    else:
        state_vals = opt.vals.split(',')
        bad_state_vals = set(state_vals).difference(allowed_state_vals)
        if bad_state_vals:
            print ('ERROR: requested --values {0} are not allowed '
                   '(see get_cmd_states.py --help)'.format(','.join(sorted(bad_state_vals))))
            sys.exit(0)

    try:
        db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server, user='aca_read', verbose=False)
    except Exception, msg:
        print 'ERROR: failed to connect to {0}:{1} server: {2}'.format(opt.dbi, opt.server, msg)
        sys.exit(0)

    stop = DateTime(opt.stop)
    start = DateTime(opt.start) if opt.start else DateTime(stop.secs - 10 * 86400)

    db_states = db.fetchall("""SELECT * from cmd_states
                               WHERE datestop > '%s'
                               AND datestart < '%s'""" % 
                               (start.date, stop.date))

    if opt.vals:
        db_states = Chandra.cmd_states.reduce_states(db_states, state_vals)
        drop_fields = set(allowed_state_vals) - set(state_vals)
        db_states = recfunctions.rec_drop_fields(db_states, drop_fields)

    out = open(opt.outfile, 'w') if opt.outfile else sys.stdout
    out.write(Ska.Numpy.pformat(db_states))

if __name__ == '__main__':
    main()
