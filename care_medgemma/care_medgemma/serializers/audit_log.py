from rest_framework import serializers

from care_medgemma.models.audit_log import AuditLogEntry


class AuditLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = [
            "external_id",
            "event_type",
            "actor_id",
            "patient_id",
            "resource_types",
            "consent_ref",
            "timestamp",
            "metadata",
            "prev_hash",
            "entry_hash",
            "created_date",
        ]
        read_only_fields = fields
