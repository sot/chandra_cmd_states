#!/usr/bin/env python

import Ska.DBI
import cmd_states
from cmd_states import generate_cmds, cmd_set

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
    opt, args = parser.parse_args()
    return opt, args

opt, args = get_options()

db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server)

# Drop all existing non-load commands
for table in ('cmd_intpars', 'cmd_fltpars', 'cmds'):
    db.execute('DELETE FROM %s WHERE timeline_id is NULL' % table)

# Normal sun mode day 2008:225
cmds = generate_cmds('2008:225:10:00:00', cmd_set('nsm')) 
cmds += generate_cmds('2008:227:20:00:00', cmd_set('manvr', 0.734142,-0.111682,0.558589,0.369515 ))
cmds += generate_cmds('2008:227:21:25:00', cmd_set('manvr', 0.784368,-0.0804672,0.535211,0.303053))
cmds += generate_cmds('2008:227:22:15:00', cmd_set('manvr', 0.946291,-0.219412,0.0853751,0.221591))
cmd_states.insert_cmds_db(cmds, None, db)

# Normal sun mode '2008:292:23:24:56'
cmds += generate_cmds('2008:292:21:24:00', cmd_set('obsid', 0))
cmds = generate_cmds('2008:292:21:24:00', cmd_set('nsm'))
cmds += generate_cmds('2008:294:22:20:00', cmd_set('manvr', 0.608789,0.335168,0.717148,0.0523189))
cmds += generate_cmds('2008:295:02:35:00', cmd_set('manvr', 0.542935,0.333876,0.766926,0.0746532))
cmds += generate_cmds('2008:295:03:25:00', cmd_set('manvr', 0.866838,0.243633,0.362662,0.240231))
cmd_states.insert_cmds_db(cmds, None, db)
