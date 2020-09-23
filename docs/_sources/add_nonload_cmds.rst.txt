:mod:`add_nonload_cmds`
==========================

Add non-load commands to the database and generate code to recreate those
commands for archive purposes.  See also cmd_states.cmd_set().

Usage
-----
::

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

Examples
--------
::

  # Print recent non-load commands
  add_nonload_cmds.py --check

  # Add a maneuver to RA, Dec, Roll = 10, 20, 30
  add_nonload_cmds.py --date '2009:065:12:13:14' --cmd-set manvr 10 20 30

  # Add an autonomous NSM transition (which also runs SCS107)
  add_nonload_cmds.py --date '2009:001:12:13:14' --interrupt --cmd-set nsm --dry-run
  add_nonload_cmds.py --date '2009:001:12:13:14' --interrupt --cmd-set scs107

  # Add ACIS CTI commanding
  add_nonload_cmds.py --date '2012:072:20:52:00.000' --cmd-set aciscti




