-- Himalayan Willow Chatbot Database Schema
-- Migration 001: Initial Schema

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    in_stock BOOLEAN DEFAULT true,
    stock_quantity INTEGER DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    image_url TEXT,
    specifications JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for products
CREATE INDEX idx_products_category ON products(category, in_stock, price);
CREATE INDEX idx_products_rating ON products(rating DESC, sales_count DESC);
CREATE INDEX idx_products_store ON products(store_id, in_stock);
CREATE INDEX idx_products_sku ON products(sku);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(20) UNIQUE NOT NULL,
    store_id INTEGER NOT NULL DEFAULT 1,
    user_id INTEGER,
    session_id VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payment_method VARCHAR(20) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    payment_reference VARCHAR(100),
    subtotal INTEGER NOT NULL,
    discount INTEGER DEFAULT 0,
    delivery_charge INTEGER DEFAULT 0,
    total_amount INTEGER NOT NULL,
    delivery_address JSONB NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(100),
    courier_name VARCHAR(50),
    tracking_number VARCHAR(100),
    estimated_delivery DATE,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT
);

-- Indexes for orders
CREATE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_session ON orders(session_id);
CREATE INDEX idx_orders_status ON orders(store_id, status, created_at DESC);
CREATE INDEX idx_orders_payment ON orders(payment_status, payment_method);
CREATE INDEX idx_orders_phone ON orders(customer_phone);

-- Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(50) NOT NULL,
    unit_price INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    subtotal INTEGER NOT NULL,
    product_specifications JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for order items
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Chat Sessions Table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    store_id INTEGER NOT NULL DEFAULT 1,
    user_id INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    conversation_summary TEXT,
    user_context JSONB DEFAULT '{}',
    escalated BOOLEAN DEFAULT false,
    escalation_reason TEXT,
    escalated_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    products_viewed INTEGER DEFAULT 0,
    cart_items_added INTEGER DEFAULT 0,
    order_created BOOLEAN DEFAULT false
);

-- Indexes for chat sessions
CREATE INDEX idx_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX idx_sessions_user ON chat_sessions(user_id, started_at DESC);
CREATE INDEX idx_sessions_activity ON chat_sessions(last_activity_at DESC);
CREATE INDEX idx_sessions_store ON chat_sessions(store_id);

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES chat_sessions(session_id),
    sender VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    response_data JSONB,
    llm_model VARCHAR(50),
    llm_tokens_used INTEGER,
    llm_latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for chat messages
CREATE INDEX idx_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_messages_created ON chat_messages(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE products IS 'Cricket equipment product catalogue';
COMMENT ON TABLE orders IS 'Customer orders with payment and delivery tracking';
COMMENT ON TABLE order_items IS 'Line items for each order with product snapshot';
COMMENT ON TABLE chat_sessions IS 'Chat session tracking with user context';
COMMENT ON TABLE chat_messages IS 'Full conversation history for analysis';

COMMENT ON COLUMN products.specifications IS 'JSONB field for cricket-specific specs like bat_type, weight, size';
COMMENT ON COLUMN orders.subtotal IS 'Amount in paisa (1 NPR = 100 paisa)';
COMMENT ON COLUMN orders.total_amount IS 'Total amount in paisa';
COMMENT ON COLUMN orders.delivery_address IS 'JSONB with street, city, postal_code fields';
