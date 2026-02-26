# Sales Enhancement Deployment Guide

## Pre-Deployment Checklist

### 1. Backup Current System

```bash
# Backup database
pg_dump -U your_user himalayan_willow > backup_$(date +%Y%m%d).sql

# Backup code
git commit -am "Pre-deployment backup"
git tag pre-sales-enhancement
```

### 2. Review Changes

```bash
# Check what's changed
git status
git diff

# Review new files
ls -la backend/app/services/
ls -la backend/migrations/
```

## Deployment Steps

### Step 1: Database Migration (5 minutes)

```bash
# Connect to database
psql -U your_user -d himalayan_willow

# Run migration
\i backend/migrations/002_sales_enhancements.sql

# Verify tables created
\dt

# Check indexes
\di

# Expected output: 5 new tables
# - user_profiles
# - session_analytics
# - product_recommendations
# - conversion_metrics
# - product_bundles
```

**Verification**:
```sql
-- Check table structure
\d user_profiles
\d session_analytics
\d product_recommendations
\d conversion_metrics
\d product_bundles

-- Verify foreign keys
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f'
AND conrelid::regclass::text LIKE '%user_profiles%';
```

### Step 2: Install Dependencies (10 minutes)

```bash
cd backend

# Update requirements
pip install -r requirements.txt

# Optional: Install visual search dependencies
# Only if you want visual search feature
pip install transformers torch pillow

# Verify installation
python -c "import transformers; print('Visual search: OK')" || echo "Visual search: Skipped"
```

### Step 3: Update Environment (2 minutes)

```bash
# No new environment variables required
# But verify existing ones
cat .env | grep -E "GEMINI_API_KEY|DATABASE_URL"

# Optional: Add visual search config
echo "VISUAL_SEARCH_ENABLED=true" >> .env  # Only if installed ML deps
```

### Step 4: Test Backend (15 minutes)

```bash
# Start server
python -m uvicorn app.main:app --reload

# In another terminal, test endpoints
```

**Test Script**:
```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "Test 1: Health check"
curl -s "$BASE_URL/health" | jq

# Test 2: Create session
echo -e "\nTest 2: Create session"
SESSION_ID=$(curl -s -X POST "$BASE_URL/api/chat/session" \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}' | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# Test 3: Enhanced chat message
echo -e "\nTest 3: Enhanced chat message"
curl -s -X POST "$BASE_URL/api/chat/message-enhanced" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"I want to buy a bat\",
    \"session_id\": \"$SESSION_ID\"
  }" | jq

# Test 4: Analytics endpoint
echo -e "\nTest 4: Analytics - Conversion lift"
curl -s "$BASE_URL/api/analytics/metrics/conversion-lift?start_date=2024-01-01&end_date=2024-12-31" | jq

# Test 5: Analytics dashboard
echo -e "\nTest 5: Analytics dashboard summary"
curl -s "$BASE_URL/api/analytics/dashboard/summary" | jq '.success'

echo -e "\n✅ All tests completed"
```

Save as `test_deployment.sh` and run:
```bash
chmod +x test_deployment.sh
./test_deployment.sh
```

### Step 5: Verify Services (10 minutes)

```bash
# Test consultative service
python -c "
from app.services.consultative import ConsultativeService
from app.db.database import Database
import asyncio

async def test():
    db = Database()
    await db.connect()
    service = ConsultativeService(db)
    context = await service.gather_user_context(
        'test-session',
        'I am a beginner looking for a bat under 3000 rupees for cement wickets',
        {}
    )
    print('Context:', context)
    await db.disconnect()

asyncio.run(test())
"

# Test recommendation engine
python -c "
from app.services.recommendations import RecommendationEngine
from app.db.database import Database
import asyncio

async def test():
    db = Database()
    await db.connect()
    engine = RecommendationEngine(db)
    suggestions = await engine.suggest_complementary_products([1], 'test-session', 3)
    print('Suggestions:', len(suggestions))
    await db.disconnect()

asyncio.run(test())
"

# Test analytics service
python -c "
from app.services.analytics import AnalyticsService
from app.db.database import Database
from datetime import date, timedelta
import asyncio

async def test():
    db = Database()
    await db.connect()
    service = AnalyticsService(db)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    metrics = await service.calculate_conversion_lift(start_date, end_date)
    print('Metrics:', metrics)
    await db.disconnect()

asyncio.run(test())
"
```

