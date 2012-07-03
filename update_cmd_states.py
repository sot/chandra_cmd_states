#!/usr/bin/env python
"""
Update the cmd_states table to reflect current load segments / timelines
in database.  This is normally run as a cron job.

Usage: update_cmd_states.py [options]::

  Options:
    -h, --help            show this help message and exit
    --dbi=DBI             Database interface (sqlite|sybase)
    --server=SERVER       DBI server (<filename>|sybase)
    --user=USER           database user (default=Ska.DBI default)
    --database=DATABASE   database name (default=Ska.DBI default)
    --datestart=DATESTART
                          Starting date for update (default=Now-10 days)
    --mp_dir=DIR          MP directory. (default=/data/mpcrit1/mplogs)
    --loglevel=LOGLEVEL   Log level (10=debug, 20=info, 30=warnings)
"""

import Chandra.cmd_states
Chandra.cmd_states.update_cmd_states()
