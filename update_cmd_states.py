#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Update the cmd_states table to reflect current load segments / timelines
in database.  This is normally run as a cron job.
"""

if __name__ == '__main__':
    from Chandra.cmd_states import update_cmd_states
    update_cmd_states.main()
