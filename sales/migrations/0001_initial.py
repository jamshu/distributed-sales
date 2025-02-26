# Generated by Django 5.1.4 on 2024-12-24 11:23

import django.db.models.deletion
import django.utils.timezone
import timescale.db.models.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('retail_point_id', models.PositiveIntegerField()),
                ('retail_point_name', models.CharField(max_length=100)),
                ('local_retail_point_db_id', models.PositiveIntegerField()),
                ('remarks', models.CharField(max_length=100)),
                ('partner_id', models.PositiveIntegerField()),
                ('debtors_account_id', models.PositiveIntegerField()),
                ('sale_journal_id', models.PositiveIntegerField()),
                ('sale_counter_id', models.PositiveIntegerField()),
                ('sale_counter_name', models.CharField(max_length=50)),
                ('sale_date', models.DateField(default=django.utils.timezone.now)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('payment_journal_id', models.PositiveIntegerField()),
                ('payment_method_name', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('sale_num', models.CharField(max_length=100, unique=True)),
                ('customer_name', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_default_customer', models.BooleanField()),
                ('total_cess', models.DecimalField(decimal_places=2, max_digits=10)),
                ('confirmed_on', models.DateTimeField()),
                ('confirmed_by', models.PositiveIntegerField()),
                ('confirmed_by_name', models.CharField(max_length=50)),
                ('store_type', models.CharField(max_length=100)),
                ('miscelleneous_sale_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('miscellaneous_product_id', models.PositiveIntegerField()),
                ('miscellaneous_qty', models.DecimalField(decimal_places=2, max_digits=10)),
                ('miscellaneous_invoice_num', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'sales_order',
                'indexes': [models.Index(fields=['sale_counter_id', 'payment_journal_id'], name='sales_order_sale_co_08fe79_idx')],
            },
        ),
        migrations.CreateModel(
            name='MiscLotLine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', timescale.db.models.fields.TimescaleDateTimeField(default=django.utils.timezone.now, interval='1 day')),
                ('product_id', models.PositiveIntegerField()),
                ('lot_name', models.CharField(max_length=255)),
                ('product_name', models.CharField(max_length=255)),
                ('lot_id', models.PositiveIntegerField()),
                ('quantity', models.DecimalField(decimal_places=1, max_digits=10)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='misc_lot_lines', to='sales.sale')),
            ],
            options={
                'db_table': 'misc_sales_lot_line',
                'indexes': [models.Index(fields=['sale_id', 'product_id', 'lot_id'], name='misc_sales__sale_id_f60085_idx')],
            },
        ),
        migrations.CreateModel(
            name='LotLine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', timescale.db.models.fields.TimescaleDateTimeField(default=django.utils.timezone.now, interval='1 day')),
                ('product_id', models.PositiveIntegerField()),
                ('lot_name', models.CharField(max_length=255)),
                ('product_name', models.CharField(max_length=255)),
                ('lot_id', models.PositiveIntegerField()),
                ('quantity', models.DecimalField(decimal_places=1, max_digits=10)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lot_lines', to='sales.sale')),
            ],
            options={
                'db_table': 'sales_lot_line',
                'indexes': [models.Index(fields=['sale_id', 'product_id', 'lot_id'], name='sales_lot_l_sale_id_83aeec_idx')],
            },
        ),
        migrations.CreateModel(
            name='SaleLine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', timescale.db.models.fields.TimescaleDateTimeField(default=django.utils.timezone.now, interval='1 day')),
                ('sl_no', models.PositiveIntegerField()),
                ('product_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('product_uom_qty', models.DecimalField(decimal_places=2, max_digits=10)),
                ('product_uom', models.PositiveIntegerField()),
                ('vat_percent', models.DecimalField(decimal_places=2, max_digits=10)),
                ('account_id', models.PositiveIntegerField()),
                ('retail_sale_mrp', models.DecimalField(decimal_places=2, max_digits=10)),
                ('price_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cess_id', models.PositiveIntegerField()),
                ('cess_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_cess', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale_type', models.CharField(max_length=25)),
                ('qty_available', models.IntegerField()),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='sales.sale')),
            ],
            options={
                'db_table': 'sales_order_line',
                'indexes': [models.Index(fields=['sale_id', 'product_id'], name='sales_order_sale_id_c92a7a_idx')],
            },
        ),
    ]
