"""
This module provides the core functions for creating, manipulating and updating
the Chandra commanded states database.
"""

import re
import logging
import os
import time
import pprint

import numpy as np

import Ska.File
import Ska.DBI
from Chandra.Time import DateTime
import Chandra.Maneuver
from Quaternion import Quat
import Ska.Sun
import Ska.ParseCM
import Ska.Numpy

# Canonical state0 giving spacecraft state at beginning of timelines
# 2002:007:13 fetch --start 2002:007:13:00:00 --stop 2002:007:13:02:00 aoattqt1
# aoattqt2 aoattqt3 aoattqt4 cobsrqid aopcadmd tscpos
STATE0 = {'ccd_count': 5,
          'clocking': 0,
          'datestart': '2002:007:13:00:00.000',
          'datestop': '2099:001:00:00:00.000',
          'dec': -11.500,
          'fep_count': 0,
          'hetg': 'RETR',
          'letg': 'RETR',
          'obsid': 61358,
          'pcad_mode': 'NPNT',
          'pitch': 61.37,
          'power_cmd': 'AA00000000',
          'q1': -0.568062,
          'q2': 0.121674,
          'q3': 0.00114141,
          'q4': 0.813941,
          'ra': 352.000,
          'roll': 289.37,
          'si_mode': 'undef',
          'simfa_pos': -468,
          'simpos': -99616,
          'trans_keys': 'undef',
          'tstart': 127020624.552,
          'tstop': 3187296066.184,
          'vid_board': 0,
          'dither': 'None'}


def decode_power(mnem):
    """
    Decode number of chips and feps from a ACIS power command
    Return a dictionary with the number of chips and their identifiers

    Example::

     >>> decode_power("WSPOW08F3E")
     {'ccd_count': 5,
      'ccds': 'I0 I1 I2 I3 S3 ',
      'fep_count': 5,
      'feps': '1 2 3 4 5 '}

    :param mnem: power command string

    """
    # the hex for the commanding is after the WSPOW
    powstr = mnem[5:]
    if (len(powstr) != 5):
        raise ValueError("%s in unexpected format" % mnem)

    # convert the hex to decimal and "&" it with 63 (binary 111111)
    fepkey = int(powstr, 16) & 63
    fep_info = {'fep_count': 0,
                'ccd_count': 0,
                'feps': '',
                'ccds': ''}
    # count the true binary bits
    for bit in xrange(0, 6):
        if (fepkey & (1 << bit)):
            fep_info['fep_count'] = fep_info['fep_count'] + 1
            fep_info['feps'] = fep_info['feps'] + str(bit) + ' '

    # convert the hex to decimal and right shift by 8 places
    vidkey = int(powstr, 16) >> 8

    # count the true bits
    for bit in xrange(0, 10):
        if (vidkey & (1 << bit)):
            fep_info['ccd_count'] = fep_info['ccd_count'] + 1
            # position indicates I or S chip
            if (bit < 4):
                fep_info['ccds'] = fep_info['ccds'] + 'I' + str(bit) + ' '
            else:
                fep_info['ccds'] = fep_info['ccds'] + 'S' + str(bit - 4) + ' '

    return fep_info


def _make_add_trans(transitions, date, exclude):
    def add_trans(date=date, **kwargs):
        # If no key in kwargs is in the exclude set then update transition
        # And, when doing any update, update a bookkeeping key 'last_date'
        # that stores the latest date of any processed cmd/transition.
        # This is used to prevent overlap between the GET_PITCH mocked
        # up cmds and the inserted/mock maneuver cmds.  If any one of the
        # equally-spaced GET_PITCH cmds occurs during a maneuver, the GET_PITCH
        # will be ignored in processing because the maneuver cmd insertion
        # through the maneuver time range will have updated last_date to
        # a time later than that GET_PITCH command.
        if not (exclude and set(exclude).intersection(kwargs)):
            transitions.setdefault(date, {}).update(kwargs)
            # Only update 'last_date' if the supplied date to _make_add_trans
            # is actually later than the stored 'last_date' in the structure
            if date > transitions['last_date']:
                transitions['last_date'] = date
    return add_trans


