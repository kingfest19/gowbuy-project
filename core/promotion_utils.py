"""
Utility functions for promotion management.
Common operations, helper methods, and convenience functions.
"""
import random
import secrets
import string
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q, F
from django.core.exceptions import ValidationError

from core.models import (
    Promotion, PromotionVariant, PromotionSegmentRule,
    PromotionCode, PromotionCampaign, Order, CartItem
)


# ============= A/B Testing Helpers =============

def create_ab_test(promotion, variant_b_discount, variant_b_description=""):
    """
    Create an A/B test for a promotion.
    
    Args:
        promotion: Promotion instance
        variant_b_discount: Decimal discount value for variant B
        variant_b_description: Optional description for variant B
    
    Returns:
        tuple: (variant_a, variant_b)
    
    Raises:
        ValidationError: If variants already exist
    """
    if promotion.variants.exists():
        raise ValidationError(f"Promotion {promotion.id} already has variants")
    
    # Create variant A (control)
    variant_a = PromotionVariant.objects.create(
        promotion=promotion,
        variant_type='A',
        discount_value=promotion.discount_value,
        description='Control group (original value)'
    )
    
    # Create variant B (test)
    variant_b = PromotionVariant.objects.create(
        promotion=promotion,
        variant_type='B',
        discount_value=variant_b_discount,
        description=variant_b_description or f'Test group ({variant_b_discount}% off)'
    )
    
    return variant_a, variant_b


def get_random_variant(promotion):
    """
    Get a random variant for a promotion (for A/B testing).
    Returns variant with 50/50 split.
    
    Args:
        promotion: Promotion instance
    
    Returns:
        PromotionVariant: Random variant or None if no variants
    """
    variants = promotion.variants.all()
    if not variants.exists():
        return None
    
    return random.choice(list(variants))


def select_variant_by_weight(promotion, weights=None):
    """
    Select variant based on custom weights (for weighted A/B testing).
    
    Args:
        promotion: Promotion instance
        weights: Dict mapping variant_type to weight
                 e.g. {'A': 70, 'B': 30} for 70/30 split
    
    Returns:
        PromotionVariant: Selected variant
    """
    if not weights:
        # Default 50/50
        weights = {v.variant_type: 50 for v in promotion.variants.all()}
    
    variants = list(promotion.variants.all())
    total_weight = sum(weights.values())
    
    # Normalize weights
    probabilities = [weights.get(v.variant_type, 50) / total_weight for v in variants]
    
    return random.choices(variants, weights=probabilities, k=1)[0]


def get_variant_performance(promotion):
    """
    Get performance comparison between variants.
    
    Args:
        promotion: Promotion instance
    
    Returns:
        dict: Performance metrics for each variant
    """
    variants = promotion.variants.all()
    performance = {}
    
    for variant in variants:
        performance[variant.variant_type] = {
            'discount_value': float(variant.discount_value),
            'impressions': variant.impressions,
            'clicks': variant.clicks,
            'conversions': variant.conversions,
            'revenue': float(variant.revenue_generated),
            'ctr': round(variant.ctr, 2),
            'conversion_rate': round(variant.conversion_rate, 2),
            'avg_order_value': round(float(variant.avg_order_value), 2),
            'roi': round((variant.revenue_generated / max(variant.conversions, 1)) * 100, 2),
        }
    
    return performance


def determine_winner(promotion):
    """
    Automatically determine and mark the winning variant based on conversion rate.
    
    Args:
        promotion: Promotion instance
    
    Returns:
        PromotionVariant: Winner variant
    
    Raises:
        ValidationError: If no variants or insufficient data
    """
    variants = promotion.variants.all()
    
    if not variants.exists():
        raise ValidationError("Promotion has no variants")
    
    # Filter variants with at least 10 conversions
    viable_variants = [v for v in variants if v.conversions >= 10]
    
    if not viable_variants:
        raise ValidationError("No variant has sufficient conversion data (min 10)")
    
    # Find variant with highest conversion rate
    winner = max(viable_variants, key=lambda v: v.conversion_rate)
    
    # Mark as winner and update promotion
    PromotionVariant.objects.filter(promotion=promotion).update(is_winner=False)
    winner.is_winner = True
    winner.save(update_fields=['is_winner'])
    
    # Update promotion discount
    promotion.discount_value = winner.discount_value
    promotion.save(update_fields=['discount_value'])
    
    return winner


