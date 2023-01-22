#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Update timelines table to reflect a mission load interrupt.
"""

if __name__ == '__main__':
    import chandra_cmd_states.interrupt_loads as interrupt_loads
    interrupt_loads.main()