def _make_pitch_cmds(datestart, datestop, sample_time=5000):
    """
    Add cmds to clock out pitch for any long states
    """
    return [{'cmd': 'GET_PITCH',
             'tlmsid': 'GET_PITCH',
             'date': DateTime(t).date,}
            for t in np.arange(DateTime(datestart).secs,
                               DateTime(datestop).secs,
                               sample_time)]


def get_states(state0, cmds, exclude=None):
    """Get states resulting from the spacecraft commands ``cmds`` starting
    from an initial ``state0``.

    State keys in the ``exclude`` list or set will be excluded from causing a
    transition.  This is useful if a state parameter (e.g. simfa_pos) is not of
    interest.  An excluding parameter will have incorrect values in the
    returned states.

    A state is a dict with key values corresponding to the following database
    schema:

    ============   =========   ====
    Name           Type        Size
    ============   =========   ====
     datestart     varchar      21
     datestop      varchar      21
     obsid         int           4
     power_cmd     varchar      11
     si_mode       varchar       8
     pcad_mode     varchar       6
     vid_board     bit           1
     clocking      bit           1
     fep_count     int           4
     ccd_count     int           4
     simpos        int           4
     simfa_pos     int           4
     pitch         float         8
     ra            float         8
     dec           float         8
     roll          float         8
     q1            float         8
     q2            float         8
     q3            float         8
     q4            float         8
     trans_keys    varchar      60
     letg          varchar       4
     hetg          varchar       4
     dither        varchar       4
    ============   =========   ====

    The input commands must be a list of dicts including keys ``date, vcdu,
    cmd, params, time``.  See also Ska.ParseCM.read_backstop().

    :param state0: initial state.
    :param cmds: list of commands
    :param ignore: list or set of state keys to ignore

    :returns: recarray of states starting with state0 (which might be modified)
    """

    logging.debug('get_states: starting from %s' % state0['datestart'])

    curr_att = [state0[x] for x in ('q1', 'q2', 'q3', 'q4')]

    # A transition is a dictionary of state updates occuring at one time, e.g.
    # {'simpos': -99616, 'pcad_mode': 'NMAN'}. The transition dicts are
    # collected 'transitions' dict and keyed by cmd date.  In this way multiple
    # commands at the same time can easily be accumulated to a single
    # transition.  Also use the dictionary to store a value for the
    # last transition date.
    transitions = {'last_date': cmds[0]['date']}

    # Add extra mocked-up cmds to sample pitch
    pitch_cmds = _make_pitch_cmds(state0['datestart'], cmds[-1]['date'])
    cmds.extend(pitch_cmds)
    cmds.sort(key=lambda y: y['date'])

    cmds_after_state0 = [x for x in cmds if x['date'] > state0['datestart']]

    for cmd in cmds_after_state0:
        params = cmd.get('params', {})
        # Following two might not be in cmd
        tlmsid = cmd['tlmsid'] or params.get('TLMSID', '')
        cmd_type = cmd['cmd']
        date = cmd['date']

        # Make a convenience function to add to transitions at command date
        add_trans = _make_add_trans(transitions, date, exclude)

        # Obsid
        if cmd_type == 'MP_OBSID':
            add_trans(obsid=params['ID'])

        # Mocked-up cmds to sample pitch
        elif cmd_type == 'GET_PITCH':
            # If we have made transitions with dates after
            # this mock command (maneuver transitions),
            # skip the 'GET_PITCH'
            if cmd['date'] < transitions['last_date']:
                continue
            q_att = Quat(curr_att)
            # add pitch/attitude commands
            pitch = Ska.Sun.pitch(q_att.ra, q_att.dec, date)
            add_trans(pitch=pitch)

        # SIM Z
        elif cmd_type == 'SIMTRANS':
            add_trans(simpos=params['POS'])

        # SIM focus
        elif cmd_type == 'SIMFOCUS':
            add_trans(simfa_pos=params['POS'])

        # ACIS power command section
        elif cmd_type == 'ACISPKT':
            if tlmsid.startswith('WSPOW'):
                pwr = decode_power(tlmsid)
                add_trans(fep_count=pwr['fep_count'],
                          ccd_count=pwr['ccd_count'],
                          vid_board=1, clocking=0, power_cmd=tlmsid)

            elif re.match(r'X(T|C)Z0000005', tlmsid):
                add_trans(clocking=1, power_cmd=tlmsid)

            elif tlmsid == 'WSVIDALLDN':
                add_trans(vid_board=0, power_cmd=tlmsid)

            elif tlmsid == 'AA00000000':
                add_trans(clocking=0, power_cmd=tlmsid)

            elif tlmsid == 'WSFEPALLUP':
                add_trans(fep_count=6, power_cmd=tlmsid)

            elif tlmsid.startswith('WC'):
                add_trans(si_mode='CC_' + tlmsid[2:7])

            elif tlmsid.startswith('WT'):
                add_trans(si_mode='TE_' + tlmsid[2:7])

        # Set the target attitude
        elif cmd_type == 'MP_TARGQUAT':
            targ_att = [params[x] for x in ('Q1', 'Q2', 'Q3', 'Q4')]

        # Specify auto transition to NPNT with star acq after maneuver
        elif cmd_type == 'COMMAND_SW' and re.match('AONM2NP(E|D)', tlmsid):
            auto_npnt = (tlmsid == 'AONM2NPE')

        # Transition to NMM
        elif cmd_type == 'COMMAND_SW' and tlmsid == 'AONMMODE':
            add_trans(pcad_mode='NMAN')

        # Transition to NPM
        elif cmd_type == 'COMMAND_SW' and tlmsid == 'AONPMODE':
            add_trans(pcad_mode='NPNT')

        # Transition to HETG inserted
        elif cmd_type == 'COMMAND_SW' and tlmsid == '4OHETGIN':
            add_trans(hetg='INSR')

        # Transition to HETG retracted
        elif cmd_type == 'COMMAND_SW' and tlmsid == '4OHETGRE':
            add_trans(hetg='RETR')

        # Transition to LETG inserted
        elif cmd_type == 'COMMAND_SW' and tlmsid == '4OLETGIN':
            add_trans(letg='INSR')

        # Transition to LETG retracted
        elif cmd_type == 'COMMAND_SW' and tlmsid == '4OLETGRE':
            add_trans(letg='RETR')

        elif cmd_type == 'COMMAND_SW' and tlmsid == 'AOENDITH':
            add_trans(dither='ENAB')

        elif cmd_type == 'COMMAND_SW' and tlmsid == 'AODSDITH':
            add_trans(dither='DISA')

        # Start a maneuver to targ_att or else to normal sun pointed attitude
        # via normal sun mode
        elif cmd_type == 'COMMAND_SW' and tlmsid in ('AOMANUVR', 'AONSMSAF'):
            if tlmsid == 'AONSMSAF':
                add_trans(pcad_mode='NSUN')
                targ_att = Chandra.Maneuver.NSM_attitude(curr_att, cmd['time'])
                auto_npnt = False

            # add pitch/attitude commands
            atts = Chandra.Maneuver.attitudes(curr_att, targ_att,
                                              tstart=cmd['time'])
            logging.debug('Maneuver at {0} {1}\nfrom {2}\nto {3}'.format(
                DateTime(cmd['time']).date, cmd['time'], curr_att, targ_att))
            logging.debug(Ska.Numpy.pformat(atts))
            pitches = np.hstack([(atts[:-1].pitch + atts[1:].pitch) / 2,
                                 atts[-1].pitch])
            for att, pitch in zip(atts, pitches):
                q_att = Quat([att[x] for x in ('q1', 'q2', 'q3', 'q4')])
                add_trans(date=DateTime(att.time).date,
                          pitch=pitch,
                          q1=att.q1, q2=att.q2, q3=att.q3, q4=att.q4,
                          ra=q_att.ra, dec=q_att.dec, roll=q_att.roll)
                logging.debug(pprint.pformat(dict(date=DateTime(att.time).date,
                          pitch=pitch,
                          q1=att.q1, q2=att.q2, q3=att.q3, q4=att.q4,
                          ra=q_att.ra, dec=q_att.dec, roll=q_att.roll)))
            # If auto-transition to NPM after manvr is enabled (this is
            # normally the case) then back to NPNT at end of maneuver
            if auto_npnt:
                add_trans(date=DateTime(atts[-1].time).date, pcad_mode='NPNT')

            # update the current attitude to the target attitude
            curr_att = targ_att

    # Delete the last_date bookkeeping key
    # It is no longer needed and would break the following loop
    # over sorted(transitions)
    del transitions['last_date']

    # Make the states from state0 and the final dict of transitions
    states = [state0]
    for datekey in sorted(transitions):
        new_state = states[-1].copy()
        new_state['datestart'] = datekey
        new_state.update(transitions[datekey])
        new_state['trans_keys'] = ','.join(sorted(transitions[datekey]))
        states.append(new_state)

    logging.debug('get_states: found %d states' % len(states))

    # Set datestop values to be the datestart of the next state.  Last state
    # is given a datestop far in the future
    states[-1]['datestop'] = '2099:001:00:00:00.000'
    for state_i0, state_i1 in zip(states[:-1], states[1:]):
        state_i0['datestop'] = state_i1['datestart']

    for state in states:
        state['tstart'] = DateTime(state['datestart']).secs
        state['tstop'] = DateTime(state['datestop']).secs

    statecols = sorted(states[0])
    staterecs = [tuple(row[col] for col in statecols) for row in states]

    return np.rec.fromrecords(staterecs, names=statecols)


