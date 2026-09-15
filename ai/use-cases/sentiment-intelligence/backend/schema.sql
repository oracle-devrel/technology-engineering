-- Application schema for Sentiment Intelligence.
-- Derived from the SQL used in orchestrator.py, sentiment_agent.py,
-- analytics_agent.py, and main.py. Run once as the application user.

CREATE TABLE scraped_reviews (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source        VARCHAR2(100),
    url           VARCHAR2(2000),
    author        VARCHAR2(200),
    review_text   CLOB,
    brand         VARCHAR2(200),
    product       VARCHAR2(200),
    region        VARCHAR2(100),
    rating        NUMBER,
    scraped_at    TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE sentiment_results (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id     NUMBER REFERENCES scraped_reviews(id),
    sentiment     VARCHAR2(50),
    score         NUMBER,
    aspects_json  CLOB,
    explanation   CLOB,
    emotions      CLOB,
    analyzed_at   TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE sentiment_alerts (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alert_type    VARCHAR2(100),
    title         VARCHAR2(500),
    description   CLOB,
    severity      VARCHAR2(50),
    source_count  NUMBER,
    sources       VARCHAR2(2000),
    source_urls   CLOB,
    detected_at   TIMESTAMP DEFAULT SYSTIMESTAMP,
    brand         VARCHAR2(200)
);

CREATE TABLE action_recommendations (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alert_id      NUMBER,
    action_text   VARCHAR2(4000),
    priority      VARCHAR2(50),
    impact        VARCHAR2(4000),
    category      VARCHAR2(100),
    status        VARCHAR2(50) DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP,
    brand         VARCHAR2(200)
);

-- Pre-computed weekly trend rows read by the dashboard.
CREATE TABLE sentiment_trends (
    week_start    DATE PRIMARY KEY,
    week_label    VARCHAR2(50),
    positive_pct  NUMBER,
    neutral_pct   NUMBER,
    negative_pct  NUMBER,
    total_reviews NUMBER,
    avg_score     NUMBER
);

CREATE INDEX ix_sentres_review ON sentiment_results (review_id);
CREATE INDEX ix_scraped_brand ON scraped_reviews (brand);
