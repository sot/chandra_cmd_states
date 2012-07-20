#!/usr/bin/env python
"""
Update the cmd_states table to reflect current load segments / timelines
in database.  This is normally run as a cron job.
"""

from Chandra.cmd_states import update_cmd_states
update_cmd_states.main()