def get_state0(date=None, db=None, date_margin=10, datepar='datestop'):
    """From the cmd_states table get the last state with ``datepar`` before
    ``date``.

     It is assumed that the cmd_states database table is populated and accurate
     (definitive) at times more than ``date_margin`` days before the present
     time.  The conservative default value of ``date_margin=10`` allows for
     processing downtime.  The table is accessed via the ``db`` object.

    :param db: Ska.DBI.DBI object.  Created automatically if not supplied.
    :param date: date cutoff for state0 (Chandra.Time 'date' string)
    :param date_margin: days before current time for definitive values
    :param datepar: table parameter for select (datestop|datestart)

    :returns: ``state0``
    :rtype: dict
    """
    if db is None:
        db = Ska.DBI.DBI(dbi='sybase', server='sybase', user='aca_read',
                         database='aca')

    # Date for which cmd_states are certainly reliable
    definitive_date = DateTime(time.time() - date_margin * 86400.,
                               format='unix').date
    if date is None or date > definitive_date:
        date = definitive_date
    else:
        date = DateTime(date).date

    state0 = db.fetchone("""SELECT * FROM cmd_states
                            WHERE %s < '%s'
                            AND pcad_mode = 'NPNT'
                            ORDER BY %s DESC""" % (datepar, date, datepar))

    if state0:
        logging.debug('get_state0: found definitive state at %s'
                      % state0['datestart'])
    else:
        logging.debug('get_state0: using default state at %s'
                      % STATE0['datestart'])

    # return the selected state or the default STATE0 if nothing found
    return state0 or STATE0


