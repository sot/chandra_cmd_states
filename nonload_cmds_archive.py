#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import Ska.DBI
import Chandra.cmd_states as cmd_states
from Chandra.cmd_states import generate_cmds, cmd_set, interrupt_loads

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
    parser.add_option("--user",
                      default='aca_ops')
    parser.add_option("--database",
                      default='aca')
    opt, args = parser.parse_args()
    return opt, args

opt, args = get_options()

db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server,
                 user=opt.user, database=opt.database)

# Drop all existing non-load commands
for table in ('cmd_intpars', 'cmd_fltpars', 'cmds'):
    db.execute('DELETE FROM %s WHERE timeline_id is NULL' % table)

cmds = []

# Normal sun mode day 2008:225
cmds += generate_cmds('2008:225:10:00:00', cmd_set('nsm')) 
cmds += generate_cmds('2008:227:20:00:00', cmd_set('manvr', 0.734142,-0.111682,0.558589,0.369515 ))
cmds += generate_cmds('2008:227:21:25:00', cmd_set('manvr', 0.784368,-0.0804672,0.535211,0.303053))
cmds += generate_cmds('2008:227:22:15:00', cmd_set('manvr', 0.946291,-0.219412,0.0853751,0.221591))

# Normal sun mode '2008:292:23:24:56'
cmds += generate_cmds('2008:292:21:24:00', cmd_set('nsm'))
cmds += generate_cmds('2008:292:21:24:00', cmd_set('obsid', 0))
cmds += generate_cmds('2008:294:22:20:00', cmd_set('manvr', 0.608789,0.335168,0.717148,0.0523189))
cmds += generate_cmds('2008:295:02:35:00', cmd_set('manvr', 0.542935,0.333876,0.766926,0.0746532))
cmds += generate_cmds('2008:295:03:25:00', cmd_set('manvr', 0.866838,0.243633,0.362662,0.240231))

# NSM in 2004
cmds += generate_cmds('2004:315:16:41:00', cmd_set('nsm'))


# Add StopScience and VidBoard power down at approximate time of
# CAP_1134_AUG2609A_Load_Termination_and_ACIS_Safing
cap_cmds = (dict(dur=1.025),
            dict(cmd='ACISPKT',
                 tlmsid='AA00000000',
                 ),
            dict(cmd='ACISPKT',
                 tlmsid='WSVIDALLDN',
                 ),
            )  
cmds += generate_cmds('2009:240:10:40:00.000', cap_cmds )


# ACIS Reboot; Contrived Power commands to match telemetry
cmds += generate_cmds('2010:025:09:11:00.000', ( dict(cmd='ACISPKT', tlmsid='WSPOW00306'),
                                                 dict(cmd='ACISPKT', tlmsid='AA00000000')
                                                 ))
cmds += generate_cmds('2010:025:09:11:01.025', ( dict(cmd='ACISPKT', tlmsid='WSVIDALLDN'), 
                                                 ))

cmds += generate_cmds('2010:025:14:00:00.000', ( dict(cmd='ACISPKT', tlmsid='WSPOW0EC3E'),
                                                 dict(cmd='ACISPKT', tlmsid='AA00000000')
                                                 ))
cmds += generate_cmds('2010:025:14:00:01.025', ( dict(cmd='ACISPKT', tlmsid='XTZ0000005'), 
                                                 ))

cmds += generate_cmds('2010:026:00:30:00.000', ( dict(cmd='ACISPKT', tlmsid='WSPOW01f1f'),
                                                 ))

cmds += generate_cmds('2010:026:01:36:41.000', ( dict(cmd='ACISPKT', tlmsid='WSPOW00707'), 
                                                 ))

# Day 97 CAP made a strange state at 80W that looks like a fep=3,vid_board=on,clocking=off
cmds += generate_cmds('2010:097:11:45:00.000', ( dict(cmd='ACISPKT', tlmsid='WSPOW00707'),
                                                 dict(cmd='ACISPKT', tlmsid='AA00000000')
                                                 ))




