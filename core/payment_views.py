# c:\Users\Hp\Desktop\Nexus\core\payment_views.py
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from .models import Order


def process_payment(request, order_id):
    """
    View to process the payment for a given order via PayPal.
    This view creates a PayPal button that the user clicks to pay.
    """
    # The URL will have the order's primary key (id)
    # We fetch an order that is awaiting payment. 'AWAITING_ESCROW_PAYMENT' is a good
    # status to check for, as it's used by your Paystack flow.
    order = get_object_or_404(Order, id=order_id, status='AWAITING_ESCROW_PAYMENT')

    # Use build_absolute_uri to construct the full URLs for PayPal, which is more robust,
    # especially when testing with tools like ngrok.
    notify_url = request.build_absolute_uri(reverse('paypal-ipn'))
    return_url = request.build_absolute_uri(reverse('core:payment_done'))
    cancel_url = request.build_absolute_uri(reverse('core:payment_cancelled'))

    # What you want the button to show.
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{order.total_amount:.2f}",  # Use total_amount from your Order model
        "item_name": f"Payment for Order #{order.order_id}",  # Use the user-facing order_id
        "invoice": str(order.id),  # Must be a unique identifier; use the order's primary key
        "currency_code": "USD",  # PayPal sandbox accounts are often in USD
        "notify_url": notify_url,
        "return_url": return_url,
        "cancel_return": cancel_url,
    }

    # Create the form that will render the PayPal button.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"order": order, "form": form}
    return render(request, "payments/process_payment.html", context)

@csrf_exempt
def payment_done(request):
    return render(request, "payments/payment_done.html")

@csrf_exempt
def payment_cancelled(request):
    return render(request, "payments/payment_cancelled.html")