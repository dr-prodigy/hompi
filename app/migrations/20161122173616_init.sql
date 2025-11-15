BEGIN TRANSACTION;
CREATE TABLE "gm_timetable_type_data" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`orderby`	INTEGER,
	`day_type_id`	INTEGER NOT NULL,
	`temp_id`	INTEGER NOT NULL,
	`time_hhmm`	INTEGER NOT NULL,
	`delta_calc_mm`	INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY(`day_type_id`) REFERENCES `gm_day_type`(`id`),
	FOREIGN KEY(`temp_id`) REFERENCES `gm_temp`(`id`)
);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (1,0,4,1,0000,0);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (2,0,1,2,0000,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (3,1,1,3,0600,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (4,2,1,2,0830,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (5,3,1,3,1800,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (6,4,1,2,2330,0);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (7,0,2,2,0000,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (8,1,2,3,0700,0);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (9,0,3,3,0000,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (10,1,3,2,0100,0);
INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (11,2,3,3,0700,0);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (12,0,5,4,0000,0);

INSERT INTO `gm_timetable_type_data` (id,orderby,day_type_id,temp_id,time_hhmm,delta_calc_mm) VALUES (13,0,6,5,0000,0);
CREATE TABLE `gm_timetable_day_type` (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`description`	TEXT NOT NULL
);
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (1,'Weekday');
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (2,'Pre-holiday');
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (3,'Holiday');
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (4,'Manual');
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (5,'Winter-safe');
INSERT INTO `gm_timetable_day_type` (id,description) VALUES (6,'Off');
CREATE TABLE "gm_timetable" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`description`	TEXT NOT NULL,
	`monday`	INTEGER,
	`tuesday`	INTEGER,
	`wednesday`	INTEGER,
	`thursday`	INTEGER,
	`friday`	INTEGER,
	`saturday`	INTEGER,
	`sunday`	INTEGER
);
INSERT INTO `gm_timetable` (id,description,monday,tuesday,wednesday,thursday,friday,saturday,sunday) VALUES (1,'Manual',4,4,4,4,4,4,4);
INSERT INTO `gm_timetable` (id,description,monday,tuesday,wednesday,thursday,friday,saturday,sunday) VALUES (2,'Automatic',1,1,1,1,1,2,3);
INSERT INTO `gm_timetable` (id,description,monday,tuesday,wednesday,thursday,friday,saturday,sunday) VALUES (3,'Winter-safe',5,5,5,5,5,5,5);
INSERT INTO `gm_timetable` (id,description,monday,tuesday,wednesday,thursday,friday,saturday,sunday) VALUES (4,'Off',6,6,6,6,6,6,6);
CREATE TABLE "gm_temp" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`timetable_id`	INTEGER,
	`description`	TEXT,
	`temp_c`	REAL NOT NULL,
	FOREIGN KEY(`timetable_id`) REFERENCES `gm_timetable`(`id`)
);
INSERT INTO `gm_temp` (id,timetable_id,description,temp_c) VALUES (1,1,'Manual',20.0);
INSERT INTO `gm_temp` (id,timetable_id,description,temp_c) VALUES (2,2,'Economy',17.0);
INSERT INTO `gm_temp` (id,timetable_id,description,temp_c) VALUES (3,2,'Comfort',20.0);
INSERT INTO `gm_temp` (id,timetable_id,description,temp_c) VALUES (4,3,'Winter-safe',6.0);
INSERT INTO `gm_temp` (id,timetable_id,description,temp_c) VALUES (5,4,'Off',-40.0);
CREATE TABLE `gm_log` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`datetime`	INTEGER NOT NULL,
	`int_temp_c`	REAL NOT NULL,
	`ext_temp_c`	REAL,
	`event`	TEXT,
	`description`	TEXT
);
CREATE TABLE "gm_control" (
	`id`	INTEGER PRIMARY KEY,
	`timetable_id`	INTEGER,
	FOREIGN KEY(`timetable_id`) REFERENCES `gm_timetable`(`id`)
);
INSERT INTO `gm_control` (id,timetable_id) VALUES (0,1);
COMMIT;
