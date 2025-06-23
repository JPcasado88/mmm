-- Marketing Mix Modeling Database Schema

-- Create database
CREATE DATABASE IF NOT EXISTS mmm_db;

-- Daily marketing performance data
CREATE TABLE daily_marketing_data (
    date DATE NOT NULL,
    channel VARCHAR(50) NOT NULL,
    spend DECIMAL(10,2),
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    revenue DECIMAL(10,2),
    new_customers INTEGER,
    returning_customers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, channel)
);

-- Campaign metadata
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50),
    campaign_name VARCHAR(200),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(10,2),
    campaign_type VARCHAR(50), -- 'awareness', 'conversion', 'retention'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- External factors affecting performance
CREATE TABLE external_factors (
    date DATE PRIMARY KEY,
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(100),
    competitor_activity VARCHAR(200),
    seasonality_index DECIMAL(3,2) DEFAULT 1.0, -- 1.0 = normal, 1.5 = high season
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attribution calculation results
CREATE TABLE attribution_results (
    id SERIAL PRIMARY KEY,
    date DATE,
    channel VARCHAR(50),
    model_type VARCHAR(50), -- 'linear', 'time_decay', 'u_shaped', 'data_driven'
    attributed_conversions DECIMAL(10,2),
    attributed_revenue DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_daily_data_date ON daily_marketing_data(date);
CREATE INDEX idx_daily_data_channel ON daily_marketing_data(channel);
CREATE INDEX idx_campaigns_channel ON campaigns(channel);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);
CREATE INDEX idx_attribution_date_channel ON attribution_results(date, channel);