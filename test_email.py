"""
Quick test to verify email configuration works with Zoho
Run with: python manage.py shell < test_email.py
"""

from django.core.mail import send_mail
from django.conf import settings

print("\n" + "=" * 60)
print("Testing Email Configuration")
print("=" * 60)
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email User: {settings.EMAIL_HOST_USER}")
print(f"Use TLS: {settings.EMAIL_USE_TLS}")
print(f"Use SSL: {settings.EMAIL_USE_SSL}")
print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
print("=" * 60)

try:
    # Send test email
    result = send_mail(
        subject="COVU Test Email - Email Configuration Successful",
        message="This is a test email from COVU Marketplace. If you receive this, your email configuration is working correctly!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
        fail_silently=False,
    )

    if result == 1:
        print("\n✅ SUCCESS! Test email sent successfully!")
        print(f"📧 Email sent to: {settings.EMAIL_HOST_USER}")
        print("\nCheck your inbox to verify delivery.")
    else:
        print("\n⚠️ WARNING: send_mail returned 0 (email may not have been sent)")

except Exception as e:
    print(f"\n❌ ERROR: Failed to send test email")
    print(f"Error details: {str(e)}")
    print("\nPlease check:")
    print("1. Email credentials are correct in .env file")
    print("2. Zoho account allows SMTP access")
    print("3. No firewall blocking port 587")

print("\n" + "=" * 60 + "\n")
