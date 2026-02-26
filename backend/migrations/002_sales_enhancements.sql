-- Himalayan Willow Chatbot Database Schema
-- Migration 002: Sales Enhancement Schema
-- Purpose: Add tables for consultative selling, analytics, and recommendations

-- User profiles for zero-party data collection
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    playing_level VARCHAR(20),  -- 'beginner', 'club', 'professional'
    preferred_surface VARCHAR(20),  -- 'turf', 'cement', 'matting', 'both'
    budget_range VARCHAR(20),  -- 'under_3k', '3k_7k', '7k_15k', 'no_limit'
    position VARCHAR(50),  -- 'batsman', 'bowler', 'all_rounder', 'wicket_keeper'
    age_group VARCHAR(20),  -- 'youth', 'adult', 'senior'
    team_affiliation VARCHAR(100),
    insights JSONB DEFAULT '{}',  -- Additional flexible insights
    captured_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Session analytics for behavioral tracking
CREATE TABLE IF NOT EXISTS session_analytics (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    page_views JSONB DEFAULT '[]',  -- Array of {page: string, timestamp: string}
    time_on_product_pages JSONB DEFAULT '{}',  -- {product_id: seconds_spent}
    products_viewed INTEGER[] DEFAULT '{}',  -- Array of product IDs
    cart_abandonment_stage VARCHAR(50),  -- 'browsing', 'cart', 'checkout', 'payment'
    interaction_events JSONB DEFAULT '[]',  -- Array of {event: string, timestamp: string, data: object}
    proactive_prompts_shown INTEGER DEFAULT 0,
    proactive_prompts_accepted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Product recommendations tracking
CREATE TABLE IF NOT EXISTS product_recommendations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(50) NOT NULL,  -- 'consultative', 'upsell', 'cross_sell', 'bundle', 'visual_search'
    reason TEXT,  -- Why this product was recommended
    accepted BOOLEAN DEFAULT false,  -- Did user add to cart or purchase?
    position INTEGER,  -- Position in recommendation list (1, 2, 3...)
    context JSONB DEFAULT '{}',  -- Additional context about the recommendation
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Conversion metrics for sales KPIs
CREATE TABLE IF NOT EXISTS conversion_metrics (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    chatbot_engaged BOOLEAN DEFAULT false,  -- Did user interact with chatbot?
    products_recommended INTEGER DEFAULT 0,  -- Number of products shown
    cart_value INTEGER DEFAULT 0,  -- Value of items added to cart (in paisa)
    order_value INTEGER DEFAULT 0,  -- Final order value (in paisa)
    conversion_time INTERVAL,  -- Time from first message to order
    assisted_aov INTEGER DEFAULT 0,  -- Average order value for this session (in paisa)
    recommendation_acceptance_rate DECIMAL(5, 2) DEFAULT 0.0,  -- % of recommendations accepted
    upsell_value INTEGER DEFAULT 0,  -- Additional value from upsells (in paisa)
    cross_sell_count INTEGER DEFAULT 0,  -- Number of cross-sell items purchased
    created_at TIMESTAMP DEFAULT NOW()
);

-- Product bundles for curated combinations
CREATE TABLE IF NOT EXISTS product_bundles (
    id SERIAL PRIMARY KEY,
    bundle_id VARCHAR(50) UNIQUE NOT NULL,
    bundle_name VARCHAR(255) NOT NULL,
    primary_product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    complementary_product_ids INTEGER[] NOT NULL,  -- Array of product IDs
    discount_percentage DECIMAL(5, 2) DEFAULT 0,  -- Discount on bundle (0-100)
    bundle_description TEXT,
    active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,  -- For sorting bundles
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_session ON user_profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_level ON user_profiles(playing_level);
CREATE INDEX IF NOT EXISTS idx_session_analytics_session ON session_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_session ON product_recommendations(session_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_product ON product_recommendations(product_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_type ON product_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_accepted ON product_recommendations(accepted);
CREATE INDEX IF NOT EXISTS idx_conversion_metrics_session ON conversion_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_metrics_engaged ON conversion_metrics(chatbot_engaged);
CREATE INDEX IF NOT EXISTS idx_product_bundles_primary ON product_bundles(primary_product_id);
CREATE INDEX IF NOT EXISTS idx_product_bundles_active ON product_bundles(active);

-- Add related_products column to products table for cross-sell suggestions
ALTER TABLE products ADD COLUMN IF NOT EXISTS related_products INTEGER[] DEFAULT '{}';

-- Add recommendation_context column to chat_messages for tracking
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS recommendation_context JSONB DEFAULT '{}';

-- Update trigger for user_profiles
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at_trigger
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- Update trigger for session_analytics
CREATE OR REPLACE FUNCTION update_session_analytics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_session_analytics_updated_at_trigger
    BEFORE UPDATE ON session_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_session_analytics_updated_at();

-- Update trigger for product_bundles
CREATE OR REPLACE FUNCTION update_product_bundles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_product_bundles_updated_at_trigger
    BEFORE UPDATE ON product_bundles
    FOR EACH ROW
    EXECUTE FUNCTION update_product_bundles_updated_at();

-- Comments for documentation
COMMENT ON TABLE user_profiles IS 'Zero-party data collected through consultative conversations';
COMMENT ON TABLE session_analytics IS 'Behavioral tracking for proactive interventions';
COMMENT ON TABLE product_recommendations IS 'History of all product recommendations with acceptance tracking';
COMMENT ON TABLE conversion_metrics IS 'Sales KPIs and revenue attribution metrics';
COMMENT ON TABLE product_bundles IS 'Curated product combinations for cross-selling';

COMMENT ON COLUMN user_profiles.insights IS 'Flexible JSONB field for additional cricket-specific insights';
COMMENT ON COLUMN session_analytics.interaction_events IS 'Array of user interaction events with timestamps';
COMMENT ON COLUMN product_recommendations.context IS 'Additional context like user_budget, playing_level at time of recommendation';
COMMENT ON COLUMN conversion_metrics.assisted_aov IS 'Average order value for chatbot-assisted sessions';
COMMENT ON COLUMN product_bundles.complementary_product_ids IS 'Array of product IDs that complete the bundle';
