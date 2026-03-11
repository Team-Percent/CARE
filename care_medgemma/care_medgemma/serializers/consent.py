
from rest_framework import serializers
from django.utils import timezone

from care_medgemma.models.consent import ConsentRecord


class ConsentRecordSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = ConsentRecord
        fields = [
            "external_id",
            "patient_abha_id",
            "requester_id",
            "requester_type",
            "purpose",
            "scope",
            "exclude",
            "valid_from",
            "valid_until",
            "granted_at",
            "revoked_at",
            "consent_token",
            "status",
            "is_valid",
            "created_date",
        ]
        read_only_fields = [
            "external_id",
            "granted_at",
            "revoked_at",
            "consent_token",
            "status",
            "is_valid",
            "created_date",
        ]

    def validate_valid_until(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Consent expiry must be in the future."
            )
        return value

    def validate_scope(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError(
                "Scope must be a non-empty list of FHIR resource types."
            )
        valid_types = {
            "Patient", "Observation", "DiagnosticReport", "Condition",
            "MedicationRequest", "AllergyIntolerance", "Encounter",
            "Consent", "Bundle", "AuditEvent",
        }
        for item in value:
            if item not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid FHIR resource type: {item}. "
                    f"Allowed: {', '.join(sorted(valid_types))}"
                )
        return value


class ConsentGrantSerializer(serializers.Serializer):
    """Serializer for granting consent."""
    patient_abha_id = serializers.CharField(max_length=50)
    requester_id = serializers.CharField(max_length=255)
    requester_type = serializers.ChoiceField(
        choices=ConsentRecord.RequesterType.choices
    )
    purpose = serializers.ChoiceField(
        choices=ConsentRecord.Purpose.choices
    )
    scope = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
    )
    exclude = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    valid_until = serializers.DateTimeField()
    patient_signature = serializers.CharField(
        required=False,
        default="",
    )


class ConsentRevokeSerializer(serializers.Serializer):
    """Serializer for revoking consent."""
    reason = serializers.CharField(required=False, default="")