# SCS107s
dates = """
2001:360:06:30:00

2002:331:00:00:00
2002:314:03:32:52
2002:250:17:04:10
2002:236:02:11:29
2002:230:18:43:00
2002:198:12:37:40
2002:143:09:58:00
2002:134:18:10:00
2002:111:05:07:07
2002:109:14:15:00
2002:107:12:54:22
2002:092:22:00:00
2002:077:14:07:09
2002:024:04:17:00
2002:011:03:17:00

2003:336:17:31:10
2003:326:01:24:54
2003:306:20:52:34
2003:301:13:02:04
2003:299:19:22:00
2003:297:13:34:00
2003:213:11:38:00
2003:173:18:48:41
2003:149:22:01:44
2003:128:20:08:06
2003:120:23:37:13
2003:107:20:36:00

2004:315:16:41:00
2004:312:19:54:46
2004:257:21:38:00
2004:215:18:21:00
2004:213:12:01:55
2004:210:19:24:29
2004:208:21:59:00
2004:208:03:54:00
2004:181:19:17:00
2004:021:11:51:00
2004:009:14:29:11

2005:016:14:44:00
2005:257:01:06:00
2005:251:03:44:43
2005:236:22:38:00
2005:234:19:40:20
2005:214:01:28:49
2005:134:13:24:19
2005:016:14:44:00

2006:347:22:45:39
2006:344:08:59:38
2006:340:16:16:00
2006:080:01:32:00

2008:292:21:24:00
2008:225:10:00:00
"""
for date in dates.split('\n'):
    date = date.strip()
    if date:
        print date
        cmds += generate_cmds(date, cmd_set('scs107'))
        cmd_states.interrupt_loads(date, db, current_only=True)


cmd_states.insert_cmds_db(cmds, None, db)

# 2010:150 NSM commands 
# date=2010:150:04:00:00.000 cmd_set=nsm args=
cmds = generate_cmds('2010:150:04:00:00.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2010:150:04:00:00.000', db, current_only=True)

