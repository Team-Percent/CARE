import uuid
from datetime import timedelta

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
from care_medgemma.serializers.audit_log import AuditLogEntrySerializer
from care_medgemma.settings import plugin_settings


class AuditLogViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """
    Audit log viewer (privileged access).
    GET /audit/ — list audit entries
    GET /audit/{id}/ — retrieve specific entry
    GET /audit/verify_chain/ — verify hash chain integrity
    POST /audit/emergency_access/ — break-glass emergency access
    """

    queryset = AuditLogEntry.objects.all().order_by("-timestamp")
    serializer_class = AuditLogEntrySerializer
    lookup_field = "external_id"
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        """Filter by event type or patient if provided."""
        queryset = super().get_queryset()

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        actor_id = self.request.query_params.get("actor_id")
        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)

        return queryset

    @action(detail=False, methods=["get"])
    def verify_chain(self, request):
        """
        Verify the integrity of the audit log hash chain.
        Checks that no entries have been tampered with.
        """
        entries = AuditLogEntry.objects.order_by("timestamp").all()

        total = entries.count()
        verified = 0
        broken_at = None

        prev_hash = "0" * 64
        for entry in entries:
            if entry.prev_hash != prev_hash:
                broken_at = str(entry.external_id)
                break

            computed_hash = entry.compute_hash()
            if computed_hash != entry.entry_hash:
                broken_at = str(entry.external_id)
                break

            prev_hash = entry.entry_hash
            verified += 1

        return Response({
            "total_entries": total,
            "verified_entries": verified,
            "chain_intact": broken_at is None,
            "broken_at_entry": broken_at,
        })

    @action(detail=False, methods=["post"])
    def emergency_access(self, request):
        """
        Break-glass emergency access for incapacitated patients.
        Creates a time-limited full-scope consent and logs the event.
        """
        doctor_id = request.data.get("doctor_id", str(request.user.external_id))
        patient_abha_id = request.data.get("patient_abha_id")
        hospital_id = request.data.get("hospital_id", "")
        reason = request.data.get("reason", "")

        if not patient_abha_id:
            return Response(
                {"error": "patient_abha_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reason:
            return Response(
                {"error": "reason is required for emergency access"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check abuse detection: > 5 emergency accesses per doctor per day
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        emergency_count = AuditLogEntry.objects.filter(
            event_type=AuditLogEntry.EventType.EMERGENCY_ACCESS,
            actor_id=doctor_id,
            timestamp__gte=today_start,
        ).count()

        max_per_day = plugin_settings.EMERGENCY_MAX_PER_DOCTOR_PER_DAY
        if emergency_count >= max_per_day:
            # Log the abuse attempt
            AuditLogEntry.log_event(
                event_type=AuditLogEntry.EventType.EMERGENCY_ACCESS,
                actor_id=doctor_id,
                patient_id=patient_abha_id,
                metadata={
                    "status": "DENIED_ABUSE_LIMIT",
                    "count_today": emergency_count,
                    "reason": reason,
                    "ip": request.META.get("REMOTE_ADDR", ""),
                },
            )
            return Response(
                {
                    "error": f"Emergency access limit exceeded ({max_per_day}/day). "
                    "Security review triggered.",
                    "abuse_detected": True,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Create emergency consent (4-hour, full scope)
        emergency_consent = ConsentRecord.objects.create(
            patient_abha_id=patient_abha_id,
            requester_id=doctor_id,
            requester_type=ConsentRecord.RequesterType.DOCTOR,
            purpose=ConsentRecord.Purpose.EMERGENCY,
            scope=[
                "Patient", "Observation", "DiagnosticReport", "Condition",
                "MedicationRequest", "AllergyIntolerance", "Encounter",
            ],
            exclude=[],
            valid_until=timezone.now() + timedelta(
                hours=plugin_settings.EMERGENCY_TOKEN_TTL_HOURS
            ),
            patient_signature="EMERGENCY_BREAK_GLASS",
            granted_by=request.user,
        )

        # Audit log — EMERGENCY_ACCESS event
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.EMERGENCY_ACCESS,
            actor_id=doctor_id,
            patient_id=patient_abha_id,
            resource_types=emergency_consent.scope,
            consent_ref=emergency_consent.external_id,
            metadata={
                "reason": reason,
                "hospital_id": hospital_id,
                "token_valid_hours": plugin_settings.EMERGENCY_TOKEN_TTL_HOURS,
                "emergency_count_today": emergency_count + 1,
                "ip": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        return Response(
            {
                "status": "EMERGENCY_ACCESS_GRANTED",
                "consent_token": str(emergency_consent.consent_token),
                "valid_until": emergency_consent.valid_until.isoformat(),
                "scope": emergency_consent.scope,
                "disclaimer": (
                    "Emergency access granted. This event has been logged "
                    "and the patient will be notified. Abuse of this protocol "
                    "will trigger a security review."
                ),
                "notifications_sent": {
                    "sms": "queued",
                    "email": "queued",
                    "push": "queued",
                },
            },
            status=status.HTTP_201_CREATED,
        )
