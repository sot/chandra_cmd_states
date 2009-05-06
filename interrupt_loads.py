#!/usr/bin/env python

"""
Update timelines table to reflect an mission load interrupt.  Normally all
timeline entries with datestop after the supplied ``datestop`` are updated to
set the table datestop to ``datestop``.  If --running-only is supplied then
only the load segment actually containing ``datestop`` will be truncated.
This is to clean up archival load segment values that are wrong.

Usage: interrupt_loads.py [options]::

  Options:
    -h, --help           show this help message and exit
    --dbi=DBI            Database interface (sqlite|sybase)
    --server=SERVER      DBI server (<filename>|sybase)
    --datestop=DATESTOP  Interrupt date
    --current-only       Only interrupt load segment current at datestop
    --loglevel=LOGLEVEL  Log level (10=debug, 20=info, 30=warnings)
  
Example::

  interrupt_loads.py --datestop 2009:065:12:34:56

"""
import sys
import logging

import Ska.DBI
import cmd_states

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
    parser.add_option("--datestop",
                      help="Interrupt date")
    parser.add_option("--current-only",
                      action="store_true",
                      help="Only interrupt load segment running at datestop")
    parser.add_option("--loglevel",
                      type='int',
                      default=20,
                      help='Log level (10=debug, 20=info, 30=warnings)')
    
    (opt, args) = parser.parse_args()
    return (opt, args)

def main():
    opt, args = get_options()

    # Configure logging to emit msgs to stdout
    logging.basicConfig(level=opt.loglevel,
                        format='%(message)s',
                        stream=sys.stdout)

    logging.info('Connecting to db: dbi=%s server=%s' % (opt.dbi, opt.server))
    db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server)

    cmd_states.interrupt_loads(opt.datestop, db, opt.current_only)

if __name__ == '__main__':
    main()
