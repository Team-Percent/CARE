#!/bin/bash
# ─── Hospital A — CityCare Setup Script ───
# Run this on PC-1 (Internal Network 1)

set -e
echo "═══ Setting Up Hospital A — CityCare Multispeciality ═══"

# 1. Clone CARE Backend (OHC fork with MedGemma support)
if [ ! -d "care_be" ]; then
    echo "📦 Cloning CARE Backend..."
    git clone https://github.com/Team-Percent/care_be.git care_be
fi

# 2. Clone CARE Frontend (OHC fork with MedGemma dashboard)
if [ ! -d "care_fe" ]; then
    echo "📦 Cloning CARE Frontend..."
    git clone https://github.com/Team-Percent/care_fe.git care_fe
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
echo "🚀 Starting Hospital A services..."
docker compose up -d

echo ""
echo "═══ Hospital A Ready! ═══"
echo "  Backend:  http://localhost:9000"
echo "  Frontend: http://localhost:4000"
echo "  MedGemma: http://localhost:4000/medgemma"
echo ""
echo "Next: Register this hospital with UHI Switch"
echo "  curl -X POST \$UHI_SWITCH_URL/hospital/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\":\"CityCare Multispeciality Hospital\",\"endpoint_url\":\"http://localhost:9000\",\"city\":\"Chennai\",\"state\":\"Tamil Nadu\"}'"
