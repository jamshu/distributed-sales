from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = "Run migrations on all shard databases"

    def handle(self, *args, **kwargs):
        for alias, db_config in settings.DATABASES.items():
            if alias != 'default':  # Skip the default database
                self.stdout.write(f'Applying migrations to {alias}...')
                call_command('migrate', database=alias)
                self.stdout.write(f'Migrations applied to {alias}')
