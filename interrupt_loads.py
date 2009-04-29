#!/usr/bin/env python

"""
Update timelines table to reflect an mission load interrupt.  All timeline entries
with datestop after the supplied ``datestop`` are updated to set the table datestop
to ``datestop``.

Usage: interrupt_loads.py [options]::

  Options:
    -h, --help           show this help message and exit
    --dbi=DBI            Database interface (sqlite|sybase)
    --server=SERVER      DBI server (<filename>|sybase)
    --datestop=DATESTOP  Interrupt date
    --loglevel=LOGLEVEL  Log level (10=debug, 20=info, 30=warnings)
  
Example::

  interrupt_loads.py --datestop 2009:065:12:34:56

"""
import sys
import logging

import Ska.DBI
from Chandra.Time import DateTime

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--dbi",
                      default='sqlite',
                      help="Database interface (sqlite|sybase)")
    parser.add_option("--server",
                      default='test.db3',
                      help="DBI server (<filename>|sybase)")
    parser.add_option("--datestop",
                      help="Interrupt date")
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

    datestop = DateTime(opt.datestop).date

    timelines = db.fetchall("SELECT * FROM timelines WHERE datestop > '%s'" % datestop)
    logging.info('Updating %d timelines with datestop > %s' % (len(timelines), datestop))
    for tl in timelines:
        logging.info("%s %s %s" % (tl['datestart'], tl['datestop'], tl['dir']))

    # Get confirmation to update timeslines table in database
    a = raw_input('Proceed [N]? ')
    if a.lower().strip().startswith('y'):
        logging.info('Revert with:')
        for tl in timelines:
            logging.info("UPDATE timelines SET datestop='%s' where id=%d ;" % (tl['datestop'], tl['id']))

        db.execute("UPDATE timelines SET datestop='%s' WHERE datestop > '%s'" % (datestop, datestop))

if __name__ == '__main__':
    main()