# date=2010:150:04:00:00.000 cmd_set=scs107 args=
cmds = generate_cmds('2010:150:04:00:00.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2010:150:04:00:00.000', db, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Jun  8 10:57:43 2011
# date=2011:158:15:23:10.000 cmd_set=scs107 args=
cmds = generate_cmds('2011:158:15:23:10.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2011:158:15:23:10.000', db, current_only=True)



# Autogenerated by add_nonload_cmds.py at Thu Jul  7 10:56:59 2011
# date=2011:187:12:29:14.000 cmd_set=scs107 args=
cmds = generate_cmds('2011:187:12:29:14.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2011:187:12:29:14.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Thu Jul  7 11:13:29 2011
# date=2011:187:12:29:14.000 cmd_set=nsm args=
cmds = generate_cmds('2011:187:12:29:14.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Jul 18 15:29:13 2011
# date=2011:192:05:12:00.000 cmd_set=manvr args=295.50 7.50 169.06
cmds = generate_cmds('2011:192:05:12:00.000', cmd_set('manvr',295.50,7.50,169.06))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Aug  4 10:27:11 2011
# date=2011:216:07:03:34.000 cmd_set=scs107 args=
cmds = generate_cmds('2011:216:07:03:34.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2011:216:07:03:34.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Oct 24 14:57:34 2011
# date=2011:297:18:28:41.000 cmd_set=scs107 args=
cmds = generate_cmds('2011:297:18:28:41.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2011:297:18:28:41.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Thu Oct 27 10:14:41 2011
# date=2011:299:04:58:40.000 cmd_set=scs107 args=
cmds = generate_cmds('2011:299:04:58:40.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2011:299:04:58:40.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Thu Oct 27 10:15:23 2011
# date=2011:299:04:58:40.000 cmd_set=nsm args=
cmds = generate_cmds('2011:299:04:58:40.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Jan 23 12:56:53 2012
# date=2012:023:06:00:38.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:023:06:00:38.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:023:06:00:38.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Fri Jan 27 17:57:12 2012
# date=2012:027:19:39:14.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:027:19:39:14.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:027:19:39:14.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Feb 27 06:37:16 2012
# date=2012:058:03:24:21.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:058:03:24:21.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:058:03:24:21.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Mar  7 08:28:48 2012
# date=2012:067:05:30:05.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:067:05:30:05.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:067:05:30:05.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Mar 13 19:33:57 2012
# date=2012:073:22:45:13.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:073:22:45:13.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:073:22:45:13.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Apr 18 14:00:25 2012
# date=2012:058:20:29:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2012:058:20:29:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed Apr 18 14:01:26 2012
# date=2012:072:20:52:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2012:072:20:52:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu May 17 09:51:01 2012
# date=2012:138:02:18:14.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:138:02:18:14.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:138:02:18:14.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon May 21 10:13:55 2012
# date=2012:138:19:52:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2012:138:19:52:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue May 29 16:58:59 2012
# date=2012:150:03:33:29.000 cmd_set=nsm args=
cmds = generate_cmds('2012:150:03:33:29.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:150:03:33:29.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue May 29 16:59:01 2012
# date=2012:150:03:33:29.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:150:03:33:29.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)

# Mocked up maneuver cmds to match telem after 2012:150 safe mode recovery
# The first maneuver corresponds to the quaternion update and not to an actual maneuver
cmds = generate_cmds('2012:152:01:42:09.816', cmd_set('manvr',0.4391227365,-0.7020152211,0.3264989555,0.4557897747))
cmds += generate_cmds('2012:152:02:39:29.816', cmd_set('manvr',0.5550038218,-0.8291832805,0.0464709997,0.0476069339))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Jul 13 07:34:02 2012
# date=2012:194:19:59:42.088 cmd_set=scs107 args=
cmds = generate_cmds('2012:194:19:59:42.088', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:194:19:59:42.088', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sun Jul 15 09:44:10 2012
# date=2012:196:21:08:00.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:196:21:08:00.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:196:21:08:00.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sun Jul 15 09:47:00 2012
# date=2012:197:03:45:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2012:197:03:45:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Jul 17 15:08:05 2012
# date=2012:197:20:12:38.869 cmd_set=acis args=AA00000000 WSVIDALLDN
# hand-edit to quote the TLMSID arguments
cmds = generate_cmds('2012:197:20:12:38.869', cmd_set('acis','AA00000000','WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jul 19 10:36:49 2012
# date=2012:201:11:44:57.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:201:11:44:57.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:201:11:44:57.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Sep  3 11:53:00 2012
# date=2012:247:12:57:33.000 cmd_set=scs107 args=
cmds = generate_cmds('2012:247:12:57:33.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2012:247:12:57:33.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sun Mar 17 09:26:41 2013
# date=2013:076:12:32:40.000 cmd_set=scs107 args=
cmds = generate_cmds('2013:076:12:32:40.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2013:076:12:32:40.000', db, observing_only=True, current_only=True)

# forgot to set permissions on nonload_cmd_archive before running
# add_nonload_cmds.  Cmds added here manually
# date=2013:076:21:19:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2013:076:21:19:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)
# date=2013:077:18:50:00.000 cmd_set=acis args=AA00000000 WSVIDALLDN
cmds = generate_cmds('2013:077:18:50:00.000', cmd_set('acis','AA00000000','WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed May 22 16:29:25 2013
# date=2013:142:14:49:13.000 cmd_set=scs107 args=
cmds = generate_cmds('2013:142:14:49:13.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2013:142:14:49:13.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Thu May 23 13:09:48 2013
# date=2013:143:05:07:00.000 cmd_set=obsid args=65534
cmds = generate_cmds('2013:143:05:07:00.000', cmd_set('obsid',65534))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri May 24 16:57:02 2013
# date=2013:144:20:39:14.000 cmd_set=scs107 args=
cmds = generate_cmds('2013:144:20:39:14.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2013:144:20:39:14.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Oct  1 22:16:02 2013
# date=2013:275:02:05:23.000 cmd_set=scs107 args=
cmds = generate_cmds('2013:275:02:05:23.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2013:275:02:05:23.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Jan  8 07:07:35 2014
# date=2014:007:20:39:16.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:007:20:39:16.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2014:007:20:39:16.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Jan 13 14:00:28 2014
# date=2014:009:19:31:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2014:009:19:31:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Jan 13 14:11:31 2014
# date=2014:009:19:31:00.000 cmd_set=obsid args=62674
cmds = generate_cmds('2014:009:19:31:00.000', cmd_set('obsid',62674))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Jan 13 14:15:08 2014
# date=2014:008:23:07:20.000 cmd_set=obsid args=65532
cmds = generate_cmds('2014:008:23:07:20.000', cmd_set('obsid',65532))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul  6 21:47:00 2014
# date=2014:187:23:36:36.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:187:23:36:36.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sat Jul 26 13:23:29 2014
# date=2014:207:07:03:55.000 cmd_set=nsm args=
cmds = generate_cmds('2014:207:07:03:55.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2014:207:07:03:55.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sat Jul 26 13:24:19 2014
# date=2014:207:07:03:55.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:207:07:03:55.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul 27 10:22:27 2014
# date=2014:207:23:05:09.000 cmd_set=manvr args=45.136 -28.259 113.850
cmds = generate_cmds('2014:207:23:05:09.000', cmd_set('manvr',45.136,-28.259,113.850))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul 27 10:22:29 2014
# date=2014:208:01:11:11.000 cmd_set=manvr args=45.582 -28.087 112.993
cmds = generate_cmds('2014:208:01:11:11.000', cmd_set('manvr',45.582,-28.087,112.993))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul 27 10:22:31 2014
# date=2014:208:01:39:08.000 cmd_set=manvr args=74.00 42.00 79.949
cmds = generate_cmds('2014:208:01:39:08.000', cmd_set('manvr',74.00,42.00,79.949))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul 27 10:22:33 2014
# date=2014:208:02:31:11.000 cmd_set=obsid args=62673
cmds = generate_cmds('2014:208:02:31:11.000', cmd_set('obsid',62673))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sun Jul 27 10:22:35 2014
# date=2014:208:02:35:17.000 cmd_set=aciscti args=
cmds = generate_cmds('2014:208:02:35:17.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep 12 12:34:35 2014
# date=2014:255:11:51:18.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:255:11:51:18.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2014:255:11:51:18.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Dec 22 00:14:04 2014
# date=2014:356:04:52:35.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:356:04:52:35.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2014:356:04:52:35.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Dec 23 14:49:57 2014
# date=2014:357:11:32:25.000 cmd_set=scs107 args=
cmds = generate_cmds('2014:357:11:32:25.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2014:357:11:32:25.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sun Dec 28 13:03:14 2014
# date=2014:357:20:40:44.000 cmd_set=obsid args=65531
cmds = generate_cmds('2014:357:20:40:44.000', cmd_set('obsid',65531))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Jan  6 10:50:55 2015
# date=2015:006:08:22:59.000 cmd_set=nsm args=
cmds = generate_cmds('2015:006:08:22:59.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2015:006:08:22:59.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Jan  6 10:50:57 2015
# date=2015:006:08:22:59.000 cmd_set=scs107 args=
cmds = generate_cmds('2015:006:08:22:59.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed Jan  7 20:30:35 2015
# date=2015:007:22:27:07.000 cmd_set=manvr args=112.0 49.0 170.735
cmds = generate_cmds('2015:007:22:27:07.000', cmd_set('manvr',112.0,49.0,170.735))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jan  8 09:33:28 2015
# date=2015:007:05:54:20.000 cmd_set=manvr args=112.0 49.0 170.730
cmds = generate_cmds('2015:007:05:54:20.000', cmd_set('manvr',112.0,49.0,170.730))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jan  8 10:57:10 2015
# date=2015:008:00:47:00.000 cmd_set=obsid args=62671
cmds = generate_cmds('2015:008:00:47:00.000', cmd_set('obsid',62671))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jan  8 10:57:14 2015
# date=2015:008:00:49:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2015:008:00:49:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jan  8 15:53:03 2015
# date=2015:008:17:37:52.000 cmd_set=acis args=AA00000000
cmds = generate_cmds('2015:008:17:37:52.000', cmd_set('acis', 'AA00000000'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Jan  8 15:53:07 2015
# date=2015:008:17:38:02.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2015:008:17:38:02.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Add cmds to include dither disable and obsid=0 during NSM
cmds = []
dith_on = (dict(dur=1.025),
           dict(cmd='COMMAND_SW',
                tlmsid='AOENDITH',
                ))
dith_off = (dict(dur=1.025),
            dict(cmd='COMMAND_SW',
                 tlmsid='AODSDITH',
                 ))
cmds += generate_cmds('2015:006:12:53:43.100', cmd_set('obsid', 0))
cmds += generate_cmds('2015:006:12:53:43.100', dith_off)
cmds += generate_cmds('2015:009:03:38:36.100', dith_on)
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Mar 17 09:11:14 2015
# date=2015:076:04:37:42.000 cmd_set=scs107 args=
cmds = generate_cmds('2015:076:04:37:42.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2015:076:04:37:42.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Mar 25 14:52:57 2015
# date=2015:076:21:47:41.000 cmd_set=obsid args=62670
cmds = generate_cmds('2015:076:21:47:41.000', cmd_set('obsid',62670))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed Mar 25 14:53:00 2015
# date=2015:076:21:48:00.000 cmd_set=aciscti args=
cmds = generate_cmds('2015:076:21:48:00.000', cmd_set('aciscti'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed Mar 25 14:53:02 2015
# date=2015:077:16:40:00.000 cmd_set=acis args=AA00000000 WSVIDALLDN
cmds = generate_cmds('2015:077:16:40:00.000', cmd_set('acis', 'AA00000000' , 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Jun 22 21:42:53 2015
# date=2015:173:22:41:05.000 cmd_set=scs107 args=
cmds = generate_cmds('2015:173:22:41:05.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2015:173:22:41:05.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Sep 21 04:10:12 2015
# date=2015:264:04:35:00.000 cmd_set=scs107 args=
cmds = generate_cmds('2015:264:04:35:00.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2015:264:04:35:00.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Sep 22 14:02:00 2015
# date=2015:264:22:20:09.000 cmd_set=nsm args=
cmds = generate_cmds('2015:264:22:20:09.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Sep 22 14:05:36 2015
# date=2015:265:13:20:20.000 cmd_set=manvr args=89.124 -2.411 90.144
cmds = generate_cmds('2015:265:13:20:20.000', cmd_set('manvr',89.124,-2.411,90.144))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Sep 22 16:12:30 2015
# date=2015:264:04:36:00.000 cmd_set=nsm args=
cmds = generate_cmds('2015:264:04:36:00.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Sep 22 16:14:36 2015
# date=2015:265:14:15:00.000 cmd_set=manvr args=24.3 0 90.7
cmds = generate_cmds('2015:265:14:15:00.000', cmd_set('manvr',24.3,0,90.7))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Mar  3 16:51:22 2016
# date=2016:063:12:11:30.000 cmd_set=scs107 args=
cmds = generate_cmds('2016:063:17:11:30.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2016:063:17:11:30.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Fri Mar  4 12:37:36 2016
# date=2016:064:01:52:02.000 cmd_set=nsm args=
cmds = generate_cmds('2016:063:17:12:48.960', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar  4 18:22:45 2016
# date=2016:064:21:45:03.000 cmd_set=manvr args=158.900 -17.400 343.301
cmds = generate_cmds('2016:064:21:45:03.000', cmd_set('manvr',158.900,-17.400,343.301))
cmd_states.insert_cmds_db(cmds, None, db)

# Realtime load interruption for MAR1116 replan
cmd_states.interrupt_loads('2016:071:12:05:00.000', db, observing_only=False, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sun Aug 21 09:04:43 2016
# date=2016:234:07:24:00.000 cmd_set=scs107 args=
cmds = generate_cmds('2016:234:07:24:00.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2016:234:07:24:00.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Aug 24 17:20:05 2016
# date=2016:234:16:51:47.000 cmd_set=manvr args=313.163 6.515 225.032
cmds = generate_cmds('2016:234:16:51:47.000', cmd_set('manvr',313.163,6.515,225.032))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sat Nov 19 17:12:35 2016
# date=2016:324:12:59:32.000 cmd_set=scs107 args=
cmds = generate_cmds('2016:324:12:59:32.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2016:324:12:59:32.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Sat Nov 19 17:14:02 2016
# date=2016:324:12:59:34.000 cmd_set=nsm args=
cmds = generate_cmds('2016:324:12:59:34.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Sat Nov 19 23:50:58 2016
# date=2016:325:04:09:02.000 cmd_set=manvr args=79.116 34.287 121.978
cmds = generate_cmds('2016:325:04:09:02.000', cmd_set('manvr',79.116,34.287,121.978))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Dec 15 11:32:40 2016
# date=2016:344:22:29:00.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2016:344:22:29:00.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Mar  7 09:23:24 2017
# date=2017:066:00:24:21.000 cmd_set=nsm args=
cmds = generate_cmds('2017:066:00:24:21.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2017:066:00:24:21.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Tue Mar  7 09:27:09 2017
# date=2017:066:00:24:21.000 cmd_set=scs107 args=
cmds = generate_cmds('2017:066:00:24:21.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Mar  7 16:10:48 2017
# date=2017:066:11:22:02.000 cmd_set=manvr args=-0.20072072 -0.64411512 0.06371088 0.73536918
cmds = generate_cmds('2017:066:11:22:02.000', cmd_set('manvr',-0.20072072,-0.64411512,0.06371088,0.73536918))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Mar  9 23:25:10 2017
# date=2017:068:17:00:42.000 cmd_set=scs107 args=
cmds = generate_cmds('2017:068:17:00:42.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2017:068:17:00:42.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Fri Mar 10 11:43:00 2017
# date=2017:069:15:22:36.265 cmd_set=manvr args=144.997 -11.999 300.041
cmds = generate_cmds('2017:069:15:22:36.265', cmd_set('manvr',144.997,-11.999,300.041))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 10 11:43:00 2017
# date=2017:069:15:33:00.000 cmd_set=obsid args=62663
cmds = generate_cmds('2017:069:15:33:00.000', cmd_set('obsid',62663))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 10 11:43:03 2017
# date=2017:069:15:39:00.000 cmd_set=acis args=WSVIDALLDN WSPOW08E1E WT00C62014 XTZ0000005
cmds = generate_cmds('2017:069:15:39:00.000', cmd_set('acis', 'WSVIDALLDN' , 'WSPOW08E1E', 'WT00C62014' , 'XTZ0000005'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 16:45:46 2017
# date=2017:090:19:01:57.000 cmd_set=scs107 args=
cmds = generate_cmds('2017:090:19:01:57.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2017:090:19:01:57.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 23:12:35 2017
# date=2017:091:00:53:01.000 cmd_set=manvr args=170.001 -45.00 330.184
cmds = generate_cmds('2017:091:00:53:01.000', cmd_set('manvr',170.001,-45.00,330.184))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 23:24:25 2017
# date=2017:091:01:09:02.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2017:091:01:09:02.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 23:24:27 2017
# date=2017:091:01:09:03.000 cmd_set=acis args=WSPOW08E1E
cmds = generate_cmds('2017:091:01:09:03.000', cmd_set('acis', 'WSPOW08E1E'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 23:24:29 2017
# date=2017:091:01:09:04.000 cmd_set=acis args=WT00C62014
cmds = generate_cmds('2017:091:01:09:04.000', cmd_set('acis', 'WT00C62014'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Mar 31 23:24:30 2017
# date=2017:091:01:09:05.000 cmd_set=acis args=XTZ0000005
cmds = generate_cmds('2017:091:01:09:05.000', cmd_set('acis', 'XTZ0000005'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Apr  4 09:46:58 2017
# date=2017:091:01:03:30.000 cmd_set=obsid args=62662
cmds = generate_cmds('2017:091:01:03:30.000', cmd_set('obsid',62662))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Thu Sep  7 07:48:22 2017
# date=2017:250:02:41:48.000 cmd_set=scs107 args=
cmds = generate_cmds('2017:250:02:41:48.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2017:250:02:41:48.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:41 2017
# date=2017:250:18:32:02.000 cmd_set=obsid args=65530
cmds = generate_cmds('2017:250:18:32:02.000', cmd_set('obsid', 65530))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:42 2017
# date=2017:251:19:45:00.000 cmd_set=obsid args=62661
cmds = generate_cmds('2017:251:19:45:00.000', cmd_set('obsid', 62661))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:43 2017
# date=2017:251:19:45:10.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2017:251:19:45:10.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:44 2017
# date=2017:251:19:45:11.000 cmd_set=acis args=WSPOW08E1E
cmds = generate_cmds('2017:251:19:45:11.000', cmd_set('acis', 'WSPOW08E1E'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:45 2017
# date=2017:251:19:45:12.000 cmd_set=acis args=WT00C62014
cmds = generate_cmds('2017:251:19:45:12.000', cmd_set('acis', 'WT00C62014'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Fri Sep  8 13:37:46 2017
# date=2017:251:19:45:13.000 cmd_set=acis args=XTZ0000005
cmds = generate_cmds('2017:251:19:45:13.000', cmd_set('acis', 'XTZ0000005'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Mon Sep 11 08:14:17 2017
# date=2017:254:07:51:39.000 cmd_set=scs107 args=
cmds = generate_cmds('2017:254:07:51:39.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2017:254:07:51:39.000', db, observing_only=True, current_only=True)

# Autogenerated by add_nonload_cmds.py at Mon Sep 18 11:10:15 2017
# date=2017:254:20:00:40.000 cmd_set=obsid args=65529
cmds = generate_cmds('2017:254:20:00:40.000', cmd_set('obsid', 65529))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Wed Oct 10 14:45:31 2018
# date=2018:283:13:54:39.000 cmd_set=scs107 args=
cmds = generate_cmds('2018:283:13:54:39.000', cmd_set('scs107'))
cmd_states.insert_cmds_db(cmds, None, db)
cmd_states.interrupt_loads('2018:283:13:54:39.000', db, observing_only=None, current_only=True)

# Autogenerated by add_nonload_cmds.py at Wed Oct 10 14:45:35 2018
# date=2018:283:13:54:39.000 cmd_set=nsm args=
cmds = generate_cmds('2018:283:13:54:39.000', cmd_set('nsm'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:15 2018
# date=2018:285:22:10:47.122 cmd_set=manvr args=-0.0184166682591 0.341397078463 0.144720785765 0.928528273971
cmds = generate_cmds('2018:285:22:10:47.122', cmd_set('manvr', -0.0184166682591, 0.341397078463, 0.144720785765, 0.928528273971))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:15 2018
# date=2018:286:12:28:00.000 cmd_set=obsid args=62660
cmds = generate_cmds('2018:286:12:28:00.000', cmd_set('obsid', 62660))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:16 2018
# date=2018:286:12:32:00.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2018:286:12:32:00.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:17 2018
# date=2018:286:12:32:01.000 cmd_set=acis args=WSPOW08F3E
cmds = generate_cmds('2018:286:12:32:01.000', cmd_set('acis', 'WSPOW08F3E'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:17 2018
# date=2018:286:12:32:02.000 cmd_set=acis args=WT00C60014
cmds = generate_cmds('2018:286:12:32:02.000', cmd_set('acis', 'WT00C60014'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:18 2018
# date=2018:286:12:32:03.000 cmd_set=acis args=XTZ0000005
cmds = generate_cmds('2018:286:12:32:03.000', cmd_set('acis', 'XTZ0000005'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:19 2018
# date=2018:288:23:07:47.110 cmd_set=manvr args=-0.861635360527 -0.168040851008 -0.47501314504 0.0609039421983
cmds = generate_cmds('2018:288:23:07:47.110', cmd_set('manvr', -0.861635360527, -0.168040851008, -0.47501314504, 0.0609039421983))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:19 2018
# date=2018:288:23:20:00.000 cmd_set=obsid args=62659
cmds = generate_cmds('2018:288:23:20:00.000', cmd_set('obsid', 62659))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:20 2018
# date=2018:288:23:21:00.000 cmd_set=acis args=WSVIDALLDN
cmds = generate_cmds('2018:288:23:21:00.000', cmd_set('acis', 'WSVIDALLDN'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:21 2018
# date=2018:288:23:21:01.000 cmd_set=acis args=WSPOW08F3E
cmds = generate_cmds('2018:288:23:21:01.000', cmd_set('acis', 'WSPOW08F3E'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:21 2018
# date=2018:288:23:21:02.000 cmd_set=acis args=WT00C60014
cmds = generate_cmds('2018:288:23:21:02.000', cmd_set('acis', 'WT00C60014'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:22 2018
# date=2018:288:23:21:03.000 cmd_set=acis args=XTZ0000005
cmds = generate_cmds('2018:288:23:21:03.000', cmd_set('acis', 'XTZ0000005'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:23 2018
# date=2018:290:01:00:00.000 cmd_set=acis args=AA00000000
cmds = generate_cmds('2018:290:01:00:00.000', cmd_set('acis', 'AA00000000'))
cmd_states.insert_cmds_db(cmds, None, db)

# Autogenerated by add_nonload_cmds.py at Tue Oct 16 09:58:23 2018
# date=2018:290:01:00:01.000 cmd_set=acis args=WSPOW00000
cmds = generate_cmds('2018:290:01:00:01.000', cmd_set('acis', 'WSPOW00000'))
cmd_states.insert_cmds_db(cmds, None, db)
