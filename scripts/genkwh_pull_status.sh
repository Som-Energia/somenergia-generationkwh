psql -d somenergia -c "SELECT date_pull,status,message FROM generationkwh_production_notifier where date_pull > current_timestamp -interval '2 day'"
