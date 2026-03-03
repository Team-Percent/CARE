import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def expire_consents():
    """
    Background task to mark expired consents.
    Runs periodically to clean up expired consent artifacts.
    """
    from care_medgemma.models.consent import ConsentRecord

    expired = ConsentRecord.objects.filter(
        status=ConsentRecord.Status.ACTIVE,
        valid_until__lt=timezone.now(),
    )
    count = expired.update(status=ConsentRecord.Status.EXPIRED)
    if count:
        logger.info("care_medgemma: Expired %d consent(s)", count)


@shared_task
def process_fhir_export(patient_abha_id, requester_id):
    """
    Async FHIR bundle generation for large patient records.
    Can be called when immediate response is not needed.
    """
    logger.info(
        "care_medgemma: Processing FHIR export for patient %s (requester: %s)",
        patient_abha_id,
        requester_id,
    )
    # In production, this would generate the full FHIR bundle
    # and cache it for quick retrieval


@shared_task
def run_medgemma_analysis(analysis_id):
    """
    Async MedGemma analysis for large or complex inputs.
    """
    from care_medgemma.models.medgemma import MedGemmaAnalysis
    from care_medgemma import mock_medgemma

    try:
        analysis = MedGemmaAnalysis.objects.get(external_id=analysis_id)
        analysis.status = MedGemmaAnalysis.Status.PROCESSING
        analysis.save(update_fields=["status"])

        result = mock_medgemma.analyze(
            analysis.analysis_type,
            analysis.input_bundle,
        )

        analysis.analysis_result = result
        analysis.status = MedGemmaAnalysis.Status.COMPLETED
        analysis.processing_time_ms = result.get("processing_time_ms")
        analysis.save(
            update_fields=["analysis_result", "status", "processing_time_ms"]
        )

        logger.info(
            "care_medgemma: Completed analysis %s (%s)",
            analysis_id,
            analysis.analysis_type,
        )
    except MedGemmaAnalysis.DoesNotExist:
        logger.error("care_medgemma: Analysis %s not found", analysis_id)
    except Exception as e:
        logger.error("care_medgemma: Analysis %s failed: %s", analysis_id, str(e))
        try:
            analysis.status = MedGemmaAnalysis.Status.FAILED
            analysis.save(update_fields=["status"])
        except Exception:
            pass