### Step 6: Deploy to Production (30 minutes)

#### Option A: Railway Deployment

```bash
# Commit changes
git add .
git commit -m "Add sales enhancement features"

# Push to Railway
git push railway main

# Run migration on Railway
railway run psql $DATABASE_URL -f backend/migrations/002_sales_enhancements.sql

# Monitor logs
railway logs
```

#### Option B: Manual Server Deployment

```bash
# SSH to server
ssh user@your-server.com

# Pull latest code
cd /path/to/himalayan-willow-bot
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run migration
psql $DATABASE_URL -f backend/migrations/002_sales_enhancements.sql

# Restart service
sudo systemctl restart himalayan-willow-backend

# Check status
sudo systemctl status himalayan-willow-backend

# Monitor logs
tail -f /var/log/himalayan-willow/backend.log
```

## Post-Deployment Verification

### 1. Smoke Tests (5 minutes)

```bash
# Test production endpoint
PROD_URL="https://your-production-url.com"

# Health check
curl "$PROD_URL/health"

# Create session
curl -X POST "$PROD_URL/api/chat/session" \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'

# Test enhanced chat
curl -X POST "$PROD_URL/api/chat/message-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me bats",
    "session_id": null
  }'
```

### 2. Database Verification (5 minutes)

```sql
-- Connect to production database
psql $PRODUCTION_DATABASE_URL

-- Check table counts
SELECT 
    'user_profiles' as table_name, COUNT(*) as count FROM user_profiles
UNION ALL
SELECT 'session_analytics', COUNT(*) FROM session_analytics
UNION ALL
SELECT 'product_recommendations', COUNT(*) FROM product_recommendations
UNION ALL
SELECT 'conversion_metrics', COUNT(*) FROM conversion_metrics
UNION ALL
SELECT 'product_bundles', COUNT(*) FROM product_bundles;

-- Check recent activity
SELECT 
    session_id, 
    playing_level, 
    budget_range, 
    captured_at 
FROM user_profiles 
ORDER BY captured_at DESC 
LIMIT 5;
```

### 3. Monitor Initial Metrics (24 hours)

```bash
# Set up monitoring queries
cat > monitor_metrics.sql << 'EOF'
-- Daily metrics check
SELECT 
    DATE(started_at) as date,
    COUNT(DISTINCT session_id) as sessions,
    SUM(message_count) as messages,
    COUNT(DISTINCT session_id) FILTER (WHERE order_created = true) as conversions
FROM chat_sessions
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;

-- Recommendation acceptance
SELECT 
    recommendation_type,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE accepted = true) as accepted,
    ROUND(100.0 * COUNT(*) FILTER (WHERE accepted = true) / COUNT(*), 2) as acceptance_rate
FROM product_recommendations
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY recommendation_type;

-- Cross-sell performance
SELECT 
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT o.id) FILTER (
        WHERE EXISTS (
            SELECT 1 FROM product_recommendations pr
            WHERE pr.session_id = o.session_id
            AND pr.recommendation_type IN ('cross_sell', 'bundle')
            AND pr.accepted = true
        )
    ) as orders_with_cross_sell,
    ROUND(100.0 * COUNT(DISTINCT o.id) FILTER (
        WHERE EXISTS (
            SELECT 1 FROM product_recommendations pr
            WHERE pr.session_id = o.session_id
            AND pr.recommendation_type IN ('cross_sell', 'bundle')
            AND pr.accepted = true
        )
    ) / NULLIF(COUNT(DISTINCT o.id), 0), 2) as cross_sell_rate
FROM orders o
WHERE o.created_at >= NOW() - INTERVAL '24 hours';
EOF

# Run monitoring
psql $DATABASE_URL -f monitor_metrics.sql
```

## Rollback Plan

If issues occur, follow this rollback procedure:

### Quick Rollback (5 minutes)

```bash
# Revert code
git revert HEAD
git push

# Restart service
sudo systemctl restart himalayan-willow-backend
```

### Full Rollback (15 minutes)

