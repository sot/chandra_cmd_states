#!/usr/bin/env python
"""
Add non-load commands to the database and generate code to recreate those
commands for archive purposes.
"""

import Chandra.cmd_states.add_nonload_cmds as add_nonload_cmds
add_nonload_cmds.main()
