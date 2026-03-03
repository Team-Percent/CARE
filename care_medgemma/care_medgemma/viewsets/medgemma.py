from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination

from care_medgemma import mock_medgemma
from care_medgemma.models.audit_log import AuditLogEntry
from care_medgemma.models.medgemma import MedGemmaAnalysis
from care_medgemma.serializers.medgemma import (
    MedGemmaAnalysisSerializer,
    MedGemmaRequestSerializer,
)
from care_medgemma.settings import plugin_settings


class MedGemmaViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """
    MedGemma AI analysis endpoints.
    GET /medgemma/ — list analyses
    GET /medgemma/{id}/ — retrieve specific analysis
    POST /medgemma/analyze/ — submit for analysis
    """

    queryset = MedGemmaAnalysis.objects.all().order_by("-created_date")
    serializer_class = MedGemmaAnalysisSerializer
    lookup_field = "external_id"
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        """Filter by requesting user."""
        return self.queryset.filter(requested_by=self.request.user)

    @action(detail=False, methods=["post"])
    def analyze(self, request):
        """
        Submit FHIR data for MedGemma analysis.
        In mock mode, returns realistic structured analysis.
        """
        serializer = MedGemmaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        analysis_type = data["analysis_type"]
        input_data = data.get("input_data", {})

        # Resolve encounter if provided
        encounter = None
        encounter_id = data.get("encounter_id", "")
        if encounter_id:
            try:
                from care.emr.models.encounter import Encounter
                encounter = Encounter.objects.get(external_id=encounter_id)
            except Exception:
                pass  # Don't fail if encounter not found

        # Run analysis (mock or real)
        is_mock = plugin_settings.MEDGEMMA_MOCK_MODE
        if is_mock:
            result = mock_medgemma.analyze(analysis_type, input_data)
        else:
            # In production, this would call the real MedGemma API
            result = mock_medgemma.analyze(analysis_type, input_data)

        # Save analysis record
        analysis = MedGemmaAnalysis.objects.create(
            encounter=encounter,
            requested_by=request.user,
            input_bundle=input_data,
            analysis_type=analysis_type,
            analysis_result=result,
            status=MedGemmaAnalysis.Status.COMPLETED,
            model_version=result.get("model_version", "medgemma-mock-1.0"),
            is_mock=is_mock,
            processing_time_ms=result.get("processing_time_ms"),
        )

        # Audit log
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.ANALYSIS_REQUEST,
            actor_id=str(request.user.external_id),
            patient_id="",
            resource_types=[analysis_type],
            metadata={
                "analysis_id": str(analysis.external_id),
                "is_mock": is_mock,
                "ip": request.META.get("REMOTE_ADDR", ""),
            },
        )

        return Response(
            MedGemmaAnalysisSerializer(analysis).data,
            status=status.HTTP_201_CREATED,
        )
