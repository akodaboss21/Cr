import pytest
from packages.core.database import get_db
from packages.core.identity.models import BusinessProfile, Organization
from packages.core.identity.schemas import BusinessProfileCreate, BusinessProfileUpdate

# Test data
TEST_ORG_NAME = "Test Organization"
TEST_BUSINESS_NAME = "Test Business"
TEST_BUSINESS_DESCRIPTION = "A test business profile"

@pytest.fixture
async def db_session():
    db = get_db()
    yield db
    db.rollback()  # Rollback after each test

def test_create_business_profile(db_session):
    db = db_session
    # Ensure organization exists
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Create business profile
    profile_data = BusinessProfileCreate(
        organization_id=org.id,
        name=TEST_BUSINESS_NAME,
        description=TEST_BUSINESS_DESCRIPTION
    )
    profile = BusinessProfile(**profile_data.dict())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    assert profile.id is not None
    assert profile.name == TEST_BUSINESS_NAME

def test_unique_business_name_constraint(db_session):
    db = db_session
    # Ensure organization exists
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Create first business profile
    profile1 = BusinessProfileCreate(
        organization_id=org.id,
        name=TEST_BUSINESS_NAME,
        description=TEST_BUSINESS_DESCRIPTION
    )
    bp1 = BusinessProfile(**profile1.dict())
    db.add(bp1)
    db.commit()
    db.refresh(bp1)
    # Try creating duplicate name for same org
    with pytest.raises(Exception) as exc_info:
        profile2 = BusinessProfileCreate(
            organization_id=org.id,
            name=TEST_BUSINESS_NAME,
            description="Another description"
        )
        bp2 = BusinessProfile(**profile2.dict())
        db.add(bp2)
        db.commit()
    # Assuming unique constraint on name within organization
    assert "unique constraint" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()

def test_relationship_to_organization(db_session):
    db = db_session
    # Setup
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Create business profile linked to org
    profile = BusinessProfileCreate(
        organization_id=org.id,
        name=TEST_BUSINESS_NAME,
        description=TEST_BUSINESS_DESCRIPTION
    )
    bp = BusinessProfile(**profile.dict())
    db.add(bp)
    db.commit()
    db.refresh(bp)
    # Verify relationship
    assert bp.organization_id == org.id
    assert bp.organization == org

def test_update_business_profile(db_session):
    db = db_session
    # Setup
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Create profile
    profile = BusinessProfileCreate(
        organization_id=org.id,
        name=TEST_BUSINESS_NAME,
        description=TEST_BUSINESS_DESCRIPTION
    )
    bp = BusinessProfile(**profile.dict())
    db.add(bp)
    db.commit()
    db.refresh(bp)
    # Update
    bp.name = "Updated Business Name"
    bp.description = "Updated description"
    db.add(bp)
    db.commit()
    db.refresh(bp)
    assert bp.name == "Updated Business Name"
    assert bp.description == "Updated description"

def test_delete_business_profile(db_session):
    db = db_session
    # Setup
    org = Organization(name=TEST_ORG_NAME)
    db.add(org)
    db.commit()
    db.refresh(org)
    # Create profile
    profile = BusinessProfileCreate(
        organization_id=org.id,
        name=TEST_BUSINESS_NAME,
        description=TEST_BUSINESS_DESCRIPTION
    )
    bp = BusinessProfile(**profile.dict())
    db.add(bp)
    db.commit()
    db.refresh(bp)
    # Delete
    db.delete(bp)
    db.commit()
    with pytest.raises(Exception) as exc_info:
        db.session.get(BusinessProfile, bp.id)
    assert "deleted" in str(exc_info.value).lower()