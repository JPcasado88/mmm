#!/bin/bash

echo "🚀 Setting up MMM Platform..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "PostgreSQL is required but not installed. Aborting." >&2; exit 1; }

# Backend setup
echo "📦 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy env file
cp .env.example .env
echo "⚠️  Please update backend/.env with your database credentials"

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend
npm install

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your database credentials"
echo "2. Create database: createdb mmm_db"
echo "3. Run backend: cd backend && python main.py"
echo "4. Run frontend: cd frontend && npm start"
echo ""
echo "Or use Docker: docker-compose up"