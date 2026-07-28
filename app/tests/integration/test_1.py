from app.it_practice import User, Article
from app.tests.integration.conftest import client, db_session


def test_there_are_no_users(client, db_session):
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.json()== []

    users_number = db_session.query(User).count()
    assert users_number == 0
    print("\n No users found")

def test_create_user(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "alice3", "email": "alice3@example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice3"
    user_id = data["id"]
    print("\n User is created")

    db_user = db_session.query(User).filter(User.id == user_id).first()
    assert db_user is not None
    assert db_user.username == "alice3"
    print("\n User is found in db")

def test_get_users(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "alice4", "email": "alice4@example.com"}
    )
    assert response.status_code == 201
    print("\n We created a new user")

    response2 = client.get("/users/")
    assert response2.status_code == 200
    print(response2.json())
    users_number = db_session.query(User).count()
    assert users_number == 1
    print("\n Record with user is found")

def test_create_user_with_used_email(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "alice8", "email": "alice8@example.com"}
    )
    assert response.status_code == 201
    user_number = db_session.query(User).count()
    assert user_number == 1

    response2 = client.post(
        "/users/",
        params={"username": "alice89", "email": "alice8@example.com"}
    )
    assert response2.status_code == 400
    data = response2.json()
    assert data["detail"] == "Email already registered"
    print(data["detail"])

    user_number1 = db_session.query(User).count()
    assert user_number1 == 1
    print("\n No new users are added")

def test_create_article(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "kate", "email": "test@example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    owner = data["id"]
    user_count = db_session.query(User).count()
    assert user_count == 1
    print("We created a user")

    db_session.commit()

    response2 = client.post(
        "/articles/",
        params={"title": "test", "content": "test message", "owner_id": owner}
    )
    assert response2.status_code == 201
    article_info = db_session.query(Article).filter(Article.title == "test").first()
    assert article_info is not None
    assert article_info.title == "test"
    print("\n We created an article")

def test_non_existing_user_creates_article(client, db_session):
    response = client.post(
        "/articles/",
        params={"title": "test", "content": "test", "owner_id": 1}
    )
    assert response.status_code == 404
    data= response.json()
    assert data["detail"] == "User not found"
    print("\n User is not found. Article is not created")

    article_number = db_session.query(Article).count()
    assert article_number == 0
    print("No articles found")

def test_no_articles(client, db_session):
    response = client.get("/articles/")
    assert response.status_code == 200
    assert response.json() == []
    print("\n No articles found")

    articles_number = db_session.query(Article).count()
    assert articles_number == 0
    print("\n No articles found in db")

def test_get_articles(client, db_session):
    response = client.post(
        "/users/",
        params={"username": "superman", "email": "superman@example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    owner = data["id"]
    user_count = db_session.query(User).count()
    assert user_count == 1
    print("We created a user")

    db_session.commit()

    response2 = client.post(
        "/articles/",
        params={"title": "my 1st article", "content": "test message", "owner_id": owner}
    )
    assert response2.status_code == 201
    article_info = db_session.query(Article).filter(Article.title == "my 1st article").first()
    assert article_info is not None
    assert article_info.title == "my 1st article"
    print("\n We created an article")

    db_session.commit()

    response3 = client.get(
        "/articles/",
    )
    assert response3.status_code == 200

    articles_number = db_session.query(Article).count()
    assert articles_number == 1
    print("\n 1 article is found in db")
