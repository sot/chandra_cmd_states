#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Add non-load commands to the database and generate code to recreate those
commands for archive purposes.
"""

if __name__ == '__main__':
    import chandra_cmd_states.add_nonload_cmds as add_nonload_cmds
    add_nonload_cmds.main()
