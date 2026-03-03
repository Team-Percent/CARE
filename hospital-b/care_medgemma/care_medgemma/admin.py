from django.contrib import admin

from care_medgemma.models.audit_log import AuditLogEntry
from care_medgemma.models.consent import ConsentRecord
from care_medgemma.models.fhir_export import FHIRExportRecord
from care_medgemma.models.medgemma import MedGemmaAnalysis


@admin.register(FHIRExportRecord)
class FHIRExportRecordAdmin(admin.ModelAdmin):
    list_display = ["external_id", "patient_abha_id", "fhir_version", "resource_count", "created_date"]
    list_filter = ["fhir_version"]
    search_fields = ["patient_abha_id"]
    readonly_fields = ["external_id", "created_date"]


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ["external_id", "patient_abha_id", "requester_type", "purpose", "status", "valid_until"]
    list_filter = ["status", "requester_type", "purpose"]
    search_fields = ["patient_abha_id", "requester_id"]
    readonly_fields = ["external_id", "consent_token", "granted_at", "created_date"]


@admin.register(MedGemmaAnalysis)
class MedGemmaAnalysisAdmin(admin.ModelAdmin):
    list_display = ["external_id", "analysis_type", "status", "is_mock", "created_date"]
    list_filter = ["analysis_type", "status", "is_mock"]
    readonly_fields = ["external_id", "created_date"]


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ["external_id", "event_type", "actor_id", "patient_id", "timestamp"]
    list_filter = ["event_type"]
    search_fields = ["actor_id", "patient_id"]
    readonly_fields = ["external_id", "entry_hash", "prev_hash", "created_date"]
