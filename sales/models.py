     # sales/models.py
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager
import uuid

class SaleBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Meta:
        abstract = True


class TimescaleModel(SaleBase):
    """
    A helper class for using Timescale within Django, has the TimescaleManager and
    TimescaleDateTimeField already present. This is an abstract class it should
    be inherited by another class for use.
    """
    time = TimescaleDateTimeField(interval="1 day", default=now)
    objects = TimescaleManager()

    class Meta:
        abstract = True

class Sale(SaleBase):
    
    retail_point_id = models.PositiveIntegerField()
    local_retail_point_db_id = models.PositiveIntegerField()
    remarks = models.CharField(max_length=100)
    partner_id = models.PositiveIntegerField()
    debtors_account_id = models.PositiveIntegerField()
    sale_journal_id = models.PositiveIntegerField()
    sale_counter_id = models.PositiveIntegerField()
    sale_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_journal_id = models.PositiveIntegerField()
    name = models.CharField(max_length=100, null=False, blank=False)
    sale_num = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    is_default_customer = models.BooleanField()
    total_cess = models.DecimalField(max_digits=10,decimal_places=2)
    confirmed_on = models.DateTimeField()
    confirmed_by = models.PositiveIntegerField()
    store_type = models.CharField(max_length=100)
    miscelleneous_sale_price = models.DecimalField(max_digits=10,decimal_places=2)
    miscellaneous_product_id = models.PositiveIntegerField()
    miscellaneous_qty = models.DecimalField(max_digits=10,decimal_places=2)
    miscellaneous_invoice_num = models.CharField(max_length=100, null=False, blank=False)
    
    class Meta:
        db_table = 'sales_order'
        indexes = [
            models.Index(fields=['sale_counter_id', 'payment_journal_id']),
        ]

class SaleLine(TimescaleModel):
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='lines'
    )
    sl_no = models.PositiveIntegerField()
    product_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    product_uom_qty = models.DecimalField(max_digits=10, decimal_places=2)
    product_uom = models.PositiveIntegerField()
    vat_percent = models.DecimalField(max_digits=10, decimal_places=2)
    account_id = models.PositiveIntegerField()
    retail_sale_mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price_unit = models.DecimalField(max_digits=10, decimal_places=2)
    cess_id = models.PositiveIntegerField()
    cess_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_cess = models.DecimalField(max_digits=10, decimal_places=2)
    sale_type = models.CharField(max_length=25)
    qty_available = models.IntegerField()

    class Meta:
        db_table = 'sales_order_line'
        indexes = [ 
            models.Index(fields=['sale_id','product_id'])
        ]

class LotLine(TimescaleModel):
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='lot_lines'
    )
    product_id = models.PositiveIntegerField()
    lot_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    lot_id = models.PositiveIntegerField()
    quantity = models.DecimalField(max_digits=10,decimal_places=1)

    class Meta:
        db_table = 'sales_lot_line'
        indexes = [ 
            models.Index(fields=['sale_id','product_id','lot_id'])
        ]

class MiscLotLine(TimescaleModel):
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='misc_lot_lines'
    )
    product_id = models.PositiveIntegerField()
    lot_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    lot_id = models.PositiveIntegerField()
    quantity = models.DecimalField(max_digits=10,decimal_places=1)

    class Meta:
        db_table = 'misc_sales_lot_line'
        indexes = [ 
            models.Index(fields=['sale_id','product_id','lot_id'])
        ] 
