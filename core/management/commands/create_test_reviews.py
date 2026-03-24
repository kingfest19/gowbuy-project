from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Vendor, VendorReview
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test vendor reviews for demonstration'

    def handle(self, *args, **kwargs):
        # Get or create test users
        test_usernames = ['alice_customer', 'bob_buyer', 'charlie_user', 'diana_shopper', 'edward_client']
        test_users = []
        
        self.stdout.write('\n👥 Setting up test users...')
        for username in test_usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.split('_')[0].capitalize(),
                    'last_name': 'Customer'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'  ✓ Created: {username}')
            else:
                self.stdout.write(f'  • Using: {username}')
            test_users.append(user)
        
        # Get first vendor
        vendor = Vendor.objects.first()
        if not vendor:
            self.stdout.write(self.style.ERROR('❌ No vendor found!'))
            return
        
        self.stdout.write(f'\n📦 Found vendor: {vendor.name}')
        
        # Clear existing reviews
        existing = VendorReview.objects.filter(vendor=vendor).count()
        if existing > 0:
            VendorReview.objects.filter(vendor=vendor).delete()
            self.stdout.write(f'🗑️  Cleared {existing} existing reviews')
        
        # Review data
        reviews_data = [
            ("Great service! Fast delivery and excellent communication.", 5),
            ("Good quality products, but shipping took longer than expected.", 4),
            ("Average experience. Product was as described.", 3),
            ("Not satisfied with the quality. Expected better.", 2),
            ("Terrible experience. Product was damaged and no response.", 1),
            ("Amazing vendor! Will definitely buy again. Highly recommended!", 5),
            ("Quick response to my questions. Very professional.", 4),
            ("Product quality is decent for the price.", 3),
            ("Package arrived late and customer service was unhelpful.", 2),
            ("Best shopping experience ever! Five stars all the way!", 5),
        ]
        
        self.stdout.write('\n⭐ Creating test reviews...')
        created = []
        
        for i, (text, rating) in enumerate(reviews_data):
            user = test_users[i % len(test_users)]
            days_ago = random.randint(1, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            has_reply = random.choice([True, False, False])
            
            review, created_flag = VendorReview.objects.update_or_create(
                vendor=vendor,
                user=user,
                defaults={
                    'rating': rating,
                    'review': text,
                    'is_approved': True,
                    'created_at': created_at,
                    'reply': None,
                    'replied_at': None
                }
            )
            
            if has_reply:
                reply_time = created_at + timedelta(hours=random.randint(2, 48))
                review.reply = f"Thank you for your feedback! We appreciate your {rating}-star review."
                review.replied_at = reply_time
                review.save()
            
            created.append(review)
            status = "✓" if has_reply else "⏳"
            action = "Created" if created_flag else "Updated"
            self.stdout.write(f'  {status} {rating}⭐ by {user.username} ({action})')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {len(created)} test reviews!'))
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   5⭐: {sum(1 for r in created if r.rating == 5)}')
        self.stdout.write(f'   4⭐: {sum(1 for r in created if r.rating == 4)}')
        self.stdout.write(f'   3⭐: {sum(1 for r in created if r.rating == 3)}')
        self.stdout.write(f'   2⭐: {sum(1 for r in created if r.rating == 2)}')
        self.stdout.write(f'   1⭐: {sum(1 for r in created if r.rating == 1)}')
        self.stdout.write(f'   With replies: {sum(1 for r in created if r.reply)}')
        self.stdout.write(f'   Pending: {sum(1 for r in created if not r.reply)}')
        self.stdout.write('\n🎉 Refresh http://127.0.0.1:1000/dashboard/reviews/')
