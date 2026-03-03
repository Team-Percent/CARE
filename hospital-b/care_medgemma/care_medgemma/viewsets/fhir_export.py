from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination

from care_medgemma.fhir_utils import create_sample_bundle, filter_bundle_by_scope
from care_medgemma.models.audit_log import AuditLogEntry
from care_medgemma.models.consent import ConsentRecord
from care_medgemma.models.fhir_export import FHIRExportRecord
from care_medgemma.serializers.fhir_export import FHIRExportSerializer


class FHIRExportViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """
    FHIR R5 bundle export endpoint.
    GET /fhir/ — list all exports
    GET /fhir/{id}/ — retrieve specific export
    GET /fhir/patient_bundle/?abha_id=xxx — generate FHIR bundle for patient
    """

    queryset = FHIRExportRecord.objects.all().order_by("-created_date")
    serializer_class = FHIRExportSerializer
    lookup_field = "external_id"
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=["get"], url_path="patient_bundle")
    def patient_bundle(self, request):
        """
        Generate and return a FHIR R5 bundle for a patient.
        Query params:
            abha_id (required): Patient ABHA ID
            consent_token (optional): Consent token for scope filtering
        """
        abha_id = request.query_params.get("abha_id")
        consent_token = request.query_params.get("consent_token")

        if not abha_id:
            return Response(
                {"error": "abha_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate sample FHIR bundle (in production, this would query CARE DB)
        bundle = create_sample_bundle(
            abha_id=abha_id,
            patient_name="Demo Patient",
        )

        # Apply consent scope filtering if consent token provided
        scope = []
        exclude = []
        consent_ref = None

        if consent_token:
            try:
                consent = ConsentRecord.objects.get(
                    consent_token=consent_token,
                    status=ConsentRecord.Status.ACTIVE,
                )
                if not consent.is_valid:
                    return Response(
                        {"error": "Consent token is expired or revoked"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                scope = consent.scope
                exclude = consent.exclude
                consent_ref = consent.external_id
            except ConsentRecord.DoesNotExist:
                return Response(
                    {"error": "Invalid consent token"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if scope or exclude:
            bundle = filter_bundle_by_scope(bundle, scope, exclude)

        # Save export record
        export_record = FHIRExportRecord.objects.create(
            patient_abha_id=abha_id,
            requester=request.user,
            bundle_json=bundle,
            resource_types=[
                entry["resource"]["resourceType"]
                for entry in bundle.get("entry", [])
            ],
            consent_ref=consent_ref,
            resource_count=bundle.get("total", 0),
        )

        # Audit log
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.FHIR_EXPORT,
            actor_id=str(request.user.external_id),
            patient_id=abha_id,
            resource_types=export_record.resource_types,
            consent_ref=consent_ref,
            metadata={
                "ip": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        return Response(bundle, status=status.HTTP_200_OK)