def _tl_to_bs_cmds(tl_cmds, tl_id, db):
    """
    Convert the commands ``tl_cmds`` (numpy recarray) that occur in the
    timeline ``tl_id'' to a format mimicking backstop commands from
    Ska.ParseCM.read_backstop().  This includes reading parameter values
    from the ``db``.

    :param tl_cmds: numpy recarray of commands from timeline load segment
    :param tl_id: timeline id
    :param db: Ska.DBI db object

    :returns: list of command dicts
    """
    bs_cmds = [dict((col, row[col]) for col in tl_cmds.dtype.names)
               for row in tl_cmds]
    cmd_index = dict((x['id'], x) for x in bs_cmds)

    # Add 'params' dict of command parameter key=val pairs to each tl_cmd
    for par_table in ('cmd_intpars', 'cmd_fltpars'):
        tl_params = db.fetchall("SELECT * FROM %s WHERE timeline_id %s" %
                                (par_table,
                                 '= %d' % tl_id if tl_id else 'IS NULL'))

        # Build up the params dict for each command in timeline load segment
        for par in tl_params:
            # I.e. cmd_index[par.cmd_id]['params'][par.name] = par.value
            # but create the ['params'] dict as needed.
            if par.cmd_id in cmd_index:
                cmd_index[par.cmd_id].setdefault('params', {})[par.name] = par.value

    return bs_cmds


