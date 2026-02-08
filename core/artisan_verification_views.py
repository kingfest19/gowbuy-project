"""
AJAX endpoints for artisan/handmade product verification.

These endpoints provide real-time validation for handmade, artisan, and resold products.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging

from core.artisan_verification import ArtisanVerificationEngine

logger = logging.getLogger(__name__)


@login_required
@require_POST
@csrf_exempt
def ajax_verify_artisan_product(request):
    """
    Real-time verification endpoint for artisan/handmade products.
    
    POST data expected:
    {
        'price': 350.00,
        'vendor_sales': 5,
        'vendor_rating': 4.2,
        'product_title': 'Handmade Oil Painting',
        'description': 'Beautiful landscape painting...',
        'category': 'Art & Collectibles',
        'acquisition_type': 'created',  # or 'purchased_new', etc.
        'acquisition_details': 'I painted this in my studio',
        'has_certificate': false,
        'has_provenance': false,
        'image_count': 5,
        'vendor_is_creator': true
    }
    """
    try:
        data = json.loads(request.body)
        
        # Initialize verification engine
        engine = ArtisanVerificationEngine()
        
        # Verify product
        result = engine.verify_artisan_product(data)
        
        return JsonResponse({
            'success': True,
            'valid': result['valid'],
            'score': result['score'],
            'confidence': result['confidence'],
            'status': result['status'],
            'vendor_tier': result['vendor_tier'],
            'reasoning': result['reasoning'],
            'requirements_met': result['requirements_met'],
            'next_steps': result['next_steps'],
            'vendor_badge': result.get('vendor_badge'),
            'visibility_boost': result.get('visibility_boost', 1.0),
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
        }, status=400)
    except Exception as e:
        logger.error(f"Artisan verification error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Verification error',
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def ajax_validate_acquisition_info(request):
    """
    Validate acquisition information for high-value items.
    
    POST data expected:
    {
        'price': 1500.00,
        'acquisition_type': 'purchased_used',
        'acquisition_details': 'Bought at estate sale in 2024'
    }
    """
    try:
        data = json.loads(request.body)
        engine = ArtisanVerificationEngine()
        
        price = float(data.get('price', 0))
        acquisition_type = data.get('acquisition_type', '')
        acquisition_details = data.get('acquisition_details', '')
        
        # Validate
        is_valid, message = engine.validate_acquisition_info(
            acquisition_type,
            acquisition_details,
            price
        )
        
        return JsonResponse({
            'success': True,
            'valid': is_valid,
            'message': message,
            'required': price >= 500,  # THRESHOLD_HIGH_VALUE
        })
    
    except Exception as e:
        logger.error(f"Acquisition validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Validation error',
        }, status=500)


@login_required
def ajax_get_acquisition_options(request):
    """
    Get list of acquisition type options for dropdown.
    
    Returns:
    {
        'success': true,
        'options': [
            ['created', 'I made/created this item'],
            ['purchased_new', 'Purchased new from manufacturer/brand'],
            ...
        ]
    }
    """
    try:
        engine = ArtisanVerificationEngine()
        options = engine.get_acquisition_options()
        
        return JsonResponse({
            'success': True,
            'options': list(options),
        })
    
    except Exception as e:
        logger.error(f"Error getting acquisition options: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error loading options',
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def ajax_get_vendor_tier_requirements(request):
    """
    Get requirements based on vendor tier and product price.
    Helps vendors understand what they need to provide.
    
    POST data expected:
    {
        'vendor_sales': 5,
        'vendor_rating': 4.2,
        'price': 350.00
    }
    """
    try:
        data = json.loads(request.body)
        engine = ArtisanVerificationEngine()
        
        # Get vendor tier
        vendor_tier = engine._get_vendor_tier(
            data.get('vendor_sales', 0),
            data.get('vendor_rating', 0)
        )
        
        price = float(data.get('price', 0))
        
        # Determine requirements
        requirements = {
            'basic': ['Product title', 'Description', 'Price', 'Photos (3+)', 'Category'],
        }
        
        if price >= 500:
            requirements['high_value'] = [
                'How did you acquire this item?',
                'Examples: Made it, Purchased from supplier, Estate sale, etc.',
            ]
        
        if price >= 2000:
            requirements['luxury'] = [
                'Certificate of authenticity (if available)',
                'Provenance details (recommended)',
            ]
        
        tier_info = {
            'new': {
                'label': 'New Seller',
                'description': 'Build trust through sales and reviews',
                'trust_score': 50,
            },
            'verified': {
                'label': 'Verified Seller',
                'description': '3+ sales with 4.0★ average',
                'trust_score': 70,
            },
            'trusted': {
                'label': 'Trusted Artisan',
                'description': '10+ sales with 4.5★ average',
                'trust_score': 85,
            },
            'master': {
                'label': 'Master Craftsman',
                'description': '50+ sales with 4.8★ average',
                'trust_score': 95,
            },
        }
        
        return JsonResponse({
            'success': True,
            'vendor_tier': vendor_tier,
            'tier_info': tier_info[vendor_tier],
            'requirements': requirements,
            'price_threshold': {
                'high_value': 500,
                'luxury': 2000,
            },
        })
    
    except Exception as e:
        logger.error(f"Error getting tier requirements: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error loading requirements',
        }, status=500)