# ============= Customer Segmentation Helpers =============

def get_segment_customers(segment_rule):
    """
    Get all customers matching a segment rule.
    
    Args:
        segment_rule: PromotionSegmentRule instance
    
    Returns:
        QuerySet: Users matching the segment
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    segment_type = segment_rule.segment_type
    users_qs = User.objects.all()
    
    if segment_type == 'new_customers':
        # Users with 0-1 orders
        user_ids = Order.objects.values('customer').annotate(
            order_count=Count('id')
        ).filter(order_count__lte=1).values_list('customer', flat=True)
        return users_qs.filter(id__in=user_ids)
    
    elif segment_type == 'high_value':
        # Users with high lifetime spending
        user_ids = Order.objects.filter(
            status='completed'
        ).values('customer').annotate(
            total_spent=Sum('total_amount')
        ).filter(total_spent__gte=segment_rule.min_total_spent or 0).values_list(
            'customer', flat=True
        )
        return users_qs.filter(id__in=user_ids)
    
    elif segment_type == 'abandoned_cart':
        # Users with items in cart
        user_ids = CartItem.objects.values_list('user', flat=True).distinct()
        return users_qs.filter(id__in=user_ids)
    
    elif segment_type == 'first_time':
        # Users with no orders
        user_ids = Order.objects.values_list('customer', flat=True).distinct()
        return users_qs.exclude(id__in=user_ids)
    
    elif segment_type == 'geographic':
        # Users in specified countries
        countries = segment_rule.country_codes.split(',')
        return users_qs.filter(userprofile__location__in=countries)
    
    return users_qs


def get_segment_size(segment_rule):
    """
    Get the number of customers in a segment.
    
    Args:
        segment_rule: PromotionSegmentRule instance
    
    Returns:
        int: Number of customers
    """
    return get_segment_customers(segment_rule).count()


def check_multiple_segments(user, promotion):
    """
    Check which segments a user qualifies for.
    
    Args:
        user: User instance
        promotion: Promotion instance
    
    Returns:
        list: List of segment types user qualifies for
    """
    rules = promotion.segment_rules.filter(is_active=True)
    qualified_segments = []
    
    for rule in rules:
        if rule.qualifies_customer(user):
            qualified_segments.append(rule.segment_type)
    
    return qualified_segments


# ============= Bulk Code Generation Helpers =============

def generate_code(prefix='', length=10, charset=None):
    """
    Generate a single promotion code.
    
    Args:
        prefix: Optional prefix (e.g., 'SUM' for SUMMER20-XXXXX)
        length: Length of random part
        charset: Character set (default: uppercase + digits)
    
    Returns:
        str: Generated code
    """
    if not charset:
        charset = string.ascii_uppercase + string.digits
    
    code = ''.join(secrets.choice(charset) for _ in range(length))
    return f"{prefix}{code}" if prefix else code


def generate_bulk_codes(promotion, quantity, prefix='', length=10):
    """
    Generate and save bulk promotion codes.
    
    Args:
        promotion: Promotion instance
        quantity: Number of codes to generate
        prefix: Optional prefix for codes
        length: Length of random part
    
    Returns:
        list: Created PromotionCode instances
    
    Raises:
        ValidationError: If quantity > 10000
    """
    if quantity > 10000:
        raise ValidationError("Maximum 10,000 codes per batch")
    
    codes = []
    existing_codes = set(
        PromotionCode.objects.values_list('code', flat=True)
    )
    
    while len(codes) < quantity:
        code = generate_code(prefix, length)
        if code not in existing_codes:
            codes.append(PromotionCode(promotion=promotion, code=code))
            existing_codes.add(code)
    
    # Bulk create and return
    return PromotionCode.objects.bulk_create(codes)


def export_codes_as_csv_data(promotion, status=None):
    """
    Export promotion codes as CSV data (ready to write).
    
    Args:
        promotion: Promotion instance
        status: Filter by status (optional)
    
    Returns:
        str: CSV-formatted string
    """
    codes_qs = promotion.promo_codes.all()
    if status:
        codes_qs = codes_qs.filter(status=status)
    
    csv_lines = ['Code,Status,Redeemed By,Redeemed At,Created At']
    
    for code in codes_qs:
        csv_lines.append(
            f'{code.code},'
            f'{code.get_status_display()},'
            f'{code.redeemed_by.username if code.redeemed_by else "N/A"},'
            f'{code.redeemed_at or "N/A"},'
            f'{code.created_at}'
        )
    
    return '\n'.join(csv_lines)


def get_codes_statistics(promotion):
    """
    Get comprehensive code usage statistics.
    
    Args:
        promotion: Promotion instance
    
    Returns:
        dict: Code statistics
    """
    codes = promotion.promo_codes.all()
    
    total = codes.count()
    active = codes.filter(status='active').count()
    redeemed = codes.filter(status='redeemed').count()
    disabled = codes.filter(status='disabled').count()
    expired = codes.filter(status='expired').count()
    
    return {
        'total_codes': total,
        'active_codes': active,
        'redeemed_codes': redeemed,
        'disabled_codes': disabled,
        'expired_codes': expired,
        'redemption_rate': (redeemed / total * 100) if total > 0 else 0,
        'active_percentage': (active / total * 100) if total > 0 else 0,
    }


# ============= Campaign Management Helpers =============

def create_campaign(vendor, name, promotions, start_date, end_date, emoji='🎉', description=''):
    """
    Create a new promotion campaign.
    
    Args:
        vendor: Vendor instance
        name: Campaign name
        promotions: List of Promotion instances
        start_date: Start datetime
        end_date: End datetime
        emoji: Optional emoji
        description: Optional description
    
    Returns:
        PromotionCampaign: Created campaign
    """
    campaign = PromotionCampaign.objects.create(
        vendor=vendor,
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        emoji=emoji,
        status='draft'
    )
    
    campaign.promotions.set(promotions)
    return campaign


def get_active_campaigns(vendor=None):
    """
    Get currently active campaigns.
    
    Args:
        vendor: Optional vendor filter
    
    Returns:
        QuerySet: Active campaigns
    """
    now = timezone.now()
    qs = PromotionCampaign.objects.filter(
        status='active',
        start_date__lte=now,
        end_date__gte=now
    )
    
    if vendor:
        qs = qs.filter(vendor=vendor)
    
    return qs


def get_upcoming_campaigns(vendor=None, days=7):
    """
    Get campaigns starting within specified days.
    
    Args:
        vendor: Optional vendor filter
        days: Number of days to look ahead
    
    Returns:
        QuerySet: Upcoming campaigns
    """
    now = timezone.now()
    future = now + timedelta(days=days)
    
    qs = PromotionCampaign.objects.filter(
        status='scheduled',
        start_date__range=[now, future]
    )
    
    if vendor:
        qs = qs.filter(vendor=vendor)
    
    return qs


def campaign_performance_summary(campaign):
    """
    Get performance summary for a campaign.
    
    Args:
        campaign: PromotionCampaign instance
    
    Returns:
        dict: Performance summary
    """
    metrics = campaign.get_performance_metrics()
    
    total_revenue = metrics['total_revenue']
    total_conversions = metrics['total_conversions']
    
    summary = {
        'status': campaign.status,
        'is_active_now': campaign.is_active_now,
        'promotion_count': campaign.promotion_count,
        'total_revenue': float(total_revenue),
        'total_conversions': total_conversions,
        'conversion_rate': metrics['conversion_rate'],
        'avg_revenue_per_conversion': float(
            total_revenue / max(total_conversions, 1)
        ),
        'roi_estimate': 'Calculating...' if total_conversions == 0 else f"{metrics['conversion_rate']:.1f}%"
    }
    
    return summary


# ============= Analytics Helpers =============

def get_promotion_roi(promotion):
    """
    Calculate ROI for a promotion.
    
    Args:
        promotion: Promotion instance
    
    Returns:
        dict: ROI metrics
    """
    variants = promotion.variants.all()
    
    total_revenue = variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0
    total_conversions = variants.aggregate(Sum('conversions'))['conversions__sum'] or 0
    
    # Estimate cost: assume 10% of discount value per conversion
    estimated_cost = (
        (promotion.discount_value * total_conversions) * Decimal('0.10')
    )
    
    roi = ((total_revenue - estimated_cost) / max(estimated_cost, 1)) * 100 if estimated_cost > 0 else 0
    
    return {
        'total_revenue': float(total_revenue),
        'total_conversions': total_conversions,
        'estimated_cost': float(estimated_cost),
        'roi_percentage': round(roi, 2),
        'avg_order_value': float(total_revenue / max(total_conversions, 1)) if total_conversions > 0 else 0,
    }


def get_trend_data(promotion, days=30):
    """
    Get trend data for a promotion over time.
    
    Args:
        promotion: Promotion instance
        days: Number of days to analyze
    
    Returns:
        list: Daily trend data
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    trend_data = []
    current = start_date
    
    while current <= end_date:
        variants = promotion.variants.filter(
            created_at__date__lte=current
        )
        
        daily_revenue = variants.aggregate(
            Sum('revenue_generated')
        )['revenue_generated__sum'] or 0
        
        daily_conversions = variants.aggregate(
            Sum('conversions')
        )['conversions__sum'] or 0
        
        trend_data.append({
            'date': current.isoformat(),
            'revenue': float(daily_revenue),
            'conversions': daily_conversions,
        })
        
        current += timedelta(days=1)
    
    return trend_data


