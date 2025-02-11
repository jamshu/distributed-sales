from django.db.models import Prefetch
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Sale, SaleLine, LotLine


class ShardedQuerysetMixin(LoginRequiredMixin):
    login_url = '/login/'  # Optional: specify a custom login page
    redirect_field_name = 'next'  # Optional: customize redirect parameter
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
        query = self.request.GET.get('q')
        counter_id = self.request.GET.get('counter_id')
        date = self.request.GET.get('date')
        payment_journal_id = self.request.GET.get('payment_journal_id')

        if query:
            queryset = queryset.filter(sale_num__icontains=query)
        if date:
            queryset = queryset.filter(sale_date=date)
        if counter_id:
            queryset = queryset.filter(sale_counter_id=counter_id)
        if payment_journal_id:
            queryset = queryset.filter(payment_journal_id=payment_journal_id)
        return queryset.select_related().only(
            'sale_num', 'sale_date', 'customer_name',
            'payment_method_name', 'sale_counter_name'
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
               
                Prefetch('lot_lines', queryset=LotLine.objects.using(f'shard_{retail_point_id}')),
            
                
            ).filter(id=sale_id)
