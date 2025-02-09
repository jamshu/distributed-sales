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
- sudo supervisorctl reload


## PgBouncer:
- sudo ./install_pgbouncer.sh

## DB Schema Migration
- add .env in django root folder and add SECRET_KEY="MY SECRET KEY"
- run the migration command (make sure you ADDED SECRET_KEY in .env file)
- ./run_django_migrations.sh
## Gunicorn
- run django as gunicorn service
- ./gunicorn_nginx.sh
- create superuser using 
- python3 manage.py createsuperuser
- To Restart Django Service: sudo systemctl restart gunicorn.service

## Notes
- install bcrypt in odoo cloud using: pip install bcrypt
- set a secret key in odoo.conf : secret_key = super-strong-key
- same secret key add in django root folder inside .env file : SECRET_KEY = super-strong-key
- create super user using: 
- django folder: . venv/bin/activate
- python3 manage.py createsuperuser
- in django admin page create user token
- add this user token on retail point django user token