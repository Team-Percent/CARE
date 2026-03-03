import uuid

from care.utils.models.base import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class FHIRExportRecord(BaseModel):
    """Tracks FHIR R5 bundle exports per patient for audit and caching."""

    class FHIRVersion(models.TextChoices):
        R5 = "R5", "FHIR R5"
        R4 = "R4", "FHIR R4"

    patient_abha_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="ABHA ID of the patient whose records are exported",
    )
    requester = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        help_text="User who requested the export",
    )
    bundle_json = models.JSONField(
        default=dict,
        help_text="The FHIR R5 Bundle JSON content",
    )
    fhir_version = models.CharField(
        max_length=5,
        choices=FHIRVersion.choices,
        default=FHIRVersion.R5,
    )
    resource_types = models.JSONField(
        default=list,
        help_text="List of FHIR resource types included in this bundle",
    )
    consent_ref = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to the consent artifact that authorized this export",
    )
    resource_count = models.IntegerField(
        default=0,
        help_text="Number of resources in the bundle",
    )

    class Meta:
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=["patient_abha_id", "-created_date"]),
        ]

    def __str__(self):
        return f"FHIRExport {self.external_id} - {self.patient_abha_id} ({self.fhir_version})"
