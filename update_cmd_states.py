#!/usr/bin/env python
"""
Update the cmd_states table to reflect current load segments / timelines
in database.  This is normally run as a cron job.

Usage: update_cmd_states.py [options]::

Options:
  -h, --help            show this help message and exit
  --dbi=DBI             Database interface (sqlite|sybase)
  --server=SERVER       DBI server (<filename>|sybase)
  --user=USER           sybase user (default=Ska.DBI default)
  --database=DATABASE   sybase database (default=Ska.DBI default)
  --mp_dir=MP_DIR       MP load directory
  --h5file=H5FILE       filename for HDF5 version of cmd_states
  --datestart=DATESTART
                        Starting date for update (default=Now-10 days)
  --loglevel=LOGLEVEL   Log level (10=debug, 20=info, 30=warnings)
"""

from Chandra.cmd_states.update_cmd_states import update_cmd_states
update_cmd_states()
