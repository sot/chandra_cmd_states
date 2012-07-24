import sys
import logging

from Chandra.Time import DateTime
from Ska.Matplotlib import plot_cxctime, pointpair
import Ska.ParseCM
import Chandra.cmd_states as cmd_states
import Ska.DBI
from matplotlib import pyplot
from Ska.TelemArchive.fetch import fetch

# Configure logging to emit msgs to stdout
logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s',
                    stream=sys.stdout)

if 'drop' not in globals():
    drop = True

state0 = {'ccd_count': 5,
          'clocking': 0,
          'datestart': '2007:340:03:03:11.557',
          'datestop': '2099:001:03:03:21.808',
          'dec': 54.278148000000002,
          'fep_count': 5,
          'obsid': 10313,
          'pcad_mode': 'NPNT',
          'pitch': 144.67541499999999,
          'power_cmd': 'AA00000000',
          'q1': -0.52736700000000003,
          'q2': -0.67509300000000005,
          'q3': -0.45243499999999998,
          'q4': 0.247864,
          'ra': 123.340818,
          'roll': 143.23679200000001,
          'si_mode': 'TE_00782',
          'simfa_pos': -468,
          'simpos': 90520,
          'tstart': 347166257.741,
          'tstop': 347166267.99199998,
          'trans_keys': '',
          'vid_board': 1}

db = Ska.DBI.DBI(dbi='sqlite', server='test.db3', verbose=False)
# db = Ska.DBI.DBI(dbi='sybase')

if drop:
    tables = ('cmd_states', 'cmds', 'cmd_intpars', 'cmd_fltpars')
    for table in reversed(tables):
        try:
            db.execute('DROP TABLE %s' % table)
        except:
            print '%s not found' % table

    for table in tables:
        sqldef = file(table + '_def.sql').read()
        db.execute(sqldef, commit=True)

datestart = state0['datestart']
timeline_loads = db.fetchall("""SELECT * from timeline_loads
                                WHERE datestop > '%s'""" % datestart)

timeline_loads_mod = timeline_loads.copy()[:-2]
timeline_loads_mod[-1].datestop = '2009:053:00:00:00.000'

print '=' * 40
print 'Processing with timeline_loads'
cmds = cmd_states.get_cmds(datestart, db=db, update_db=True, timeline_loads=timeline_loads)
states = cmd_states.get_states(state0, cmds)
print 'len(cmds) =',len(cmds)
cmd_states.update_states_db(states, db)

if 0:
    print '=' * 40
    print 'Processing with timeline_loads_mod'
    cmds = cmd_states.get_cmds(datestart, db=db, update_db=True, timeline_loads=timeline_loads_mod)
    states = cmd_states.get_states(state0, cmds)
    print 'len(cmds) =',len(cmds)
    print states[0]
    print states[-1]
    cmd_states.update_states_db(states, db)

    print '=' * 40
    print 'Processing with timeline_loads'
    cmds = cmd_states.get_cmds(datestart, db=db, update_db=True, timeline_loads=timeline_loads)
    states = cmd_states.get_states(state0, cmds)
    print 'len(cmds) =',len(cmds)
    print states[0]
    print states[-1]
    cmd_states.update_states_db(states, db)
