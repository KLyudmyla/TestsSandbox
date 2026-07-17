from app.it_practice import User

def test_create_user_integration(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "alice", "email": "alice@example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    user_id = data["id"]

    db_user = db_session.query(User).filter(User.id == user_id).first()
    assert db_user is not None
    assert db_user.username == "alice"
