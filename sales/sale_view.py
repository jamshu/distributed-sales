from django.db.models import Prefetch
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Sale, SaleLine

class ShardedQuerysetMixin:
    def get_queryset(self):
        # Get retail_point_id from session or URL
        retail_point_id = self.request.session.get('retail_point_id') or self.kwargs.get('retail_point_id')
        if not retail_point_id:
            raise ValueError("retail_point_id is required")
            
        # Create a queryset with the shard hint
        return self.model.objects.using(f'shard_{retail_point_id}').all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['retail_point_id'] = self.kwargs['retail_point_id']
        return context

class SaleListView(ShardedQuerysetMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    ordering = ['-created_at']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related().only(
            'sale_num', 'sale_date', 'customer_name',
            'confirmed_on'
        ).order_by('-created_at')

class SaleDetailView(ShardedQuerysetMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        # Get the current sale_id from URL parameters
        sale_id = self.kwargs['pk']
        retail_point_id = self.kwargs['retail_point_id']

        # Prefetch SaleLine and LotLine, using the correct shard
        return Sale.objects.using(f'shard_{retail_point_id}') \
            .prefetch_related(
                Prefetch('lines', queryset=SaleLine.objects.using(f'shard_{retail_point_id}')),
                'lot_lines'  # Prefetch lot_lines if needed
            ).filter(id=sale_id)
