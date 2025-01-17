# sales/management/commands/create_shard_databases.py
from django.core.management.base import BaseCommand
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os


class Command(BaseCommand):
    help = 'Create shard databases'

    def handle(self, *args, **options):
        # Database connection parameters
        db_params = {
            'dbname': 'postgres',
            'user': os.getenv('DB_USER', 'django'),
            'password': os.getenv('DB_PASSWORD', 'secure_password'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }

        retail_ids = [
    81, 115, 116, 119, 68, 82, 69, 83, 70, 117, 71, 85, 72, 113, 73, 
    77, 78, 79, 80, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 
    99, 100, 101, 102, 103, 104, 105, 106, 108, 109, 110, 111, 118, 
    74, 93, 75, 114
]
        
        try:
            # Establish connection
            conn = psycopg2.connect(**db_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Create central database
            central_db_name = os.getenv('CENTRAL_DB_NAME', 'central_sales_db')
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{central_db_name}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f'CREATE DATABASE "{central_db_name}"')
                self.stdout.write(self.style.SUCCESS(f'Created database {central_db_name}'))

            # Create shard databases
            for retail_id in retail_ids:
                db_name = f'retail_point_shard_{retail_id}'
                
                cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
                exists = cursor.fetchone()
                
                if not exists:
                    cursor.execute(f'CREATE DATABASE "{db_name}"')
                    self.stdout.write(self.style.SUCCESS(f'Created database {db_name}'))

            cursor.close()
            conn.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
