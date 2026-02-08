"""
Origin Verification Engine for GOWBUY Marketplace

This module validates and verifies product origin claims made by vendors.
It uses rule-based matching against product details to detect suspicious or mismatched origins.
"""

import logging
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django_countries import countries
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class OriginVerificationEngine:
    """
    Validates vendor-claimed product origins against:
    - Product manufacturer information
    - Brand location data
    - Certification origins
    - Electronic device identifiers
    - Historical product origin patterns
    """
    
    # Brand-to-country mapping (common brands)
    BRAND_COUNTRY_MAP = {
        # Electronics & Tech
        'apple': 'US',
        'samsung': 'KR',
        'lg': 'KR',
        'sony': 'JP',
        'toshiba': 'JP',
        'panasonic': 'JP',
        'canon': 'JP',
        'nikon': 'JP',
        'hp': 'US',
        'dell': 'US',
        'lenovo': 'CN',
        'asus': 'TW',
        'acer': 'TW',
        'msi': 'TW',
        'intel': 'US',
        'amd': 'US',
        'nvidia': 'US',
        
        # Luxury Brands
        'louis vuitton': 'FR',
        'gucci': 'IT',
        'prada': 'IT',
        'chanel': 'FR',
        'hermes': 'FR',
        'rolex': 'CH',
        'omega': 'CH',
        'cartier': 'FR',
        'dior': 'FR',
        
        # Clothing & Fashion
        'nike': 'US',
        'adidas': 'DE',
        'puma': 'DE',
        'levi': 'US',
        'tommy hilfiger': 'US',
        'ralph lauren': 'US',
        'zara': 'ES',
        'h&m': 'SE',
        'uniqlo': 'JP',
        
        # Automotive
        'bmw': 'DE',
        'mercedes': 'DE',
        'audi': 'DE',
        'volkswagen': 'DE',
        'porsche': 'DE',
        'ferrari': 'IT',
        'lamborghini': 'IT',
        'rolls royce': 'GB',
        'bentley': 'GB',
        'jaguar': 'GB',
        'tesla': 'US',
        'toyota': 'JP',
        'honda': 'JP',
        'nissan': 'JP',
        'mazda': 'JP',
    }
    
    # Device identifier patterns by country
    IMEI_PREFIX_MAPPING = {
        # US manufacturers (Starting with certain prefixes)
        '01': 'US',
        '02': 'US',
        '03': 'US',
        '04': 'US',
        '05': 'US',
        '06': 'US',
        '07': 'US',
        '08': 'US',
        '09': 'US',
        '10': 'US',
        '11': 'US',
        '12': 'US',
        '13': 'US',
        '14': 'US',
        '15': 'US',
        '16': 'US',
        '17': 'US',
        '18': 'US',
        '19': 'US',
        
        # Apple iPhones typically start with:
        '35': 'US',  # Apple
        '86': 'CN',  # China
        '99': 'CN',  # China
    }
    
    # Certification patterns by country
    CERTIFICATION_COUNTRY_HINTS = {
        'fcc': 'US',  # Federal Communications Commission (USA)
        'ce mark': 'EU',  # Conformité Européenne
        'rohs': 'EU',  # Restriction of Hazardous Substances
        'ccc': 'CN',  # China Compulsory Certification
        'kc mark': 'KR',  # Korea Certification
        'pse': 'JP',  # Product Safety Electrical Mark (Japan)
        'jis': 'JP',  # Japanese Industrial Standards
        'csa': 'CA',  # Canadian Standards Association
        'bs': 'GB',  # British Standards
        'as/nzs': 'AU',  # Australian/New Zealand Standards
        'bsi': 'GB',  # British Standards Institution
        'dse': 'IN',  # India
        'inmetro': 'BR',  # Brazil
    }
    
    # Price range indicators by origin (rough guidelines)
    PRICE_PREMIUM_BY_ORIGIN = {
        'US': 1.0,  # Baseline
        'JP': 1.0,
        'DE': 1.0,
        'CH': 1.2,  # Premium
        'IT': 0.9,
        'FR': 1.0,
        'GB': 1.0,
        'SE': 1.0,
        'CN': 0.7,  # Budget
        'IN': 0.6,  # Budget
        'BR': 0.8,
        'MX': 0.8,
    }
    
    def __init__(self):
        self.verification_rules_applied = []
        self.confidence_score = 0.5
        
    def verify_origin(self, product_data: Dict) -> Dict:
        """
        Main verification method. Validates vendor-claimed origin against product details.
        
        Returns a dictionary with:
        - is_suspicious: bool - whether the origin claim is suspicious
        - confidence: float - confidence score (0-1)
        - mismatches: List[str] - list of detected mismatches
        - flags: List[str] - warning flags
        - reasoning: str - explanation of the verification
        - suggested_origin: Optional[str] - alternative origin if detected
        - verification_score: float - 0-100 score
        """
        
        vendor_origin = product_data.get('origin_country')
        if not vendor_origin:
            return {
                'is_suspicious': False,
                'confidence': 0.0,
                'mismatches': [],
                'flags': ['No origin specified'],
                'reasoning': 'Product has no specified origin country.',
                'suggested_origin': None,
                'verification_score': 0
            }
        
        self.verification_rules_applied = []
        mismatches = []
        flags = []
        suggested_origins = []
        
        # Rule 1: Brand-based verification
        brand_origin = self._check_brand_origin(product_data.get('brand', ''), vendor_origin)
        if brand_origin and brand_origin['origin']:
            suggested_origins.append(brand_origin)
            if brand_origin['mismatch']:
                mismatches.append(f"Brand '{product_data.get('brand')}' typically originates from {countries.name(brand_origin['origin'])}")
                flags.append(f"Brand mismatch: Expected {countries.name(brand_origin['origin'])}")
        
        # Rule 2: Manufacturer address verification
        manuf_origin = self._check_manufacturer_origin(product_data, vendor_origin)
        if manuf_origin['mismatch']:
            mismatches.append(manuf_origin['detail'])
            flags.append('Manufacturer location mismatch')
        
        # Rule 3: Device identifier verification (for electronics)
        if product_data.get('product_type') == 'electronics':
            device_check = self._check_device_identifier(product_data, vendor_origin)
            if device_check['mismatch']:
                mismatches.append(device_check['detail'])
                flags.append('Device identifier mismatch')
        
        # Rule 4: Certification verification
        cert_origin = self._check_certifications(product_data, vendor_origin)
        if cert_origin['mismatches']:
            mismatches.extend(cert_origin['mismatches'])
            flags.extend(cert_origin['flags'])
        
        # Rule 5: Price range verification
        price_check = self._check_price_reasonableness(product_data, vendor_origin)
        if price_check['suspicious']:
            flags.append(f"Unusual pricing for origin: {price_check['detail']}")
        
        # Rule 6: Category-specific rules
        category_check = self._check_category_rules(product_data, vendor_origin)
        if category_check['flags']:
            flags.extend(category_check['flags'])
        
        # Calculate verification score
        verification_score = self._calculate_verification_score(
            mismatches=mismatches,
            flags=flags,
            category=product_data.get('category_name', 'General'),
            authenticity_status=product_data.get('authenticity_status', 'unknown')
        )
        
        # Determine if origin is suspicious
        is_suspicious = verification_score < 40  # Below 40 is suspicious
        
        # Select suggested origin (if not matching)
        final_suggested_origin = None
        if mismatches and suggested_origins:
            final_suggested_origin = suggested_origins[0]['origin']
        
        return {
            'is_suspicious': is_suspicious,
            'confidence': 1.0 - (len(mismatches) * 0.1),  # Decrease confidence per mismatch
            'mismatches': mismatches,
            'flags': flags,
            'reasoning': self._generate_reasoning(mismatches, flags, vendor_origin),
            'suggested_origin': final_suggested_origin,
            'verification_score': verification_score,  # 0-100
            'detailed_checks': {
                'brand': brand_origin,
                'manufacturer': manuf_origin,
                'certifications': cert_origin,
                'price': price_check,
                'category': category_check,
            }
        }
    
    def _check_brand_origin(self, brand: str, vendor_origin: str) -> Dict:
        """Check if brand matches typical origin."""
        if not brand:
            return {'origin': None, 'mismatch': False, 'detail': ''}
        
        brand_lower = brand.lower().strip()
        known_origin = self.BRAND_COUNTRY_MAP.get(brand_lower)
        
        if known_origin:
            self.verification_rules_applied.append('brand_check')
            is_mismatch = known_origin != vendor_origin
            return {
                'origin': known_origin,
                'mismatch': is_mismatch,
                'detail': f"Brand '{brand}' typically from {countries.name(known_origin)} but vendor claims {countries.name(vendor_origin)}"
            }
        
        return {'origin': None, 'mismatch': False, 'detail': ''}
    
    def _check_manufacturer_origin(self, product_data: Dict, vendor_origin: str) -> Dict:
        """Check if manufacturer information matches claimed origin."""
        manufacturer = product_data.get('manufacturer', '')
        manufacturer_address = product_data.get('manufacturer_address', '')
        
        if not manufacturer and not manufacturer_address:
            return {'mismatch': False, 'detail': ''}
        
        # Simple heuristic: check if manufacturer_address contains country clues
        address_lower = (manufacturer_address or '').lower()
        manufacturer_lower = (manufacturer or '').lower()
        
        # Look for geographic clues in address
        country_hints = {
            'China': 'CN',
            'Shenzhen': 'CN',
            'Beijing': 'CN',
            'Shanghai': 'CN',
            'Germany': 'DE',
            'Japan': 'JP',
            'Tokyo': 'JP',
            'USA': 'US',
            'New York': 'US',
            'California': 'US',
            'France': 'FR',
            'Italy': 'IT',
            'India': 'IN',
            'Brazil': 'BR',
            'Taiwan': 'TW',
            'South Korea': 'KR',
        }
        
        detected_origin = None
        for clue, country_code in country_hints.items():
            if clue.lower() in address_lower or clue.lower() in manufacturer_lower:
                detected_origin = country_code
                break
        
        if detected_origin and detected_origin != vendor_origin:
            self.verification_rules_applied.append('manufacturer_check')
            return {
                'mismatch': True,
                'detail': f"Manufacturer address/name suggests origin in {countries.name(detected_origin)}"
            }
        
        return {'mismatch': False, 'detail': ''}
    
    def _check_device_identifier(self, product_data: Dict, vendor_origin: str) -> Dict:
        """Check if device identifier matches origin (for electronics)."""
        identifier_type = product_data.get('device_identifier_type', '')
        identifier_value = product_data.get('device_identifier_value', '')
        
        if not identifier_value:
            return {'mismatch': False, 'detail': ''}
        
        if identifier_type == 'imei' or identifier_type == 'mac':
            # Get first 2 digits
            prefix = str(identifier_value)[:2]
            expected_origin = self.IMEI_PREFIX_MAPPING.get(prefix)
            
            if expected_origin and expected_origin != vendor_origin:
                self.verification_rules_applied.append('device_identifier_check')
                return {
                    'mismatch': True,
                    'detail': f"Device identifier prefix suggests origin in {countries.name(expected_origin)}"
                }
        
        return {'mismatch': False, 'detail': ''}
    
    def _check_certifications(self, product_data: Dict, vendor_origin: str) -> Dict:
        """Check if certifications match origin."""
        certifications = (product_data.get('certification_numbers', '') or '').lower()
        
        mismatches = []
        flags = []
        
        for cert_keyword, origin_hint in self.CERTIFICATION_COUNTRY_HINTS.items():
            if cert_keyword in certifications:
                if origin_hint != vendor_origin:
                    mismatches.append(f"Certification '{cert_keyword.upper()}' typically from {countries.name(origin_hint)}")
                    flags.append(f'Certification origin mismatch: {cert_keyword}')
                self.verification_rules_applied.append('certification_check')
        
        return {
            'mismatches': mismatches,
            'flags': flags,
        }
    
    def _check_price_reasonableness(self, product_data: Dict, vendor_origin: str) -> Dict:
        """Check if price is reasonable for the claimed origin."""
        price = product_data.get('price')
        product_type = product_data.get('product_type', 'general')
        
        if not price:
            return {'suspicious': False, 'detail': ''}
        
        try:
            price = Decimal(str(price))
        except:
            return {'suspicious': False, 'detail': ''}
        
        # Very basic price heuristic
        # Premium origins should have higher prices
        multiplier = self.PRICE_PREMIUM_BY_ORIGIN.get(vendor_origin, 1.0)
        
        # If claimed origin is premium but price is very low, flag it
        if multiplier > 1.0 and price < 50:
            self.verification_rules_applied.append('price_check')
            return {
                'suspicious': True,
                'detail': f"Price ${price} seems low for premium origin {countries.name(vendor_origin)}"
            }
        
        # If claimed origin is budget but price is very high, flag it
        if multiplier < 0.9 and price > 1000:
            self.verification_rules_applied.append('price_check')
            return {
                'suspicious': True,
                'detail': f"Price ${price} seems high for budget origin {countries.name(vendor_origin)}"
            }
        
        return {'suspicious': False, 'detail': ''}
    
    def _check_category_rules(self, product_data: Dict, vendor_origin: str) -> Dict:
        """Apply category-specific verification rules."""
        category = product_data.get('category_name', '').lower()
        flags = []
        
        # Rule: Electronics from unusual origins
        if 'electronics' in category or 'gadget' in category:
            common_electronics_origins = ['US', 'JP', 'CN', 'TW', 'KR', 'DE']
            if vendor_origin not in common_electronics_origins:
                flags.append(f'Electronics from {countries.name(vendor_origin)} is uncommon')
                self.verification_rules_applied.append('category_rule_electronics')
        
        # Rule: Luxury items require higher verification
        if 'luxury' in category or 'premium' in category:
            authenticity = product_data.get('authenticity_status', 'unknown')
            if authenticity == 'unknown':
                flags.append('Luxury item without authenticity status set')
                self.verification_rules_applied.append('category_rule_luxury')
        
        # Rule: Food/beverage from expected regions
        if 'food' in category or 'beverage' in category:
            # Most food is local, so any reasonable origin is okay
            pass
        
        return {'flags': flags}
    
    def _calculate_verification_score(self, mismatches: List, flags: List, 
                                     category: str, authenticity_status: str) -> int:
        """
        Calculate overall verification score (0-100).
        Higher = more trustworthy origin claim
        """
        score = 100
        
        # Deduct for mismatches (-15 each)
        score -= len(mismatches) * 15
        
        # Deduct for flags (-5 each)
        score -= len(flags) * 5
        
        # Luxury items need high authenticity
        if 'luxury' in category.lower():
            if authenticity_status == 'unknown':
                score -= 20
            elif authenticity_status == 'replica':
                score -= 50
        
        # Electronics need proper documentation
        if 'electronics' in category.lower():
            if authenticity_status == 'unknown':
                score -= 10
        
        return max(0, min(100, score))  # Clamp between 0-100
    
    def _generate_reasoning(self, mismatches: List, flags: List, vendor_origin: str) -> str:
        """Generate human-readable reasoning."""
        if not mismatches and not flags:
            return f"Origin claim of {countries.name(vendor_origin)} appears legitimate based on available product information."
        
        if mismatches:
            reason = f"Origin verification detected {len(mismatches)} mismatch(es): "
            reason += "; ".join(mismatches[:2])  # Show first 2
            if len(mismatches) > 2:
                reason += f" and {len(mismatches) - 2} more."
            return reason
        
        if flags:
            reason = f"Several flags were raised during verification: "
            reason += "; ".join(flags[:2])
            if len(flags) > 2:
                reason += f" and {len(flags) - 2} more."
            return reason
        
        return f"Origin {countries.name(vendor_origin)} requires manual verification."


def verify_product_origin(product) -> Dict:
    """
    Convenience function to verify a Product instance's origin.
    
    Usage:
        from core.origin_verification import verify_product_origin
        result = verify_product_origin(product)
        if result['is_suspicious']:
            # Flag for admin review
    """
    engine = OriginVerificationEngine()
    
    product_data = {
        'origin_country': str(product.origin_country) if product.origin_country else None,
        'brand': product.brand or '',
        'manufacturer': product.manufacturer or '',
        'manufacturer_address': product.manufacturer_address or '',
        'device_identifier_type': product.device_identifier_type or '',
        'device_identifier_value': product.device_identifier_value or '',
        'certification_numbers': product.certification_numbers or '',
        'price': product.price,
        'product_type': product.product_type,
        'category_name': product.category.name if product.category else '',
        'authenticity_status': product.authenticity_status or 'unknown',
    }
    
    return engine.verify_origin(product_data)
