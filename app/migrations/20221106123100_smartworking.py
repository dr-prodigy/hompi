"""
a caribou migration

name: smartworking
version: 20221106123100
"""


def upgrade(connection):
    sql = "INSERT INTO `gm_timetable_day_type` (id, description) VALUES (7, 'Smart-working');"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable` " \
          "(id, description, monday, tuesday, wednesday, thursday, friday, saturday, sunday, " \
          "short_description, pre_holiday, holiday) " \
          "VALUES (5, 'Smart-working', 7, 7, 7, 7, 7, 2, 3,'A', 2, 3)"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_temp` (id, timetable_id, temp_id) VALUES (6, 5, 2)"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_temp` (id, timetable_id, temp_id) VALUES (7, 5, 3)"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_type_data` " \
          "(id, orderby, day_type_id, temp_id, time_hhmm, delta_calc_mm) " \
          "VALUES (14, 0, 7, 2, 0, 0)"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_type_data` " \
          "(id, orderby, day_type_id, temp_id, time_hhmm, delta_calc_mm) " \
          "VALUES (15, 1, 7, 3, 500, 0)"
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_type_data` " \
          "(id, orderby, day_type_id, temp_id, time_hhmm, delta_calc_mm) " \
          "VALUES (16, 2, 7, 2, 2330, 0)"
    connection.execute(sql)
    connection.commit()


def downgrade(connection):
    sql = "DELETE FROM `gm_timetable_type_data` " \
          "WHERE id IN (14, 15, 16)"
    connection.execute(sql)
    connection.commit()

    sql = "DELETE FROM `gm_timetable_temp` " \
          "WHERE id IN (6, 7)"
    connection.execute(sql)
    connection.commit()

    sql = "DELETE FROM `gm_timetable` " \
          "WHERE id IN (5)"
    connection.execute(sql)
    connection.commit()

    sql = "DELETE FROM `gm_timetable_day_type` " \
          "WHERE id IN (7)"
    connection.execute(sql)
    connection.commit()
