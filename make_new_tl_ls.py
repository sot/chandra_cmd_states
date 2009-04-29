#!/usr/bin/env python

import os
import Ska.DBI

def ls_key(year, load_segment):
    return '%d:%s' % (year, load_segment)

syb = Ska.DBI.DBI(dbi='sybase', numpy=False, verbose=True)
db = Ska.DBI.DBI(dbi='sqlite', server='test.db3', numpy=False)

for drop in ('VIEW timeline_loads', 'TABLE timelines', 'TABLE load_segments'):
    try:
        db.execute('DROP %s' % drop)
    except:
        print '%s not found' % drop

for sqldef in ('load_segments', 'timelines', 'timeline_loads'):
    cmd = file(sqldef + '_def.sql').read()
    db.execute(cmd, commit=True)

for table in ('timelines', 'load_segments'):
    for col in ('datestart', 'datestop'):
        cmd = """CREATE INDEX idx_%(table)s_%(col)s
                 ON %(table)s ( %(col)s ) """ % dict(table=table, col=col)
        db.execute(cmd)

timelines = syb.fetchall('select * from timeline where load_year >= 2007')
load_segments = syb.fetchall('select * from load_segment where year >= 2007')

ls_index = {}

for ls in load_segments:
    ls['id'] = int(ls['tstart'])
    key = ls_key(ls['year'], ls['load_segment'])
    ls_index[key] = ls

    print 'Inserting ls %s' % key
    for key in ('week', 'tstart', 'tstop'):
        del ls[key]
    db.insert(ls, 'load_segments')

for tl in timelines:
    tl['id'] = int(tl['tstart'])
    ls = ls_index[ ls_key(tl['load_year'], tl['load_segment']) ]
    tl['load_segment_id'] = ls['id']

    print 'Insert tl %s %s %d' % (tl['datestart'], tl['datestop'], tl['id'])
    for key in ('load_segment', 'load_year', 'tstart', 'tstop'):
        del tl[key]
    db.insert(tl, 'timelines')

db.commit()

        
