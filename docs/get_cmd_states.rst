:mod:`get_cmd_states`
========================

.. automodule:: get_cmd_states


Usage
-----
::

  Usage: get_cmd_states.py [options]

  Options:
    -h, --help         Show this help message and exit
    --start=START      Start date for update (default=stop-10 days)
    --stop=STOP        Stop date for update (default=Now)
    --vals=VALS        Comma-separated list of state values.  Possible values
                       are: obsid power_cmd si_mode vid_board clocking fep_count
                       ccd_count simpos simfa_pos hetg letg pcad_mode pitch ra
                       dec roll q1 q2 q3 q4 trans_keys dither
    --outfile=OUTFILE  Output file (default=stdout)
    --dbi=DBI          Database interface (default=sybase) 
    --server=SERVER    DBI server (default=sybase)
    --user=USER        Ska.DBI default database user
    --database=DB      Ska.DBI default database
Examples
--------
::

  # Set PATH so get_cmd_states is found
  % setenv PATH ${PATH}:/proj/sot/ska/bin

  # Print help
  % get_cmd_states --help

  # Get attitude info for the last 10 days
  % get_cmd_states --vals pcad_mode,ra,dec,roll

  # Get grating config from 2010:001 to present and output to file gratings.dat
  % get_cmd_states --vals hetg,letg --start 2010:001 --outfile gratings.dat 

  # Get Obsid and ACIS config for 2010:001 to 2010:010
  % get_cmd_states --vals obsid,power_cmd,si_mode,vid_board,clocking,fep_count --stop 2010:010

  # Get all state values using different valid time formats to specify start and stop times
  % get_cmd_states --start 347198466.18 --stop 2009-01-03T12:00:00 --outfile all_states.dat

State values
------------

============   =========  
Name           Type                
============   =========  
 obsid         int        
 power_cmd     varchar    
 si_mode       varchar    
 pcad_mode     varchar    
 vid_board     bit        
 clocking      bit        
 fep_count     int        
 ccd_count     int        
 simpos        int        
 simfa_pos     int        
 hetg          varchar    
 letg          varchar    
 pitch         float      
 ra            float      
 dec           float      
 roll          float      
 q1            float      
 q2            float      
 q3            float      
 q4            float      
 dither        varchar
============   =========  
