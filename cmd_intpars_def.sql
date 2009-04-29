CREATE TABLE cmd_intpars (
 cmd_id            int          not null,
 timeline_id       int                  ,
 name              varchar(15)  not null,
 value             int          not null,
 CONSTRAINT fk_cmd_intpars_cmd_id FOREIGN KEY (cmd_id) REFERENCES cmds (id)
) 
;
CREATE INDEX idx_cmd_intpars_timeline_id ON cmd_intpars (timeline_id)
