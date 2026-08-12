# Carai CRM Search System

## Executive Summary
This document defines the Search System for Carai CRM, which enables comprehensive customer search functionality. The system allows users to search for customers by various criteria including name, phone, email, conversation content, and services.

## Search System Features

### 1. Search Capabilities
- **Name Search**: Search by customer name
- **Phone Search**: Search by phone number
- **Email Search**: Search by email address
- **Conversation Search**: Search within conversation history
- **Service Search**: Search by services requested

### 2. Search Functionality
- **Full-text Search**: Search across all customer data
- **Field-specific Search**: Search within specific fields
- **Advanced Search**: Complex search queries with filters
- **Autocomplete**: Search suggestions as user types

### 3. Integration Points
- **CRM Controller**: Search endpoint in CRM controller
- **Database**: Search across CRM database
- **Frontend**: Search UI components
- **Analytics**: Search analytics and insights

## Search Data Model
```python
class SearchQuery:
    def __init__(self, query, filters=None, sort=None, pagination=None):
        self.query = query
        self.filters = filters or {}
        self.sort = sort or {}
        self.pagination = pagination or {}
```

## Search Implementation

### 1. Basic Search
```python
def search_customers(query, organization_id):
    # Build search query
    search_term = f"%{query}%"
    
    # Search across multiple fields
    results = CRM.query.filter(
        or_(
            func.lower(CRM.name).like(func.lower(search_term)),
            func.lower(CRM.email).like(func.lower(search_term)),
            func.lower(CRM.phone).like(func.lower(search_term)),
            func.lower(CRM.notes).like(func.lower(search_term)),
            func.lower(CRM.tags).like(func.lower(search_term)),
            func.lower(CRM.preferences).like(func.lower(search_term)),
            # Search in conversation content
            # func.lower(CRM.conversation_content).like(func.lower(search_term))
        ),
        CRM.organization_id == organization_id
    ).all()
    
    return results
```

### 2. Advanced Search
```python
def advanced_search(query, filters, organization_id):
    # Build complex search query with filters
    search_query = build_search_query(query, filters)
    
    # Apply filters
    if filters.get('status'):
        search_query = search_query.filter(CRM.status == filters['status'])
    
    if filters.get('pipeline_stage'):
        search_query = search_query.filter(CRM.pipeline_stage == filters['pipeline_stage'])
    
    if filters.get('date_range'):
        search_query = search_query.filter(
            CRM.created_at.between(filters['date_range']['start'], filters['date_range']['end'])
        )
    
    return search_query.all()
```

## Integration Requirements
1. Add search functionality to CRM controller
2. Implement search service
3. Create search API endpoints
4. Develop search UI components
5. Implement search analytics

## Benefits
- Enables quick customer lookup
- Improves customer service
- Supports sales activities
- Enhances analytics capabilities
- Reduces manual search time

## Next Steps
1. Implement search in CRM controller
2. Create search service
3. Develop search API endpoints
4. Create search UI components
5. Implement search analytics