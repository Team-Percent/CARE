import uuid

from care.utils.models.base import BaseModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class ConsentRecord(BaseModel):
    """
    DEPA-compliant consent artifact for patient data sharing.
    Implements the consent model from SECURITY.md and PRD.md.
    """

    class RequesterType(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        HOSPITAL = "hospital", "Hospital"
        PATIENT = "patient", "Patient"

    class Purpose(models.TextChoices):
        DIAGNOSIS = "diagnosis", "Diagnosis"
        SECOND_OPINION = "second_opinion", "Second Opinion"
        RESEARCH = "research", "Research"
        EMERGENCY = "emergency", "Emergency"
        FOLLOW_UP = "follow_up", "Follow Up"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"
        PENDING = "PENDING", "Pending"

    # Identity
    patient_abha_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="ABHA ID of the patient granting consent",
    )
    requester_id = models.CharField(
        max_length=255,
        help_text="ID of the doctor/hospital/patient requesting access",
    )
    requester_type = models.CharField(
        max_length=20,
        choices=RequesterType.choices,
    )

    # Scope
    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
    )
    scope = models.JSONField(
        default=list,
        help_text='FHIR resource types allowed. e.g. ["DiagnosticReport", "Observation"]',
    )
    exclude = models.JSONField(
        default=list,
        help_text='FHIR resource types explicitly excluded. e.g. ["MentalHealthRecord"]',
    )

    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(
        help_text="Consent expiry time",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Auth
    patient_signature = models.TextField(
        blank=True,
        default="",
        help_text="Patient-signed JWT claim for non-repudiation",
    )
    consent_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Short-lived scoped consent token",
    )

    # Status
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    granted_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="consents_granted",
    )

    class Meta:
        ordering = ["-granted_at"]
        indexes = [
            models.Index(fields=["patient_abha_id", "status"]),
            models.Index(fields=["consent_token"]),
            models.Index(fields=["requester_id", "requester_type"]),
        ]

    @property
    def is_valid(self):
        """Check if consent is currently valid."""
        now = timezone.now()
        return (
            self.status == self.Status.ACTIVE
            and self.valid_from <= now <= self.valid_until
            and self.revoked_at is None
        )

    def revoke(self):
        """Revoke this consent immediately."""
        self.status = self.Status.REVOKED
        self.revoked_at = timezone.now()
        self.save(update_fields=["status", "revoked_at", "modified_date"])

    def __str__(self):
        return (
            f"Consent {self.external_id} - {self.patient_abha_id} → "
            f"{self.requester_type}:{self.requester_id} ({self.status})"
        )
