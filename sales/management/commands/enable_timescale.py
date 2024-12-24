from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = "Enable the TimescaleDB extension on all configured databases"

    def handle(self, *args, **options):
        for alias, connection in connections.databases.items():
            self.stdout.write(f"Processing database alias: {alias}")
            try:
                with connections[alias].cursor() as cursor:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                self.stdout.write(self.style.SUCCESS(f"Successfully enabled TimescaleDB on '{alias}'"))
            except OperationalError as e:
                self.stderr.write(self.style.ERROR(f"Failed to enable TimescaleDB on '{alias}': {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred on '{alias}': {e}"))
