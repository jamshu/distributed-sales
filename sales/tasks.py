# sales/tasks.py
import django_rq
from django.db import connections, transaction
from django.db.models import Sum, Count
from django.utils import timezone
import requests
import logging
import json
from .models import Sale, SaleLine, LotLine, MiscLotLine
from .validators import validate_sale_data

logger = logging.getLogger(__name__)

@django_rq.job('sales_processing')
def process_sale_order(sale_data):
    try:
        # Validate incoming data
        validated_data = json.loads(sale_data)
        print(validated_data)        
        # Determine shard
        retail_point_id = validated_data['retail_point_id']
        
        shard_db = f'shard_{retail_point_id}'
        
        # Use transaction to ensure data integrity
        with transaction.atomic(using=shard_db):
            # Create sale
            sale = Sale.objects.using(shard_db).create(
                retail_point_id=retail_point_id,
                retail_point_name=validated_data['retail_point_name'],
                local_retail_point_db_id=validated_data['local_retail_point_db_id'],
                sale_journal_id=validated_data['sale_journal_id'],
                payment_journal_id=validated_data['payment_journal_id'],
                payment_method_name=validated_data['payment_method_name'],
                remarks=validated_data['remarks'],
                partner_id=validated_data['partner_id'],
                sale_date=validated_data['sale_date'],
                sale_counter_id=validated_data['sale_counter_id'],
                sale_counter_name=validated_data['sale_counter_name'],
                debtors_account_id=validated_data['debtors_account_id'],
                confirmed_by=validated_data['confirmed_by'], 
                confirmed_by_name=validated_data['confirmed_by_name'],
                miscellaneous_product_id=validated_data['miscellaneous_product_id'],
                miscellaneous_qty=validated_data['miscellaneous_qty'],
                miscelleneous_sale_price=validated_data['miscelleneous_sale_price'],
                total_amount=validated_data['total_including_miscellaneous'],
                miscellaneous_invoice_num=validated_data['miscellaneous_invoice_num'],
                customer_name=validated_data['customer_name'],
                is_default_customer=validated_data['is_default_customer'],
                total_cess=validated_data['total_cess'],
                confirmed_on=validated_data['confirmed_on'],
                name=validated_data['name'],
                sale_num=validated_data['sale_num'],
                store_type=validated_data['store_type']
            )

            
            # Prepare sale lines
            sale_lines = [
                SaleLine(
                    sale_id=sale.id,
                    sl_no=line['sl_no'],
                    product_id=line['product_id'],
                    name=line['name'],
                    product_uom_qty=line['product_uom_qty'],
                    product_uom=line['product_uom'],
                    vat_percent=line['vat_percent'],
                    price_unit=line['price_unit'],
                    total=float(line['price_unit']) * float(line['product_uom_qty']), 
                    account_id=line['account_id'],
                    retail_sale_mrp=line['retail_sale_mrp'],
                    cess_id=line['cess_id'],
                    cess_amount=line['cess_amount'],
                    total_cess=line['total_cess'],
                    qty_available=line['qty_available'],
                    sale_type=line['sale_type'],

                    
                )
                for line in validated_data['sale_line_ids']
            ]
            
            # Bulk create sale lines
            SaleLine.objects.using(shard_db).bulk_create(sale_lines)
            # Prepare Lot lines
            if len(validated_data.get('lot_details_ids',[])) >0:
                lot_lines = [
                        LotLine(
                            sale_id= sale.id,
                            lot_id=line['lot_id'],
                            product_id=line['product_id'],
                            lot_name=line['lot_name'],
                            product_name=line['product_name'],
                            quantity=line['quantity'],


                            )
                        for line in validated_data['lot_details_ids']
                        ]
                LotLine.objects.using(shard_db).bulk_create(lot_lines)
            # Prepare Misc Lot lines
            if len(validated_data.get('miscellaneous_lot_details_ids',[])) >0:
                misc_lot_lines = [
                        MiscLotLine(
                            sale_id= sale.id,
                            lot_id=line['lot_id'],
                            product_id=line['product_id'],
                            lot_name=line['lot_name'],
                            product_name=line['product_name'],
                            quantity=line['quantity'],
                            

                            )
                        for line in validated_data['miscellaneous_lot_details_ids']
                        ]
                MiscLotLine.objects.using(shard_db).bulk_create(misc_lot_lines)

                

        return {
            'status': 'success', 
            'sale_id': sale.id, 
            'retail_point_id': retail_point_id
        }
    
    except Exception as e:
        job = django_rq.get_current_job()  # Get the current job
        if job:
            job.meta['status'] = 'failed'
            job.save()  # Save the job with status 'failed'
        logger.error(f"Error processing sale order: {e}")
        return {'status': 'error', 'message': str(e)}

def send_summary_to_odoo(summary_payload):
    try:
        # Replace with actual Odoo API endpoint
        response = requests.post(
            'https://your-odoo-instance.com/api/sales-summary',
            json=summary_payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending summary to Odoo: {e}")
        return None
@django_rq.job('day_close')
def generate_day_close_summary(retail_point_id, date=None):
    """
    Generate aggregated day-close summary grouped by counter_id and payment_method.
    """
    if date is None:
        date = timezone.now().date()

    try:
        # Use the shard database corresponding to the retail_point_id
        shard_db = f'shard_{retail_point_id}'
        
        # Aggregate sales data by counter_id and payment_method
        sales= (
            Sale.objects.using(shard_db)
            .filter(retail_point_id=retail_point_id, order_date__date=date)
            .values('counter_id', 'payment_method')
            .annotate(
                total_sales=Sum('total_amount'),
                total_transactions=Count('id')
            )
        )
        
        result = []

        # For each counter and payment method combination, gather product sales data
        for sale in sales:
            counter_id = sale['counter_id']
            payment_method = sale['payment_method']
            total_sales = sale['total_sales']
            total_transactions = sale['total_transactions']

            # Aggregate product sales for this counter and payment method
            product_sales = (
                SaleLine.objects.using(shard_db)
                .filter(
                    sale__retail_point_id=retail_point_id,
                    sale__order_date__date=date,
                    sale__counter_id=counter_id,
                    sale__payment_method=payment_method
                    )
                .values('product_id')
                .annotate(
                    qty_sold=Sum('quantity'),
                    total_revenue=Sum('subtotal')
                )
            )

            # Prepare the summary
            result.append({
                "retail_point_id": retail_point_id,
                "counter_id": counter_id,
                "payment_method": payment_method,
                "total_sales": float(total_sales or 0),
                "total_transactions": total_transactions,
                "product_lines": [
                    {
                        "product_id": line['product_id'],
                        "qty_sold": line['qty_sold'],
                        "total_revenue": float(line['total_revenue'] or 0),
                    }
                    for line in product_sales
                ]
            })

        return result

    except Exception as e:
        logger.error(f"Error generating day-close summary for retail_point_id {retail_point_id}: {e}")
        return {"error": str(e)}
