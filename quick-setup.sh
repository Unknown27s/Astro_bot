#!/bin/bash
# AstroBot Quick Setup Script

echo "🚀 Setting up AstroBot..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose required"; exit 1; }

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Cloud LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./data/astrobot.db
CHROMA_PERSIST_DIR=./data/chroma_db

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created. Please edit with your API keys."
fi

# Create data directories
mkdir -p data/uploads data/chroma_db

# Pull and start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost:8000/health || echo "⚠️ API service not ready"
curl -f http://localhost:8080/actuator/health || echo "⚠️ Backend service not ready"

echo "✅ Setup complete!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 API: http://localhost:8000/docs"
echo "📊 Admin: http://localhost:8080/admin"
