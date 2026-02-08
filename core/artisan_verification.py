"""
Artisan/Handmade Product Verification System

This module handles verification for handmade, artisan, and resold products.
Focuses on vendor reputation, reviews, and transparency rather than strict 
documentation requirements.

Philosophy: "Trust but Verify" - Lower barrier to entry, natural reputation-based filtering
"""

import logging
from decimal import Decimal
from django_countries import countries

logger = logging.getLogger(__name__)


class ArtisanVerificationEngine:
    """
    Verification engine for handmade, artisan, and resold products.
    
    Key Difference from OriginVerificationEngine:
    - Doesn't require proof of creation
    - Supports vendor as creator OR reseller
    - Reputation-based scoring for established vendors
    - Simple transparency for high-value items
    """
    
    # Acquisition source types
    ACQUISITION_TYPES = {
        'created': 'I made/created this item',
        'purchased_new': 'Purchased new from manufacturer/brand',
        'purchased_used': 'Purchased used/secondhand',
        'consignment': 'On consignment from creator',
        'estate_sale': 'Estate sale/auction',
        'inherited': 'Inherited/gifted',
        'sourced': 'Sourced from verified supplier',
        'other': 'Other (please explain)',
    }
    
    # Price thresholds for additional requirements
    THRESHOLD_HIGH_VALUE = Decimal('500.00')
    THRESHOLD_LUXURY = Decimal('2000.00')
    
    # Vendor tier criteria
    VENDOR_TIERS = {
        'new': {'min_sales': 0, 'min_rating': 0, 'trust_score': 50},
        'verified': {'min_sales': 3, 'min_rating': 4.0, 'trust_score': 70},
        'trusted': {'min_sales': 10, 'min_rating': 4.5, 'trust_score': 85},
        'master': {'min_sales': 50, 'min_rating': 4.8, 'trust_score': 95},
    }
    
    def verify_artisan_product(self, product_data):
        """
        Main verification method for artisan/handmade products.
        
        Args:
            product_data (dict): Product information including:
                - price: Product price
                - vendor_sales: Number of previous sales
                - vendor_rating: Average rating (0-5)
                - product_title: Product name
                - category: Product category
                - acquisition_type: How vendor acquired item
                - acquisition_details: Explanation/story
                - has_certificate: Has certificate of authenticity
                - has_provenance: Has provenance documentation
                - image_count: Number of product photos
                - vendor_is_creator: Boolean - is vendor the creator?
        
        Returns:
            dict: Verification result with score, feedback, and recommendations
        """
        try:
            # Get vendor trust tier
            vendor_tier = self._get_vendor_tier(
                product_data.get('vendor_sales', 0),
                product_data.get('vendor_rating', 0)
            )
            
            # Start with vendor trust score
            score = self.VENDOR_TIERS[vendor_tier]['trust_score']
            
            # Add points for documentation quality
            score += self._check_product_documentation(product_data)
            
            # Price threshold checks
            price = Decimal(str(product_data.get('price', 0)))
            if price >= self.THRESHOLD_LUXURY:
                score += self._check_luxury_item_requirements(product_data)
            elif price >= self.THRESHOLD_HIGH_VALUE:
                score += self._check_high_value_requirements(product_data)
            else:
                score += self._check_basic_requirements(product_data)
            
            # Cap score at 100
            score = min(score, 100)
            
            # Determine verification status
            if score >= 75:
                status = 'APPROVED'
                confidence = 'High'
            elif score >= 60:
                status = 'APPROVED_WITH_REVIEW'
                confidence = 'Medium'
            else:
                status = 'NEEDS_REVIEW'
                confidence = 'Low'
            
            return {
                'valid': status in ['APPROVED', 'APPROVED_WITH_REVIEW'],
                'score': int(score),
                'confidence': confidence,
                'status': status,
                'vendor_tier': vendor_tier,
                'reasoning': self._get_reasoning(product_data, vendor_tier, score),
                'requirements_met': self._get_requirements_summary(product_data, price),
                'next_steps': self._get_next_steps(status, product_data),
                'vendor_badge': self._get_vendor_badge(vendor_tier),
                'visibility_boost': self._get_visibility_boost(product_data, score),
            }
        
        except Exception as e:
            logger.error(f"Artisan verification error: {str(e)}")
            return {
                'valid': True,  # Default to allow on error
                'score': 50,
                'confidence': 'Unknown',
                'status': 'APPROVED_WITH_REVIEW',
                'reasoning': 'Product verification in progress. Manual review may be needed.',
                'requirements_met': [],
                'next_steps': ['Please wait for admin review'],
            }
    
    def _get_vendor_tier(self, sales_count, rating):
        """Determine vendor trust tier based on sales and rating."""
        if sales_count >= 50 and rating >= 4.8:
            return 'master'
        elif sales_count >= 10 and rating >= 4.5:
            return 'trusted'
        elif sales_count >= 3 and rating >= 4.0:
            return 'verified'
        else:
            return 'new'
    
    def _check_basic_requirements(self, product_data):
        """Check basic requirements for <$500 items. Max +25 points."""
        points = 0
        
        # Good photos (3+)
        image_count = product_data.get('image_count', 0)
        if image_count >= 5:
            points += 15
        elif image_count >= 3:
            points += 10
        else:
            points -= 5  # Penalize low photo count
        
        # Good description
        description_length = len(product_data.get('description', ''))
        if description_length >= 200:
            points += 10
        elif description_length >= 100:
            points += 5
        
        return points
    
    def _check_high_value_requirements(self, product_data):
        """
        Check requirements for $500-$2000 items.
        Main requirement: Transparency on acquisition.
        Max +20 points.
        """
        points = 0
        
        # Acquisition info provided (main requirement)
        acquisition_type = product_data.get('acquisition_type')
        if acquisition_type:
            # All acquisition types are acceptable
            points += 15
            
            # Bonus if vendor is creator
            if acquisition_type == 'created':
                points += 10
            # Bonus if detailed explanation provided
            elif product_data.get('acquisition_details', ''):
                points += 5
        else:
            # No acquisition info = problem
            points -= 10
        
        # Bonus for certificate if provided
        if product_data.get('has_certificate'):
            points += 10
        
        return points
    
    def _check_luxury_item_requirements(self, product_data):
        """
        Check requirements for >$2000 luxury/investment items.
        Requirements: Acquisition info + provenance for non-branded.
        Max +15 points.
        """
        points = 0
        
        # Acquisition info (required)
        acquisition_type = product_data.get('acquisition_type')
        if acquisition_type:
            points += 10
        else:
            points -= 10
        
        # Provenance details if handmade/artisan
        if acquisition_type == 'created':
            if product_data.get('has_provenance'):
                points += 10
            else:
                points += 5  # Some credit for artist statement
        
        # Certificate if available
        if product_data.get('has_certificate'):
            points += 10
        
        return points
    
    def _check_product_documentation(self, product_data):
        """Check product documentation quality. Max +15 points."""
        points = 0
        
        # Title quality
        title = product_data.get('product_title', '')
        if len(title) >= 15:
            points += 3
        
        # Description quality
        description = product_data.get('description', '')
        if len(description) >= 300:
            points += 7
        elif len(description) >= 150:
            points += 4
        
        # Category properly selected
        if product_data.get('category'):
            points += 2
        
        # Has images
        if product_data.get('image_count', 0) >= 3:
            points += 3
        
        return points
    
    def _get_reasoning(self, product_data, vendor_tier, score):
        """Generate human-readable reasoning for the score."""
        reasons = []
        
        # Vendor tier
        tier_messages = {
            'new': 'This is a new vendor on the platform',
            'verified': 'This vendor is verified with some sales history',
            'trusted': 'This vendor has a good reputation',
            'master': 'This vendor is a trusted community member',
        }
        reasons.append(tier_messages.get(vendor_tier, 'Vendor status checked'))
        
        # Price-based messaging
        price = Decimal(str(product_data.get('price', 0)))
        if price >= 2000:
            acquisition = product_data.get('acquisition_type', '')
            if acquisition:
                reasons.append(f"High-value item: Acquisition documented ({acquisition})")
            else:
                reasons.append("High-value item: Waiting for acquisition details")
        elif price >= 500:
            acquisition = product_data.get('acquisition_type', '')
            if acquisition:
                reasons.append(f"Item source identified: {self.ACQUISITION_TYPES.get(acquisition, acquisition)}")
            else:
                reasons.append("Please indicate how you acquired this item")
        
        # Photo quality
        image_count = product_data.get('image_count', 0)
        if image_count >= 5:
            reasons.append(f"Good documentation: {image_count} clear photos")
        elif image_count >= 3:
            reasons.append(f"Standard documentation: {image_count} photos")
        else:
            reasons.append(f"Limited photos: Consider adding more ({image_count} current)")
        
        return " | ".join(reasons)
    
    def _get_requirements_summary(self, product_data, price):
        """Summarize which requirements are met."""
        met = []
        
        if product_data.get('image_count', 0) >= 3:
            met.append(f"✓ Photos ({product_data.get('image_count', 0)} provided)")
        else:
            met.append(f"✗ Photos ({product_data.get('image_count', 0)}/3)")
        
        if product_data.get('description', ''):
            met.append("✓ Description")
        else:
            met.append("✗ Description")
        
        if price >= 500:
            if product_data.get('acquisition_type'):
                met.append(f"✓ Acquisition ({product_data.get('acquisition_type')})")
            else:
                met.append("✗ Acquisition info needed")
        
        if price >= 2000:
            if product_data.get('has_certificate'):
                met.append("✓ Certificate of authenticity")
            elif product_data.get('has_provenance'):
                met.append("✓ Provenance documentation")
        
        return met
    
    def _get_next_steps(self, status, product_data):
        """Get recommended next steps for vendor."""
        if status == 'APPROVED':
            return [
                "✓ Your product is approved and ready to list!",
                "💡 Tip: Products with more photos get more visibility",
            ]
        elif status == 'APPROVED_WITH_REVIEW':
            return [
                "✓ Your product is approved and queued for listing",
                "📋 An admin may review high-value items (24-48 hours)",
                "💡 Tip: You can edit and add more details while we review",
            ]
        else:
            price = Decimal(str(product_data.get('price', 0)))
            if price >= 500 and not product_data.get('acquisition_type'):
                return [
                    "⚠️ Please tell us where you got this item",
                    "📝 Our question: How did you acquire this product?",
                    "💭 Examples: 'I made it', 'Bought from supplier', 'Estate sale'",
                ]
            else:
                return [
                    "📋 Your product is being reviewed by our team",
                    "⏱️ Expected time: 24-48 hours",
                    "📧 We'll notify you when it's approved",
                ]
    
    def _get_vendor_badge(self, vendor_tier):
        """Get vendor badge for display."""
        badges = {
            'new': None,
            'verified': {
                'text': 'Verified Seller',
                'color': 'blue',
                'icon': '✓',
            },
            'trusted': {
                'text': 'Trusted Artisan',
                'color': 'green',
                'icon': '✓✓',
            },
            'master': {
                'text': 'Master Craftsman',
                'color': 'gold',
                'icon': '★',
            },
        }
        return badges.get(vendor_tier)
    
    def _get_visibility_boost(self, product_data, score):
        """Calculate visibility/ranking boost based on score and documentation."""
        boost = 1.0  # Base visibility
        
        # Score-based boost
        if score >= 80:
            boost += 0.3
        elif score >= 70:
            boost += 0.15
        
        # Documentation boost
        if product_data.get('image_count', 0) >= 5:
            boost += 0.1
        
        if product_data.get('acquisition_type') == 'created':
            boost += 0.15  # Boost for creators
        
        # Cap at 2x visibility
        return min(boost, 2.0)
    
    def get_acquisition_options(self):
        """Return acquisition type options for forms."""
        return [
            ('created', 'I made/created this item'),
            ('purchased_new', 'Purchased new from manufacturer/brand'),
            ('purchased_used', 'Purchased used/secondhand'),
            ('consignment', 'On consignment from creator'),
            ('estate_sale', 'Estate sale/auction'),
            ('inherited', 'Inherited/gifted'),
            ('sourced', 'Sourced from verified supplier'),
            ('other', 'Other (please explain)'),
        ]
    
    def validate_acquisition_info(self, acquisition_type, details, price):
        """
        Validate acquisition information for high-value items.
        
        Returns: (is_valid, message)
        """
        if Decimal(str(price)) < self.THRESHOLD_HIGH_VALUE:
            # Not required for low-value items
            return True, None
        
        if not acquisition_type:
            return False, "Please select how you acquired this item"
        
        if acquisition_type == 'other' and (not details or len(details) < 20):
            return False, "Please provide more details about how you acquired this item (minimum 20 characters)"
        
        return True, None
