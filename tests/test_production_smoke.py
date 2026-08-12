def test_identity_models_import_consistently():
    from packages.core.identity.models import Organization as CoreOrganization
    from packages.core.identity.organizations.models import Organization as OrgOrganization

    assert CoreOrganization is OrgOrganization
