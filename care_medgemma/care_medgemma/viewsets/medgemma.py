import base64
import io
import logging

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

logger = logging.getLogger(__name__)

# Supported MIME types for MedGemma analysis
ANALYZABLE_MIME_TYPES = {
    # Documents
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/rtf",
    "application/msword",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/tiff",
    # Any other type — we'll try to read it as text
}


def _extract_text_from_pdf(content_bytes):
    """Extract text from PDF bytes using PyPDF2."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"PDF text extraction failed: {e}")
        return ""


def _resolve_patient(patient_id_str):
    """
    Resolve a patient by ABHA ID (from meta) or UUID.
    Returns (Patient, method) or (None, None).
    """
    from care.emr.models import Patient

    if not patient_id_str:
        return None, None

    # Try ABHA ID lookup (stored in Patient.meta.abha_id)
    patient = Patient.objects.filter(meta__abha_id=patient_id_str).first()
    if patient:
        return patient, "abha"

    # Try by external_id (UUID)
    try:
        patient = Patient.objects.get(external_id=patient_id_str)
        return patient, "uuid"
    except (Patient.DoesNotExist, ValueError):
        pass

    # Try by name (fallback)
    patient = Patient.objects.filter(name__icontains=patient_id_str).first()
    if patient:
        return patient, "name"

    return None, None


def _pull_patient_files(patient):
    """
    Pull all uploaded files for a patient from MinIO.
    Returns list of dicts: [{filename, mime_type, text_content, is_image, base64_data}]
    """
    from care.emr.models.file_upload import FileUpload

    file_uploads = FileUpload.objects.filter(
        associating_id=str(patient.external_id),
        upload_completed=True,
    ).order_by("created_date")

    patient_files = []

    for file_obj in file_uploads:
        mime_type = file_obj.meta.get("mime_type", "application/octet-stream")

        try:
            content_type, content_bytes = file_obj.files_manager.file_contents(file_obj)
        except Exception as e:
            logger.warning(f"Failed to download {file_obj.name} from MinIO: {e}")
            continue

        file_entry = {
            "filename": file_obj.name,
            "mime_type": mime_type,
            "text_content": "",
            "is_image": False,
            "base64_data": None,
        }

        if mime_type == "application/pdf":
            file_entry["text_content"] = _extract_text_from_pdf(content_bytes)
        elif mime_type.startswith("image/"):
            file_entry["is_image"] = True
            file_entry["base64_data"] = base64.b64encode(content_bytes).decode("utf-8")
        elif mime_type.startswith("text/"):
            try:
                file_entry["text_content"] = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                file_entry["text_content"] = content_bytes.decode("latin-1", errors="replace")
        else:
            # Try to read as text for unknown types
            try:
                file_entry["text_content"] = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                logger.warning(f"Cannot extract content from {file_obj.name} ({mime_type})")
                continue

        patient_files.append(file_entry)

    return patient_files


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
        Submit patient data for MedGemma analysis.

        When patient_id (ABHA ID) is provided, the system:
        1. Looks up the patient by ABHA ID, UUID, or name
        2. Pulls all uploaded files from MinIO
        3. Extracts text from PDFs and encodes images
        4. Feeds everything to the MedGemma/Ollama engine

        Accepts all file types: PDF, images, text, CSV, spreadsheets, etc.
        """
        serializer = MedGemmaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        analysis_type = data["analysis_type"]
        input_data = data.get("input_data", {})
        preset = data.get("preset", "")
        patient_id_str = data.get("patient_id", "")

        # Resolve encounter if provided
        encounter = None
        encounter_id = data.get("encounter_id", "")
        if encounter_id:
            try:
                from care.emr.models.encounter import Encounter
                encounter = Encounter.objects.get(external_id=encounter_id)
            except Exception:
                pass

        # Resolve patient and pull files from MinIO
        patient = None
        patient_files = []
        patient_resolve_method = None

        if patient_id_str:
            patient, patient_resolve_method = _resolve_patient(patient_id_str)
            if patient:
                patient_files = _pull_patient_files(patient)
                # Enrich input_data with patient info
                input_data["patient_info"] = {
                    "name": patient.name,
                    "gender": patient.gender,
                    "blood_group": patient.blood_group or "unknown",
                    "abha_id": patient.meta.get("abha_id", ""),
                    "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else "",
                    "address": patient.address or "",
                }
                input_data["files_count"] = len(patient_files)
                input_data["files_summary"] = [
                    {
                        "filename": f["filename"],
                        "mime_type": f["mime_type"],
                        "has_text": bool(f["text_content"]),
                        "is_image": f["is_image"],
                    }
                    for f in patient_files
                ]

        # Run analysis (mock or real)
        is_mock = plugin_settings.MEDGEMMA_MOCK_MODE
        if is_mock:
            result = mock_medgemma.analyze(analysis_type, input_data)
        else:
            from care_medgemma import real_medgemma
            result = real_medgemma.analyze(
                analysis_type,
                input_data,
                preset=preset or None,
                patient_files=patient_files,
            )

        # Save analysis record
        analysis = MedGemmaAnalysis.objects.create(
            encounter=encounter,
            requested_by=request.user,
            input_bundle=input_data,
            analysis_type=analysis_type,
            analysis_result=result,
            status=MedGemmaAnalysis.Status.COMPLETED,
            model_version=result.get("model_version", "medgemma-mock-1.0"),
            is_mock=result.get("is_mock", is_mock),
            processing_time_ms=result.get("processing_time_ms"),
        )

        # Audit log
        AuditLogEntry.log_event(
            event_type=AuditLogEntry.EventType.ANALYSIS_REQUEST,
            actor_id=str(request.user.external_id),
            patient_id=str(patient.external_id) if patient else "",
            resource_types=[analysis_type],
            metadata={
                "analysis_id": str(analysis.external_id),
                "is_mock": result.get("is_mock", is_mock),
                "preset": preset or analysis_type,
                "patient_id": patient_id_str,
                "patient_resolved_by": patient_resolve_method or "",
                "files_analyzed": len(patient_files),
                "ip": request.META.get("REMOTE_ADDR", ""),
            },
        )

        return Response(
            MedGemmaAnalysisSerializer(analysis).data,
            status=status.HTTP_201_CREATED,
        )

