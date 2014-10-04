import sys
import os
import logging
import time
from itertools import count, izip
import Ska.ftp


import numpy as np
import tables
import Ska.DBI
from kadi import occweb

from . import cmd_states

CMD_STATES_DTYPE = [('datestart', '|S21'),
                    ('datestop', '|S21'),
                    ('tstart', '<f8'),
                    ('tstop', '<f8'),
                    ('obsid', '<i8'),
                    ('power_cmd', '|S11'),
                    ('si_mode', '|S8'),
                    ('pcad_mode', '|S6'),
                    ('vid_board', '<i8'),
                    ('clocking', '<i8'),
                    ('fep_count', '<i8'),
                    ('ccd_count', '<i8'),
                    ('simpos', '<i8'),
                    ('simfa_pos', '<i8'),
                    ('pitch', '<f8'),
                    ('ra', '<f8'),
                    ('dec', '<f8'),
                    ('roll', '<f8'),
                    ('q1', '<f8'),
                    ('q2', '<f8'),
                    ('q3', '<f8'),
                    ('q4', '<f8'),
                    ('trans_keys', '|S60'),
                    ('hetg', '|S4'),
                    ('letg', '|S4'),
                    ('dither', '|S4')]


def log_mismatch(mismatches, db_states, states, i_diff):
    """Log the states and state differences leading to a diff between the
    database cmd_states and the proposed states from commanding / products
    """
    mismatches = sorted(mismatches)
    logging.debug('update_states_db: mismatch between existing DB cmd_states'
                  ' and new cmd_states for {0}'.format(mismatches))
    logging.debug('  DB datestart: {0}   New datestart: {1}'.format(
        db_states[i_diff]['datestart'], states[i_diff]['datestart']))
    for mismatch in mismatches:
        if mismatch == 'attitude':
            logging.debug('  DB  ra: {0:9.5f} dec: {1:9.5f}'
                          .format(db_states[i_diff]['ra'],
                                  db_states[i_diff]['dec']))
            logging.debug('  New ra: {0:9.5f} dec: {1:9.5f}'
                          .format(states[i_diff]['ra'],
                                  states[i_diff]['dec']))
        else:
            logging.debug('  DB  {0}: {1}'
                          .format(mismatch, db_states[i_diff][mismatch]))
            logging.debug('  New {0}: {1}'
                          .format(mismatch, states[i_diff][mismatch]))
    i0 = max(i_diff - 4, 0)
    i1 = min(i_diff + 4, len(db_states))
    logging.debug('** Existing DB states')
    logging.debug(Ska.Numpy.pformat(db_states[i0:i1]))
    i1 = min(i_diff + 4, len(states))

    colnames = db_states.dtype.names
    states = np.rec.fromarrays([states[x][i0:i1] for x in colnames],
                               names=colnames)

    logging.debug('** New states')
    logging.debug(Ska.Numpy.pformat(states))


def get_states_i_diff(db_states, states):
    """Get the index position where db_states and states differ.

    If the states are identical then None is returned.

    :param db_states: states in database
    :param states: new reference states
    :returns: i_diff
    """

    # Get states columns that are not float type. descr gives list of
    # (colname, type_descr)
    match_cols = [x[0] for x in states.dtype.descr if 'f' not in x[1]]

    # Find mismatches: direct compare or where pitch or attitude differs by
    # > 1 arcsec
    for i_diff, db_state, state in izip(count(), db_states, states):
        mismatches = set(x for x in match_cols if db_state[x] != state[x])
        if abs(db_state.pitch - state.pitch) > 0.0003:
            mismatches.add('pitch')
        if Ska.Sun.sph_dist(db_state.ra, db_state.dec,
                            state.ra, state.dec) > 0.0003:
            mismatches.add('attitude')
        if mismatches:
            # Case 1: direct mismatch in states
            log_mismatch(mismatches, db_states, states, i_diff)
            break
    else:
        # At this point the for loop finished with no detected diffs.
        # Now i_diff = min(len(db_states), len(states)) - 1.

        if len(states) == len(db_states):
            # Case 2: made it with no mismatches and the number of states
            # match so no action is required.
            return None  # No states changed

        # Otherwise there is an indirect mismatch in states because one
        # table has a valid state row where the other table has no row
        # (i.e. the table ends).  There are two more cases here:
        #
        # Case 3. The typical case is when len(db_states) > len(states):
        #   * Every db_state is in states but states was extended by adding
        #     new timeline load segments due to new weekly products.
        #
        # Case 4. Less common case is when len(states) < len(db_states):
        #   * db_states needs to be shortened to delete states, probably
        #     due to a load interrupt like NSM or safemode (but not SCS107)
        #
        # Now increment i_diff by one to point at the position of the
        # "mismatch", between an existing state and a null state beyond the
        # end of available states.

        i_diff += 1

    return i_diff


