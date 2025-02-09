from django.views.generic import TemplateView
from django.db import connections
from django.db.models import Q, Sum
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import Sale
from django.conf import settings
from functools import partial

class SalesDashboardView(TemplateView):
    template_name = 'sales/dashboard.html'
    max_workers = 8  # Adjust based on your server's capabilities

    def process_retail_point(self, retail_point, current_date):
        """Process a single retail point and return its data."""
        shard_name = f'shard_{retail_point}'
        
        if shard_name not in connections:
            return None
            
        # Filter sales for the current date
        sales_today = Sale.objects.using(shard_name).filter(sale_date=current_date)
        
        # Get the total number of sales for today
        total_sales = sales_today.count()
        
        # Get the total revenue for today
        total_revenue = sales_today.aggregate(
            total_revenue=Sum('total_amount')
        )['total_revenue'] or 0
        
        # Get cash revenue
        cash_revenue = sales_today.filter(
            Q(payment_method_name__icontains='cash')
        ).aggregate(
            total_revenue=Sum('total_amount')
        )['total_revenue'] or 0
        
        # Get retail point name
        retail_point_name = (
            sales_today.first().retail_point_name if sales_today.exists() 
            else Sale.objects.using(shard_name).filter(
                retail_point_id=retail_point
            ).values_list('retail_point_name', flat=True).first() or ''
        )
        
        return {
            'retail_point': retail_point,
            'retail_point_name': retail_point_name,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'cash_revenue': cash_revenue
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the current date
        custom_date_str = self.request.GET.get('date')
        try:
            if custom_date_str:
                current_date = timezone.datetime.strptime(
                    custom_date_str, '%Y-%m-%d'
                ).date()
            else:
                current_date = timezone.now().date()
        except ValueError:
            current_date = timezone.now().date()
        
        search_query = self.request.GET.get('search', '').strip()
        # List of retail points (shards)
        retail_points = settings.RETAIL_IDS
        dashboard_data = []
        
        # Create a partial function with fixed current_date
        process_point = partial(self.process_retail_point, current_date=current_date)
        
        # Process retail points concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_point = {
                executor.submit(process_point, point): point 
                for point in retail_points
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_point):
                result = future.result()
                if result is not None:
                    dashboard_data.append(result)
        
        # Filter dashboard data based on search query
        if search_query:
            dashboard_data = [
                data for data in dashboard_data 
                if search_query.lower() in data['retail_point_name'].lower()
            ]
        # Sort dashboard data by total revenue
        dashboard_data.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        # Calculate totals
        total_sales_all = sum(data['total_sales'] for data in dashboard_data)
        total_revenue_all = sum(data['total_revenue'] for data in dashboard_data)
        total_cash_revenue_all = sum(data['cash_revenue'] for data in dashboard_data)
        
        # Update context
        context.update({
            'dashboard_data': dashboard_data,
            'current_date': current_date,
            'total_sales_all': total_sales_all,
            'total_revenue_all': total_revenue_all,
            'total_cash_revenue_all': total_cash_revenue_all
        })
        
        return context