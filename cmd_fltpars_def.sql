CREATE TABLE cmd_fltpars (
 cmd_id            int          not null,
 timeline_id       int                  ,
 name              varchar(15)  not null,
 value             float(16)      not null,
 CONSTRAINT fk_cmd_fltpars_cmd_id FOREIGN KEY (cmd_id) REFERENCES cmds (id)
) 
;
CREATE INDEX idx_cmd_fltpars_timeline_id ON cmd_fltpars (timeline_id)
