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


class ProductOriginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor_user = User.objects.create_user(username='vendor_country', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='Country Vendor', is_approved=True, is_verified=True)
        cls.category = Category.objects.create(name='Home', slug='home')
        cls.product_gb = Product.objects.create(vendor=cls.vendor, category=cls.category, name='GB Product', slug='gb-product', price=Decimal('10.00'), stock=5, is_active=True, origin_country='GB')
        cls.product_ng = Product.objects.create(vendor=cls.vendor, category=cls.category, name='NG Product', slug='ng-product', price=Decimal('12.00'), stock=3, is_active=True, origin_country='NG')

    def test_origin_country_field_on_products(self):
        self.assertEqual(self.product_gb.origin_country, 'GB')
        self.assertEqual(self.product_ng.origin_country, 'NG')

    def test_product_filter_by_country(self):
        response = self.client.get(reverse('core:product_list') + '?origin_country=GB')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GB Product')
        self.assertNotContains(response, 'NG Product')

    def test_origin_detail_view(self):
        response = self.client.get(reverse('core:origin_detail', kwargs={'country_code': 'GB'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GB Product')
        self.assertNotContains(response, 'NG Product')
        self.assertTemplateUsed(response, 'core/origin_detail.html')

    def test_country_flag_template_filter(self):
        from django.template import Template, Context
        t = Template("{% load core_extras %}{{ 'GB'|country_flag }}")
        rendered = t.render(Context({}))
        self.assertIn('🇬🇧', rendered)


class OriginSuggestionCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor_user = User.objects.create_user(username='vendor_origin', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='Origin Vendor', is_approved=True, is_verified=True, location_country='China')
        cls.category = Category.objects.create(name='Misc', slug='misc')
        cls.product_desc = Product.objects.create(vendor=cls.vendor, category=cls.category, name='MadeInDE', slug='madein-de', price=Decimal('5.00'), stock=2, is_active=True, description='High quality. Made in Germany')
        cls.product_vendor = Product.objects.create(vendor=cls.vendor, category=cls.category, name='VendorCountryProduct', slug='vendor-country', price=Decimal('6.00'), stock=1, is_active=True, description='Local product')

    def test_preview_does_not_persist(self):
        from django.core.management import call_command
        out = self._run_command('generate_origin_suggestions', '--only-missing', '--limit', '10')
        # Ensure suggested fields are still not set (falsy)
        p1 = Product.objects.get(pk=self.product_desc.pk)
        p2 = Product.objects.get(pk=self.product_vendor.pk)
        self.assertFalse(p1.suggested_origin_country)
        self.assertFalse(p2.suggested_origin_country)

    def test_apply_persists_suggestions(self):
        self._run_command('generate_origin_suggestions', '--apply', '--only-missing')
        p1 = Product.objects.get(pk=self.product_desc.pk)
        p2 = Product.objects.get(pk=self.product_vendor.pk)
        # Description contained 'Made in Germany' -> DE
        self.assertEqual(p1.suggested_origin_country, 'DE')
        # Vendor location 'China' should map to CN or remain string - accept either
        self.assertIn(p2.suggested_origin_country, ('CN', 'China'))

    def _run_command(self, *args):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command(*args, stdout=out)
        return out.getvalue()


class VendorSuggestOriginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor_user = User.objects.create_user(username='vendor_sugg', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='Suggest Vendor', is_approved=True, is_verified=True)
        cls.category = Category.objects.create(name='Electronics', slug='electronics-sugg')
        cls.product_ml = Product.objects.create(vendor=cls.vendor, category=cls.category, name='Phone', slug='phone-sugg', price=Decimal('1.00'), stock=1, is_active=True)
        cls.product_rule = Product.objects.create(vendor=cls.vendor, category=cls.category, name='MadeInDE', slug='madein-de-sugg', price=Decimal('2.00'), stock=1, is_active=True, description='Nice product. Made in Germany')

    def setUp(self):
        self.client.login(username='vendor_sugg', password='password123')

    def test_vendor_gets_ml_suggestion(self):
        from unittest.mock import patch
        from django.urls import reverse
        with patch('core.ml.origin_trainer.predict_products') as mock_predict:
            mock_predict.return_value = {'checked':1, 'suggested':1, 'applied':0, 'samples':[{'product_id': self.product_ml.id, 'predicted_country': 'CN', 'confidence': 0.87}]}
            url = reverse('core:vendor_product_suggest_origin', kwargs={'pk': self.product_ml.pk})
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get('suggested_country'), 'CN')
            self.assertEqual(data.get('method'), 'ml')

    def test_vendor_gets_rule_suggestion(self):
        from django.urls import reverse
        url = reverse('core:vendor_product_suggest_origin', kwargs={'pk': self.product_rule.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('suggested_country'), 'DE')
        self.assertEqual(data.get('method'), 'rule')

    def test_vendor_can_apply_suggestion(self):
        from django.urls import reverse
        import json
        url = reverse('core:vendor_product_apply_origin', kwargs={'pk': self.product_ml.pk})
        resp = self.client.post(url, data=json.dumps({'country': 'CN', 'confidence': 0.8, 'method': 'rule'}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.product_ml.refresh_from_db()
        self.assertEqual(self.product_ml.origin_country, 'CN')
        from .models import OriginLabel
        ol = OriginLabel.objects.filter(product=self.product_ml, label_country='CN', labeler=self.vendor_user)
        self.assertTrue(ol.exists())

    def test_form_contains_suggest_toast_markup(self):
        """Ensure the toast markup exists on the vendor product update page for accessibility."""
        from django.urls import reverse
        url = reverse('core:vendor_product_update', kwargs={'pk': self.product_ml.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="suggestOriginToast"')
        self.assertContains(resp, 'aria-live="polite"')


class ExportImportLabelingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor_user = User.objects.create_user(username='vendor_label', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='Label Vendor', is_approved=True, is_verified=True)
        cls.category = Category.objects.create(name='Gadgets', slug='gadgets')
        cls.p = Product.objects.create(vendor=cls.vendor, category=cls.category, name='ExportProduct', slug='export-product', price=Decimal('9.99'), stock=1, is_active=True)

    def test_export_and_import_labels(self):
        import tempfile, csv
        from django.core.management import call_command
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        tmp_path = tmp.name
        tmp.close()
        # Export
        call_command('export_for_labeling', '--output', tmp_path, '--only-missing')
        # Read exported file
        with open(tmp_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 1)
        # Prepare import file
        import_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        import_path = import_tmp.name
        import_tmp.close()
        with open(import_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['product_id','label_country','confidence','note','source','labeler_username'])
            writer.writerow([self.p.id,'US','0.9','Labeled via test','import',''])
        # Import and apply
        call_command('import_labels', '--input', import_path, '--apply')
        self.p.refresh_from_db()
        self.assertEqual(self.p.suggested_origin_country, 'US')


class AdminMLActionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor_user = User.objects.create_user(username='vendor_ml', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='ML Vendor', is_approved=True, is_verified=True)
        cls.category = Category.objects.create(name='Tools', slug='tools')
        cls.p1 = Product.objects.create(vendor=cls.vendor, category=cls.category, name='Tool A', slug='tool-a', price=Decimal('4.99'), stock=3, is_active=True)
        cls.p2 = Product.objects.create(vendor=cls.vendor, category=cls.category, name='Tool B', slug='tool-b', price=Decimal('5.99'), stock=2, is_active=True)

    def test_admin_actions_call_predict(self):
        from unittest.mock import patch
        from django.contrib import admin
        from core import admin as core_admin
        # Patch predict_products to a stub that returns a predictable summary
        with patch('core.admin.predict_products') as mock_predict:
            mock_predict.return_value = {'checked': 2, 'suggested': 1, 'applied': 0}
            pa = admin.site._registry[Product]
            qs = Product.objects.filter(pk__in=[self.p1.pk, self.p2.pk])
            # Preview (no apply)
            core_admin.ml_preview_suggestions(pa, None, qs)
            mock_predict.assert_called_with(queryset=qs, apply=False)
            # Apply
            core_admin.ml_apply_suggestions(pa, None, qs)
            mock_predict.assert_called_with(queryset=qs, apply=True)

    def test_accept_and_reject_suggestion_methods(self):
        # Create a suggestion
        self.p1.suggested_origin_country = 'GB'
        self.p1.origin_confidence = 0.8
        self.p1.origin_inference_status = 'suggested'
        self.p1.save()
        # Accept
        self.p1.apply_suggested_origin()
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.origin_country, 'GB')
        self.assertEqual(self.p1.origin_inference_status, 'accepted')
        # Create new suggestion then reject
        self.p1.suggested_origin_country = 'FR'
        self.p1.origin_inference_status = 'suggested'
        self.p1.save()
        self.p1.reject_suggested_origin()
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.origin_inference_status, 'rejected')


class AdminMLRunViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a superuser to access admin views
        cls.admin = User.objects.create_superuser(username='adminuser', email='admin@example.com', password='adminpass')
        cls.vendor_user = User.objects.create_user(username='vendor_ml2', password='password123')
        cls.vendor = Vendor.objects.create(user=cls.vendor_user, name='ML Vendor 2', is_approved=True, is_verified=True)
        cls.category = Category.objects.create(name='MiscTools', slug='misctools')
        cls.p1 = Product.objects.create(vendor=cls.vendor, category=cls.category, name='Widget A', slug='widget-a', price=Decimal('4.99'), stock=3, is_active=True)
        cls.p2 = Product.objects.create(vendor=cls.vendor, category=cls.category, name='Widget B', slug='widget-b', price=Decimal('5.99'), stock=2, is_active=True)

    def setUp(self):
        self.client.login(username='adminuser', password='adminpass')

    def test_get_preview_page_calls_predict(self):
        from unittest.mock import patch
        from django.urls import reverse
        url = reverse('admin:core_product_run_ml_suggestions')
        with patch('core.admin.predict_products') as mock_predict:
            mock_predict.return_value = {'checked': 2, 'suggested': 1, 'applied': 0, 'samples': []}
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            mock_predict.assert_called_with(apply=False, limit=20)

    def test_post_apply_calls_predict_with_apply_true(self):
        from unittest.mock import patch
        from django.urls import reverse
        url = reverse('admin:core_product_run_ml_suggestions')
        with patch('core.tasks.run_origin_inference_job.delay') as mock_delay:
            resp = self.client.post(url, {'apply': '1', 'min_confidence': '0.8'})
            self.assertEqual(resp.status_code, 200)
            # A job should be created and the task enqueued
            from core.models import OriginInferenceJob
            job = OriginInferenceJob.objects.first()
            self.assertIsNotNone(job)
            mock_delay.assert_called_with(job.id, 0.8)

    def test_run_origin_inference_task_marks_job_success(self):
        from unittest.mock import patch
        from core.models import OriginInferenceJob
        job = OriginInferenceJob.objects.create(params={'min_confidence': 0.5})
        # Patch predict_products to return a fake summary
        with patch('core.ml.origin_trainer.predict_products') as mock_predict:
            mock_predict.return_value = {'checked': 1, 'suggested': 1, 'applied': 1, 'samples': []}
            # Call the task synchronously
            from core.tasks import run_origin_inference_job
            # Call the pure task function directly to run synchronously in tests
            from core.tasks import run_origin_inference_job_task
            run_origin_inference_job_task(job.id, 0.5)
            job.refresh_from_db()
            self.assertEqual(job.status, job.STATUS_SUCCESS)
            self.assertEqual(job.summary.get('applied'), 1)

    def test_product_changelist_has_run_ml_button_and_modal(self):
        from django.urls import reverse
        url = reverse('admin:core_product_changelist')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Run ML Origin Suggestions')
        self.assertContains(resp, 'id="ml-modal-backdrop"')
        self.assertContains(resp, 'id="run-ml-btn"')


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


# --- Subcategory populate tests ---
from django.core.management import call_command
from io import StringIO

class PopulateSubcategoriesCommandTests(TestCase):
    def test_preview_outputs_create_lines(self):
        # Ensure a top-level category exists so preview has items to show
        Category.objects.create(name='Electronics', slug='electronics')
        out = StringIO()
        call_command('populate_subcategories', '--preview', stdout=out)
        output = out.getvalue()
        self.assertIn("CREATE:", output)

    def test_apply_creates_subcategories(self):
        # Ensure a top-level category exists
        top = Category.objects.create(name='Electronics', slug='electronics')
        call_command('populate_subcategories', '--create-top-level')
        # Expect some child categories now exist
        self.assertTrue(Category.objects.filter(parent=top, name__iexact='Phones').exists())


class AdminPopulateSubcategoriesIntegrationTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.client.force_login(self.admin_user)

    def test_admin_preview_view(self):
        # Ensure top-level exists so preview shows actions
        Category.objects.create(name='Electronics', slug='electronics')
        url = reverse('admin:core_category_populate_subcategories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Preview with POST
        response = self.client.post(url, {'preview': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CREATE:')

    def test_admin_apply_creates(self):
        # Ensure top-level exists
        Category.objects.create(name='Electronics', slug='electronics')
        url = reverse('admin:core_category_populate_subcategories')
        response = self.client.post(url, {'apply': '1', 'create_top': '1'})
        # Should redirect back to changelist
        self.assertEqual(response.status_code, 302)
        # Check that at least one expected subcategory was created
        self.assertTrue(Category.objects.filter(name__iexact='Phones').exists())


class CategoryMenuUITests(TestCase):
    def setUp(self):
        # Build a nested category structure
        self.top = Category.objects.create(name='Food', slug='food')
        self.beverages = Category.objects.create(name='Beverages', slug='beverages', parent=self.top)
        self.alcohol = Category.objects.create(name='Alcohol', slug='alcohol', parent=self.beverages)

    def test_menu_page_shows_multi_level_toggles(self):
        from django.test import Client
        client = Client()
        # Ensure rendering the menu does not hit the DB for each level (eager-loaded up to 3 levels)
        with self.assertNumQueries(4):
            response = client.get(reverse('core:menu'))
        self.assertEqual(response.status_code, 200)
        # Expect the top-level category to appear
        self.assertContains(response, 'Food')
        # Expect a toggle button for Beverages (has children)
        self.assertContains(response, 'aria-controls="subcats-')
        # Expect Alcohol to be present as a leaf
        self.assertContains(response, 'Alcohol')


class CategoryPickerTests(TestCase):
    def setUp(self):
        self.vendor_user = User.objects.create_user(username='vendorpicker', password='password123')
        self.vendor = Vendor.objects.create(user=self.vendor_user, name='Picker Vendor', is_approved=True, is_verified=True)
        # Create some categories
        self.top = Category.objects.create(name='Food', slug='food')
        self.child = Category.objects.create(name='Beverages', slug='beverages', parent=self.top)
        self.grandchild = Category.objects.create(name='Alcohol', slug='alcohol', parent=self.child)
        self.client.force_login(self.vendor_user)

    def test_inline_picker_present_in_create_form(self):
        response = self.client.get(reverse('core:vendor_product_create'))
        self.assertEqual(response.status_code, 200)
        # Inline picker container should be present
        self.assertContains(response, 'id="categoryInlinePicker"')
        # The picker partial should be namespaced for inline usage
        self.assertContains(response, 'aria-controls="inline-picker-subcats-')
        # Picker leafs should be present
        self.assertContains(response, 'picker-select')
        # Breadcrumb is JS-inserted; we ensure server-rendered picker markup (labels, toggles, leaves) is present for JS to operate on.

