#  Django Distributed  Application to store Sales
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

## Install Supervisor Workers

- clone the repo
- sudo ./setup_django_supervisor.sh


## Superviosor commands
- sudo supervisorctl status
- sudo supervisorctl start rq_day_close:*
- sudo supervisorctl stop rq_day_close:*


## PgBouncer:
- sudo ./install_pgbouncer.sh
- sudo su - postgres
- (do not copy the below command from web interface of Readme this command,copy from the raw file of readme, its removing some characters) 
- psql -c "SELECT concat('\"django\" \"', passwd, '\"') FROM pg_shadow WHERE usename='django'" -t -A
- Add the output to /etc/pgbouncer/userlist.txt
- sudo systemctl reload pgbouncer
## Migration
- run the migration command
- ./run_django_migrations.sh
## Gunicorn
- run django as gunicorn service
- ./gunicorn_nginx.sh
- create superuser using 
- python3 manage.py createsuperuser
- To Restart Django Service: sudo systemctl restart gunicorn.service