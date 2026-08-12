import pytest
from packages.core.database import get_db
from packages.core.identity.models import Organization, User
from packages.core.identity.schemas import OrganizationCreate, OrganizationUpdate

# Test data
TEST_ORG_NAME = "Test Org"
TEST_USER_EMAIL = "test@example.com"

@pytest.fixture
async def db_session():  # Use async if using async DB
    db = get_db()
    yield db
    db.rollback()  # Rollback after each test

def test_create_organization(db_session):
    db = db_session
    org_data = OrganizationCreate(name=TEST_ORG_NAME, description="Test organization")
    org = Organization(**org_data.dict())
    db.add(org)
    db.commit()
    db.refresh(org)
    assert org.id is not None
    assert org.name == TEST_ORG_NAME

def test_unique_name_constraint(db_session):
    db = db_session
    # Create first org
    org1 = Organization(name=TEST_ORG_NAME)
    db.add(org1)
    db.commit()
    db.refresh(org1)
    # Try creating duplicate
    with pytest.raises(Exception) as exc_info:
        org2 = Organization(name=TEST_ORG_NAME)
        db.add(org2)
        db.commit()
    assert "unique constraint" in str(exc_info.value).lower()

def test_relationships(db_session):
    db = db_session
    # Create org and user
    org = Organization(name=TEST_ORG_NAME)
    user = User(email=TEST_USER_EMAIL, organization_id=org.id)
    db.add(org)
    db.add(user)
    db.commit()
    db.refresh(org)
    assert len(org.users) == 1
    assert user.organization == org

def test_update_organization(db_session):
    db = db_session
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Update
    org.name = "Updated Org"
    org.description = "New description"
    db.add(org)
    db.commit()
    db.refresh(org)
    assert org.name == "Updated Org"
    assert org.description == "New description"

def test_delete_organization(db_session):
    db = db_session
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Delete
    db.delete(org)
    db.commit()
    with pytest.raises(Exception) as exc_info:
        db.session.get(Organization, org.id)
    assert "deleted" in str(exc_info.value).lower()