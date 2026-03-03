#!/bin/bash
# ─── Hospital B — Metro Radiology Setup Script ───
# Run this on PC-2 (Internal Network 2)

set -e
echo "═══ Setting Up Hospital B — Metro Radiology & Diagnostics ═══"

# 1. Clone CARE Backend
if [ ! -d "care_be" ]; then
    echo "📦 Cloning CARE Backend..."
    git clone https://github.com/ohcnetwork/care.git care_be
fi

# 2. Clone CARE Frontend
if [ ! -d "care_fe" ]; then
    echo "📦 Cloning CARE Frontend..."
    git clone https://github.com/ohcnetwork/care_fe.git care_fe
fi

# 3. Clone MedGemma Plugin
if [ ! -d "care_medgemma" ]; then
    echo "📦 Cloning MedGemma Plugin..."
    cp -r ../care_medgemma ./care_medgemma
fi

# 4. Create .env from example
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from .env.example..."
    cp .env.example .env
    echo "   ⚠️  Edit .env to set your UHI_SWITCH_URL"
fi

# 5. Start services
echo "🚀 Starting Hospital B services..."
docker compose up -d

echo ""
echo "═══ Hospital B Ready! ═══"
echo "  Backend:  http://localhost:9001"
echo "  Frontend: http://localhost:4001"
echo "  MedGemma: http://localhost:4001/medgemma"
echo ""
echo "Next: Register this hospital with UHI Switch"
echo "  curl -X POST \$UHI_SWITCH_URL/hospital/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\":\"Metro Radiology & Diagnostics\",\"endpoint_url\":\"http://localhost:9001\",\"city\":\"Mumbai\",\"state\":\"Maharashtra\"}'"