```bash
# Restore code
git reset --hard pre-sales-enhancement
git push --force

# Restore database (CAUTION: This will lose new data)
psql $DATABASE_URL < backup_YYYYMMDD.sql

# Drop new tables (alternative to full restore)
psql $DATABASE_URL << 'EOF'
DROP TABLE IF EXISTS product_recommendations CASCADE;
DROP TABLE IF EXISTS conversion_metrics CASCADE;
DROP TABLE IF EXISTS session_analytics CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS product_bundles CASCADE;

-- Remove added columns
ALTER TABLE products DROP COLUMN IF EXISTS related_products;
ALTER TABLE chat_messages DROP COLUMN IF EXISTS recommendation_context;
EOF

# Restart service
sudo systemctl restart himalayan-willow-backend
```

## Monitoring & Alerts

### Set Up Monitoring

```bash
# Add to monitoring system (e.g., Datadog, New Relic)
# Monitor these metrics:

# 1. API Response Times
# - /api/chat/message-enhanced: < 2s
# - /api/analytics/*: < 5s

# 2. Error Rates
# - Overall error rate: < 1%
# - LLM errors: < 5%

# 3. Database Performance
# - Query time: < 500ms
# - Connection pool: < 80% utilized

# 4. Business Metrics
# - Conversion lift: Track daily
# - AOV lift: Track daily
# - Recommendation acceptance: Track hourly
```

### Alert Thresholds

```yaml
alerts:
  - name: High Error Rate
    condition: error_rate > 5%
    action: Page on-call engineer
  
  - name: Slow API Response
    condition: p95_response_time > 5s
    action: Send Slack notification
  
  - name: Database Connection Issues
    condition: db_connection_errors > 10
    action: Page on-call engineer
  
  - name: Low Conversion Lift
    condition: conversion_lift < 0%
    action: Send email to product team
```

## Troubleshooting

### Common Issues

**Issue 1: Migration fails with "relation already exists"**
```sql
-- Check if tables exist
\dt user_profiles

-- If exists, either:
-- Option A: Drop and recreate
DROP TABLE user_profiles CASCADE;
-- Then rerun migration

-- Option B: Skip that part of migration
-- Comment out the CREATE TABLE in migration file
```

**Issue 2: Import errors for new services**
```bash
# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check imports
python -c "from app.services.consultative import ConsultativeService; print('OK')"
```

**Issue 3: Analytics queries timeout**
```sql
-- Check query performance
EXPLAIN ANALYZE 
SELECT * FROM conversion_metrics 
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Add missing indexes if needed
CREATE INDEX IF NOT EXISTS idx_conversion_metrics_created 
ON conversion_metrics(created_at);
```

**Issue 4: Visual search not working**
```bash
# Check if dependencies installed
python -c "import transformers, torch, PIL; print('All deps OK')"

# If not installed
pip install transformers torch pillow

# Or disable visual search
# In code, check visual_search_service.is_available() before using
```

## Success Validation

After 24 hours, verify:

- [ ] No critical errors in logs
- [ ] Database tables populated with data
- [ ] Analytics endpoints returning valid data
- [ ] Consultative flow working (check user_profiles table)
- [ ] Recommendations being tracked (check product_recommendations table)
- [ ] No performance degradation (response times similar to before)

After 7 days, check:

- [ ] Conversion lift calculation shows data
- [ ] AOV metrics available
- [ ] Recommendation acceptance rates > 20%
- [ ] Cross-sell rate > 10%
- [ ] No major bugs reported

After 30 days, evaluate:

- [ ] Conversion lift ≥ 15%
- [ ] AOV lift ≥ 20%
- [ ] Cross-sell rate ≥ 30%
- [ ] Customer satisfaction maintained or improved

## Support

For deployment issues:
1. Check logs: `tail -f /var/log/himalayan-willow/backend.log`
2. Review error tracking: Sentry dashboard
3. Database queries: Use monitoring queries above
4. Contact: dev team via Slack #himalayan-willow-support

## Appendix: Useful Commands

```bash
# Check service status
sudo systemctl status himalayan-willow-backend

# View logs
journalctl -u himalayan-willow-backend -f

# Restart service
sudo systemctl restart himalayan-willow-backend

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor API requests
tail -f /var/log/nginx/access.log | grep "/api/chat"

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top -bn1 | grep "Cpu(s)"
```
