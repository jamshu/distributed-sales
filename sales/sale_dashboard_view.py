from django.views.generic import TemplateView
from django.db import connections
from django.db.models import Sum
from django.utils import timezone
from .models import Sale
from django.conf import settings

class SalesDashboardView(TemplateView):
    template_name = 'sales/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the current date
        current_date = timezone.now().date()
        
        # List of retail points (shards)
        retail_points = settings.RETAIL_IDS
        dashboard_data = []
        total_sales_all = 0  # Total sales across all retail points
        total_revenue_all = 0  # Total revenue across all retail points
        
        for retail_point in retail_points:
            
            shard_name = f'shard_{retail_point}'
            
            # Check if the shard exists in the database connections
            if shard_name in connections:
                # Filter sales for the current date
                sales_today = Sale.objects.using(shard_name).filter(sale_date=current_date)
                
                # Get the total number of sales for today
                total_sales = sales_today.count()
                
                # Get the total revenue for today
                total_revenue = sales_today.aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
                
              
                retail_point_name = (
                sales_today.first().retail_point_name if sales_today.exists() 
                else Sale.objects.using(shard_name).filter(retail_point_id=retail_point).values_list('retail_point_name', flat=True).first() or ''
            )
                # Add to dashboard data
                dashboard_data.append({
                    'retail_point': retail_point,
                    'retail_point_name': retail_point_name,
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                  
                })
                
                # Accumulate totals for all retail points
                total_sales_all += total_sales
                total_revenue_all += total_revenue
        dashboard_data.sort(key=lambda x: x['total_revenue'], reverse=True)
        context['dashboard_data'] = dashboard_data
        context['current_date'] = current_date  # Pass current date to the template
        context['total_sales_all'] = total_sales_all  # Total sales across all retail points
        context['total_revenue_all'] = total_revenue_all  # Total revenue across all retail points
        return context