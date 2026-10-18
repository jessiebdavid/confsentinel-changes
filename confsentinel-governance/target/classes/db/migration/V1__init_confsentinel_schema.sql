CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE microservices (
    id VARCHAR(64) PRIMARY KEY,
    slug VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    team VARCHAR(128) NOT NULL DEFAULT 'Unassigned',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_microservices_slug ON microservices(slug);

CREATE TABLE rules (
    id UUID PRIMARY KEY,
    rule_code VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    target_pattern VARCHAR(255) NOT NULL,
    key_path VARCHAR(255) NOT NULL,
    check_type VARCHAR(64) NOT NULL,
    parameter TEXT,
    min_value NUMERIC(12, 4),
    max_value NUMERIC(12, 4),
    remediation TEXT NOT NULL,
    rule_hash VARCHAR(64) NOT NULL,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_rules_active ON rules(active);
CREATE INDEX idx_rules_code ON rules(rule_code);
CREATE UNIQUE INDEX idx_rules_code_hash ON rules(rule_code, rule_hash);

CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id VARCHAR(64) NOT NULL REFERENCES microservices(id) ON DELETE CASCADE,
    environment VARCHAR(32) NOT NULL,
    commit_hash VARCHAR(64) NOT NULL,
    branch VARCHAR(128) NOT NULL,
    author VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK (status IN ('PASSED', 'WARNINGS', 'FAILED')),
    blockers_count INT DEFAULT 0 NOT NULL,
    warnings_count INT DEFAULT 0 NOT NULL,
    duration_ms INT NOT NULL,
    drift_summary JSONB,
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_evaluations_service_env ON evaluations(service_id, environment);
CREATE INDEX idx_evaluations_executed_at ON evaluations(executed_at DESC);
CREATE INDEX idx_evaluations_status ON evaluations(status);

CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES rules(id) ON DELETE RESTRICT,
    file_path VARCHAR(512) NOT NULL,
    line_number INT NOT NULL,
    snippet TEXT NOT NULL,
    remediation TEXT NOT NULL
);

CREATE INDEX idx_violations_evaluation_id ON violations(evaluation_id);
CREATE INDEX idx_violations_rule_id ON violations(rule_id);