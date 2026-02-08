"""
AJAX endpoints for origin verification during product creation.

These endpoints provide real-time origin validation as vendors fill out product forms.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging

from core.origin_verification import OriginVerificationEngine
from django_countries import countries

logger = logging.getLogger(__name__)


@login_required
@require_POST
@csrf_exempt
def ajax_validate_product_origin(request):
    """
    Real-time origin validation endpoint.
    
    POST data expected:
    {
        'brand': 'Apple',
        'manufacturer': 'Foxconn',
        'manufacturer_address': 'Shenzhen, China',
        'origin_country': 'US',
        'device_identifier_type': 'imei',
        'device_identifier_value': '123456789012345',
        'certification_numbers': 'FCC ID: ABC123',
        'price': '999.99',
        'product_type': 'physical',
        'category_name': 'Electronics',
        'authenticity_status': 'authentic'
    }
    """
    try:
        data = json.loads(request.body)
        
        # Validate that we have at least origin_country
        origin = data.get('origin_country')
        if not origin:
            return JsonResponse({
                'valid': False,
                'warning': 'Origin country is required',
                'severity': 'error'
            })
        
        # Run verification engine
        engine = OriginVerificationEngine()
        result = engine.verify_origin(data)
        
        # Prepare response
        response = {
            'valid': not result['is_suspicious'],
            'score': result['verification_score'],
            'confidence': round(result['confidence'] * 100, 1),
            'reasoning': result['reasoning'],
            'severity': 'error' if result['is_suspicious'] else ('warning' if result['flags'] else 'info'),
        }
        
        # Add actionable information
        if result['is_suspicious']:
            response['warning'] = f"⚠️ Origin verification score: {result['verification_score']}/100"
            response['action'] = 'Please review your origin claim. High-risk claims require admin verification.'
            response['mismatches'] = result['mismatches']
            response['suggested_origin'] = result['suggested_origin']
            if result['suggested_origin']:
                response['suggestion'] = f"Did you mean {countries.name(result['suggested_origin'])}?"
        
        elif result['flags']:
            response['warning'] = f"ℹ️ Verification flags detected"
            response['action'] = 'Please review before proceeding'
            response['flags'] = result['flags']
        
        else:
            response['success_message'] = '✓ Origin claim verified'
        
        return JsonResponse(response)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in ajax_validate_product_origin: {e}", exc_info=True)
        return JsonResponse({'error': 'Server error during validation'}, status=500)


@login_required
@require_POST
def ajax_get_origin_suggestions(request):
    """
    Get origin suggestions based on product details.
    
    Returns similar products with their origins to help vendor decide.
    """
    try:
        data = json.loads(request.body)
        brand = data.get('brand', '')
        category = data.get('category_name', '')
        
        from core.models import Product
        from django.db.models import Q
        
        # Find similar products
        similar_products = Product.objects.filter(
            Q(brand__icontains=brand) | Q(category__name__icontains=category)
        ).exclude(
            origin_country__isnull=True
        ).values(
            'origin_country'
        ).distinct()[:5]
        
        origins = []
        for item in similar_products:
            if item['origin_country']:
                origins.append({
                    'code': item['origin_country'],
                    'name': countries.name(item['origin_country']),
                })
        
        return JsonResponse({
            'similar_product_origins': origins,
            'message': 'Based on similar products in this category' if origins else 'No similar products found'
        })
        
    except Exception as e:
        logger.error(f"Error in ajax_get_origin_suggestions: {e}", exc_info=True)
        return JsonResponse({'error': 'Could not fetch suggestions'}, status=500)


@login_required
@require_POST
def ajax_check_authenticity_risk(request):
    """
    Check authenticity risk based on product category and origin combination.
    """
    try:
        data = json.loads(request.body)
        product_type = data.get('product_type', 'physical')
        category = data.get('category_name', '')
        origin = data.get('origin_country')
        authenticity_status = data.get('authenticity_status', 'unknown')
        
        # High-risk category/origin combinations
        high_risk_combinations = {
            ('electronics', 'Unknown'): 'Electronic products require trusted origins',
            ('luxury', None): 'Luxury items require verification status',
            ('watches', 'CN'): 'Counterfeit luxury watches often claim Chinese origin',
            ('designer clothing', 'Unknown'): 'Designer items require brand verification',
        }
        
        risk_level = 'low'
        warning = ''
        
        # Check for risky combinations
        for (cat, risky_origin), msg in high_risk_combinations.items():
            if cat.lower() in category.lower():
                if not origin or origin == risky_origin:
                    risk_level = 'high'
                    warning = msg
                    break
        
        # Electronics without device identifier
        if 'electronics' in category.lower() and not data.get('device_identifier_value'):
            risk_level = 'medium' if risk_level == 'low' else risk_level
            warning = 'Electronics should have device identifiers for verification'
        
        # Luxury without authenticity status
        if 'luxury' in category.lower() and authenticity_status == 'unknown':
            risk_level = 'medium' if risk_level == 'low' else risk_level
            warning = 'Luxury items require authenticity status'
        
        return JsonResponse({
            'risk_level': risk_level,
            'warning': warning,
            'requires_admin_review': risk_level == 'high'
        })
        
    except Exception as e:
        logger.error(f"Error in ajax_check_authenticity_risk: {e}", exc_info=True)
        return JsonResponse({'error': 'Could not assess authenticity risk'}, status=500)