def get_smart_recommendations(vendor):
    """
    Generate smart recommendations for promotion optimization.
    
    Args:
        vendor: Vendor instance
    
    Returns:
        list: Recommendation objects
    """
    recommendations = []
    promotions = vendor.promotions.all()
    
    # Rec 1: High performers
    high_performers = []
    for promo in promotions:
        roi_data = get_promotion_roi(promo)
        if roi_data['roi_percentage'] > 300:
            high_performers.append(promo.name)
    
    if high_performers:
        recommendations.append({
            'title': 'Continue High Performers',
            'description': f'{", ".join(high_performers[:2])} showing 300%+ ROI',
            'action': 'Keep active',
            'priority': 'high',
            'emoji': '📈'
        })
    
    # Rec 2: Low performers
    low_performers = []
    for promo in promotions:
        if promo.usage_count > 0:
            roi_data = get_promotion_roi(promo)
            if 0 < roi_data['roi_percentage'] < 50:
                low_performers.append(promo.name)
    
    if low_performers:
        recommendations.append({
            'title': 'Optimize Low Performers',
            'description': f'Test different discount for {low_performers[0]}',
            'action': 'Create A/B test',
            'priority': 'medium',
            'emoji': '⚡'
        })
    
    # Rec 3: Test new segments
    recommendations.append({
        'title': 'Target New Segments',
        'description': 'Create loyalty program exclusive discount',
        'action': 'Add segment rule',
        'priority': 'medium',
        'emoji': '👥'
    })
    
    return recommendations


