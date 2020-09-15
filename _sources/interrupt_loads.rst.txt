:mod:`interrupt_loads`
=======================

Update timelines table to reflect an mission load interrupt.

Normally all timeline entries with datestop after the supplied ``datestop`` are
updated to set the table datestop to ``datestop``.  If ``--current-only`` is
supplied then only the load segment actually containing ``datestop`` will be
truncated.  This is to clean up archival load segment values that are wrong.

Usage
-----
::

  Usage: interrupt_loads.py [options]

  Options:
    -h, --help           show this help message and exit
    --dbi=DBI            Database interface (sqlite|sybase)
    --server=SERVER      DBI server (<filename>|sybase)
    --datestop=DATESTOP  Interrupt date
    --current-only       Only interrupt load segment current at datestop
    --observing-only     Only interrupt 'observing' segments
    --loglevel=LOGLEVEL  Log level (10=debug, 20=info, 30=warnings)


Example
-------
::

  interrupt_loads.py --datestop 2009:065:12:34:56

