update timelines set datestop='2008:353:05:00:00.000' where id=345905553;
update timelines set fixed_by_hand=1 where id=345905553;
update load_segments set fixed_by_hand=1 where id=345905551;
update load_segments set datestop='2008:353:05:00:00.000' where id=345905551;

update timelines set datestop='2003:001:00:00:00.000' where id=183963768;
update timelines set fixed_by_hand=1 where id=183963768;
update load_segments set fixed_by_hand=1 where id=183963766;
update load_segments set datestop='2003:001:00:00:00.000' where id=183963766;
