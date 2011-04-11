#!/usr/bin/env python
"""
Copy timelines and load_segments tables from sybase to local sqlite db and create
timeline_loads view.
"""

import os
import Ska.DBI

def get_options():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] [cmd_set_arg1 ...]")
    parser.set_defaults()
    parser.add_option("--server",
                      default='db_base.db3',
                      help="DBI server (<filename>|sybase)")
    opt, args = parser.parse_args()
    return opt, args

def main():
    opt, args = get_options()

    syb = Ska.DBI.DBI(dbi='sybase', user='aca_read', database='aca', numpy=False, verbose=True)
    db = Ska.DBI.DBI(dbi='sqlite', server=opt.server, numpy=False, verbose=False)

    for drop in ('VIEW timeline_loads', 'TABLE timelines', 'TABLE load_segments'):
        try:
            db.execute('DROP %s' % drop)
        except:
            print '%s not found' % drop

    for sqldef in ('load_segments', 'timelines', 'timeline_loads'):
        cmd = file(sqldef + '_def.sql').read()
        db.execute(cmd, commit=True)

    timelines = syb.fetchall('select * from timelines')
    load_segments = syb.fetchall('select * from load_segments')

    for ls in load_segments:
        print 'Inserting ls %d:%s' % (ls['year'], ls['load_segment'])
        db.insert(ls, 'load_segments')

    for tl in timelines:
        print 'Insert tl %s %s %d' % (tl['datestart'], tl['datestop'], tl['id'])
        db.insert(tl, 'timelines')

    db.commit()

if __name__ == '__main__':
    main()
