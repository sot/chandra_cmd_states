#!/usr/bin/env python
"""
Get the Chandra commanded states over a range of time as a space-delimited
ASCII table.

Usage: get_cmd_states.py [options]

Options:
  -h, --help           show this help message and exit
  --start=START        Start date (default=Now-10 days)
  --stop=STOP          Stop date (default=None)
  --vals=VALS          Comma-separated list of state values.  Possible values
                       are:     obsid power_cmd si_mode vid_board clocking
                       fep_count ccd_count     simpos simfa_pos hetg letg
                       pcad_mode pitch ra dec roll q1 q2 q3 q4     trans_keys
                       dither
  --allow-identical    Allow identical states from cmd_states table
                       (default=False)
  --outfile=OUTFILE    Output file (default=stdout)
  --dbi=DBI            Database interface (default=sybase)
  --server=SERVER      DBI server (default=sybase)
  --user=USER          sybase database user (default='aca_read')
  --database=DATABASE  sybase database (default=Ska.DBI default)
"""

import Chandra.cmd_states
Chandra.cmd_states.get_cmd_states()
