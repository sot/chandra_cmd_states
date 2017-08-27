.. _get_cmd_states:

:mod:`get_cmd_states`
========================

Get the Chandra commanded states over a range of time as a space-delimited
ASCII table.

This tool is a wrapper around the ``Chandra.cmd_states.get_cmd_states()``
function.  This function should be used within any Python code that requires
use of commanded states.

Usage
-----
::

  Usage: get_cmd_states.py [-h] [--start START] [--stop STOP] [--vals VALS]
                           [--allow-identical] [--outfile OUTFILE] [--dbi DBI]
                           [--server SERVER] [--user USER] [--database DATABASE]

  optional arguments:
    -h, --help           show this help message and exit
    --start START        Start date (default=Now-10 days)
    --stop STOP          Stop date (default=None)
    --vals VALS          Comma-separated list of state values. Possible values
                         are: obsid power_cmd si_mode pcad_mode vid_board
                         clocking fep_count ccd_count simpos simfa_pos pitch ra
                         dec roll q1 q2 q3 q4 trans_keys hetg letg dither
    --allow-identical    Allow identical states from cmd_states table
                         (default=False)
    --outfile OUTFILE    Output file (default=stdout)
    --dbi DBI            Cmd states data source (sybase|hdf5|sqlite)
                         (default=hdf5)
    --server SERVER      DBI server (sybase) or data file (hdf5 or sqlite)
    --user USER          sybase database user (default='aca_read')
    --database DATABASE  sybase database (default=Ska.DBI default)

Examples
--------
::

  # Set PATH so get_cmd_states is found
  % setenv PATH ${PATH}:/proj/sot/ska/bin

  # Print help
  % get_cmd_states --help

  # Get attitude info for the last 10 days and into the available future
  % get_cmd_states --vals pcad_mode,ra,dec,roll

  # Get grating config from 2010:001 and output to file gratings.dat
  % get_cmd_states --vals hetg,letg --start 2010:001 --outfile gratings.dat

  # Get Obsid and ACIS config for 2010:001 to 2010:010
  % get_cmd_states --vals obsid,power_cmd,si_mode,vid_board,clocking,fep_count --stop 2010:010

  # Get all state values using different valid time formats to specify start and stop times
  % get_cmd_states --start 347198466.18 --stop 2009-01-03T12:00:00 --outfile all_states.dat

HDF5 and Sybase
---------------

Starting with version 0.08 of the commanded states package, the commanded
states table is also stored in an HDF5 table
(/proj/sot/ska/data/cmd_states/cmd_states.h5 by default).  This supplements the
heritage Sybase version which is available on the HEAD network.

The choice of which one to use is controlled by the ``--dbi`` command line
option.  In general the default choice of ``hdf5`` is preferred because it is
typically at least 20 times faster and is available on both HEAD and GRETA
networks.


State values
------------

==================== =========
Name                 Type
==================== =========
 datestart           varchar
 datestop            varchar
 obsid               int
 power_cmd           varchar
 si_mode             varchar
 pcad_mode           varchar
 vid_board           bit
 clocking            bit
 fep_count           int
 ccd_count           int
 simpos              int
 simfa_pos           int
 pitch               float
 ra                  float
 dec                 float
 roll                float
 q1                  float
 q2                  float
 q3                  float
 q4                  float
 trans_keys          varchar
 letg                varchar
 hetg                varchar
 dither              varchar
 dither_ampl_pitch   float
 dither_ampl_yaw     float
 dither_period_pitch float
 dither_period_yaw   float
==================== =========
