import sys
import os
import logging
import time

import numpy as np
import tables
import Ska.DBI

from . import cmd_states


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


def update_states_db(states, db, h5):
    """Make the ``db`` database cmd_states table consistent with the supplied
    ``states``.  Match ``states`` to corresponding values in cmd_states
    tables, then delete from table at the point of a mismatch (if any).

    :param states: input states (numpy recarray)
    :param db: Ska.DBI.DBI object
    :param h5: HDF5 object holding commanded states table (as h5.root.data)

    :rtype: None
    """
    from itertools import count, izip

    # If the HDF5 version does not exist then try to make it now.
    if h5 and not hasattr(h5.root, 'data'):
        make_hdf5_cmd_states(db, h5)

    # Get existing cmd_states from the database that overlap with states
    db_states = db.fetchall("""SELECT * from cmd_states
                               WHERE datestop > '%s'
                               AND datestart < '%s'""" %
                               (states[0].datestart, states[-1].datestop))

    if len(db_states) > 0:
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
                log_mismatch(mismatches, db_states, states, i_diff)
                break
        else:
            if len(states) == len(db_states):
                # made it with no mismatches and number of states match so no
                # action required
                logging.debug('update_states_db: No database update required')
                return

            # Else there is a mismatch in number of states.  This catches the
            # typical case when every db_state is in states but states was
            # extended by the addition of new timeline load segments.  In this
            # case just drop through with i_diff left at the last available
            # index in db_states and states.

        # Mismatch occured at i_diff.  Drop cmd_states after
        # db_state['datesstart'][i_diff]
        delete_cmd_states(db_states['datestart'][i_diff], db, h5)

    else:
        # No cmd_states in database so just insert all new states
        i_diff = 0

    insert_cmd_states(states, i_diff, db, h5)


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
            raise ValueError('Expected to delete HDF5 cmd_states after {} '
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
            raise ValueError('ERROR: HDF5 cmd_states table is not ordered '
                             'by datestart after {}'.format(datestart))

        logging.info('udpate_states_db: '
                     'removed HDF5 cmd_states rows from {} to {}'
                     .format(idxs[0], h5d.nrows - 1))
        h5d.removeRows(idxs[0], h5d.nrows)

    # Delete rows from database table
    cmd = ("DELETE FROM cmd_states WHERE datestart >= '{}'"
           .format(datestart))
    logging.info('udpate_states_db: ' + cmd)
    db.execute(cmd)


def insert_cmd_states(states, i_diff, db, h5):
    """Insert new ``states[idiff:]`` into ``db`` and ``h5d``.
    """
    # As for delete_cmd_states do the h5d insert first so if something
    # goes wrong then it is more likely the two tables will remain
    # consistent.
    if h5 and hasattr(h5.root, 'data'):
        h5d = h5.root.data
        logging.info('udpate_states_db: '
                     'inserting states[{}:{}] to HDF5 cmd_states'
                     .format(i_diff, len(states)))
        # Create new struct array from states which is in the column
        # order required to append to h5d.
        sdiff = states[i_diff:]
        rows = np.empty(len(sdiff), dtype=h5d.dtype)
        for name in sdiff.dtype.names:
            rows[name][:] = sdiff[name]
        h5d.append(rows)
        h5d.flush()

    logging.info('udpate_states_db: '
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
    rows = db.fetchall('select * from cmd_states')
    if len(rows) == 0:
        # Need some initial data in SQL version so just return
        logging.info('No values in SQL db so doing nothing')
        return

    logging.info('Creating HDF5 cmd_states table ..')
    h5.createTable(h5.root, 'data', rows,
                   "Cmd_states", expectedrows=5e5)
    h5.flush()
    logging.info('HDF5 cmd_states table successfully created')


def get_update_cmd_states_options():
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

    (opt, args) = parser.parse_args()
    return (opt, args)


def update_cmd_states():
    """
    Update the cmd_states table to reflect current load segments / timelines
    in database.  This function is run only via the command line.

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
    """
    opt, args = get_update_cmd_states_options()

    # Configure logging to emit msgs to stdout
    logging.basicConfig(level=opt.loglevel,
                        format='%(message)s',
                        stream=sys.stdout)

    logging.info('Running {0} at {1}'
                 .format(os.path.basename(sys.argv[0]), time.ctime()))
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
        print 'No h5 file'
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
    update_states_db(states, db, h5)

    if h5 and not _check_consistency(db, h5):
        logging.error('ERROR: database and HDF5 commands '
                      'states are inconsistent')

    # Close down for good measure.
    db.conn.close()
    if h5:
        h5.close()


def _check_consistency(db, h5):
    """Check that the cmd_states table in ``db`` has the same length and
    final datestart.
    """
    h5d = h5.root.data
    db_len = db.fetchone('select count(*) as cnt from cmd_states')['cnt']
    h5d_len = h5d.nrows
    db_last = db.fetchone('select datestart from cmd_states '
                          'order by datestart desc')
    h5d_last = h5d[-1]
    ok = (db_len == h5d_len and
          db_last['datestart'] == h5d_last['datestart'])
    return ok
