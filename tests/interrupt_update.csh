cp -p db_base.db3 db_test.db3
mkdir -p t/

echo Get initial database values
sqlite3 db_test.db3 'select * from timeline_loads order by datestart desc limit 5' > ! t/timelines_0.dat
sqlite3 db_test.db3 'select datestart,datestop,pitch,obsid from cmd_states order by datestart desc limit 5' > ! t/cmd_states_0.dat

# Edit date appropriately
echo Interrupt loads
./interrupt_loads.py --server db_test.db3 --date 2009:120:00:00:00 >! t/interrupt.log

echo Update command states after interrupt
./update_cmd_states.py --server db_test.db3

echo Get database values after interrupt
sqlite3 db_test.db3 'select * from timeline_loads order by datestart desc limit 5' > ! t/timelines_1.dat
sqlite3 db_test.db3 'select datestart,datestop,pitch,obsid from cmd_states order by datestart desc limit 5' > ! t/cmd_states_1.dat

echo Check that timeline datestops got set
grep '2009:120' t/timelines_1.dat

echo Check that cmd_states are different
echo diff t/cmd_states_1.dat t/cmd_states_0.dat
diff t/cmd_states_1.dat t/cmd_states_0.dat

echo Revert to nominal uninterrupted timelines
grep UPDATE t/interrupt.log
grep UPDATE t/interrupt.log | sqlite3 db_test.db3

echo Update command states after reverting
./update_cmd_states.py --server db_test.db3

echo Get database values after revert and update
sqlite3 db_test.db3 'select * from timeline_loads order by datestart desc limit 5' > ! t/timelines_2.dat
sqlite3 db_test.db3 'select datestart,datestop,pitch,obsid from cmd_states order by datestart desc limit 5' > ! t/cmd_states_2.dat

echo Compare original to post-reverted values

echo diff t/timelines_2.dat t/timelines_0.dat 
diff t/timelines_2.dat t/timelines_0.dat 

echo diff t/cmd_states_2.dat t/cmd_states_0.dat
diff t/cmd_states_2.dat t/cmd_states_0.dat

