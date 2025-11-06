"""
Complaints Models - User Complaint/Report System
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import uuid


class Complaint(models.Model):
    """
    Base model for all types of complaints/reports from users.
    Supports seller reports, buyer reports, order issues, and transaction issues.
    """

    COMPLAINT_TYPE_CHOICES = [
        ("SELLER", "Report Seller"),
        ("BUYER", "Report Buyer"),
        ("ORDER", "Report Order"),
        ("TRANSACTION", "Report Transaction"),
    ]

    # Complaint categories for better classification
    CATEGORY_CHOICES = [
        # Seller/Buyer categories
        ("FRAUD", "Fraudulent Activity"),
        ("HARASSMENT", "Harassment or Abuse"),
        ("FAKE_PRODUCT", "Fake/Counterfeit Product"),
        ("POOR_SERVICE", "Poor Customer Service"),
        ("SCAM", "Scam/Deception"),
        ("SPAM", "Spam or Unwanted Messages"),
        # Order categories
        ("NOT_RECEIVED", "Product Not Received"),
        ("WRONG_ITEM", "Wrong Item Delivered"),
        ("DAMAGED", "Damaged Product"),
        ("NOT_AS_DESCRIBED", "Not As Described"),
        ("LATE_DELIVERY", "Late Delivery"),
        ("QUALITY_ISSUE", "Quality Issue"),
        # Transaction categories
        ("PAYMENT_FAILED", "Payment Failed"),
        ("DOUBLE_CHARGE", "Double Charged"),
        ("REFUND_ISSUE", "Refund Not Received"),
        ("WALLET_ISSUE", "Wallet Issue"),
        ("UNAUTHORIZED", "Unauthorized Transaction"),
        # General
        ("OTHER", "Other Issue"),
    ]

    URGENCY_CHOICES = [
        ("LOW", "Low - Not urgent"),
        ("MEDIUM", "Medium - Needs attention"),
        ("HIGH", "High - Important"),
        ("URGENT", "Urgent - Immediate action required"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending Review"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
        ("REJECTED", "Rejected"),
    ]

    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint_type = models.CharField(
        max_length=20, choices=COMPLAINT_TYPE_CHOICES, help_text="Type of complaint"
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        help_text="Specific category of the complaint",
    )
    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default="MEDIUM",
        help_text="Urgency level of the complaint",
    )

    # Reporter Info
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints_filed",
        help_text="User who filed the complaint",
    )
    reporter_email = models.EmailField(help_text="Reporter's email for follow-up")
    reporter_phone = models.CharField(
        max_length=20, blank=True, help_text="Reporter's phone (optional)"
    )

    # Complaint Details
    subject = models.CharField(max_length=200, help_text="Brief complaint subject")
    description = models.TextField(help_text="Detailed description of the issue")

    # Related Objects (optional - depends on complaint type)
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints_received",
        help_text="User being reported (for seller/buyer reports)",
    )
    reported_user_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of reported user/store (if user is deleted)",
    )

    order_id = models.CharField(
        max_length=100, blank=True, help_text="Order number (for order complaints)"
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction ID (for transaction complaints)",
    )
    transaction_type = models.CharField(
        max_length=50, blank=True, help_text="Type of transaction (deposit/withdrawal)"
    )

    # Evidence
    attachment = models.FileField(
        upload_to="complaints/%Y/%m/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])],
        help_text="Screenshot or evidence (optional)",
    )

    # Admin Response
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        help_text="Current status of the complaint",
    )
    admin_notes = models.TextField(
        blank=True, help_text="Internal notes from admin/support team"
    )
    admin_response = models.TextField(blank=True, help_text="Response sent to the user")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints_resolved",
        help_text="Admin who resolved the complaint",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "complaints"
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["complaint_type", "status"]),
            models.Index(fields=["reporter", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["urgency", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.get_complaint_type_display()} - {self.subject[:50]} ({self.status})"
        )

    @property
    def complaint_number(self):
        """Short complaint reference number"""
        return str(self.id)[:8].upper()

    @property
    def is_resolved(self):
        """Check if complaint is resolved"""
        return self.status in ["RESOLVED", "CLOSED"]
