Chandra commanded states database
==================================

This suite of tools provides the interface for creation and maintenance of the
Chandra commanded states database. This database provides the commanded state
of Chandra from 2002 through to the end of all approved command loads that are
ingested to the OFLS database.  The database thus contains both the definitive
state and a predictive state at any time.

.. Warning:: Use of the commanded states database described here is deprecated
   in favor of the `Kadi commands and states
   package <http://cxc.cfa.harvard.edu/mta/ASPECT/tool_doc/kadi/commands_states.html>`_.
   The replacement for the :func:`~Chandra.cmd_states.fetch_states` function is described
   in the `Chandra states and continuity
   <http://cxc.cfa.harvard.edu/mta/ASPECT/tool_doc/kadi/commands_states.html#states>`_
   section which makes use of the `get_states
   <http://cxc.cfa.harvard.edu/mta/ASPECT/tool_doc/kadi/api.html#kadi.commands.states.get_states>`_
   function.

   The commanded states database is still being maintained, but no new development
   is expected.

A commanded state is an interval of time over which certain parameters of
interest (obsid, SIM-Z position, commanded attitude, ACIS power configuration,
etc) are invariant.  This database is useful for several reasons:

1. It goes out into the future to the extent of approved load products
2. It is extremely fast and the commanded states for the entire mission can be
   retrieved in a few seconds.
3. It takes care of the difficult task of tracking which command loads and
   mission planning products actually ran on the spacecraft.
4. It provides a path from each command back to the mission planning products
   responsible for that command.

Note: only a select set of commands that affect the commanded state are
tracked.

Database access
---------------

A convenient linux command line tool to access the commanded states database is
available via the :ref:`get_cmd_states` tool.  For example::

  % get_cmd_states --start 2012:121 --stop 2012:122 --vals obsid,simpos
  datestart             datestop              tstart        tstop         obsid simpos
  2012:121:10:32:46.375 2012:121:13:17:43.375 452169232.559 452179129.559 54646 -99616
  2012:121:13:17:43.375 2012:121:15:08:21.375 452179129.559 452185767.559 14212 75624
  2012:121:15:08:21.375 2012:121:16:04:07.192 452185767.559 452189113.376 13331 75624
  2012:121:16:04:07.192 2012:123:11:23:20.985 452189113.376 452345067.169 13847 75624

To access the commanded states database from within a Python script use the
:func:`~Chandra.cmd_states.fetch_states` function.  For instance::

  >>> from Chandra.cmd_states import fetch_states
  >>> states = fetch_states('2011:100', '2011:101')
  >>> states[['datestart', 'datestop', 'obsid', 'simpos']]
  array([('2011:100:11:53:12.378', '2011:101:00:23:01.434', 13255, 75624),
         ('2011:101:00:23:01.434', '2011:101:00:26:01.434', 13255, 91272),
         ('2011:101:00:26:01.434', '2011:102:13:39:07.421', 12878, 91272)],
        dtype=[('datestart', '|S21'), ('datestop', '|S21'), ('obsid', '<i8'), ('simpos', '<i8')])


cmd_states table
------------------
The main table is the ``cmd_states`` table with the following columns:

============   =========   ====
Name           Type        Size
============   =========   ====
 datestart     varchar      21
 datestop      varchar      21
 obsid         int           4
 power_cmd     varchar      11
 si_mode       varchar       8
 pcad_mode     varchar       6
 vid_board     bit           1
 clocking      bit           1
 fep_count     int           4
 ccd_count     int           4
 simpos        int           4
 simfa_pos     int           4
 pitch         float         8
 ra            float         8
 dec           float         8
 roll          float         8
 q1            float         8
 q2            float         8
 q3            float         8
 q4            float         8
 trans_keys    varchar      60
 hetg          varchar       4
 letg          varchar       4
 dither        varchar       4
============   =========   ====

cmds table
----------

In addition the ``cmds`` table maintains a history (definitive and predictive)
of every on-board command that will affect the commanded state.  The command
parameter values are stored in secondary tables.  In addition to commands from
the mission loads there are also "non-load" commands which result from
autonomous or ground commanding (e.g. SCS107, Normal Sun Mode transitions,
anomaly recovery, etc).

================  ========  =======
name              type      length
================  ========  =======
id (PK)            int        4
timeline_id        int        4
date               char      21
time              float       8
cmd               varchar    12
tlmsid            varchar    10
msid              varchar     8
vcdu              int         4
step              int         4
scs               int         4
================  ========  =======

**cmd_intpars** and **cmd_fltpars**

================  ==========  =======
name              type        length
================  ==========  =======
cmd_id (FK)        int           4
timeline_id (FK)   int           4
name               varchar      15
value              int/float     8
================  ==========  =======

Note that unlike the commanded states table, the cmds tables are only available
on Sybase on the HEAD network.

Tools
------

.. toctree::
   :maxdepth: 1

   add_nonload_cmds
   get_cmd_states
   fix_pitch_simz
   interrupt_loads
   make_cmd_tables
   update_cmd_states

Chandra.cmd_states functions
-----------------------------

The following key functions within the ``Chandra.cmd_states`` module are
available for users.

.. automodule:: Chandra.cmd_states

get_cmds
^^^^^^^^^
.. autofunction:: get_cmds

fetch_states
^^^^^^^^^^^^^^
.. autofunction:: fetch_states

get_states
^^^^^^^^^^
.. autofunction:: get_states

interpolate_states
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: interpolate_states

reduce_states
^^^^^^^^^^^^^^
.. autofunction:: reduce_states

API docs
--------------

The full API docs for ``Chandra.cmd_states`` are available here:

.. toctree::
   :maxdepth: 2

   api
