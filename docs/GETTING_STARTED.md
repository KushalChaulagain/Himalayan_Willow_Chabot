# Getting Started with Himalayan Willow AI Chatbot

This guide will help you set up and run the Himalayan Willow AI Chatbot locally for development.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- **PostgreSQL** database (local or cloud)
- **Git** installed
- **Google AI Studio** account (for Gemini API key)

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/himalayan-willow-bot.git
cd himalayan-willow-bot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Edit .env file with your credentials
# Minimum required:
# - GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)
# - DATABASE_URL (PostgreSQL connection string)
# - JWT_SECRET (any random string)
```

### 3. Database Setup

```bash
# Run migrations
python scripts/run_migrations.py

# Seed sample products
python scripts/seed_products.py
```

### 4. Start Backend Server

```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 5. Frontend Setup (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Edit .env file
# VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 6. Test the Chatbot

Open `http://localhost:5173` in your browser. You should see a chat widget button in the bottom-right corner. Click it and start chatting!

## Configuration

### Environment Variables

#### Backend (.env)

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/himalayan_willow
JWT_SECRET=your_random_secret_key

# Optional (for full functionality)
ESEWA_MERCHANT_ID=your_esewa_merchant_id
ESEWA_SECRET_KEY=your_esewa_secret_key
KHALTI_SECRET_KEY=your_khalti_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

#### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
```

## Getting API Keys

### Google Gemini API Key (Required)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add to backend `.env` as `GEMINI_API_KEY`

**Free Tier**: 15 requests/minute, 1M tokens/day

### PostgreSQL Database (Required)

#### Option 1: Local PostgreSQL

```bash
# Install PostgreSQL
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
CREATE DATABASE himalayan_willow;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/himalayan_willow
```

#### Option 2: Free Cloud Database (Recommended for beginners)

Use [Supabase](https://supabase.com) or [Neon](https://neon.tech):

1. Create free account
2. Create new project
3. Copy connection string
4. Add to `.env` as `DATABASE_URL`

### eSewa & Khalti (Optional - for payment testing)

#### eSewa Test Credentials

1. Go to [eSewa Developer Portal](https://developer.esewa.com.np)
2. Sign up for test account
3. Get test merchant ID and secret key

#### Khalti Test Credentials

1. Go to [Khalti Merchant Dashboard](https://khalti.com)
2. Sign up for merchant account
3. Get test secret key from dashboard

### Telegram Bot (Optional - for notifications)

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to create bot
4. Copy bot token
5. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

## Project Structure

```
himalayan-willow-bot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── config.py       # Configuration
│   │   ├── models/         # Pydantic models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── db/             # Database layer
│   ├── migrations/         # SQL migrations
│   ├── scripts/            # Utility scripts
│   └── tests/              # Tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # State management
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
└── docs/                   # Documentation
```

## Common Tasks

### Add New Products

Edit `backend/scripts/seed_products.py` and add your products to the `SAMPLE_PRODUCTS` list, then run:

```bash
python scripts/seed_products.py
```

### View API Documentation

With backend running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Check Database

```bash
# Connect to database
psql $DATABASE_URL

# View tables
\dt

# View products
SELECT * FROM products LIMIT 5;

# View orders
SELECT * FROM orders;
```

### Clear Chat History

```bash
# Connect to database
psql $DATABASE_URL

# Clear messages
DELETE FROM chat_messages;

# Clear sessions
DELETE FROM chat_sessions;
```

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Make sure you're in the `backend` directory and virtual environment is activated.

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**: Check DATABASE_URL is correct and PostgreSQL is running.

### Frontend won't start

**Error**: `Cannot find module 'react'`

**Solution**: Run `npm install` in frontend directory.

**Error**: `Network Error when sending message`

**Solution**: Ensure backend is running on port 8000 and VITE_API_URL is correct.

### Chat not responding

**Error**: `LLM timeout` or `Gemini API error`

**Solution**: 
1. Check GEMINI_API_KEY is valid
2. Verify you haven't exceeded free tier limits (15 RPM)
3. Check internet connection

### Products not showing

**Solution**: Run seed script:
```bash
cd backend
python scripts/seed_products.py
```

## Next Steps

1. **Customize Products**: Edit `seed_products.py` with your actual cricket products
2. **Customize Branding**: Update colors in `frontend/tailwind.config.js`
3. **Add Real Images**: Replace placeholder images with actual product photos
4. **Configure Payments**: Set up eSewa/Khalti test accounts
5. **Deploy**: Follow [DEPLOYMENT.md](./DEPLOYMENT.md) to deploy to production

## Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and test locally

# 3. Run tests
cd backend && pytest
cd frontend && npm test

# 4. Commit changes
git add .
git commit -m "Add your feature"

# 5. Push to GitHub
git push origin feature/your-feature-name

# 6. Create Pull Request on GitHub
```

## Getting Help

- **Documentation**: Check `docs/` folder
- **API Reference**: `http://localhost:8000/docs`
- **Issues**: Create issue on GitHub
- **PRD**: See `himalayan_willow_chatbot_PRD.docx` for full requirements

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [LangChain Documentation](https://python.langchain.com)
- [eSewa API Documentation](https://developer.esewa.com.np)
- [Khalti API Documentation](https://docs.khalti.com)

## License

Proprietary - Himalayan Willow

---

**Ready to build?** Start with the Quick Start section above and you'll have a working chatbot in 5 minutes! 🏏
