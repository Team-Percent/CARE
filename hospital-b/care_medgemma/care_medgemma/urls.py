from django.shortcuts import HttpResponse
from django.urls import path
from rest_framework.routers import DefaultRouter

from care_medgemma.viewsets.fhir_export import FHIRExportViewSet
from care_medgemma.viewsets.consent import ConsentViewSet
from care_medgemma.viewsets.medgemma import MedGemmaViewSet
from care_medgemma.viewsets.audit_log import AuditLogViewSet


def healthy(request):
    return HttpResponse("OK")


router = DefaultRouter()
router.register("fhir", FHIRExportViewSet, basename="fhir-export")
router.register("consent", ConsentViewSet, basename="consent")
router.register("medgemma", MedGemmaViewSet, basename="medgemma")
router.register("audit", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("health", healthy),
] + router.urls
