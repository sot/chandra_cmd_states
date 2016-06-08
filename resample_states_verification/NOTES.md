
Testing of changes to use mock GET_PITCH commands
=================================================

To create a body of test outputs for a good chunk of time, I used a pre-existing
test setup from the timelines project to run this new code on a year of data (and a year's
worth of calls to "update" that data).  To have the timelines test code run against this
testing version of cmd_states, I did not use a custom PYTHONPATH but instead just
installed the testing version to my devska in /data/fido/ska.  Then, from a timelines repo
I ran:

    import timelines_test
    timelines_test.all_2010(cmd_state_ska='/data/fido/ska')

This "all_2010" stepped through "days" and ran the testing version of cmd_states via calls
to update_cmd_states, and as output created both a testing cmd_states.h5 file and left the
testing cmd_states in the sybase test database.

I then used fetch_states against the flight cmd_states.h5 and the testing cmd_states.h5 to
create dat files limited to the columns that really should not be changing due to this
update.

    from Chandra.cmd_states.get_cmd_states import fetch_states
    from astropy.table import Table
    
    official = fetch_states(start='2010:005', stop='2010:360', vals=['obsid', 'power_cmd',
      'si_mode', 'pcad_mode', 'vid_board', 'clocking', 'fep_count', 'ccd_count', 'simpos',
      'simfa_pos', 'hetg', 'letg'], server='/proj/sot/ska/data/cmd_states/cmd_states.h5')
    Table(official).write('official_minus_point.dat', format='ascii')
    
    test = fetch_states(start='2010:005', stop='2010:360', vals=['obsid', 'power_cmd',
      'si_mode', 'pcad_mode', 'vid_board', 'clocking', 'fep_count', 'ccd_count', 'simpos',
      'simfa_pos', 'hetg', 'letg'], server='t/all_2010/cmd_states.h5')
    Table(test).write('test_minus_point.dat', format='ascii')
    
    meld official_minus_point.dat test_minus_point.dat

There are fewer than a dozen timing diffs of less than 0.04 seconds in the NMAN / NPNT
transition times.  This is acceptable.


    official = fetch_states(start='2010:005', stop='2010:360',
         server='/proj/sot/ska/data/cmd_states/cmd_states.h5')
    test = fetch_states(start='2010:005', stop='2010:360', server='t/all_2010/cmd_states.h5')

I then verified that for each state in the original list, the pitch in a matching state
starting at the same time in the new table matches within a degree or so:

    run -i check_code.py

In [24]: np.nanmax(diffs)
Out[24]: 1.3951456857497249

In [25]: np.nanmin(diffs)
Out[25]: -0.95967993552620356

For any states "missing" from the new states (as in a new state does not exist at exactly
the same starting time as the old states), I confirmed that the interpolated pitch at the
time of the old state would be very close:

    run -i check_missing.py

In [22]: run -i check_missing.py
biggest offset is 0.00215984350712


![some_bigger_discontinuities.png](some_bigger_discontinuities.png)