def get_cmds(datestart='1998:001:00:00:00.000',
             datestop='2099:001:00:00:00.000',
             db=None, update_db=None, timeline_loads=None,
             mp_dir='/data/mpcrit1/mplogs'):
    """Get all commands with ``datestart`` < date <= ``datestop`` using DBI
    object ``db``.  This includes both commands already in the database and new
    commands.  If ``update_db`` is True then update the database cmds table
    to reflect new and/or deleted commands.

    Use ``datestart`` < date instead of <= because in typical ussage
    ``datestart`` is the start date of a state and one wants commands *after*
    those that generated the original state transition.

    The timeline_loads table is relied upon as the final authority of which
    commands were (will be) run on-board.  The timeline_load values can change
    in the database in the event of an autonomous or ground-commanded load
    segment interrupt.  The strategy is to regenerate the list of commands that
    were (will be) run on-board using commands already in the database
    supplemented by backstop commands found in the SOTMP repository of load
    products.

    :param datestart: start date (Chandra.Time 'date' str) (default=1998:001)
    :param datestop: stop date (default=2099:001)
    :param db: Ska.DBI.DBI object (required)
    :param update_db: update the 'cmds' table

    :returns: ``cmds``
    :rtype: list of dicts
    """
    # Get timeline_loads including and after datestart
    if timeline_loads is None:
        timeline_loads = db.fetchall("""SELECT * from timeline_loads
                                        WHERE datestop > '%s'""" % datestart)

    # Get non-load commands (from autonomous or ground SCS107, NSM, etc)
    nl_cmds = db.fetchall("""SELECT * from cmds where timeline_id IS NULL""")
    cmds = _tl_to_bs_cmds(nl_cmds, None, db)

    # Values of cmd or tlmsid for commands that are retained
    cmd_types = set(('MP_OBSID', 'SIMTRANS', 'SIMFOCUS',
                     'ACISPKT', 'MP_TARGQUAT'))
    tlmsids = set(('AONM2NPE', 'AONM2NPD', 'AONMMODE',
                   'AONPMODE', 'AOMANUVR', 'AONSMSAF',
                   '4OHETGRE', '4OLETGRE', '4OHETGIN',
                   '4OLETGIN', 'AOENDITH', 'AODSDITH'))

    for tl in timeline_loads:
        tl_cmds = db.fetchall("SELECT * from cmds WHERE timeline_id = %d"
                              % tl.id)

        logging.debug('get_cmds: got %3d cmds from db for timeline_id=%d '
                      '(%s - %s)'
                      % (len(tl_cmds), tl.id, tl.datestart, tl.datestop))

        # If not yet in DB then read from MP backstop file.  Put into DB if
        # needed.
        if len(tl_cmds) == 0:
            bs_file = Ska.File.get_globfiles(os.path.join(mp_dir + tl.mp_dir,
                                                          '*.backstop'))[0]
            bs_cmds = Ska.ParseCM.read_backstop(bs_file)
            # Retain state-changing cmds within timeline for database
            bs_cmds = [x for x in bs_cmds
                       if tl.datestart <= x['date'] <= tl.datestop
                       and (x['cmd'] in cmd_types or x['params'].get('TLMSID')
                            in tlmsids)]
            # Only store commands for this timelines's scs
            bs_cmds = [x for x in bs_cmds if x['scs'] == tl['scs']]
            logging.info('get_cmds: got %d commands from %s'
                         % (len(bs_cmds), bs_file))
            if update_db and bs_cmds:
                insert_cmds_db(bs_cmds, tl.id, db)
        else:
            # Check for commands before the timeline start, which is a problem.
            if any(tl_cmds.date < tl.datestart):
                raise ValueError('Found commands in database before start '
                                 'of %d:%s load segment' %
                                 (tl.year, tl.name))
            # Check for commands after the timeline stop, which is normal for
            # an interrupt.
            after = tl_cmds.date > tl.datestop
            if any(after):
                logging.debug('get_cmds: %d commands were after datestop'
                              % (len(np.flatnonzero(after))))
                # Filter out commands after tl.datestop
                tl_cmds = tl_cmds[np.logical_not(after)]

            # Now flatten to a list of dicts to emulate read_backstop and
            # incorporate params
            bs_cmds = _tl_to_bs_cmds(tl_cmds, tl.id, db)

        cmds.extend(bs_cmds)

    # Filter commands on date and sort by date.
    # IS THE "datestart <=" CORRECT?  docstring above says "<".  ?????
    return sorted((x for x in cmds if datestart <= x['date'] <= datestop),
                  key=lambda y: y['date'])


