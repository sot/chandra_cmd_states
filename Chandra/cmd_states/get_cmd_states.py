import sys
import argparse
import os

from Chandra.Time import DateTime
import Ska.Numpy

from .cmd_states import reduce_states

STATE_VALS = """\
obsid power_cmd si_mode vid_board clocking fep_count ccd_count
simpos simfa_pos hetg letg
pcad_mode pitch ra dec roll q1 q2 q3 q4
trans_keys
dither
"""


def get_cmd_states_cmd_line():
    descr = ('Get the Chandra commanded states over a range '
             'of time as a space-delimited ASCII table.')
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("--start",
                        help="Start date (default=Now-10 days)")
    parser.add_argument("--stop",
                        help="Stop date (default=None)")
    parser.add_argument("--vals",
                        help="Comma-separated list of state values.  "
                             "Possible values are:\n" + STATE_VALS,)
    parser.add_argument("--allow-identical",
                        default=False,
                        action='store_true',
                        help="Allow identical states from cmd_states table "
                        "(default=False)")
    parser.add_argument("--outfile",
                        help="Output file (default=stdout)")
    parser.add_argument("--dbi",
                        default='sybase',
                        help="Database interface (default=sybase)")
    parser.add_argument("--server",
                        default='',
                        help="DBI server (default=sybase)")
    parser.add_argument("--user",
                        default='aca_read',
                        help="sybase database user (default='aca_read')")
    parser.add_argument("--database",
                        help="sybase database (default=Ska.DBI default)")

    args = parser.parse_args()
    kwargs = vars(args)
    outfile = kwargs['outfile']
    del kwargs['outfile']

    if kwargs['vals'] is not None:
        kwargs['vals'] = kwargs['vals'].split(',')

    states = get_states(**kwargs)

    out = open(outfile, 'w') if outfile else sys.stdout
    out.write(Ska.Numpy.pformat(states))


def get_states(start=None, stop=None, vals=None, allow_identical=False,
                   dbi=None, server=None, user=None, database=None):
    """Get the Chandra commanded states over a range of time as a
    space-delimited ASCII table.  Used strictly as a command line function.
    """
    import Ska.Numpy

    allowed_state_vals = STATE_VALS.split()

    if vals is None:
        state_vals = allowed_state_vals
    else:
        state_vals = vals
        bad_state_vals = set(state_vals).difference(allowed_state_vals)
        if bad_state_vals:
            raise ValueError('ERROR: requested --values {0} are not allowed '
                             '(see get_cmd_states.py --help)'
                             .format(','.join(sorted(bad_state_vals))))

    start = DateTime(start) if start else DateTime() - 10
    if stop:
        stop = DateTime(stop)

    if dbi == 'hdf5':
        import tables
        import numpy as np

        if server is None:
            server = os.path.join(os.environ['SKA'], 'share', 'cmd_states.h5')

        if not os.path.exists(server):
            raise IOError('HDF5 cmd_states file {} not found'
                          .format(server))
        h5 = tables.openFile(server, mode='r')
        h5d = h5.root.data

        query = "(datestop > '{}')".format(start.date)
        if stop:
            query += " & (datestart < '{})'".format(stop.date)
        idxs = h5d.getWhereList(query)
        idx0, idx1 = np.min(idxs), np.max(idxs)
        if idx1 - idx0 != len(idxs) - 1:
            raise ValueError('HDF5 table seems to have elements out of order')
        states = h5d[idx0:idx1 + 1]
        h5.close()
    else:
        import Ska.DBI
        try:
            db = Ska.DBI.DBI(dbi=dbi, server=server, user=user,
                             database=database, verbose=False)
        except Exception, msg:
            raise IOError('ERROR: failed to connect to {0}:{1} server: {2}'
                          .format(dbi, server, msg))

        query = ("SELECT * from cmd_states WHERE datestop > '{}'"
                 .format(start.date))
        if stop:
            query += " AND datestart < '{}'".format(stop.date)
        states = db.fetchall(query)

    states = reduce_states(states, state_vals,
                           allow_identical=allow_identical)
    states = Ska.Numpy.structured_array(states,
                                        colnames=['datestart', 'datestop',
                                                  'tstart', 'tstop'] + state_vals)

    return states
