CREATE TABLE cmds (
 id                 int        not null,
 timeline_id        int,
 date              varchar(21) not null,
 time              float(16)   not null,
 cmd               varchar(12) not null,
 tlmsid            varchar(10),
 msid              varchar( 8),
 vcdu              int,
 step              int,
 scs               int,
 CONSTRAINT pk_cmds_id PRIMARY KEY (id)
)
;
CREATE INDEX idx_cmds_timeline_id ON cmds (timeline_id)
