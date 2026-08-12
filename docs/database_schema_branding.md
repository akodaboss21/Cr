"""
Database Schema for Business Intelligence and Branding System

This document defines the database tables required for the branding system.
"""

## Brand Profiles Table

```sql
CREATE TABLE brand_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    logo_url TEXT,
    primary_color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    secondary_color VARCHAR(7) NOT NULL DEFAULT '#64748B',
    accent_color VARCHAR(7) NOT NULL DEFAULT '#F59E0B',
    background_color VARCHAR(7) NOT NULL DEFAULT '#FFFFFF',
    text_color VARCHAR(7) NOT NULL DEFAULT '#1F2937',
    theme_settings JSONB NOT NULL DEFAULT '{}',
    style_classification VARCHAR(50),
    voice_profile JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one brand profile per organization
    UNIQUE(organization_id)
);

-- Index for fast lookups
CREATE INDEX idx_brand_profiles_organization_id ON brand_profiles(organization_id);
```

## Website Sources Table

```sql
CREATE TABLE website_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    last_scraped TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    extracted_data JSONB NOT NULL DEFAULT '{}',
    scrape_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_website_sources_organization_id ON website_sources(organization_id);
CREATE INDEX idx_website_sources_status ON website_sources(status);
```

## Onboarding Sessions Table

```sql
CREATE TABLE onboarding_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    current_step INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    data JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_onboarding_sessions_organization_id ON onboarding_sessions(organization_id);
CREATE INDEX idx_onboarding_sessions_status ON onboarding_sessions(status);
```

## Knowledge Base Table

```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    content JSONB NOT NULL DEFAULT '{}',
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_knowledge_bases_organization_id ON knowledge_bases(organization_id);
CREATE INDEX idx_knowledge_bases_status ON knowledge_bases(status);
```

## Migration Notes

1. **brand_profiles**: Stores the complete brand theme for each organization
2. **website_sources**: Tracks website scraping history and extracted data
3. **onboarding_sessions**: Manages the multi-step onboarding process
4. **knowledge_bases**: Stores generated knowledge content pending approval

## Relationships

- organizations (1) → (1) brand_profiles
- organizations (1) → (N) website_sources
- organizations (1) → (N) onboarding_sessions
- organizations (1) → (N) knowledge_bases

## Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE brand_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;

-- Policies for brand_profiles
CREATE POLICY "Users can view their organization's brand profile" ON brand_profiles
    FOR SELECT USING (organization_id = current_user_organization_id());

CREATE POLICY "Users can update their organization's brand profile" ON brand_profiles
    FOR UPDATE USING (organization_id = current_user_organization_id());

-- Policies for website_sources
CREATE POLICY "Users can view their organization's website sources" ON website_sources
    FOR SELECT USING (organization_id = current_user_organization_id());

CREATE POLICY "Users can insert website sources for their organization" ON website_sources
    FOR INSERT WITH CHECK (organization_id = current_user_organization_id());

-- Policies for onboarding_sessions
CREATE POLICY "Users can view their organization's onboarding sessions" ON onboarding_sessions
    FOR SELECT USING (organization_id = current_user_organization_id());

CREATE POLICY "Users can manage their organization's onboarding sessions" ON onboarding_sessions
    FOR ALL USING (organization_id = current_user_organization_id());

-- Policies for knowledge_bases
CREATE POLICY "Users can view their organization's knowledge bases" ON knowledge_bases
    FOR SELECT USING (organization_id = current_user_organization_id());

CREATE POLICY "Users can manage their organization's knowledge bases" ON knowledge_bases
    FOR ALL USING (organization_id = current_user_organization_id());