def insert_cmds_db(cmds, timeline_id, db):
    """Insert the ``cmds`` into the ``db`` table 'cmds' with ``timeline_id``.
    Command parameters are also inserted into 'cmd_intpars' and 'cmd_fltpars'
    tables.  ``timeline_id`` can be None to indicate non-load commands (from
    ground or autonomous).

    Each command must be dict with at least the following keys:

    ========= ======
    date      char
    time      float
    cmd       char
    ========= ======

    Optional keys are:

    ========= ======
    params    dict
    paramstr  char
    tlmsid    char
    msid      char
    vcdu      int
    step      int
    scs       int
    ========= ======

    The input ``cmds`` are used to populate three tables:

    **cmds**

    ================  ========  =======
    name              type      length
    ================  ========  =======
    id (PK)            int        4
    timeline_id        int        4
    date               char      21
    time              float       8,
    cmd               varchar    12
    tlmsid            varchar    10
    msid              varchar     8
    vcdu              int         4
    step              int         4
    scs               int         4
    ================  ========  =======

    **cmd_intpars** and **cmd_fltpars**

    ================  ==========  =======
    name              type        length
    ================  ==========  =======
    cmd_id (FK)        int           4
    timeline_id (FK)   int           4
    name               varchar      15
    value              int/float     8
    ================  ==========  =======

    :param cmds: list of command dicts, e.g. from Ska.ParseCM.read_backstop()
    :param db: Ska.DBI.DBI object
    :param timeline_id: id of timeline load segment that contains commands

    :returns: None
    """
    cmd_id = db.fetchone('SELECT max(id) AS max_id FROM cmds')['max_id'] or 0
    logging.info('insert_cmds_db: inserting %d cmds to commands tables'
                 % (len(cmds)))

    for cmd in cmds:
        cmd_id += 1

        # Make a copy of the cmd while skipping any None values
        db_cmd = dict((key, val) for (key, val) in cmd.items()
                      if val is not None)
        db_cmd['id'] = cmd_id
        if timeline_id is not None:
            db_cmd['timeline_id'] = timeline_id

        # The params and paramstr don't get stored to db
        for key in set(['params', 'paramstr']).intersection(db_cmd):
            del db_cmd[key]

        db.insert(db_cmd, 'cmds', commit=False)

        # Insert int and float command parameters
        for name, value in cmd.get('params', {}).items():
            if name in ('MSID', 'TLMSID', 'SCS', 'STEP', 'VCDU'):
                continue

            par = dict(cmd_id=cmd_id,
                       timeline_id=timeline_id,
                       name=name,
                       value=value)
            if isinstance(value, int):
                db.insert(par, 'cmd_intpars', commit=False)
            elif isinstance(value, float):
                db.insert(par, 'cmd_fltpars', commit=False)

    db.conn.commit()


