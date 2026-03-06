def test_login_page_load(client):

    response = client.get("/login")

    assert response.status_code == 200

def test_register_page_load(client):

    response = client.get("/register")

    assert response.status_code == 200

def test_login_invalid_user(client):

    response = client.post("/login", data={
        "email": "wrong@gmail.com",
        "password": "Wrong123!"
    })

    assert response.status_code == 200