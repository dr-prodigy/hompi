PRAGMA foreign_keys=off;

UPDATE `gm_timetable_type_data_area`
SET `timetable_type_data_id` = `timetable_type_data_id` + 10
WHERE `timetable_type_data_id` > 11;

UPDATE `gm_timetable_type_data`
SET `id` = `id` + 10
WHERE `id` > 11;

UPDATE `gm_timetable_type_data_area`
SET `timetable_type_data_id` = `timetable_type_data_id` + 5
WHERE `timetable_type_data_id` BETWEEN 9 AND 11;

UPDATE `gm_timetable_type_data`
SET `id` = `id` + 5
WHERE `id` BETWEEN 9 AND 11;

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (9, 2, 2, 3, 2030, 0);

INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (75,9,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (76,9,2,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (77,9,3,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (78,9,4,2);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (17, 3, 3, 3, 2030, 0);

INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (110,17,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (111,17,2,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (112,17,3,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (113,17,4,2);

PRAGMA foreign_keys=on;