def interpolate_states(states, times):
    """Interpolate ``states`` np.recarray at given times.

    :param states: states (np.recarray)
    :param times: times (np.array or list)

    :returns: ``states`` view at ``times``
    """
    indexes = np.searchsorted(states['tstop'], times)
    return states[indexes]


def generate_cmds(time, cmd_set):
    """
    Generate a set of commands based on the supplied ``cmd_set`` starting
    from the specified ``time``.

    The ``cmd_set`` is a list of command definitions like the output of
    read_backstop() but with an optional 'dur' key in each command and no
    absolute time values.  This key specifies the duration of that command in
    seconds.  Normally this routine is used with the predefined ``CMD_SET``
    values.

    :param cmd_set: list of command definitions
    :param time: starting time for command set

    :returns: list of command dicts ala read_backstop()
    """

    cmds = []
    time = DateTime(time).secs
    for cmd in cmd_set:
        if 'cmd' in cmd:
            # Generate a copy of cmd except for 'dur' key.
            newcmd = dict(time=time,
                          date=DateTime(time).date,
                          tlmsid=None,
                          msid=None)
            newcmd.update(cmd)
            if 'dur' in newcmd:
                del newcmd['dur']
            cmds.append(newcmd)
        time += cmd.get('dur', 0.0)

    return cmds


def cmd_set(name, *args):
    """
    Return a predefined cmd_set ``name`` generated with \*args.

    :param name: cmd set name (manvr|scs107|nsm)
    :param \*args: optional args
    :returns: cmd set
    """
    def obsid(*args):
        """Return a command set that initiates a maneuver to the given attitude
        ``att``.

        :param att: attitude compatible with Quat() initializer
        :returns: list of command defs suitable for generate_cmds()
        """
        return (dict(cmd='MP_OBSID',
                     params=dict(ID=args[0])),
                )

    def manvr(*args):
        """Return a command set that initiates a maneuver to the given attitude
        ``att``.

        :param att: attitude compatible with Quat() initializer
        :returns: list of command defs suitable for generate_cmds()
        """
        att = Quat(args)
        return (dict(cmd='COMMAND_SW',
                     tlmsid='AONMMODE',
                     msid='AONMMODE',
                     dur=0.25625),
                dict(cmd='COMMAND_SW',
                     tlmsid='AONM2NPE',
                     msid='AONM2NPE',
                     dur=4.1),
                dict(cmd='MP_TARGQUAT',
                     tlmsid='AOUPTARQ',
                     params=dict(Q1=att.q[0], Q2=att.q[1],
                                 Q3=att.q[2], Q4=att.q[3]),
                     dur=5.894),
                dict(cmd='COMMAND_SW',
                     tlmsid='AOMANUVR',
                     msid='AOMANUVR'),
                )

    def acis(*args):
        cmds = [dict(cmd='ACISPKT', tlmsid=tlmsid) for tlmsid in args]
        return cmds

    def aciscti():
        return (dict(cmd='ACISPKT',
                     tlmsid='WSVIDALLDN',
                     dur=1.025),
                dict(cmd='ACISPKT',
                     tlmsid='WSPOW0CF3F',
                     dur=1.025),
                dict(cmd='ACISPKT',
                     tlmsid='WT00216024',
                     dur=67),
                dict(cmd='ACISPKT',
                     tlmsid='XTZ0000005'))

    def scs107():
        return (dict(dur=1.025),
                dict(cmd='SIMTRANS',
                     params=dict(POS=-99616),
                     dur=65.66),
                dict(cmd='ACISPKT',
                     tlmsid='AA00000000',
                     dur=1.025),
                dict(cmd='ACISPKT',
                     tlmsid='AA00000000',
                     dur=10.25),
                dict(cmd='ACISPKT',
                     tlmsid='WSPOW00000'),
                )

    def nsm():
        return (dict(cmd='COMMAND_SW',
                     tlmsid='AONSMSAF'),
                )

    cmd_sets = dict(manvr=manvr, scs107=scs107, nsm=nsm, obsid=obsid,
                    acis=acis, aciscti=aciscti)
    return cmd_sets[name](*args)


