.. cmd_states documentation master file, created by
   sphinx-quickstart on Thu May  7 14:33:29 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Chandra commanded states database
==================================

This suite of tools provides the interface for creation and maintenance of the
Chandra commanded states database. This database provides the commanded state
of Chandra from 2002 through to the end of all approved command loads that are
ingested to the OFLS database.  The database thus contains both the definitive
state and a predictive state at any time.

A commanded state is an interval of time over which certain parameters of
interest (obsid, SIM-Z position, commanded attitude, ACIS power configuration,
etc) are invariant.  This database is useful for several reasons: 

1. It goes out into the future to the extent of approved load products
2. It is extremely fast and the commanded states for the entire mission can be 
   retrieved in 15 seconds.
3. It takes care of the difficult task of tracking which command loads and
   mission planning products actually ran on the spacecraft.
4. It provides a path from each command back to the mission planning products
   responsible for that command.

Note: only a select set of commands that affect the commanded state are
tracked.

Database access
---------------
A convenient front end to access the commanded states database is available
via the `get_cmd_states <get_cmd_states.html>`_ tool.

Low-level database access and manipulation is done via the Chandra.cmd_states_ module.

.. _Chandra.cmd_states: ../pydocs/Chandra.cmd_states.html

cmd_states
-----------
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
 hetg          varchar       4
 letg          varchar       4
 pitch         float         8
 ra            float         8
 dec           float         8
 roll          float         8
 q1            float         8
 q2            float         8
 q3            float         8
 q4            float         8
 trans_keys    varchar      60
============   =========   ====

cmds
----

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


Tools
====================

.. toctree::
   :maxdepth: 2

   add_nonload_cmds
   get_cmd_states
   fix_pitch_simz
   interrupt_loads
   make_cmd_tables
   update_cmd_states

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

