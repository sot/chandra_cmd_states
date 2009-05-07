#!/usr/bin/env python
"""
Make command tables cmd_states, cmds, cmd_intpar, cmd_fltpars.
Drop tables if already existing.

Usage: make_cmd_tables.py [options]::

  Options:
    -h, --help       show this help message and exit
    --dbi=DBI        Database interface (sqlite|sybase)
    --server=SERVER  DBI server (<filename>|sybase)
"""

import Ska.DBI

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

def main():
    opt, args = get_options()

    db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server, numpy=False, verbose=True)

    tables = ('cmd_states', 'cmds', 'cmd_intpars', 'cmd_fltpars')
    for table in reversed(tables):
        try:
            db.execute('DROP TABLE %s' % table)
        except:
            print '%s not found' % table

    for table in tables:
        sqldef = file(table + '_def.sql').read()
        db.execute(sqldef, commit=True)

if __name__ == '__main__':
    main()
