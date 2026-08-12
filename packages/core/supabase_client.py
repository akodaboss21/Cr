"""
Supabase client integration for Carai Receptionist
"""
import os
from supabase import create_client, Client
from typing import Optional

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create clients for different use cases
if supabase_url and supabase_key:
    supabase_client: Client = create_client(supabase_url, supabase_key)
else:
    supabase_client = None

if supabase_url and supabase_service_key:
    supabase_admin_client: Client = create_client(supabase_url, supabase_service_key)
else:
    supabase_admin_client = None

def get_supabase_client() -> Optional[Client]:
    """Get the Supabase client for public operations"""
    return supabase_client

def get_supabase_admin_client() -> Optional[Client]:
    """Get the Supabase admin client for privileged operations"""
    return supabase_admin_client

def init_supabase() -> bool:
    """Initialize Supabase connection and return status"""
    if not supabase_client:
        return False
    try:
        # Test connection
        supabase_client.table("organizations").select("count", count="exact").limit(1).execute()
        return True
    except Exception as e:
        print(f"Supabase initialization failed: {e}")
        return False