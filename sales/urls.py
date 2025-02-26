from django.urls import path
from .views import SaleOrderProcessView,DayCloseSummaryView
from  .sale_view import  SaleListView, SaleDetailView
from .sale_dashboard_view import SalesDashboardView
urlpatterns = [
    path('enqueue_sales/', SaleOrderProcessView.as_view(), name='enqueue_sales'),
    path('enqueue_day_close/', DayCloseSummaryView.as_view(), name='enqueue_day_close'),
    path('dashboard/', SalesDashboardView.as_view(), name='dashboard'),
    path('retail-point/<int:retail_point_id>/data/', SaleListView.as_view(), name='sale_list'),
    path('retail-point/<int:retail_point_id>/data/<uuid:pk>/', SaleDetailView.as_view(), name='sale_detail'),
]
