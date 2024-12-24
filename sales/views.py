from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .tasks import process_sale_order, generate_day_close_summary
import logging

logger = logging.getLogger(__name__)

class SaleOrderProcessView(APIView):
    """
    API endpoint for processing sale orders
    
    Accepts sale order data and queues it for processing
    """
    def post(self, request):
        try:
            # Get sale data from request
            sale_data = request.data
            
            # Validate basic request structure
            if not sale_data:
                return Response(
                    {'error': 'No sale data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Queue the sale order processing job
            job = process_sale_order.delay(sale_data)
            
            # Return job ID and initial success response
            return Response({
                'status': 'queued', 
                'job_id': job.id
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Sale order processing API error: {e}")
            return Response(
                {'error': 'Internal server error during sale processing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class DayCloseSummaryView(APIView):
    """
    API endpoint for generating day close summaries
    
    Allows generating summary for current day or a specific date
    Supports both immediate and queued processing
    """
    def post(self, request):
        try:
            # Get date from request, default to current date if not provided
            date_str = request.data.get('date')
            process_mode = request.data.get('mode', 'queue')  # 'queue' or 'immediate'
            
            # Parse date if provided
            if date_str:
                try:
                    summary_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                summary_date = timezone.now().date()
            
            # Process based on mode
            if process_mode == 'immediate':
                # Direct processing for smaller systems or testing
                summaries = generate_day_close_summary(summary_date)
                return Response({
                    'status': 'completed',
                    'date': str(summary_date),
                    'summaries': summaries
                }, status=status.HTTP_200_OK)
            
            # Default to queued processing
            job = generate_day_close_summary.delay(summary_date)
            
            return Response({
                'status': 'queued', 
                'job_id': job.id,
                'date': str(summary_date)
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Day close summary API error: {e}")
            return Response(
                {'error': 'Internal server error during day close summary generation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# In your urls.py, add:
# from django.urls import path
# from .views import SaleOrderProcessView
# 
# urlpatterns = [
#     path('api/sales/process/', SaleOrderProcessView.as_view(), name='process_sale_order'),
# ]
