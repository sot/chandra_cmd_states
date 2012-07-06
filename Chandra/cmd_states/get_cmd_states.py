import sys

import Ska.DBI
from Chandra.Time import DateTime

from .cmd_states import reduce_states


def get_cmd_states_options(STATE_VALS):
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--start",
                      help="Start date (default=Now-10 days)")
    parser.add_option("--stop",
                      help="Stop date (default=None)")
    parser.add_option("--vals",
                      help="Comma-separated list of state values.  "
                      "Possible values are:\n" + STATE_VALS,)
    parser.add_option("--allow-identical",
                      default=False,
                      action='store_true',
                      help="Allow identical states from cmd_states table "
                      "(default=False)")
    parser.add_option("--outfile",
                      help="Output file (default=stdout)")
    parser.add_option("--dbi",
                      default='sybase',
                      help="Database interface (default=sybase)")
    parser.add_option("--server",
                      default='',
                      help="DBI server (default=sybase)")
    parser.add_option("--user",
                      default='aca_read',
                      help="sybase database user (default='aca_read')")
    parser.add_option("--database",
                      help="sybase database (default=Ska.DBI default)")

    (opt, args) = parser.parse_args()
    return (opt, args)


def get_cmd_states():
    """Get the Chandra commanded states over a range of time as a
    space-delimited ASCII table.  Used strictly as a command line function.
    """
    STATE_VALS = """\
    obsid power_cmd si_mode vid_board clocking fep_count ccd_count
    simpos simfa_pos hetg letg
    pcad_mode pitch ra dec roll q1 q2 q3 q4
    trans_keys
    dither
    """
    from numpy.lib import recfunctions

    opt, args = get_cmd_states_options(STATE_VALS)

    allowed_state_vals = STATE_VALS.split()
    if opt.vals is None:
        state_vals = allowed_state_vals
    else:
        state_vals = opt.vals.split(',')
        bad_state_vals = set(state_vals).difference(allowed_state_vals)
        if bad_state_vals:
            print ('ERROR: requested --values {0} are not allowed '
                   '(see get_cmd_states.py --help)'
                   .format(','.join(sorted(bad_state_vals))))
            sys.exit(0)

    try:
        db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server, user=opt.user,
                         database=opt.database, verbose=False)
    except Exception, msg:
        print ('ERROR: failed to connect to {0}:{1} server: {2}'
               .format(opt.dbi, opt.server, msg))
        sys.exit(0)

    start = DateTime(opt.start) if opt.start else DateTime() - 10
    db_states_q = """SELECT * from cmd_states
                     WHERE datestop > '%s'""" % (start.date)
    if opt.stop:
        db_states_q += " AND datestart < '%s'" % DateTime(opt.stop).date
    db_states = db.fetchall(db_states_q)

    if opt.vals:
        db_states = reduce_states(db_states, state_vals,
                                  allow_identical=opt.allow_identical)
        drop_fields = set(allowed_state_vals) - set(state_vals)
        db_states = recfunctions.rec_drop_fields(db_states, drop_fields)

    out = open(opt.outfile, 'w') if opt.outfile else sys.stdout
    out.write(Ska.Numpy.pformat(db_states))
