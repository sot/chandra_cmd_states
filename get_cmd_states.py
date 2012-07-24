#!/usr/bin/env python
"""
Get the Chandra commanded states over a range of time as a space-delimited
ASCII table.
"""

if __name__ == '__main__':
    from Chandra.cmd_states import get_cmd_states
    get_cmd_states.main()
