# sales/tasks.py
import django_rq
from django.db import connections, transaction
from django.db.models import Sum, Count
from django.utils import timezone
import requests
import json
from .models import Sale, SaleLine, LotLine, MiscLotLine
from .validators import validate_sale_data
from decimal import Decimal
from django.conf import settings
from requests.exceptions import RequestException
import json
import logging

logger = logging.getLogger(__name__)

class SubmissionError(Exception):
    """Custom exception for  submission failures"""
    pass

SECRET_KEY = settings.SECRET_KEY
KEY_CRYPT_CONTEXT = settings.KEY_CRYPT_CONTEXT

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

logger = logging.getLogger(__name__)

@django_rq.job('sales_processing')
def process_sale_order(sale_data):
    try:
        # Validate incoming data
        validated_data = json.loads(sale_data)
            
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
    
    except RequestException as e:
        error_message = f"HTTP request failed: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)


def encrypt_value(value: str) -> str:
    return KEY_CRYPT_CONTEXT.hash(value + SECRET_KEY)

@django_rq.job('send_summary')
def send_summary_to_odoo(summary_payload, url):
    try:
        # Encrypt the `sale_num` before sending
        summary_payload['encrypted_sale_num'] = encrypt_value(summary_payload['sale_num'])
        payload_json = json.dumps(summary_payload, cls=DecimalEncoder)
        
        response = requests.post(
            url,
            data=payload_json,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()
        
        # Check if the response indicates a failure
        if isinstance(data, dict) and data.get('result', {}).get('status') == 'Failed':
            error_message = data.get('result', {}).get('message', 'Unknown error occurred')
            logger.error(f"Failed to send summary to Odoo: {error_message}")
            raise SubmissionError(error_message)
            
        return data
        
    except RequestException as e:
        error_message = f"HTTP request failed: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)
        
    except Exception as e:
        error_message = f"Error sending summary to Odoo: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)


def get_local_retail_point_id(shard_db):
    # Replace with actual logic to map retail_point_id to local_retail_point_id
    result = Sale.objects.using(shard_db).last().local_retail_point_db_id
    return result

@django_rq.job('day_close')
def generate_day_close_summary(retail_point_id, date=None, url=None):
    """
    Generate aggregated day-close summary grouped by counter_id and payment_method.
    """
    if date is None:
        date = timezone.now().date()

    try:
        # Use the shard database corresponding to the retail_point_id
        shard_db = f'shard_{retail_point_id}'
        local_retail_point_db_id = get_local_retail_point_id(shard_db)

        # Aggregate sales data by counter_id and payment method
        sales = (
            Sale.objects.using(shard_db)
            .filter(retail_point_id=retail_point_id, sale_date=date)
            .values('sale_counter_id', 'payment_journal_id')
            .annotate(
                total_sales=Sum('total_amount'),
                total_cess=Sum('total_cess'),
                total_transactions=Count('id')
            )
        )
        
        result = []

        # For each counter and payment method combination, gather product sales data
        for sale in sales:
            counter_id = sale['sale_counter_id']
            payment_method = sale['payment_journal_id']
            total_sales = sale['total_sales']
            total_cess = sale['total_cess']

            # Fetch sale lines aggregated by product
            sale_lines = (
                SaleLine.objects.using(shard_db)
                .filter(
                    time__date=date,
                    sale__sale_counter_id=counter_id,
                    sale__payment_journal_id=payment_method,
                )
                .values(
                    'product_id', 'name', 'product_uom', 'vat_percent', 
                    'price_unit', 'account_id', 'retail_sale_mrp', 
                    'cess_id', 'qty_available','cess_amount', 'sale_type'
                )
                .annotate(
                    product_uom_qty=Sum('product_uom_qty'),
                    total_cess=Sum('total_cess'),
                )
            )

            # Fetch lot lines aggregated by product and lot
            lot_lines = (
                LotLine.objects.using(shard_db)
                .filter(
                    time__date=date,
                    sale__sale_counter_id=counter_id,
                    sale__payment_journal_id=payment_method,
                )
                .values('product_id', 'lot_id')
                .annotate(quantity=Sum('quantity'))
            )

            # Map lot data by product
            lot_dicts = {}
            for lot in lot_lines:
                product_id = lot['product_id']
                lot_id = lot['lot_id']
                if product_id not in lot_dicts:
                    lot_dicts[product_id] = {}
                if lot_id not in lot_dicts[product_id]:
                    lot_dicts[product_id][lot_id] = 0
                lot_dicts[product_id][lot_id] = lot['quantity']

            # Prepare product aggregates
            product_aggregates = {}
            for line in sale_lines:
                product_id = line['product_id']
                # Initialize or update product aggregate data
                if product_id not in product_aggregates:
                    product_aggregates[product_id] = {
                        'product_id': product_id,
                        'name': line['name'],
                        'product_uom_qty': 0,  # Total quantity should be initialized to 0
                        'product_uom': line['product_uom'],
                        'vat_percent': line['vat_percent'],
                        'price_unit': line['price_unit'],
                        'account_id': line['account_id'],
                        'retail_sale_mrp': line['retail_sale_mrp'],
                        'cess_id': line['cess_id'],
                        'taxes_ids': [],  # Can be adjusted if required
                        'cess_amount': line['cess_amount'],  # Can be adjusted if required
                        'total_cess': line['total_cess'],
                        'qty_available': line['qty_available'],
                        'lot_details_ids': [],  # Initialize empty list for lot details
                        'sale_type': line['sale_type'],
                    }

                # Update product_uom_qty
                product_aggregates[product_id]['product_uom_qty'] += line['product_uom_qty']

                # Add lot details if available
                if product_id in lot_dicts:
                    # Include lot quantity data here
                    product_aggregates[product_id]['lot_details_ids'] = [
                        [0, 0, {'lot_id': lot_id, 'quantity': qty}]
                        for lot_id, qty in lot_dicts[product_id].items()
                    ]

            # Prepare the summary
            sale_num = f"{date.strftime('%Y%m%d')}/{retail_point_id}/{counter_id}/{payment_method}"
            summary = {
                'local_retail_point_db_id': local_retail_point_db_id,
                'retail_point_id': int(retail_point_id),
                'sale_date': date.strftime('%Y-%m-%d'),
                'payment_journal_id': payment_method,
                'debtors_account_id': 0,
                'sale_journal_id': 0,
                'miscelleneous_sale_price': 0.0,
                'miscellaneous_product_id': 0,
                'miscellaneous_qty': 0,
                'miscellaneous_invoice_num': False,
                'sale_num': sale_num,
                'name': sale_num,
                'miscellaneous_name': 'New',
                'sale_counter_id': counter_id,
                'customer_name':'',
                'is_default_customer': True,
                'total_including_miscellaneous': float(total_sales or 0),
                'total_cess': float(total_cess or 0),
                'amount_total': float(total_sales or 0),
                'confirmed_on': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sale_line_ids': [],
                'miscellaneous_lot_details_ids': [],
                'store_type': 'FLS'
            }

            for product in product_aggregates.values():
                summary['sale_line_ids'].append([0, 0, product])
            job = send_summary_to_odoo.delay(summary, url)
            result.append(job.id)

        
        return result

    except RequestException as e:
        error_message = f"HTTP request failed: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message)
        raise SubmissionError(error_message)
