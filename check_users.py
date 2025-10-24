"""
Check test user accounts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'covu.settings')
django.setup()

from users.models import CustomUser
from django.contrib.auth.hashers import check_password

print("=" * 80)
print("  CHECKING TEST USER ACCOUNTS")
print("=" * 80)

# Check buyer
print("\n1. BUYER ACCOUNT:")
buyer = CustomUser.objects.filter(email='buyer@test.com').first()

if buyer:
    print(f"   ✅ Account exists")
    print(f"   Email: {buyer.email}")
    print(f"   Full Name: {buyer.full_name}")
    print(f"   Has usable password: {buyer.has_usable_password()}")
    print(f"   Is active: {buyer.is_active}")
    
    # Test password
    test_password = 'testpass123'
    password_valid = buyer.check_password(test_password)
    print(f"   Password 'testpass123' valid: {password_valid}")
    
    if not password_valid:
        print(f"\n   ⚠️  FIXING PASSWORD...")
        buyer.set_password(test_password)
        buyer.save()
        print(f"   ✅ Password reset to 'testpass123'")
else:
    print(f"   ❌ Account does NOT exist")

# Check seller
print("\n2. SELLER ACCOUNT:")
seller = CustomUser.objects.filter(email='seller@test.com').first()

if seller:
    print(f"   ✅ Account exists")
    print(f"   Email: {seller.email}")
    print(f"   Full Name: {seller.full_name}")
    print(f"   Has usable password: {seller.has_usable_password()}")
    print(f"   Is active: {seller.is_active}")
    
    # Test password
    test_password = 'testpass123'
    password_valid = seller.check_password(test_password)
    print(f"   Password 'testpass123' valid: {password_valid}")
    
    if not password_valid:
        print(f"\n   ⚠️  FIXING PASSWORD...")
        seller.set_password(test_password)
        seller.save()
        print(f"   ✅ Password reset to 'testpass123'")
else:
    print(f"   ❌ Account does NOT exist")

print("\n" + "=" * 80)
print("  CHECK COMPLETE!")
print("=" * 80)
print("\nIf passwords were fixed, try logging in again with:")
print("  Email: buyer@test.com")
print("  Password: testpass123")
print("=" * 80)
