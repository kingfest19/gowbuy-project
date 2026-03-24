"""
Quick script to create test vendor reviews for testing the review management page.
Run with: python manage.py shell < create_test_vendor_reviews.py
"""

from django.contrib.auth import get_user_model
from core.models import Vendor, VendorReview
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

# Get or create test users
def get_or_create_test_users():
    users = []
    test_usernames = ['alice_customer', 'bob_buyer', 'charlie_user', 'diana_shopper', 'edward_client']
    
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
            print(f"✓ Created test user: {username}")
        else:
            print(f"  Using existing user: {username}")
        users.append(user)
    
    return users

# Get first vendor (your account)
try:
    vendor = Vendor.objects.first()
    if not vendor:
        print("❌ No vendor found! Please create a vendor account first.")
        exit(1)
    
    print(f"\n📦 Found vendor: {vendor.name} (User: {vendor.user.username})")
    
    # Get or create test users
    print("\n👥 Setting up test users...")
    test_users = get_or_create_test_users()
    
    # Clear existing reviews for this vendor
    existing_count = VendorReview.objects.filter(vendor=vendor).count()
    if existing_count > 0:
        VendorReview.objects.filter(vendor=vendor).delete()
        print(f"\n🗑️  Cleared {existing_count} existing reviews")
    
    # Review templates
    review_texts = [
        ("Great service! Fast delivery and excellent communication.", 5),
        ("Good quality products, but shipping took longer than expected.", 4),
        ("Average experience. Product was as described.", 3),
        ("Not satisfied with the quality. Expected better.", 2),
        ("Terrible experience. Product was damaged and no response from vendor.", 1),
        ("Amazing vendor! Will definitely buy again. Highly recommended!", 5),
        ("Quick response to my questions. Very professional.", 4),
        ("Product quality is decent for the price.", 3),
        ("Package arrived late and customer service was unhelpful.", 2),
        ("Best shopping experience ever! Five stars all the way!", 5),
    ]
    
    print("\n⭐ Creating test reviews...")
    created_reviews = []
    
    for i, (review_text, rating) in enumerate(review_texts):
        user = test_users[i % len(test_users)]
        
        # Create review with varying timestamps
        days_ago = random.randint(1, 30)
        created_at = timezone.now() - timedelta(days=days_ago)
        
        # Randomly decide if review has a reply
        has_reply = random.choice([True, False, False])  # 33% chance of reply
        
        review = VendorReview.objects.create(
            vendor=vendor,
            user=user,
            rating=rating,
            review=review_text,
            is_approved=True,
            created_at=created_at
        )
        
        if has_reply:
            reply_time = created_at + timedelta(hours=random.randint(2, 48))
            review.reply = f"Thank you for your feedback! We appreciate your {rating}-star review."
            review.replied_at = reply_time
            review.save()
        
        created_reviews.append(review)
        status = "✓ Replied" if has_reply else "⏳ Pending"
        print(f"  {status} | {rating}⭐ | {review_text[:50]}... | by {user.username}")
    
    print(f"\n✅ Successfully created {len(created_reviews)} test reviews!")
    print(f"\n📊 Summary:")
    print(f"   • 5-star reviews: {sum(1 for r in created_reviews if r.rating == 5)}")
    print(f"   • 4-star reviews: {sum(1 for r in created_reviews if r.rating == 4)}")
    print(f"   • 3-star reviews: {sum(1 for r in created_reviews if r.rating == 3)}")
    print(f"   • 2-star reviews: {sum(1 for r in created_reviews if r.rating == 2)}")
    print(f"   • 1-star reviews: {sum(1 for r in created_reviews if r.rating == 1)}")
    print(f"   • With replies: {sum(1 for r in created_reviews if r.reply)}")
    print(f"   • Pending reply: {sum(1 for r in created_reviews if not r.reply)}")
    print(f"\n🎉 Now refresh your review page at http://127.0.0.1:1000/dashboard/reviews/")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
