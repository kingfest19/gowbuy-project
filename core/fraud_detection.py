from decimal import Decimal
from django.utils import timezone

def calculate_fraud_score(order):
    """
    Calculates a fraud score for a given order.
    Returns a dictionary with the score and a list of reasons.
    """
    score = 0
    reasons = []

    # Rule 1: High order value
    if order.total_amount > 1000: # Threshold can be adjusted
        score += 25
        reasons.append(f"High order value: {order.total_amount}")

    # Rule 2: New user account
    if order.user:
        if (timezone.now() - order.user.date_joined).days < 1:
            score += 15
            reasons.append("Order from a very new user account.")

    # Rule 3: Mismatched billing and shipping country
    if order.billing_address and order.shipping_address:
        if order.billing_address.country != order.shipping_address.country:
            score += 20
            reasons.append("Billing and shipping country mismatch.")

    # Rule 4: IP address location mismatch (requires GeoIP setup, placeholder for now)
    # For now, this is a placeholder. A real implementation would need a GeoIP database.
    # For example, using GeoIP2:
    # from django.contrib.gis.geoip2 import GeoIP2
    # g = GeoIP2()
    # try:
    #     ip_country = g.country(order.ip_address)['country_code']
    #     if order.billing_address and ip_country != order.billing_address.country:
    #         score += 30
    #         reasons.append("IP address country does not match billing address country.")
    # except Exception:
    #     pass # Could fail if IP is local or not found

    return {"score": score, "reasons": reasons}
