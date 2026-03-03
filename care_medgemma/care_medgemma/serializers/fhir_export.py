from rest_framework import serializers

from care_medgemma.models.fhir_export import FHIRExportRecord


class FHIRExportSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(
        source="requester.get_full_name", read_only=True
    )

    class Meta:
        model = FHIRExportRecord
        fields = [
            "external_id",
            "patient_abha_id",
            "requester_name",
            "bundle_json",
            "fhir_version",
            "resource_types",
            "consent_ref",
            "resource_count",
            "created_date",
        ]
        read_only_fields = [
            "external_id",
            "requester_name",
            "bundle_json",
            "resource_count",
            "created_date",
        ]
