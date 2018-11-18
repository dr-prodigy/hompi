select datetime(datetime,'unixepoch'), * from gm_log
order by id desc
limit 100