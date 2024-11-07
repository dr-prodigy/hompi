PRAGMA foreign_keys=off;

UPDATE `gm_timetable_type_data_area`
SET `id` = `id` + 10, `timetable_type_data_id` = `timetable_type_data_id` + 1
WHERE `timetable_type_data_id` = 28;

UPDATE `gm_timetable_type_data_area`
SET `id` = `id` + 10, `timetable_type_data_id` = `timetable_type_data_id` + 1
WHERE `id` = 233;
UPDATE `gm_timetable_type_data_area`
SET `id` = `id` + 10, `timetable_type_data_id` = `timetable_type_data_id` + 1
WHERE `id` = 232;
UPDATE `gm_timetable_type_data_area`
SET `id` = `id` + 10, `timetable_type_data_id` = `timetable_type_data_id` + 1
WHERE `id` = 231;
UPDATE `gm_timetable_type_data_area`
SET `id` = `id` + 10, `timetable_type_data_id` = `timetable_type_data_id` + 1
WHERE `id` = 230;

UPDATE `gm_timetable_type_data`
SET `id` = `id` + 1, `orderby` = `orderby` + 1
WHERE `id` = 28;
UPDATE `gm_timetable_type_data`
SET `id` = `id` + 1, `orderby` = `orderby` + 1, `temp_id` = 3
WHERE `id` = 27;

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (27, 3, 7, 3, 1730, 0);

INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (230,27,null,3);

PRAGMA foreign_keys=on;
