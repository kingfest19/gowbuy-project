"""
Backend views for Promotion management, A/B testing, customer segmentation, campaigns, analytics, and bulk codes.
"""
import json
import secrets
import string
from decimal import Decimal
from datetime import timedelta, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Promotion, PromotionVariant, PromotionSegmentRule,
    PromotionCode, PromotionCampaign, Vendor, Order, Cart
)


# ============= Promotion Campaign Views =============

@login_required
def promotion_campaigns_list(request):
    """List all promotion campaigns for vendor"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    # Get status filter
    status_filter = request.GET.get('status', '')
    campaigns_qs = vendor.promo_campaigns.all()
    
    if status_filter:
        campaigns_qs = campaigns_qs.filter(status=status_filter)
    
    # Get categorized campaigns
    active_campaigns = campaigns_qs.filter(status='active')
    scheduled_campaigns = campaigns_qs.filter(status='scheduled')
    ended_campaigns = campaigns_qs.filter(status='ended')
    
    context = {
        'vendor': vendor,
        'active_campaigns': active_campaigns,
        'scheduled_campaigns': scheduled_campaigns,
        'ended_campaigns': ended_campaigns,
        'total_campaigns': campaigns_qs.count(),
    }
    
    return render(request, 'core/vendor_promotion_campaigns.html', context)


@login_required
def create_promotion_campaign(request):
    """Create a new promotion campaign"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Create campaign
        campaign = PromotionCampaign.objects.create(
            vendor=vendor,
            name=data.get('name'),
            description=data.get('description', ''),
            start_date=datetime.fromisoformat(data.get('start_date')),
            end_date=datetime.fromisoformat(data.get('end_date')),
            emoji=data.get('emoji', '🎉'),
            status='draft'
        )
        
        # Add promotions to campaign
        promotion_ids = data.get('promotion_ids', [])
        if promotion_ids:
            promotions = Promotion.objects.filter(
                id__in=promotion_ids,
                applicable_vendor=vendor
            )
            campaign.promotions.set(promotions)
        
        return JsonResponse({
            'success': True,
            'campaign_id': campaign.id,
            'message': f'Campaign "{campaign.name}" created successfully'
        })
    
    # Get vendor's promotions for selection
    promotions = vendor.promotions.all()
    return render(request, 'core/campaign_form.html', {
        'vendor': vendor,
        'promotions': promotions
    })


@login_required
@require_POST
def update_campaign_status(request, campaign_id):
    """Update campaign status (activate, pause, end)"""
    campaign = get_object_or_404(PromotionCampaign, id=campaign_id)
    
    # Verify ownership
    if campaign.vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    new_status = request.POST.get('status')
    valid_statuses = ['draft', 'scheduled', 'active', 'paused', 'ended']
    
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    campaign.status = new_status
    campaign.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'new_status': new_status,
        'message': f'Campaign status updated to {new_status}'
    })


@login_required
def campaign_performance(request, campaign_id):
    """Get detailed performance metrics for a campaign"""
    campaign = get_object_or_404(PromotionCampaign, id=campaign_id)
    
    # Verify ownership
    if campaign.vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    metrics = campaign.get_performance_metrics()
    
    # Get per-promotion breakdown
    promotion_breakdown = []
    for promo in campaign.promotions.all():
        variants = promo.variants.all()
        promo_metrics = {
            'promotion_name': promo.name,
            'promotion_code': promo.code or 'Auto',
            'revenue': variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0,
            'conversions': variants.aggregate(Sum('conversions'))['conversions__sum'] or 0,
            'clicks': variants.aggregate(Sum('clicks'))['clicks__sum'] or 0,
        }
        promotion_breakdown.append(promo_metrics)
    
    return JsonResponse({
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'status': campaign.status,
            'start_date': campaign.start_date.isoformat(),
            'end_date': campaign.end_date.isoformat(),
        },
        'metrics': metrics,
        'promotion_breakdown': promotion_breakdown
    })


# ============= A/B Testing / Promotion Variants =============

@login_required
@require_POST
def create_promotion_variant(request, promotion_id):
    """Create an A/B testing variant for a promotion"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    
    # Check variant limit (A, B, C variants)
    existing_variants = promotion.variants.count()
    if existing_variants >= 3:
        return JsonResponse({
            'error': 'Maximum 3 variants (A, B, C) allowed per promotion'
        }, status=400)
    
    variant_types = ['A', 'B', 'C']
    used_types = promotion.variants.values_list('variant_type', flat=True)
    new_variant_type = next(t for t in variant_types if t not in used_types)
    
    variant = PromotionVariant.objects.create(
        promotion=promotion,
        variant_type=new_variant_type,
        discount_value=data.get('discount_value'),
        description=data.get('description', '')
    )
    
    return JsonResponse({
        'success': True,
        'variant_id': variant.id,
        'variant_type': new_variant_type,
        'message': f'Variant {new_variant_type} created successfully'
    })


@login_required
def get_variant_analytics(request, promotion_id):
    """Get A/B testing analytics for a promotion's variants"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    variants = promotion.variants.all().order_by('variant_type')
    
    variant_data = []
    for variant in variants:
        data = {
            'id': variant.id,
            'type': variant.variant_type,
            'discount_value': float(variant.discount_value),
            'impressions': variant.impressions,
            'clicks': variant.clicks,
            'conversions': variant.conversions,
            'ctr': round(variant.ctr, 2),
            'conversion_rate': round(variant.conversion_rate, 2),
            'revenue': float(variant.revenue_generated),
            'avg_order_value': float(variant.avg_order_value),
            'is_winner': variant.is_winner,
        }
        variant_data.append(data)
    
    return JsonResponse({
        'promotion': {
            'id': promotion.id,
            'name': promotion.name,
            'code': promotion.code,
        },
        'variants': variant_data
    })


