from rest_framework import serializers

from care_medgemma.models.medgemma import MedGemmaAnalysis


class MedGemmaAnalysisSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(
        source="requested_by.get_full_name", read_only=True
    )

    class Meta:
        model = MedGemmaAnalysis
        fields = [
            "external_id",
            "encounter",
            "requester_name",
            "input_bundle",
            "analysis_type",
            "analysis_result",
            "status",
            "model_version",
            "is_mock",
            "disclaimer",
            "processing_time_ms",
            "created_date",
        ]
        read_only_fields = [
            "external_id",
            "requester_name",
            "analysis_result",
            "status",
            "model_version",
            "is_mock",
            "disclaimer",
            "processing_time_ms",
            "created_date",
        ]


class MedGemmaRequestSerializer(serializers.Serializer):
    """Serializer for submitting an analysis request."""
    analysis_type = serializers.ChoiceField(
        choices=MedGemmaAnalysis.AnalysisType.choices,
    )
    input_data = serializers.JSONField(
        required=False,
        default=dict,
    )
    encounter_id = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