def update_states_db(states, db, h5):
    """Make the ``db`` database cmd_states table consistent with the supplied
    ``states``.  Match ``states`` to corresponding values in cmd_states
    tables, then delete from table at the point of a mismatch (if any).

    :param states: input states (numpy recarray)
    :param db: Ska.DBI.DBI object
    :param h5: HDF5 object holding commanded states table (as h5.root.data)

    :rtype: None
    """
    # If input states list is empty then no update needed
    if len(states) == 0:
        raise ValueError('Unexpected input of an empty states table in '
                         'update_states_db')

    # If the HDF5 version does not exist then try to make it now.
    if h5 and not hasattr(h5.root, 'data'):
        make_hdf5_cmd_states(db, h5)

    # Get existing cmd_states from the database that overlap with states
    db_states = db.fetchall("""SELECT * from cmd_states
                               WHERE datestop > '%s'
                               AND datestart < '%s'""" %
                               (states[0].datestart, states[-1].datestop))

    if len(db_states) > 0:
        i_diff = get_states_i_diff(db_states, states)
        if i_diff is None:
            logging.debug('update_states_db: No database update required')
            return False

        # Mismatch occurred at i_diff.  If that index is within db_states
        # (cases 1 and 4 in get_states_i_diff) drop db_states after
        # db_states['datesstart'][i_diff]
        if i_diff < len(db_states):
            delete_cmd_states(db_states['datestart'][i_diff], db, h5)
    else:
        # No cmd_states in database so just insert all new states
        i_diff = 0

    insert_cmd_states(states, i_diff, db, h5)

    return True  # States were changed


def delete_cmd_states(datestart, db, h5):
    """Delete cmd_states table entries that have datestart greater than or
    equal to the supplied ``datestart`` arg.  Do this for the SQL database
    handle ``db`` and the HDF5 object handle ``h5``.
    """
    # Delete rows from HDF5 table.  It can happen (mostly during testing) that
    # the h5 file doesn't yet have the data attribute yet, meaning it hasn't
    # been initialized with cmd_states data.
    if h5 and hasattr(h5.root, 'data'):
        h5d = h5.root.data
        idxs = h5d.getWhereList("datestart >= '{}'".format(datestart))

        # Be paranoid and do a couple of consistency checks here because we
        # are always deleting from a row index to the end of the table.
        # PyTables/HDF5 is inefficient otherwise.
        idxs = np.sort(idxs)
        order_ok = True
        if len(idxs) == 0:
            logging.error('ERROR: Expected to delete HDF5 cmd_states after {} '
                          'but none matched'.format(datestart))
        if idxs[-1] != h5d.nrows - 1:
            order_ok = False
        if len(idxs) > 1:
            idxs = np.sort(idxs)
            if np.any(idxs[1:] - idxs[:-1] != 1):
                order_ok = False
        if not order_ok:
            # If there is an inconsistency stop right now and also don't
            # touch the database table.
            h5.close()
            logging.error('ERROR: HDF5 cmd_states table is not ordered '
                          'by datestart after {}'.format(datestart))

        if idxs[0] > 0:
            logging.info('update_states_db: '
                         'removed HDF5 cmd_states rows from {} to {}'
                         .format(idxs[0], h5d.nrows - 1))
            h5d.removeRows(idxs[0], h5d.nrows)
        else:
            # Remove all rows from file.  HDF5 cannot support this so just
            # issue a non-fatal error that will generate a warning email.
            logging.error('ERROR: trying to delete all HDF5 rows, IGNORING')

        h5d.flush()

    # Delete rows from database table
    cmd = ("DELETE FROM cmd_states WHERE datestart >= '{}'"
           .format(datestart))
    logging.info('update_states_db: ' + cmd)
    db.execute(cmd)


