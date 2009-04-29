from Chandra.Time import DateTime
from Ska.Matplotlib import plot_cxctime, pointpair
import Ska.ParseCM
import cmd_states
import Ska.DBI
from matplotlib import pyplot
from Ska.TelemArchive.fetch import fetch

def check_week(backstop_file, db):
    cmds = Ska.ParseCM.read_backstop(backstop_file)
    dbs = db.fetchall("""select * from cmd_states
                      where datestart > '%s' and datestart < '%s' order by datestart""" %
                      (cmds[0]['date'], cmds[-1]['date']))

    state0 = dict((x, dbs[0][x]) for x in dbs.dtype.names)
    state0['transition_keys'] = ''

    states = cmd_states.get_states(state0, cmds)

    # For plotting and evaluation cut the final state at 5 mins in length since
    # normally in ends at year 2099.
    states[-1].tstop = states[-1].tstart + 300.

    pyplot.figure(1)
    pyplot.clf()
    ticklocs, fig, ax = plot_cxctime(pointpair(dbs.tstart, dbs.tstop), pointpair(dbs.pitch), fmt='-b')
    plot_cxctime(pointpair(states.tstart, states.tstop), pointpair(states.pitch), fmt='-r')

    pyplot.figure(2)
    pyplot.clf()
    ticklocs, fig, ax = plot_cxctime(pointpair(dbs.tstart, dbs.tstop), pointpair(dbs.simpos), fmt='-b')
    plot_cxctime(pointpair(states.tstart, states.tstop), pointpair(states.simpos), fmt='-r')

    # 
    times = np.arange(dbs[0].tstart, dbs[-1].tstart, 300.)

    for col in ('power_cmd', 'obsid', 'si_mode', 'pcad_mode', 'simfa_pos', 'simpos'):
        s_vals, idxs = cmd_states.interpolate(states, times, col)
        db_vals, idxs = cmd_states.interpolate(dbs, times, col)
        if any(s_vals != db_vals):
            bad = s_vals != db_vals
            print 'Mismatch vs. orig cmd_states table for', col
            print np.flatnonzero(bad)
            print s_vals[bad]
            print db_vals[bad]

    names, vals = fetch(start=times[0], stop=times[-1]+1, dt=300.,
                        colspecs=['aopcadmd', 'cobsrqid', 'tscpos', 'fapos'])
    tlm = np.rec.fromrecords(vals, names=names)

    tlm_vals = tlm.aopcadmd
    s_vals, idxs = cmd_states.interpolate(states, tlm.date, 'pcad_mode')
    bad = tlm_vals != s_vals
    if any(bad):
        print 'Telemetry mismatch: pcad_mode', np.flatnonzero(bad)
        dates = [DateTime(x).date for x in tlm.date[bad]]
        print dates
        print s_vals[bad]
        print tlm_vals[bad]

    for tlm_col, state_col, tol in (('cobsrqid', 'obsid', 0),
                                    ('tscpos', 'simpos', 5)):
        tlm_vals = tlm[tlm_col]
        s_vals, idxs = cmd_states.interpolate(states, tlm.date, state_col)
        bad = abs(tlm_vals - s_vals) > tol
        if any(bad):
            print 'Telemetry mismatch:', state_col, np.flatnonzero(bad)
            dates = [DateTime(x).date for x in times[bad]]
            print dates
            print s_vals[bad]
            print tlm_vals[bad]

# Compare to Jean's cmd_states table
db = Ska.DBI.DBI(dbi='sybase')

backstop_files = ('/data/mpcrit1/mplogs/2009/JAN1209/ofls/CR012_0108.backstop',
                  '/data/mpcrit1/mplogs/2009/JAN2309/ofls/CR023_2105.backstop',
                  '/data/mpcrit1/mplogs/2009/JAN2609/ofls/CR026_0204.backstop',
                  '/data/mpcrit1/mplogs/2009/FEB0209/ofls/CR032_1103.backstop',
                  '/data/mpcrit1/mplogs/2009/FEB0909/ofls/CR039_0705.backstop',
                  '/data/mpcrit1/mplogs/2009/FEB1609/ofls/CR047_0600.backstop',
                  '/data/mpcrit1/mplogs/2009/FEB2309/ofls/CR054_0008.backstop')
for backstop_file in backstop_files[:1]:
    print backstop_file
    check_week(backstop_file, db)
    a = raw_input()
