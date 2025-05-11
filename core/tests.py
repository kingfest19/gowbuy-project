from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch # For mocking external API calls

# Import models from your app
from .models import Vendor, Product, Category, Order, OrderItem

User = get_user_model()

class VendorDashboardViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user who is NOT a vendor
        cls.non_vendor_user = User.objects.create_user(username='testuser', password='password123')

        # Create a user who IS a vendor
        cls.vendor_user = User.objects.create_user(username='vendoruser', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='Test Vendor Shop', is_approved=True, is_verified=True)

        # Create a category
        cls.category = Category.objects.create(name='Electronics', slug='electronics')

        # Create some products for the vendor
        cls.product1 = Product.objects.create(
            vendor=cls.vendor, category=cls.category, name='Laptop', slug='laptop', price=Decimal('1200.00'), stock=10, is_active=True
        )
        cls.product2 = Product.objects.create(
            vendor=cls.vendor, category=cls.category, name='Mouse', slug='mouse', price=Decimal('25.00'), stock=3, is_active=True # Low stock
        )
        cls.product3 = Product.objects.create(
            vendor=cls.vendor, category=cls.category, name='Keyboard', slug='keyboard', price=Decimal('75.00'), stock=0, is_active=False # Inactive
        )

        # Create an order with items from this vendor
        cls.customer = User.objects.create_user(username='customer', password='password123')
        cls.order = Order.objects.create(user=cls.customer, total_amount=Decimal('1225.00'), status='delivered')
        OrderItem.objects.create(order=cls.order, product=cls.product1, price=cls.product1.price, quantity=1)
        OrderItem.objects.create(order=cls.order, product=cls.product2, price=cls.product2.price, quantity=1)

    def test_vendor_dashboard_unauthenticated(self):
        """Test accessing dashboard when not logged in redirects to login."""
        response = self.client.get(reverse('core:vendor_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('signin')}?next={reverse('core:vendor_dashboard')}")

    def test_vendor_dashboard_non_vendor_user(self):
        """Test accessing dashboard as a user without a vendor profile redirects."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:vendor_dashboard'))
        self.assertEqual(response.status_code, 302)
        # Assuming redirect goes to 'sell_on_nexus' page as per view logic
        self.assertRedirects(response, reverse('core:sell_on_nexus'))

    def test_vendor_dashboard_authenticated_vendor(self):
        """Test vendor can access their dashboard and context is correct."""
        self.client.login(username='vendoruser', password='password123')
        response = self.client.get(reverse('core:vendor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vendor_dashboard.html')
        self.assertEqual(response.context['vendor'], self.vendor)
        self.assertEqual(response.context['total_products_count'], 3)
        self.assertEqual(response.context['active_products_count'], 2)
        self.assertEqual(response.context['total_sales'], Decimal('1225.00'))
        self.assertEqual(response.context['total_orders_count'], 1)
        self.assertEqual(len(response.context['low_stock_products']), 1)
        self.assertEqual(response.context['low_stock_products'][0], self.product2)

    def test_vendor_product_list_view(self):
        """Test vendor can access their product list."""
        self.client.login(username='vendoruser', password='password123')
        response = self.client.get(reverse('core:vendor_product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vendor_product_list.html')
        self.assertEqual(len(response.context['products']), 3) # Shows all products by default
        self.assertContains(response, self.product1.name)
        self.assertContains(response, self.product2.name)
        self.assertContains(response, self.product3.name)
        self.assertNotContains(response, "Showing only low stock items") # No filter message by default

    def test_vendor_product_list_low_stock_filter(self):
        """Test low stock filter on product list."""
        self.client.login(username='vendoruser', password='password123')
        response = self.client.get(reverse('core:vendor_product_list') + '?stock_status=low')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vendor_product_list.html')
        self.assertEqual(len(response.context['products']), 1) # Only low stock product
        self.assertEqual(response.context['products'][0], self.product2)
        self.assertContains(response, "Showing only low stock items") # Filter message should be present
        self.assertContains(response, "Clear Filter") # Clear filter button

    def test_vendor_order_list_view(self):
        """Test vendor can access their order list."""
        self.client.login(username='vendoruser', password='password123')
        response = self.client.get(reverse('core:vendor_order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vendor_order_list.html')
        self.assertEqual(len(response.context['orders']), 1)
        self.assertEqual(response.context['orders'][0], self.order)

    def test_vendor_reports_view(self):
        """Test vendor can access the reports page."""
        self.client.login(username='vendoruser', password='password123')
        response = self.client.get(reverse('core:vendor_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vendor_reports.html')
        self.assertEqual(response.context['vendor'], self.vendor)
        self.assertEqual(response.context['total_revenue'], Decimal('1225.00'))
        self.assertEqual(response.context['total_items_sold'], 2) # 1 laptop + 1 mouse
        self.assertEqual(response.context['total_orders_count'], 1)
        self.assertEqual(len(response.context['low_stock_products']), 1)
        # Check order status counts (assuming only one 'delivered' order)
        status_counts = {item['status']: item['count'] for item in response.context['order_status_counts']}
        self.assertEqual(status_counts.get('delivered', 0), 1)

    # --- Add more tests ---
    # - Test product creation/edit/delete views
    # - Test promotion/campaign views
    # - Test profile/verification/shipping/payment edit views
    # - Test cases where vendor is not approved/verified
    # - Test pagination if implemented on list views
    # - Test POST requests for forms (e.g., submitting a product)


class OrderProcessingViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testbuyer', email='buyer@example.com', password='password123')
        # Create an order that is pending payment choice
        cls.order_pending_choice = Order.objects.create(
            user=cls.user,
            total_amount=Decimal('100.00'),
            ordered=False, # This indicates it's ready for payment method choice
            status='PENDING' # Initial status before payment choice
        )
        # Create an order that is awaiting escrow payment
        cls.order_awaiting_escrow = Order.objects.create(
            user=cls.user,
            total_amount=Decimal('150.00'),
            ordered=True,
            payment_method='escrow',
            status='AWAITING_ESCROW_PAYMENT'
        )

    def setUp(self):
        self.client.login(username='testbuyer', password='password123')

    def test_process_checkout_choice_no_method_selected(self):
        response = self.client.post(reverse('core:process_checkout_choice'), {})
        self.assertRedirects(response, reverse('core:order_summary'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Please select a payment method.")

    def test_process_checkout_choice_invalid_method(self):
        response = self.client.post(reverse('core:process_checkout_choice'), {'payment_method': 'invalid_method'})
        self.assertRedirects(response, reverse('core:order_summary'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid payment method selected.")

    def test_process_checkout_choice_no_active_order(self):
        # Temporarily mark the order as already processed to simulate no active order
        self.order_pending_choice.ordered = True
        self.order_pending_choice.save()
        response = self.client.post(reverse('core:process_checkout_choice'), {'payment_method': 'escrow'})
        self.assertRedirects(response, reverse('core:home')) # Or wherever you redirect if no active order
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You do not have an active order.")
        # Revert for other tests
        self.order_pending_choice.ordered = False
        self.order_pending_choice.save()

    def test_process_checkout_choice_escrow(self):
        response = self.client.post(reverse('core:process_checkout_choice'), {'payment_method': 'escrow'})
        self.order_pending_choice.refresh_from_db()
        self.assertEqual(self.order_pending_choice.payment_method, 'escrow')
        self.assertEqual(self.order_pending_choice.status, 'AWAITING_ESCROW_PAYMENT')
        self.assertTrue(self.order_pending_choice.ordered)
        self.assertRedirects(response, reverse('core:initiate_paystack_payment', kwargs={'order_id': self.order_pending_choice.id}))

    def test_process_checkout_choice_direct(self):
        response = self.client.post(reverse('core:process_checkout_choice'), {'payment_method': 'direct'})
        self.order_pending_choice.refresh_from_db()
        self.assertEqual(self.order_pending_choice.payment_method, 'direct')
        self.assertEqual(self.order_pending_choice.status, 'AWAITING_DIRECT_PAYMENT')
        self.assertTrue(self.order_pending_choice.ordered)
        self.assertRedirects(response, self.order_pending_choice.get_absolute_url())

    @patch('requests.post')
    def test_initiate_paystack_payment_success(self, mock_post):
        # Mock Paystack's response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test_auth_url',
                'access_code': 'test_access_code',
                'reference': f"NEXUS-SVC-{self.order_awaiting_escrow.id}-sometimestamp"
            }
        }
        response = self.client.get(reverse('core:initiate_paystack_payment', kwargs={'order_id': self.order_awaiting_escrow.id}))
        self.assertRedirects(response, 'https://checkout.paystack.com/test_auth_url', fetch_redirect_response=False)
        self.order_awaiting_escrow.refresh_from_db()
        self.assertIsNotNone(self.order_awaiting_escrow.paystack_ref)

    @patch('requests.post')
    def test_initiate_paystack_payment_api_failure(self, mock_post):
        mock_post.return_value.status_code = 401 # Simulate an authorization error
        mock_post.return_value.json.return_value = {'status': False, 'message': 'Unauthorized'}
        mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error")

        response = self.client.get(reverse('core:initiate_paystack_payment', kwargs={'order_id': self.order_awaiting_escrow.id}))
        self.assertRedirects(response, reverse('core:order_detail', kwargs={'order_id': self.order_awaiting_escrow.id}))
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any("Could not connect to payment gateway" in str(m) for m in messages_list))

    def test_initiate_paystack_payment_wrong_order_status(self):
        self.order_awaiting_escrow.status = 'COMPLETED' # Change status so it's not AWAITING_ESCROW_PAYMENT
        self.order_awaiting_escrow.save()
        response = self.client.get(reverse('core:initiate_paystack_payment', kwargs={'order_id': self.order_awaiting_escrow.id}))
        self.assertEqual(response.status_code, 404) # get_object_or_404 should fail


class PaystackCallbackViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='callbackuser', email='callback@example.com', password='password123')
        cls.order = Order.objects.create(
            user=cls.user,
            total_amount=Decimal('200.00'),
            ordered=True,
            payment_method='escrow',
            status='AWAITING_ESCROW_PAYMENT',
            paystack_ref='test_paystack_ref_123' # Pre-set reference
        )

    def setUp(self):
        # Callback doesn't require login, but good to have user context if needed
        # self.client.login(username='callbackuser', password='password123')
        pass

    def test_paystack_callback_no_reference(self):
        response = self.client.get(reverse('core:paystack_callback')) # No reference query param
        self.assertRedirects(response, reverse('core:order_summary')) # Or your defined error page
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Payment reference not found" in str(m) for m in messages))

    @patch('requests.get')
    def test_paystack_callback_successful_verification(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': True,
            'message': 'Verification successful',
            'data': {
                'status': 'success',
                'reference': 'test_paystack_ref_123',
                'id': 'paystack_transaction_id_abc',
                'amount': 20000, # Amount in kobo/pesewas
                'currency': 'GHS',
                # ... other data
            }
        }
        response = self.client.get(reverse('core:paystack_callback') + '?reference=test_paystack_ref_123')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PROCESSING') # Or IN_PROGRESS
        self.assertEqual(self.order.transaction_id, 'paystack_transaction_id_abc')
        self.assertRedirects(response, self.order.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Payment successful!" in str(m) for m in messages))

    @patch('requests.get')
    def test_paystack_callback_failed_verification(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': True, # API call itself was successful
            'message': 'Verification successful',
            'data': {
                'status': 'failed', # But Paystack says the transaction failed
                'reference': 'test_paystack_ref_123',
            }
        }
        response = self.client.get(reverse('core:paystack_callback') + '?reference=test_paystack_ref_123')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'AWAITING_ESCROW_PAYMENT') # Status should not change to success
        self.assertRedirects(response, self.order.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Payment verification failed" in str(m) for m in messages))

    @patch('requests.get')
    def test_paystack_callback_api_error(self, mock_get):
        mock_get.return_value.status_code = 500 # Simulate Paystack server error
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")

        response = self.client.get(reverse('core:paystack_callback') + '?reference=test_paystack_ref_123')
        self.assertRedirects(response, self.order.get_absolute_url()) # Should redirect to order detail
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Could not verify payment status" in str(m) for m in messages))

    def test_paystack_callback_reference_not_found_in_db(self):
        response = self.client.get(reverse('core:paystack_callback') + '?reference=non_existent_ref')
        self.assertRedirects(response, reverse('core:home')) # Or your defined error page
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Order associated with this payment reference not found" in str(m) for m in messages))