def insert_cmd_states(states, i_diff, db, h5):
    """Insert new ``states[idiff:]`` into ``db`` and ``h5d``.
    """
    # As for delete_cmd_states do the h5d insert first so if something
    # goes wrong then it is more likely the two tables will remain
    # consistent.
    if h5 and hasattr(h5.root, 'data'):
        h5d = h5.root.data
        logging.info('update_states_db: '
                     'inserting states[{}:{}] to HDF5 cmd_states'
                     .format(i_diff, len(states)))
        # Create new struct array from states which is in the column
        # order required to append to h5d.
        sdiff = states[i_diff:]
        rows = np.empty(len(sdiff), dtype=CMD_STATES_DTYPE)
        for name in rows.dtype.names:
            rows[name][:] = sdiff[name]
        h5d.append(rows)
        h5d.flush()

    logging.info('update_states_db: '
                 'inserting states[{}:{}] to database cmd_states'
                 .format(i_diff, len(states)))

    for state in states[i_diff:]:
        # Need commit=True for sybase -- very large inserts will fail
        db.insert(dict((x, state[x]) for x in state.dtype.names), 'cmd_states',
                  commit=True)
    db.commit()

    if h5 and not hasattr(h5.root, 'data'):
        make_hdf5_cmd_states(db, h5)


def make_hdf5_cmd_states(db, h5):
    """Make a new HDF5 command states table in ``h5`` from the existing
    database version.
    """
    # This takes a little while...
    logging.info('Reading cmd_states table from sybase, stand by ..')
    db_rows = db.fetchall('select * from cmd_states')
    if len(db_rows) == 0:
        # Need some initial data in SQL version so just return
        logging.info('No values in SQL db so doing nothing')
        return

    logging.info('Creating HDF5 cmd_states table ..')
    rows = np.empty(len(db_rows), dtype=CMD_STATES_DTYPE)
    for name in rows.dtype.names:
        rows[name][:] = db_rows[name]
    h5.createTable(h5.root, 'data', rows,
                   "Cmd_states", expectedrows=5e5)
    h5.flush()
    logging.info('HDF5 cmd_states table successfully created')


def check_consistency(db, h5, n_check=3000):
    """Check that the cmd_states table in ``db`` has the same length and
    final datestart.
    """
    h5d = h5.root.data

    # Check that lengths match
    db_len = db.fetchone('select count(*) as cnt from cmd_states')['cnt']
    h5d_len = h5d.nrows
    if db_len != h5d_len:
        logging.error('ERROR: database and HDF5 commands '
                      'states have different length {} vs {}'
                      .format(db_len, h5d_len))

    # check that the last n_check rows are the same
    db_rows = db.fetch('select * from cmd_states order by datestart desc')
    h5_rows = h5d[-n_check:][::-1]
    all_ok = True
    for db_row, h5_row in izip(db_rows, h5_rows):
        row_ok = True
        for name in h5_row.dtype.names:
            ok = (np.allclose(db_row[name], h5_row[name])
                  if h5_row[name].dtype.kind == 'f' else
                  db_row[name] == h5_row[name])
            row_ok = row_ok and ok

        if not row_ok:
            # Since the rows are in reverse time order this will get set to
            # the *first* mismatched row
            datestart_mismatch = db_row['datestart']
            all_ok = False

    if not all_ok:
        logging.error('ERROR: database and HDF5 command states tables show'
                      'mismatch starting at {}'.format(datestart_mismatch))