# ============= Validation Helpers =============

def validate_promotion_code(code):
    """
    Validate and check promotion code availability.
    
    Args:
        code: Code string
    
    Returns:
        dict: Validation result
    
    Raises:
        ValidationError: If code invalid
    """
    if not code or len(code) < 3:
        raise ValidationError("Code must be at least 3 characters")
    
    if not code.isalnum():
        raise ValidationError("Code can only contain letters and numbers")
    
    if PromotionCode.objects.filter(code__iexact=code).exists():
        raise ValidationError(f"Code '{code}' already exists")
    
    return {'valid': True, 'code': code.upper()}


def validate_discount_value(promo_type, value):
    """
    Validate discount value based on promotion type.
    
    Args:
        promo_type: 'percentage' or 'fixed_amount'
        value: Decimal value
    
    Returns:
        dict: Validation result
    
    Raises:
        ValidationError: If value invalid
    """
    if value <= 0:
        raise ValidationError("Discount must be greater than 0")
    
    if promo_type == 'percentage' and value > 100:
        raise ValidationError("Percentage discount cannot exceed 100%")
    
    return {'valid': True, 'value': value}


# ============= Batch Operation Helpers =============

def activate_all_campaigns_in_range(vendor, start_date, end_date):
    """
    Activate all scheduled campaigns within date range.
    
    Args:
        vendor: Vendor instance
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        int: Number of campaigns activated
    """
    updated = PromotionCampaign.objects.filter(
        vendor=vendor,
        status='scheduled',
        start_date__range=[start_date, end_date]
    ).update(status='active')
    
    return updated


def expire_old_codes(promotion, days=30):
    """
    Mark unused codes as expired after specified days.
    
    Args:
        promotion: Promotion instance
        days: Days since creation
    
    Returns:
        int: Number of codes expired
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    updated = PromotionCode.objects.filter(
        promotion=promotion,
        status='active',
        created_at__lt=cutoff_date
    ).update(status='expired')
    
    return updated