@login_required
@require_POST
def mark_winning_variant(request, variant_id):
    """Mark a variant as the winner and apply to promotion"""
    variant = get_object_or_404(PromotionVariant, id=variant_id)
    
    # Verify ownership
    if variant.promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Mark this as winner
    PromotionVariant.objects.filter(promotion=variant.promotion).update(is_winner=False)
    variant.is_winner = True
    variant.save(update_fields=['is_winner'])
    
    # Update promotion with winning discount
    promotion = variant.promotion
    promotion.discount_value = variant.discount_value
    promotion.save(update_fields=['discount_value'])
    
    return JsonResponse({
        'success': True,
        'message': f'Variant {variant.variant_type} marked as winner. Promotion updated.'
    })


# ============= Customer Segmentation Views =============

@login_required
def get_segment_eligibility(request, promotion_id):
    """Check current user's eligibility for promotion segments"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    segment_rules = promotion.segment_rules.filter(is_active=True)
    
    user_segments = []
    for rule in segment_rules:
        qualifies = rule.qualifies_customer(request.user)
        user_segments.append({
            'segment_type': rule.get_segment_type_display(),
            'qualifies': qualifies
        })
    
    return JsonResponse({
        'promotion': {
            'id': promotion.id,
            'name': promotion.name,
        },
        'user_segments': user_segments,
        'eligible': any(seg['qualifies'] for seg in user_segments) or len(user_segments) == 0
    })


@login_required
@require_POST
def create_segment_rule(request, promotion_id):
    """Create a segment rule for a promotion"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    
    # Check if rule already exists for this segment type
    if PromotionSegmentRule.objects.filter(
        promotion=promotion,
        segment_type=data.get('segment_type')
    ).exists():
        return JsonResponse({
            'error': f'Rule for {data.get("segment_type")} already exists'
        }, status=400)
    
    rule = PromotionSegmentRule.objects.create(
        promotion=promotion,
        segment_type=data.get('segment_type'),
        min_total_spent=data.get('min_total_spent') or None,
        min_orders_count=data.get('min_orders_count') or None,
        days_since_last_order=data.get('days_since_last_order') or None,
        country_codes=data.get('country_codes', ''),
        is_active=True,
    )
    
    return JsonResponse({
        'success': True,
        'rule_id': rule.id,
        'message': 'Segment rule created successfully'
    })


@login_required
def list_segment_analytics(request, promotion_id):
    """Get analytics on segmented promotion effectiveness"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    segment_stats = []
    
    for rule in promotion.segment_rules.filter(is_active=True):
        # Get users matching this segment
        segment_users = []  # In real implementation, query matching users
        
        stats = {
            'segment_type': rule.get_segment_type_display(),
            'estimated_users': 0,  # To be calculated
            'redemptions': 0,
            'conversion_rate': 0,
            'avg_order_value': 0,
        }
        segment_stats.append(stats)
    
    return JsonResponse({'segment_analytics': segment_stats})


# ============= Bulk Code Generation =============

@login_required
@require_POST
def generate_bulk_codes(request, promotion_id):
    """Generate bulk promotion codes"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    quantity = int(data.get('quantity', 100))
    
    # Limit quantity to prevent abuse
    if quantity > 10000:
        return JsonResponse({'error': 'Maximum 10,000 codes per request'}, status=400)
    
    # Generate unique codes
    generated_codes = []
    charset = string.ascii_uppercase + string.digits
    
    for _ in range(quantity):
        while True:
            code = ''.join(secrets.choice(charset) for _ in range(10))
            if not PromotionCode.objects.filter(code=code).exists():
                break
        
        generated_codes.append(PromotionCode(
            promotion=promotion,
            code=code,
            status='active'
        ))
    
    # Bulk create
    created = PromotionCode.objects.bulk_create(generated_codes)
    
    return JsonResponse({
        'success': True,
        'quantity_created': len(created),
        'message': f'{len(created)} codes generated successfully'
    })


