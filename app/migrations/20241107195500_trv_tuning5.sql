PRAGMA foreign_keys=off;

/* SMARTWORKING NEW SLOT (17.30-20.30) */
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

/* SMARTWORKING: 2 DAY TYPES (Smartworking-eco, Smartworking-comfort) */
UPDATE `gm_timetable_day_type` SET `description` = 'Smartworking-eco' WHERE `id` = 7;

INSERT INTO `gm_timetable_day_type` (`id`,`description`) VALUES (8, 'Smartworking-comfort');

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (30, 1, 8, 2, 0, 0);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (31, 2, 8, 3, 500, 0);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (32, 2, 8, 3, 0830, 0);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (33, 3, 8, 3, 1130, 0);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (34, 3, 8, 3, 2030, 0);

INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
VALUES (35, 4, 8, 2, 2330, 0);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (260, 30, null, 2);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (270, 31, null, 3);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (280, 32, 1, 3);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (281, 32, 2, 2);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (282, 32, 3, 3);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (283, 32, 4, 2);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (290, 33, null, 3);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (300, 34, 1, 3);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (301, 34, 2, 3);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (302, 34, 3, 2);
INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (303, 34, 4, 2);

INSERT INTO `gm_timetable_type_data_area` (`id`, `timetable_type_data_id`, `area_id`, `temp_id`)
VALUES (310, 35, null, 2);

UPDATE `gm_timetable` SET `description` = 'Smartworking',
`monday` = 8, `tuesday` = 8, `wednesday` = 8, `thursday` = 8, `friday` = 8
WHERE `id` = 5;

PRAGMA foreign_keys=on;
