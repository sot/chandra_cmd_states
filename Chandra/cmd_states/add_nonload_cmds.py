"""
Add non-load commands to the database and generate code to recreate those
commands for archive purposes.  See also cmd_states.cmd_set().

Usage: add_nonload_cmds.py [options] [cmd_set_arg1 ...]::

 Options:
   -h, --help            show this help message and exit
   --dbi=DBI             Database interface (sqlite|sybase)
   --server=SERVER       DBI server (<filename>|sybase)
   --check               Check for recent non-load commands and do not generate
                         commands
   --date=DATE           Date for command set
   --cmd-set=CMD_SET     Command set name (obsid|manvr|scs107|nsm)
   --loglevel=LOGLEVEL   Log level (10=debug, 20=info, 30=warnings)
   --archive-file=FILE   Archive file for storing nonload cmd sets
   --interrupt           Interrupt timelines and load_segments after ``date``
   --observing-only      Interrupt only 'observing' timelines

Examples::

  # Print recent non-load commands
  add_nonload_cmds.py --check

  # Add a maneuver to RA, Dec, Roll = 10, 20, 30
  add_nonload_cmds.py --date '2009:065:12:13:14' --cmd-set manvr 10 20 30

  # Add an autonomous NSM transition (which also runs SCS107)
  add_nonload_cmds.py --date '2009:001:12:13:14' --interrupt --cmd-set nsm --dry-run
  add_nonload_cmds.py --date '2009:001:12:13:14' --interrupt --cmd-set scs107

  # Add ACIS CTI commanding
  add_nonload_cmds.py --date '2012:072:20:52:00.000' --cmd-set aciscti

"""
from __future__ import print_function

import sys
import logging
import time

import Chandra.cmd_states as cmd_states
import Ska.DBI
from Chandra.Time import DateTime
import Ska.ParseCM


def get_options():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] [cmd_set_arg1 ...]")
    parser.set_defaults()
    parser.add_option("--date",
                      help="Date for command set")
    parser.add_option("--cmd-set",
                      help="Command set name")
    parser.add_option("--interrupt",
                      action='store_true',
                      help='Interrupt all timelines and load_segments after '
                           'date')
    parser.add_option("--observing-only",
                      action='store_true',
                      help='Interrupt observing timelines after date')
    parser.add_option("--loglevel",
                      type='int',
                      default=10,
                      help='Log level (10=debug, 20=info, 30=warnings)')
    parser.add_option("--dry-run",
                      action='store_true',
                      help='Show updates without actually writing to database')
    parser.add_option("--check",
                      action="store_true",
                      help="Show recent non-load commands and exit")
    parser.add_option("--dbi",
                      default='sqlite',
                      help="Database interface (sqlite|sybase)")
    parser.add_option("--server",
                      default='test.db3',
                      help="DBI server (<filename>|sybase)")
    parser.add_option("--user")
    parser.add_option("--database")
    parser.add_option("--archive-file",
                      default="nonload_cmds_archive.py",
                      help='Archive file for storing nonload cmd sets')
    (opt, args) = parser.parse_args()
    return (opt, args)


def log_cmds(cmds):
    logging.info('%-22s %-12s %-10s %-8s' % ('Date', 'CMD', 'TLMSID', 'MSID'))
    for cmd in cmds:
        if 'params' in cmd:
            paramstr = ' '.join(['%s=%s' % (key, str(val))
                                 for key, val in cmd['params'].items()])
        else:
            paramstr = ''
        logging.info('%-22s %-12s %-10s %-8s %s' %
                     (cmd['date'], cmd['cmd'], str(cmd['tlmsid']),
                      str(cmd['msid']), paramstr))


def main():
    opt, args = get_options()
    cmd_set_args = [Ska.ParseCM._coerce_type(x) for x in args]

    # Configure logging to emit msgs to stdout
    logging.basicConfig(level=opt.loglevel,
                        format='%(message)s',
                        stream=sys.stdout)

    logging.info('Connecting to db: dbi=%s server=%s' % (opt.dbi, opt.server))
    db = Ska.DBI.DBI(dbi=opt.dbi, server=opt.server,
                     user=opt.user, database=opt.database, verbose=False)

    # Print information about recent non-load commands
    nl_cmds = db.fetchall("SELECT * FROM cmds "
                          "WHERE timeline_id IS NULL ORDER BY date DESC")
    logging.info('Most recent non-load commands')
    log_cmds(nl_cmds[:10])
    logging.info('')

    # Jump out if only doing a check
    if opt.check:
        sys.exit(0)

    # Generate commands for the specified command set
    date = DateTime(opt.date).date
    cmd_set_states = cmd_states.cmd_set(opt.cmd_set, *cmd_set_args)
    cmds = cmd_states.generate_cmds(date, cmd_set_states)

    logging.info('Add following cmds to database')
    log_cmds(cmds)
    logging.info('')

    # Add commands to database if not doing a dry run
    if not opt.dry_run:
        logging.info('Adding cmds to database')
        cmd_states.insert_cmds_db(cmds, None, db)

    # Generate python that will add the same commands to the database
    f = (sys.stdout if opt.dry_run else open(opt.archive_file, 'a'))
    logging.info('Appending cmd_set info to %s' % opt.archive_file)
    print('', file=f)
    print('# Autogenerated by add_nonload_cmds.py at %s' % time.ctime(), file=f)
    print('# date=%s cmd_set=%s args=%s' % (date,
                                                 opt.cmd_set, ' '.join(args)), file=f)
    print("cmds = generate_cmds('%s', cmd_set(%s))" % (date,
                           ','.join(["'%s'" % opt.cmd_set] + args)), file=f)
    print("cmd_states.insert_cmds_db(cmds, None, db)", file=f)

    if opt.interrupt:
        if not opt.dry_run:
            cmd_states.interrupt_loads(date, db,
                                       observing_only=opt.observing_only)
        print(("cmd_states.interrupt_loads('%s', db, "
                    "observing_only=%s, current_only=True)" %
                    (date, opt.observing_only)), file=f)


if __name__ == '__main__':
    main()
