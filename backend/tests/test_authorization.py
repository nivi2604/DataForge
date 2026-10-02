
def test_cross_tenant_isolation():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import hash_password, create_access_token
    from app.models.organization import Organization
    
    db = SessionLocal()
    try:
        # Create user A
        user_a = User(id="user_a", email="a@test.com", password_hash=hash_password("pass"))
        db.add(user_a)
        db.commit()
        
        org_a = Organization(id="org_a", name="Org A", owner_id="user_a")
        db.add(org_a)
        db.commit()
        
        # Create user B
        user_b = User(id="user_b", email="b@test.com", password_hash=hash_password("pass"))
        db.add(user_b)
        db.commit()
        
        org_b = Organization(id="org_b", name="Org B", owner_id="user_b")
        db.add(org_b)
        db.commit()
        
        token_a = create_access_token("user_a")
        token_b = create_access_token("user_b")
        
        client = TestClient(app)
        
        # User B trying to access Org A
        res = client.get("/organizations/org_a", headers={"Authorization": f"Bearer {token_b}"})
        assert res.status_code == 404 or res.status_code == 403
        
        # User A trying to access Org A -> success
        res = client.get("/organizations/org_a", headers={"Authorization": f"Bearer {token_a}"})
        assert res.status_code == 200
        
    finally:
        db.query(Organization).filter(Organization.id.in_(["org_a", "org_b"])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(["user_a", "user_b"])).delete(synchronize_session=False)
        db.commit()
        db.close()
