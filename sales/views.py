from django.utils import timezone
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
           
            
            data = request.POST.dict()
            date_str = data.get('close_date')
            retail_point_id = data.get('retail_point_id')
            url = data.get('url')
            print("data url>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", url)
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
            
            
            # Default to queued processing
            job = generate_day_close_summary.delay(retail_point_id, summary_date, url)
            return Response({
                'status': 'queued', 
                'job_id': job.id,
                'date': str(summary_date),
                'retail_point_id': retail_point_id,
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Day close summary API error: {e}")
            return Response(
                {'error': 'Internal server error during day close summary generation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

