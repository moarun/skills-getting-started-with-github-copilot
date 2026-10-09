from copy import deepcopy
from urllib.parse import quote

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import activities, app

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    original_state = deepcopy(activities)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    activities.clear()
    activities.update(deepcopy(original_state))


async def test_get_activities_returns_all_activities(client):
    # Arrange
    # No special setup needed; the app starts with the defined activities.

    # Act
    response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]


async def test_signup_for_activity_adds_email(client):
    # Arrange
    email = "new.student@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


async def test_signup_rejects_duplicate_email(client):
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


async def test_signup_unknown_activity_returns_404(client):
    # Arrange
    email = "student@mergington.edu"
    activity_name = "Not A Real Club"

    # Act
    response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


async def test_unregister_participant_removes_email(client):
    # Arrange
    email = "new.student@mergington.edu"
    activity_name = "Chess Club"
    signup_response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")
    assert signup_response.status_code == 200

    # Act
    response = await client.delete(f"/activities/{quote(activity_name)}/participants/{quote(email)}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


async def test_unregister_missing_participant_returns_404(client):
    # Arrange
    email = "missing.student@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = await client.delete(f"/activities/{quote(activity_name)}/participants/{quote(email)}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"
