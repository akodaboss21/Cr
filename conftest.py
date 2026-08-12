import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Ensure tests use an in-memory SQLite database and avoid requiring psycopg2.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Set minimal runtime environment values for tests.
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "local-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "local-service-role-key")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "*")
os.environ.setdefault("API_ENDPOINT", "http://localhost")
os.environ.setdefault("MAX_CONNECTIONS", "5")
