import pytest
from fastapi import HTTPException

def test_root_redirect(client):
    """Test that root endpoint redirects to static index.html"""
    response = client.get("/")
    assert response.status_code == 200
    # FastAPI TestClient follows redirects by default
    assert "text/html" in response.headers.get("content-type", "")

def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()

    # Check that we have activities
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    required_keys = ["description", "schedule", "max_participants", "participants"]
    for key in required_keys:
        assert key in first_activity

    assert isinstance(first_activity["participants"], list)

def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    # Use an activity that exists and has space
    response = client.post("/activities/Chess%20Club/signup?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@example.com" in data["message"]
    assert "Chess Club" in data["message"]

def test_signup_for_activity_already_signed_up(client):
    """Test signup when student is already signed up"""
    # First signup
    client.post("/activities/Chess%20Club/signup?email=duplicate@example.com")

    # Try to signup again
    response = client.post("/activities/Chess%20Club/signup?email=duplicate@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]

def test_signup_for_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent%20Activity/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]

def test_signup_for_activity_full(client):
    """Test signup when activity is full"""
    # Find an activity with low max_participants
    activities = client.get("/activities").json()

    # Find an activity with few spots
    small_activity = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            small_activity = name
            break

    if small_activity:
        # Fill up the activity
        activity_details = activities[small_activity]
        spots_left = activity_details["max_participants"] - len(activity_details["participants"])

        for i in range(spots_left):
            email = f"fill{i}@example.com"
            client.post(f"/activities/{small_activity.replace(' ', '%20')}/signup?email={email}")

        # Try to add one more
        response = client.post(f"/activities/{small_activity.replace(' ', '%20')}/signup?email=overflow@example.com")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Activity is full" in data["detail"]

def test_unregister_from_activity_success(client):
    """Test successful unregister from an activity"""
    # First signup
    client.post("/activities/Programming%20Class/signup?email=unregister@example.com")

    # Then unregister
    response = client.delete("/activities/Programming%20Class/unregister?email=unregister@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "unregister@example.com" in data["message"]
    assert "Programming Class" in data["message"]

def test_unregister_from_activity_not_signed_up(client):
    """Test unregister when student is not signed up"""
    response = client.delete("/activities/Chess%20Club/unregister?email=notsignedup@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]

def test_unregister_from_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.delete("/activities/NonExistent%20Activity/unregister?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]