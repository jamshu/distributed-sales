#  Django Distributed  Application to store Sales 2024-12-24
##  Installation
- [ ] Install Postgres
- [ ] Install TimescaleDB
- [ ] pip install -r requirments
- [ ] python manage.py create_shard_database
- [ ] python manage.py enable_timescale
- [ ] python manage.py migrate
- [ ] python manage.py migrate_shards
- [ ] python manage.py runserver 8080
- [ ] python manage.py rqworker sales_processing
- [ ] python manage.py rqworker day_close

## Use Supervisor ctl for configure as service

## to run script

- clone the repo
- chmod+x setup_django_supervisor.sh
- sudo ./setup_django_supervisor.sh

## Superviosor
- sudo supervisorctl status
- sudo supervisorctl start rq_day_close:*
- sudo supervisorctl stop rq_day_close:*

## Django service
 - To Restart Django Service: sudo systemctl restart gunicorn.service

## Notes:
- in postgreql increase max connection 100 to 250 min due to the number of shards