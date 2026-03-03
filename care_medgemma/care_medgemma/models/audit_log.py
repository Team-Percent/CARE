import hashlib
import json

from care.utils.models.base import BaseModel
from django.db import models
from django.utils import timezone


class AuditLogEntry(BaseModel):
    """
    Immutable, cryptographically chained audit log entry.
    Each entry's hash includes the previous entry's hash, making
    retroactive tampering detectable.
    """

    class EventType(models.TextChoices):
        DATA_ACCESS = "DATA_ACCESS", "Data Access"
        CONSENT_GRANT = "CONSENT_GRANT", "Consent Grant"
        CONSENT_REVOKE = "CONSENT_REVOKE", "Consent Revoke"
        EMERGENCY_ACCESS = "EMERGENCY_ACCESS", "Emergency Access"
        FHIR_EXPORT = "FHIR_EXPORT", "FHIR Export"
        ANALYSIS_REQUEST = "ANALYSIS_REQUEST", "Analysis Request"
        LOGIN = "LOGIN", "Login"

    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
    )
    actor_id = models.CharField(
        max_length=255,
        help_text="ABHA, doctor_id, or hospital_id of the actor",
    )
    patient_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="ABHA ID of the patient whose data was accessed",
    )
    resource_types = models.JSONField(
        default=list,
        help_text="FHIR resource types accessed",
    )
    consent_ref = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to consent artifact that authorized this action",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(
        default=dict,
        help_text="Additional context: ip, user_agent, etc.",
    )

    # Hash chain
    prev_hash = models.CharField(
        max_length=64,
        default="0" * 64,
        help_text="SHA-256 hash of the previous audit log entry",
    )
    entry_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of this entry (content + prev_hash)",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["event_type", "-timestamp"]),
            models.Index(fields=["actor_id", "-timestamp"]),
            models.Index(fields=["patient_id", "-timestamp"]),
        ]

    def compute_hash(self):
        """Compute the SHA-256 hash for this entry."""
        content = json.dumps(
            {
                "event_type": self.event_type,
                "actor_id": self.actor_id,
                "patient_id": self.patient_id,
                "resource_types": self.resource_types,
                "consent_ref": str(self.consent_ref) if self.consent_ref else None,
                "timestamp": self.timestamp.isoformat() if self.timestamp else "",
                "metadata": self.metadata,
            },
            sort_keys=True,
        )
        return hashlib.sha256(
            f"{content}{self.prev_hash}".encode()
        ).hexdigest()

    def save(self, *args, **kwargs):
        # Get the previous entry's hash for chaining
        if not self.entry_hash:
            last_entry = (
                AuditLogEntry.objects.order_by("-timestamp").first()
            )
            if last_entry:
                self.prev_hash = last_entry.entry_hash
            else:
                self.prev_hash = "0" * 64

            self.entry_hash = self.compute_hash()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Audit {self.event_type} by {self.actor_id} at {self.timestamp}"

    @classmethod
    def log_event(cls, event_type, actor_id, patient_id="", resource_types=None,
                  consent_ref=None, metadata=None):
        """Create a new audit log entry."""
        return cls.objects.create(
            event_type=event_type,
            actor_id=actor_id,
            patient_id=patient_id,
            resource_types=resource_types or [],
            consent_ref=consent_ref,
            metadata=metadata or {},
        )
