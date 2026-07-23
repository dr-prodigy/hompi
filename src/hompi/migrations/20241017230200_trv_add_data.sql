BEGIN TRANSACTION;

/* https://docs.google.com/spreadsheets/d/12KJjAGg3xmoStdCuaDRKbXPCOPoTDEpWBpBIpIOxVB0/edit */
/* MANUAL */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (1,1,null,1);

/* AUTOMATIC WEEKDAYS */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (10,2,null,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (20,3,null,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (30,4,null,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (40,5,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (41,5,2,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (42,5,3,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (43,5,4,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (50,6,null,2);

/* AUTOMATIC / SMART-WORKING WEEKEND */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (60,7,null,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (70,8,null,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (80,9,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (81,9,2,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (82,9,3,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (83,9,4,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (90,10,null,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (100,11,null,3);

/* SMART-WORKING WEEKDAYS */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (200,14,null,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (210,15,null,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (220,16,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (221,16,2,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (222,16,3,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (223,16,4,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (230,17,1,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (231,17,2,3);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (232,17,3,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (233,17,4,2);
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (240,18,null,2);

/* WINTER-SAFE */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (900,12,null,4);

/* OFF */
INSERT INTO `gm_timetable_type_data_area` (id,timetable_type_data_id,area_id,temp_id) VALUES (901,13,null,5);

COMMIT;
