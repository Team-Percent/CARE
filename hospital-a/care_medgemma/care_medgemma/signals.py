import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from care.emr.models.encounter import Encounter

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Encounter)
def hook_encounter_created(sender, instance, created, **kwargs):
    """
    Hook into encounter creation to trigger MedGemma analysis
    or FHIR export in the future. For now, just log it.
    """
    if created:
        logger.info(
            "care_medgemma: New encounter created: %s",
            instance.external_id,
        )