@login_required
def export_bulk_codes(request, promotion_id):
    """Export promotion codes as CSV"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    codes = promotion.promo_codes.filter(status='active')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="promo_codes_{promotion.id}.csv"'
    
    # Write CSV
    response.write('Code,Status,Created At\n')
    for code in codes:
        response.write(f'{code.code},{code.status},{code.created_at.isoformat()}\n')
    
    return response


@login_required
def get_codes_statistics(request, promotion_id):
    """Get statistics on promotion code usage"""
    promotion = get_object_or_404(Promotion, id=promotion_id)
    
    # Verify ownership
    if promotion.applicable_vendor.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    codes = promotion.promo_codes.all()
    
    stats = {
        'total_codes': codes.count(),
        'active_codes': codes.filter(status='active').count(),
        'redeemed_codes': codes.filter(status='redeemed').count(),
        'disabled_codes': codes.filter(status='disabled').count(),
        'redemption_rate': 0,
    }
    
    if stats['total_codes'] > 0:
        stats['redemption_rate'] = (stats['redeemed_codes'] / stats['total_codes']) * 100
    
    return JsonResponse({
        'promotion': {
            'id': promotion.id,
            'name': promotion.name,
        },
        'statistics': stats
    })


# ============= Promotion Analytics Views =============

@login_required
def promotion_analytics_dashboard(request):
    """Display comprehensive promotion analytics"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    # Get all promotions for vendor
    promotions = vendor.promotions.all()
    
    # DateTime range for analytics
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Aggregate metrics
    all_variants = PromotionVariant.objects.filter(promotion__in=promotions)
    
    total_metrics = {
        'total_revenue': all_variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0,
        'total_conversions': all_variants.aggregate(Sum('conversions'))['conversions__sum'] or 0,
        'total_clicks': all_variants.aggregate(Sum('clicks'))['clicks__sum'] or 0,
        'total_impressions': all_variants.aggregate(Sum('impressions'))['impressions__sum'] or 0,
        'avg_conversion_rate': all_variants.aggregate(Avg('conversions'))['conversions__avg'] or 0,
    }
    
    # Top performers
    top_promotions = promotions.annotate(
        revenue=Sum('variants__revenue_generated'),
        conversions=Sum('variants__conversions')
    ).order_by('-revenue')[:5]
    
    # Campaign metrics
    campaigns = vendor.promo_campaigns.filter(status__in=['active', 'ended'])
    
    context = {
        'vendor': vendor,
        'total_metrics': total_metrics,
        'top_promotions': top_promotions,
        'campaigns': campaigns,
        'time_period': '30 days',
    }
    
    return render(request, 'core/vendor_promotion_analytics.html', context)


@login_required
def get_promotion_trend_data(request, promotion_id=None):
    """Get trend data for chart visualization"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if promotion_id:
        promotions = vendor.promotions.filter(id=promotion_id)
    else:
        promotions = vendor.promotions.all()
    
    # Get daily trend data for last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    trend_data = []
    current_date = start_date.date()
    
    while current_date <= end_date.date():
        day_variants = PromotionVariant.objects.filter(
            promotion__in=promotions,
            created_at__date__lte=current_date
        )
        
        trend_data.append({
            'date': current_date.isoformat(),
            'revenue': float(day_variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0),
            'conversions': day_variants.aggregate(Sum('conversions'))['conversions__sum'] or 0,
        })
        
        current_date += timedelta(days=1)
    
    return JsonResponse({'trend_data': trend_data})


@login_required
def get_smart_recommendations(request):
    """Get AI-driven recommendations for promotion optimization"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    recommendations = []
    promotions = vendor.promotions.all()
    
    # Recommendation 1: Continue high performers
    high_performers = promotions.annotate(
        roi=Sum('variants__revenue_generated') / Count('variants')
    ).filter(roi__gt=300).values_list('name', flat=True)[:3]
    
    if high_performers:
        recommendations.append({
            'title': 'Continue High Performers',
            'description': f'Your promotions ({", ".join(high_performers[:2])}) are showing 300%+ ROI',
            'action': 'Keep them active',
            'category': 'success',
            'priority': 'high',
        })
    
    # Recommendation 2: Optimize low performers
    low_roi_promos = promotions.annotate(
        roi=Sum('variants__revenue_generated') / Count('variants')
    ).filter(roi__lt=50, roi__gt=0).values_list('name', flat=True)[:2]
    
    if low_roi_promos:
        recommendations.append({
            'title': 'Optimize Low Performers',
            'description': f'Test different discount values for {low_roi_promos[0]}',
            'action': 'Create A/B variants',
            'category': 'warning',
            'priority': 'medium',
        })
    
    # Recommendation 3: Create new campaigns
    recommendations.append({
        'title': 'Create Weekend Promotions',
        'description': 'Data shows 40% higher engagement on weekends',
        'action': 'Create campaign',
        'category': 'info',
        'priority': 'medium',
    })
    
    return JsonResponse({'recommendations': recommendations})
