"""
Complaint Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Complaint
from .serializers import (
    ComplaintCreateSerializer,
    ComplaintListSerializer,
    ComplaintDetailSerializer,
)
import logging

logger = logging.getLogger(__name__)


class ComplaintViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user complaints/reports.

    Users can:
    - Create complaints (POST)
    - View their own complaints (GET list)
    - View complaint details (GET detail)

    Admins can view all complaints and update status.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == "create":
            return ComplaintCreateSerializer
        elif self.action == "list":
            return ComplaintListSerializer
        else:
            return ComplaintDetailSerializer

    def get_queryset(self):
        """Users can only see their own complaints"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admins can see all complaints
            return Complaint.objects.all()
        # Regular users see only their complaints
        return Complaint.objects.filter(reporter=user)

    def create(self, request, *args, **kwargs):
        """Create a new complaint"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = serializer.save()

        logger.info(
            f"New complaint created: {complaint.complaint_number} by {request.user.email}"
        )

        # Return with detail serializer
        return Response(
            ComplaintDetailSerializer(complaint, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        """List user's complaints"""
        queryset = self.get_queryset()

        # Filter by status if provided
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Filter by type if provided
        type_filter = request.query_params.get("type")
        if type_filter:
            queryset = queryset.filter(complaint_type=type_filter.upper())

        serializer = self.get_serializer(queryset, many=True)

        return Response({"count": queryset.count(), "results": serializer.data})

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get available complaint categories grouped by type"""
        # Organize categories by complaint type
        categories_by_type = {
            "SELLER": [
                {"value": "FRAUD", "label": "Fraudulent Activity"},
                {"value": "HARASSMENT", "label": "Harassment or Abuse"},
                {"value": "FAKE_PRODUCT", "label": "Fake/Counterfeit Product"},
                {"value": "POOR_SERVICE", "label": "Poor Customer Service"},
                {"value": "SCAM", "label": "Scam/Deception"},
                {"value": "SPAM", "label": "Spam or Unwanted Messages"},
                {"value": "OTHER", "label": "Other Issue"},
            ],
            "BUYER": [
                {"value": "FRAUD", "label": "Fraudulent Activity"},
                {"value": "HARASSMENT", "label": "Harassment or Abuse"},
                {"value": "SCAM", "label": "Scam/Deception"},
                {"value": "SPAM", "label": "Spam or Unwanted Messages"},
                {"value": "OTHER", "label": "Other Issue"},
            ],
            "ORDER": [
                {"value": "NOT_RECEIVED", "label": "Product Not Received"},
                {"value": "WRONG_ITEM", "label": "Wrong Item Delivered"},
                {"value": "DAMAGED", "label": "Damaged Product"},
                {"value": "NOT_AS_DESCRIBED", "label": "Not As Described"},
                {"value": "LATE_DELIVERY", "label": "Late Delivery"},
                {"value": "QUALITY_ISSUE", "label": "Quality Issue"},
                {"value": "OTHER", "label": "Other Issue"},
            ],
            "TRANSACTION": [
                {"value": "PAYMENT_FAILED", "label": "Payment Failed"},
                {"value": "DOUBLE_CHARGE", "label": "Double Charged"},
                {"value": "REFUND_ISSUE", "label": "Refund Not Received"},
                {"value": "WALLET_ISSUE", "label": "Wallet Issue"},
                {"value": "UNAUTHORIZED", "label": "Unauthorized Transaction"},
                {"value": "OTHER", "label": "Other Issue"},
            ],
        }

        return Response(
            {
                "complaint_types": dict(Complaint.COMPLAINT_TYPE_CHOICES),
                "categories": categories_by_type,
                "urgency_levels": dict(Complaint.URGENCY_CHOICES),
            }
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get complaint statistics for the user"""
        queryset = self.get_queryset()

        return Response(
            {
                "total": queryset.count(),
                "pending": queryset.filter(status="PENDING").count(),
                "in_progress": queryset.filter(status="IN_PROGRESS").count(),
                "resolved": queryset.filter(status="RESOLVED").count(),
                "by_type": {
                    "seller": queryset.filter(complaint_type="SELLER").count(),
                    "buyer": queryset.filter(complaint_type="BUYER").count(),
                    "order": queryset.filter(complaint_type="ORDER").count(),
                    "transaction": queryset.filter(
                        complaint_type="TRANSACTION"
                    ).count(),
                },
            }
        )
