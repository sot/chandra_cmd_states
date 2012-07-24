"""
Update timelines table to reflect an mission load interrupt.
"""

import sys
import logging

import Ska.DBI
import Chandra.cmd_states as cmd_states


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
    parser.add_option("--observing-only",
                      action="store_true",
                      help="Only interrupt 'observing' timelines")
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

    cmd_states.interrupt_loads(opt.datestop, db,
                               observing_only=opt.observing_only,
                               current_only=opt.current_only)

if __name__ == '__main__':
    main()
