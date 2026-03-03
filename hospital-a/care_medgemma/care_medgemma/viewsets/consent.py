from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination

from care_medgemma.models.audit_log import AuditLogEntry
from care_medgemma.models.consent import ConsentRecord
from care_medgemma.serializers.consent import (
    ConsentGrantSerializer,
    ConsentRecordSerializer,
    ConsentRevokeSerializer,
)


class ConsentViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """
    Consent management endpoints (DEPA-compliant).
    GET /consent/ — list consents
    GET /consent/{id}/ — retrieve consent
    POST /consent/grant/ — grant new consent
    POST /consent/{id}/revoke/ — revoke consent
    """

    queryset = ConsentRecord.objects.all().order_by("-granted_at")
    serializer_class = ConsentRecordSerializer
    lookup_field = "external_id"
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        """Filter by patient_abha_id if provided."""
        queryset = super().get_queryset()
        abha_id = self.request.query_params.get("patient_abha_id")
        if abha_id:
            queryset = queryset.filter(patient_abha_id=abha_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=False, methods=["post"])
    def grant(self, request):
        """Grant a new consent artifact."""
        serializer = ConsentGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create consent record
        consent = ConsentRecord.objects.create(
            patient_abha_id=data["patient_abha_id"],
            requester_id=data["requester_id"],
            requester_type=data["requester_type"],
            purpose=data["purpose"],
            scope=data["scope"],
            exclude=data.get("exclude", []),
            valid_until=data["valid_until"],
            patient_signature=data.get("patient_signature", ""),
            granted_by=request.user,
        )

        # Audit log
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.CONSENT_GRANT,
            actor_id=str(request.user.external_id),
            patient_id=data["patient_abha_id"],
            resource_types=data["scope"],
            consent_ref=consent.external_id,
            metadata={
                "purpose": data["purpose"],
                "requester_type": data["requester_type"],
                "valid_until": data["valid_until"].isoformat(),
                "ip": request.META.get("REMOTE_ADDR", ""),
            },
        )

        return Response(
            ConsentRecordSerializer(consent).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def revoke(self, request, external_id=None):
        """Revoke an existing consent."""
        try:
            consent = ConsentRecord.objects.get(external_id=external_id)
        except ConsentRecord.DoesNotExist:
            return Response(
                {"error": "Consent not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if consent.status == ConsentRecord.Status.REVOKED:
            return Response(
                {"error": "Consent is already revoked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ConsentRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consent.revoke()

        # Audit log
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.CONSENT_REVOKE,
            actor_id=str(request.user.external_id),
            patient_id=consent.patient_abha_id,
            resource_types=consent.scope,
            consent_ref=consent.external_id,
            metadata={
                "reason": serializer.validated_data.get("reason", ""),
                "ip": request.META.get("REMOTE_ADDR", ""),
            },
        )

        return Response(
            ConsentRecordSerializer(consent).data,
            status=status.HTTP_200_OK,
        )
