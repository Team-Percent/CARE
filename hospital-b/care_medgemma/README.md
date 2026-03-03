# care_medgemma

CARE EMR Plugin for MedGemma AI Analysis, FHIR R5 Export, Consent Management, and Audit Logging.

## Features

- **FHIR R5 Bundle Export** — Export patient records as FHIR R5 bundles
- **Consent Management** — DEPA-compliant consent grant/revoke/list
- **MedGemma Analysis** — AI-powered report analysis (mocked for demo)
- **Audit Logging** — Cryptographically chained audit trail
- **Emergency Access** — Break-glass protocol for incapacitated patients

## Installation

This plugin is designed to be installed into a CARE backend instance via the plugin system.

```python
# plug_config.py
from plugs.plug import Plug

plugs = [
    Plug(
        name="care_medgemma",
        package_name="./care_medgemma",
        version="",
        configs={"MEDGEMMA_MOCK_MODE": True},
    ),
]
```

## API Endpoints

All endpoints are available at `/api/care_medgemma/`.

| Endpoint | Method | Description |
|---|---|---|
| `health` | GET | Health check |
| `fhir/<abha_id>/bundle/` | GET | FHIR R5 patient bundle |
| `consent/` | GET/POST | Consent management |
| `consent/<id>/revoke/` | POST | Revoke consent |
| `medgemma/` | POST | Submit for analysis |
| `medgemma/<id>/` | GET | Retrieve analysis |
| `audit/` | GET | View audit log |
| `emergency-access/` | POST | Break-glass access |