def interrupt_loads(datestop, db, observing_only=False, current_only=False):
    """Interrupt the timelines  with
    db.datestop > ``datestop`` by updating the table datestop accordingly.
    Use DBI handle ``db`` to access tables.  If ``current_only`` is set
    then only update the load that actually contains ``datestop``.

    :param datestop: load stop date
    :param db: Ska.DBI.DBI object
    :param observing_only: only interrupt 'observing' slots (131,132,133)
    :param current_only: only stop the load containing datestop
    :returns: None
    """
    datestop = DateTime(datestop).date

    select = "SELECT * FROM timeline_loads WHERE datestop > '%s'" % datestop
    select_datestart = (" AND datestart <= '%s'" % datestop
                        if current_only else '')
    select_observing = " AND scs > 130" if observing_only else ''

    logging.info('interrupt_loads: '
                 + select + select_datestart + select_observing)
    timelines = db.fetchall(select + select_datestart + select_observing)
    if len(timelines) == 0:
        logging.info('No timelines containing %s' % datestop)
        return

    logging.info('Updating %d timelines with datestop > %s'
                 % (len(timelines), datestop))
    for tl in timelines:
        logging.info("%s %s %s" % (tl['datestart'], tl['datestop'],
                                   tl['mp_dir']))

    # Get confirmation to update timeslines table in database
    logging.info('Revert with:')
    for tl in timelines:
        logging.info("UPDATE timelines SET datestop='%s' where id=%d ;"
                     % (tl['datestop'], tl['id']))

    for tl in timelines:
        update = ("UPDATE timelines SET datestop='%s' where id=%d"
                  % (datestop, tl['id']))
        db.execute(update)


def reduce_states(states, cols, allow_identical=True):
    """
    Reduce the input ``states`` so that only transitions in the ``cols``
    columns are noticed.

    :param states: numpy recarray of states
    :param cols: notice transitions in this list of columns
    :param allow_identical: allow null transitions between apparently identical states

    :returns: numpy recarray of reduced states
    """
    cols = set(cols)

    # Boolean func for when at least one state transition key is among the
    # supplied cols Transition keys are are the values that changed between
    # previous and current state
    trans_in_cols = lambda state: bool(cols.intersection(state['trans_keys']
                                                         .split(',')))

    # Generate the transition markers
    transitions = np.array([trans_in_cols(state) for state in states])
    transitions[0] = True

    if not allow_identical:
        i_transitions = np.flatnonzero(transitions)
        no_trans = []
        for i in i_transitions[1:]:  # Skip the first one which is index=0
            state0 = states[i - 1]
            state1 = states[i]
            trans_keys = state1['trans_keys'].split(',')
            if all(state0[key] == state1[key] for key in trans_keys):
                no_trans.append(i)
        transitions[no_trans] = False

    newstates = states[transitions].copy()
    newstates['datestop'][:-1] = newstates['datestart'][1:]
    newstates['tstop'][:-1] = newstates['tstart'][1:]
    newstates['datestop'][-1] = states['datestop'][-1]
    newstates['tstop'][-1] = states['tstop'][-1]

    return newstates
