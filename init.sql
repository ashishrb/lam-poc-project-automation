-- Project Portfolio Management System - Database Initialization

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'app')\gexec

-- Connect to the app database
\c app;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types if they don't exist
DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('planning', 'active', 'on_hold', 'completed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE project_phase AS ENUM ('initiation', 'planning', 'execution', 'monitoring', 'closure');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'review', 'done', 'blocked');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE resource_type AS ENUM ('employee', 'contractor', 'vendor', 'equipment');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE resource_status AS ENUM ('active', 'inactive', 'on_leave', 'terminated');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE budget_type AS ENUM ('labor', 'materials', 'equipment', 'travel', 'software', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE budget_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_status AS ENUM ('identified', 'assessed', 'mitigated', 'closed', 'occurred');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'error', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved', 'escalated', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_tenant_id ON projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects(phase);
CREATE INDEX IF NOT EXISTS idx_projects_health_score ON projects(health_score);

CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_resources_tenant_id ON resources(tenant_id);
CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status);
CREATE INDEX IF NOT EXISTS idx_resources_department ON resources(department);

CREATE INDEX IF NOT EXISTS idx_budgets_project_id ON budgets(project_id);
CREATE INDEX IF NOT EXISTS idx_budgets_status ON budgets(status);

CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE INDEX IF NOT EXISTS idx_alerts_entity_type ON alerts(entity_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_projects_search ON projects USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_tasks_search ON tasks USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_resources_search ON resources USING gin(to_tsvector('english', name || ' ' || COALESCE(department, '') || ' ' || COALESCE(position, '')));

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_projects_tenant_status ON projects(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_budgets_project_type ON budgets(project_id, budget_type);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE app TO app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO app;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns (these will be applied when tables are created)
-- The triggers will be created by the SQLAlchemy models

-- Insert initial configuration data
INSERT INTO tenants (name, domain, settings, is_active, created_at, updated_at)
VALUES ('demo', 'demo.local', '{"timezone": "Asia/Kolkata"}', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;

-- Create default roles
INSERT INTO roles (name, description, permissions, tenant_id, is_active, created_at, updated_at)
VALUES 
    ('admin', 'System Administrator', '{"*": ["*"]}', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('executive', 'Executive Management', '{"projects": ["read"], "portfolio": ["read"], "reports": ["read"]}', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm', 'Project Manager', '{"projects": ["read", "write"], "tasks": ["read", "write"], "resources": ["read"]}', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('team_member', 'Team Member', '{"tasks": ["read", "write"], "timesheets": ["read", "write"]}', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('vendor', 'External Vendor', '{"projects": ["read"], "invoices": ["read", "write"]}', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;

-- Create default admin user
INSERT INTO users (username, email, full_name, hashed_password, role_id, tenant_id, is_active, created_at, updated_at)
VALUES ('admin', 'admin@demo.local', 'System Administrator', 'hashed_password_here', 1, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (username) DO NOTHING;

-- Create default skills
INSERT INTO skills (name, category, description, tenant_id, created_at, updated_at)
VALUES 
    ('Python', 'technical', 'Python programming language', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('JavaScript', 'technical', 'JavaScript programming language', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Project Management', 'soft', 'Project management methodologies and tools', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Agile', 'soft', 'Agile development methodologies', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('UI/UX Design', 'technical', 'User interface and user experience design', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DevOps', 'technical', 'Development operations and infrastructure', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Data Analysis', 'technical', 'Data analysis and visualization', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Communication', 'soft', 'Effective communication skills', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Leadership', 'soft', 'Team leadership and management', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Problem Solving', 'soft', 'Analytical and problem-solving skills', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;

-- Create default alert rules
INSERT INTO alert_rules (name, description, alert_type, severity, conditions, entity_types, is_active, created_by, tenant_id, created_at, updated_at)
VALUES 
    ('Budget Variance', 'Alert when budget variance exceeds 10%', 'budget_variance', 'warning', '{"threshold": 0.1}', '["project"]', true, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Schedule Slip', 'Alert when schedule slips exceed 3 days', 'schedule_slip', 'warning', '{"threshold_days": 3}', '["project", "task"]', true, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Resource Overallocation', 'Alert when resource utilization exceeds 110%', 'resource_overallocation', 'warning', '{"threshold": 1.1}', '["resource"]', true, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Quality Issues', 'Alert when defect density increases by 30%', 'quality_issue', 'error', '{"threshold": 0.3}', '["project"]', true, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Set up initial configuration
INSERT INTO audit_logs (action, entity_type, resource_path, method, status_code, tenant_id, created_at)
VALUES ('system_init', 'system', '/init', 'POST', 200, 1, CURRENT_TIMESTAMP);

-- Print completion message
SELECT 'Database initialization completed successfully!' as status;