def get_options():
    """Get options for command line interface to update_cmd_states.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--dbi",
                      default='sqlite',
                      help="Database interface (sqlite|sybase)")
    parser.add_option("--server",
                      default='db_base.db3',
                      help="DBI server (<filename>|sybase)")
    parser.add_option("--user",
                      help="sybase user (default=Ska.DBI default)")
    parser.add_option("--database",
                      help="sybase database (default=Ska.DBI default)")
    parser.add_option("--mp_dir",
                      default='/data/mpcrit1/mplogs',
                      help="MP load directory")
    parser.add_option("--h5file",
                      default='cmd_states.h5',
                      help="filename for HDF5 version of cmd_states")
    parser.add_option("--datestart",
                      help="Starting date for update (default=Now-10 days)")
    parser.add_option("--loglevel",
                      type='int',
                      default=20,
                      help='Log level (10=debug, 20=info, 30=warnings)')
    parser.add_option("--occ",
                      action='store_true',
                      help="Running on the OCC GRETA network")

    (opt, args) = parser.parse_args()
    return (opt, args)


def main():
    """
    Command line interface to update the cmd_states table to reflect current
    load segments / timelines in database.

    Usage: update_cmd_states.py [options]::

      Options:
        -h, --help            show this help message and exit
        --dbi=DBI             Database interface (sqlite|sybase)
        --server=SERVER       DBI server (<filename>|sybase)
        --user=USER           database user (default=Ska.DBI default)
        --database=DATABASE   database name (default=Ska.DBI default)
        --h5file=H5FILE       filename for HDF5 version of cmd_states
        --datestart=DATESTART
                              Starting date for update (default=Now-10 days)
        --mp_dir=DIR          MP directory. (default=/data/mpcrit1/mplogs)
        --loglevel=LOGLEVEL   Log level (10=debug, 20=info, 30=warnings)
        --occ                 Running on OCC network (default=False)
    """
    opt, args = get_options()

    # Configure logging to emit msgs to stdout
    logging.basicConfig(level=opt.loglevel,
                        format='%(message)s',
                        stream=sys.stdout)

    logging.info('Running {0} at {1}'
                 .format(os.path.basename(sys.argv[0]), time.ctime()))

    # Set val to indicate if the output h5file is the "flight" version.
    # In that case use ftp directory cmd_states, else cmd_states_test.
    is_flight = opt.h5file == '/proj/sot/ska/data/cmd_states/cmd_states.h5'
    ftp_dirname = 'cmd_states' if is_flight else 'cmd_states_test'

    # If running on the OCC (GRETA) network then just try to get a new HDF5
    # file from lucky in /home/taldcroft/cmd_states and copy to opt.h5file.  The
    # file will appear on lucky only when the HEAD network version gets updated
    # with changed content.
    if opt.occ and opt.h5file:
        occweb.ftp_get_from_lucky(ftp_dirname, [opt.h5file], logger=logging)
        sys.exit(0)

    logging.debug('Connecting to db: dbi=%s server=%s user=%s database=%s'
                  % (opt.dbi, opt.server, opt.user, opt.database))
    try:
        db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server, user=opt.user,
                         database=opt.database, verbose=False)
        if opt.dbi == 'sqlite':
            db.conn.text_factory = str
    except Exception, msg:
        logging.error('ERROR: failed to connect to {0}:{1} server: {2}'
                      .format(opt.dbi, opt.server, msg))
        sys.exit(0)

    if opt.h5file:
        filters = tables.Filters(complevel=5, complib='zlib')
        h5 = tables.openFile(opt.h5file, mode='a', filters=filters)
    else:
        h5 = None

    # Get initial state containing the specified datestart
    logging.debug('Getting initial state0')
    state0 = cmd_states.get_state0(date=opt.datestart, db=db)
    logging.debug('Initial state0: datestart=%s datestop=%s obsid=%d' %
                 (state0['datestart'], state0['datestop'], state0['obsid']))

    # Sync up datestart to state0 and get timeline load segments including
    # state0 and beyond.
    datestart = state0['datestart']
    logging.debug('Getting timeline_loads after %s' % datestart)
    timeline_loads = db.fetchall("""SELECT * from timeline_loads
                                    WHERE datestop > '%s'""" % datestart)
    logging.debug('Found %s timeline_loads' % len(timeline_loads))

    # Get cmds since datestart.  If needed add cmds to database
    logging.debug('Getting cmds after %s' % datestart)
    cmds = cmd_states.get_cmds(datestart, db=db, update_db=True,
                               timeline_loads=timeline_loads,
                               mp_dir=opt.mp_dir)
    logging.debug('Found %s cmds after %s' % (len(cmds), datestart))

    # Get the states generated by cmds starting from state0
    logging.debug('Generating cmd_states after %s' % datestart)
    states = cmd_states.get_states(state0, cmds)
    logging.debug('Found %s states after %s' % (len(states), datestart))

    # Update cmd_states in database
    logging.debug('Updating database cmd_states table')
    states_changed = update_states_db(states, db, h5)

    if h5:
        # Check for consistency between HDF5 and SQL
        n_check = 3000 if states_changed else 100
        check_consistency(db, h5, n_check)

        # If states were updated OR the HDF5 is NOT the "flight" version (i.e. doing
        # testing) then upload to the lucky ftp server.
        if states_changed or not is_flight:
            occweb.ftp_put_to_lucky(ftp_dirname, [opt.h5file], logger=logging)

    # Close down for good measure.
    db.conn.close()
    if h5:
        h5.close()


if __name__ == '__main__':
    main()
