"""
Get the Chandra commanded states over a range of time.
"""

import sys
import argparse
import os

from Chandra.Time import DateTime
import Ska.Numpy

from .cmd_states import reduce_states

STATE_VALS = """
     obsid
     power_cmd
     si_mode
     pcad_mode
     vid_board
     clocking
     fep_count
     ccd_count
     simpos
     simfa_pos
     pitch
     ra
     dec
     roll
     q1
     q2
     q3
     q4
     trans_keys
     hetg
     letg
     dither
""".split()


def get_h5_states(start, stop, server):
    """Get states from HDF5 ``server`` file between ``start`` and ``stop``.
    """
    import tables
    import numpy as np

    if server is None:
        server = os.path.join(os.environ['SKA'], 'data', 'cmd_states',
                              'cmd_states.h5')

    if not os.path.exists(server):
        raise IOError('HDF5 cmd_states file {} not found'
                      .format(server))
    h5 = tables.openFile(server, mode='r')
    h5d = h5.root.data

    query = "(datestop > '{}')".format(start.date)
    if stop:
        query += " & (datestart < '{}')".format(stop.date)
    idxs = h5d.getWhereList(query)
    idx0, idx1 = np.min(idxs), np.max(idxs)
    if idx1 - idx0 != len(idxs) - 1:
        raise ValueError('HDF5 table seems to have elements out of order')
    states = h5d[idx0:idx1 + 1]
    h5.close()

    return states


def get_sql_states(start, stop, dbi, server, user, database):
    """Get states from SQL server between ``start`` and ``stop``.
    """
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

    return states


def fetch_states(start=None, stop=None, vals=None, allow_identical=False,
                   dbi='hdf5', server=None, user='aca_read', database='aca'):
    """Get Chandra commanded states over a range of time as a structured array.

    Examples::

      # Get commanded states using the default HDF5 table
      >>> from Chandra.cmd_states import fetch_states
      >>> states = fetch_states('2011:100', '2011:101', vals=['obsid', 'simpos'])
      >>> states[['datestart', 'datestop', 'obsid', 'simpos']]
      array([('2011:100:11:53:12.378', '2011:101:00:23:01.434', 13255, 75624),
             ('2011:101:00:23:01.434', '2011:101:00:26:01.434', 13255, 91272),
             ('2011:101:00:26:01.434', '2011:102:13:39:07.421', 12878, 91272)],
            dtype=[('datestart', '|S21'), ('datestop', '|S21'), ('obsid', '<i8'), ('simpos', '<i8')])

      # Get same states from Sybase (25 times slower)
      >>> states2 = fetch_states('2011:100', '2011:101', vals=['obsid', 'simpos'], dbi='sybase')
      >>> states2 == states
      array([ True,  True,  True], dtype=bool)

    :param start: start date (default=Now-10 days)
    :param stop: stop date (default=None)
    :param vals: list of state columns for output
    :param allow_identical: Allow identical states from cmd_states table
    :param dbi: database interface (default=hdf5)
    :param server: DBI server or HDF5 file (default=None)
    :param user: sybase database user (default='aca_read')
    :param database: sybase database (default=Ska.DBI default)
    """

    allowed_state_vals = STATE_VALS

    if vals is None:
        state_vals = allowed_state_vals
    else:
        state_vals = vals
        bad_state_vals = set(state_vals).difference(allowed_state_vals)
        if bad_state_vals:
            raise ValueError('ERROR: requested --values {} are not allowed '
                             .format(','.join(sorted(bad_state_vals))))

    start = (DateTime(start) if start else DateTime() - 10)
    if stop:
        stop = DateTime(stop)

    if dbi == 'hdf5':
        states = get_h5_states(start, stop, server)
    elif dbi in ('sybase', 'sqlite'):
        states = get_sql_states(start, stop, dbi, server, user, database)
    else:
        raise ValueError("dbi argument '{}' must be one of 'hdf5', 'sybase', "
                         "'sqlite'".format(dbi))

    states = reduce_states(states, state_vals,
                           allow_identical=allow_identical)
    states = Ska.Numpy.structured_array(
        states, colnames=['datestart', 'datestop',
                          'tstart', 'tstop'] + state_vals)

    return states


def main(main_args=None):
    """Command line interface to fetch_states.
    """

    descr = ('Get the Chandra commanded states over a range '
             'of time as a space-delimited ASCII table.')
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("--start",
                        help="Start date (default=Now-10 days)")
    parser.add_argument("--stop",
                        help="Stop date (default=None)")
    parser.add_argument("--vals",
                        help="Comma-separated list of state values.  "
                             "Possible values are:\n" + " ".join(STATE_VALS))
    parser.add_argument("--allow-identical",
                        default=False,
                        action='store_true',
                        help="Allow identical states from cmd_states table "
                        "(default=False)")
    parser.add_argument("--outfile",
                        help="Output file (default=stdout)")
    parser.add_argument("--dbi",
                        default='hdf5',
                        help="Cmd states data source (sybase|hdf5|sqlite) (default=hdf5)")
    parser.add_argument("--server",
                        help="DBI server (sybase) or data file (hdf5 or sqlite)")
    parser.add_argument("--user",
                        default='aca_read',
                        help="sybase database user (default='aca_read')")
    parser.add_argument("--database",
                        help="sybase database (default=Ska.DBI default)")

    args = parser.parse_args(main_args)
    kwargs = vars(args)
    outfile = kwargs['outfile']
    del kwargs['outfile']

    if kwargs['vals'] is not None:
        input_vals = kwargs['vals'].split(',')
        ordered_vals = []
        for state_val in STATE_VALS:
            if state_val in input_vals:
                ordered_vals.append(state_val)
        kwargs['vals'] = ordered_vals

    states = fetch_states(**kwargs)

    out = open(outfile, 'w') if outfile else sys.stdout
    out.write(Ska.Numpy.pformat(states))


if __name__ == '__main__':
    main()
