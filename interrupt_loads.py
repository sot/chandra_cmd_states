#!/usr/bin/env python
"""
Update timelines table to reflect a mission load interrupt.
"""

if __name__ == '__main__':
    import Chandra.cmd_states.interrupt_loads as interrupt_loads
    interrupt_loads.main()
