# Deployment Guide

This guide covers deploying the Himalayan Willow AI Chatbot to production.

## Prerequisites

- GitHub account
- Railway account (for backend)
- Cloudflare account (for frontend)
- PostgreSQL database (Railway provides this)
- Google AI Studio API key (Gemini)
- eSewa and Khalti test/production credentials
- Telegram Bot token (optional, for notifications)

## Backend Deployment (Railway)

### 1. Prepare Repository

```bash
git add .
git commit -m "Initial commit - Himalayan Willow Chatbot MVP"
git push origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect Python and deploy

### 3. Add PostgreSQL Database

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will create a database and set `DATABASE_URL` automatically

### 4. Configure Environment Variables

In Railway project settings, add these variables:

```
GEMINI_API_KEY=your_gemini_api_key_from_google_ai_studio
ESEWA_MERCHANT_ID=your_esewa_merchant_id
ESEWA_SECRET_KEY=your_esewa_secret_key
ESEWA_BASE_URL=https://uat.esewa.com.np
KHALTI_SECRET_KEY=your_khalti_secret_key
KHALTI_BASE_URL=https://khalti.com
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
BASE_URL=https://your-app.railway.app
CORS_ORIGINS=https://your-frontend.pages.dev,https://himalayanwillow.com.np
JWT_SECRET=generate_a_random_secret_key
ENVIRONMENT=production
```

### 5. Run Database Migrations

After first deployment, run migrations via Railway CLI:

```bash
railway run python backend/scripts/run_migrations.py
```

Or use Railway's web shell to execute:

```bash
cd backend && python scripts/run_migrations.py
```

### 6. Seed Sample Data

```bash
railway run python backend/scripts/seed_products.py
```

### 7. Configure Custom Domain (Optional)

1. In Railway project settings, go to "Settings" → "Domains"
2. Add custom domain: `api.himalayanwillow.com`
3. Update DNS records as instructed by Railway

## Frontend Deployment (Cloudflare Pages)

### 1. Build Configuration

Create `frontend/wrangler.toml`:

```toml
name = "himalayan-willow-chat"
compatibility_date = "2024-01-01"

[site]
bucket = "./dist"
```

### 2. Deploy to Cloudflare Pages

#### Option A: Via Cloudflare Dashboard

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select "Pages" → "Create a project"
3. Connect your GitHub repository
4. Configure build settings:
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `frontend`
5. Add environment variable:
   - `VITE_API_URL`: `https://your-app.railway.app`
6. Click "Save and Deploy"

#### Option B: Via Wrangler CLI

```bash
cd frontend
npm install -g wrangler
wrangler login
npm run build
wrangler pages deploy dist --project-name=himalayan-willow-chat
```

### 3. Configure Custom Domain

1. In Cloudflare Pages project, go to "Custom domains"
2. Add: `cdn.himalayanwillow.com` or `chat.himalayanwillow.com`
3. Cloudflare will automatically configure DNS

## Environment-Specific Configuration

### Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your local values
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env
# Edit .env with local API URL
npm run dev
```

### Production

- Backend: Railway auto-deploys on push to main
- Frontend: Cloudflare Pages auto-deploys on push to main

## Post-Deployment Checklist

- [ ] Backend health check: `https://your-app.railway.app/health`
- [ ] API docs accessible: `https://your-app.railway.app/docs`
- [ ] Database migrations ran successfully
- [ ] Sample products seeded
- [ ] Frontend loads correctly
- [ ] Chat widget initializes
- [ ] Message sending works
- [ ] Product search returns results
- [ ] Payment initiation works (test mode)
- [ ] Order creation works
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Logs visible in Railway dashboard

## Monitoring Setup

### Railway Logs

Railway automatically captures logs. View them in:
- Project → Deployments → View Logs

### Error Tracking (Optional - Sentry)

1. Create Sentry account at [sentry.io](https://sentry.io)
2. Create new project for Python (backend) and JavaScript (frontend)
3. Add Sentry DSN to environment variables:

```
SENTRY_DSN=your_sentry_dsn
```

4. Install Sentry SDK:

```bash
# Backend
pip install sentry-sdk[fastapi]

# Frontend
npm install @sentry/react
```

## Scaling Considerations

### Free Tier Limits

- **Railway**: $5 credit/month, ~500 hours
- **Gemini API**: 15 requests/minute free
- **Cloudflare Pages**: Unlimited requests
- **PostgreSQL**: 500MB storage

### When to Upgrade

- >1000 conversations/day → Upgrade Gemini to paid ($7/month)
- >100GB bandwidth → Upgrade Railway to Hobby ($5/month)
- >10,000 products → Consider Pinecone for vector search ($70/month)

## Troubleshooting

### Backend Won't Start

1. Check Railway logs for errors
2. Verify all environment variables are set
3. Ensure DATABASE_URL is correct
4. Check Python version (should be 3.10+)

### Frontend Not Loading

1. Check Cloudflare Pages build logs
2. Verify VITE_API_URL is correct
3. Check CORS settings in backend
4. Clear browser cache

### Database Connection Fails

1. Verify DATABASE_URL format
2. Check Railway PostgreSQL service is running
3. Ensure migrations ran successfully
4. Check connection pool settings

### Payment Integration Issues

1. Verify using test credentials in development
2. Check eSewa/Khalti API URLs (UAT vs Production)
3. Verify webhook URLs are publicly accessible
4. Check signature verification logic

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Rotate secrets regularly** - Especially JWT_SECRET
3. **Use HTTPS only** - Railway and Cloudflare provide this automatically
4. **Rate limit aggressively** - Prevent abuse
5. **Validate all inputs** - Prevent injection attacks
6. **Monitor logs** - Watch for suspicious activity
7. **Keep dependencies updated** - Run `pip list --outdated` regularly

## Backup Strategy

### Database Backups

Railway provides automatic daily backups. To manual backup:

```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

### Code Backups

- Code is backed up in GitHub
- Tag releases: `git tag v1.0.0 && git push --tags`

## Rollback Procedure

If deployment fails:

1. **Railway**: Go to Deployments → Select previous working deployment → "Redeploy"
2. **Cloudflare Pages**: Go to Deployments → Select previous build → "Rollback"
3. **Database**: Restore from backup if schema changed

## Support

For deployment issues:
- Railway: [railway.app/help](https://railway.app/help)
- Cloudflare: [developers.cloudflare.com/pages](https://developers.cloudflare.com/pages)
- GitHub Issues: Create issue in repository
