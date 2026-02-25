# Himalayan Willow AI Chatbot

An AI-powered conversational chatbot for Himalayan Willow cricket store with product recommendations, order management, and Nepal-specific payment integration (eSewa/Khalti/COD).

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **LLM**: Google Gemini Flash 1.5
- **LLM Framework**: LangChain
- **Database**: PostgreSQL
- **Vector DB**: ChromaDB
- **Payments**: eSewa & Khalti
- **Deployment**: Railway

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State**: React Context API
- **Deployment**: Cloudflare Pages

## Project Structure

```
himalayan-willow-bot/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI app entry
│   │   ├── config.py       # Environment config
│   │   ├── models/         # Pydantic models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── db/             # Database layer
│   ├── migrations/         # Database migrations
│   ├── scripts/            # Utility scripts
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React widget
│   ├── src/
│   │   ├── components/     # Chat UI components
│   │   ├── contexts/       # State management
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API client
│   └── package.json        # Node dependencies
└── docs/                   # Documentation
```

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment template:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/himalayan_willow
ESEWA_MERCHANT_ID=your_esewa_merchant_id
ESEWA_SECRET_KEY=your_esewa_secret_key
KHALTI_SECRET_KEY=your_khalti_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

6. Run database migrations:
```bash
python scripts/run_migrations.py
```

7. Start development server:
```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Development

### Running locally

The chat widget needs **both** the backend and frontend running:

- **Terminal 1 – Backend:** From the project root, run `cd backend` then `uvicorn app.main:app --reload --port 8000`. The API will be at `http://localhost:8000`.
- **Terminal 2 – Frontend:** From the project root, run `cd frontend` then `npm run dev`. The app will be at `http://localhost:5173`.

The widget calls the API at `http://localhost:8000` by default. To use a different API URL, set `VITE_API_URL` in `frontend/.env` (e.g. `VITE_API_URL=http://localhost:8000`).

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Code Quality

Backend follows the coding standards defined in `.cursor/rules/`:
- `backend-api-standards.mdc` - API design patterns
- `llm-prompt-engineering.mdc` - LLM integration
- `payment-integration.mdc` - Payment gateway standards
- `database-schema.mdc` - Database design

Frontend follows:
- `frontend-chat-widget.mdc` - React component standards

## Deployment

### Backend (Railway)

1. Connect GitHub repository to Railway
2. Add PostgreSQL database service
3. Configure environment variables
4. Deploy automatically on push to main

### Frontend (Cloudflare Pages)

1. Connect GitHub repository to Cloudflare Pages
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Deploy automatically on push to main

## Features

- **Conversational AI**: Natural language product recommendations
- **Product Search**: Hybrid semantic + filter search
- **Payment Integration**: eSewa, Khalti, and Cash on Delivery
- **Order Tracking**: Real-time order status updates
- **Multilingual**: English and Nepali support
- **Mobile-First**: Responsive design for all devices
- **Embeddable Widget**: Single script tag integration

## API Documentation

API documentation is available at `/docs` when running the backend server.

## License

Proprietary - Himalayan Willow

## Support

For issues or questions, contact the development team.
