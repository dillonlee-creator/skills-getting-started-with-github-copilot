import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to known state before each test."""
    from src.app import activities
    
    original_data = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball practice and games",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and compete in matches",
            "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
            "max_participants": 12,
            "participants": ["alex@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and mixed media techniques",
            "schedule": "Tuesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu", "ava@mergington.edu"]
        },
        "Music Ensemble": {
            "description": "Join our orchestra and chamber music groups",
            "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop critical thinking and public speaking skills through debates",
            "schedule": "Mondays and Wednesdays, 3:45 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["noah@mergington.edu", "mia@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Compete in science competitions and experiments",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 14,
            "participants": ["ethan@mergington.edu"]
        }
    }
    
    activities.clear()
    activities.update(original_data)
    yield


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Verify root endpoint redirects to index.html."""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_all_activities(self, client):
        """Retrieve all available activities."""
        # Arrange
        expected_count = 9
        expected_activities = ["Chess Club", "Programming Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) == expected_count
        for activity in expected_activities:
            assert activity in data
    
    def test_activities_have_required_fields(self, client):
        """Verify each activity contains all required fields."""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_respect_max_capacity(self, client):
        """Ensure participant count does not exceed max capacity."""
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            participant_count = len(activity_data["participants"])
            max_capacity = activity_data["max_participants"]
            assert participant_count <= max_capacity, \
                f"{activity_name}: {participant_count} exceeds max {max_capacity}"


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        """Successfully sign up a new participant."""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Verify participant is actually added to activity."""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # Assert
        assert signup_response.status_code == 200
        assert email in activities_data[activity]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Attempt to signup for activity that doesn't exist."""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_returns_400(self, client):
        """Attempt to signup with email already registered."""
        # Arrange
        activity = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": existing_email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students_same_activity(self, client):
        """Multiple different students can signup for same activity."""
        # Arrange
        activity = "Chess Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email2}
        )
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in participants
        assert email2 in participants
    
    def test_signup_single_student_multiple_activities(self, client):
        """One student can signup for multiple different activities."""
        # Arrange
        email = "multitalent@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        data = activities_response.json()
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in data[activity1]["participants"]
        assert email in data[activity2]["participants"]


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_unregister_success(self, client):
        """Successfully unregister an existing participant."""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Verify participant is actually removed from activity."""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify precondition: participant exists
        initial_response = client.get("/activities")
        assert email in initial_response.json()[activity]["participants"]
        
        # Act
        unregister_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        final_response = client.get("/activities")
        
        # Assert
        assert unregister_response.status_code == 200
        assert email not in final_response.json()[activity]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Attempt to unregister from activity that doesn't exist."""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_returns_404(self, client):
        """Attempt to unregister participant not in activity."""
        # Arrange
        activity = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in data["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Student can unregister and signup again for same activity."""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify precondition
        initial_response = client.get("/activities")
        assert email in initial_response.json()[activity]["participants"]
        
        # Act - unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        
        # Act - signup again
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        final_response = client.get("/activities")
        
        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in final_response.json()[activity]["participants"]


class TestActivityIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_signup_to_unregister_workflow(self, client):
        """End-to-end: signup, verify registration, unregister, verify removal."""
        # Arrange
        activity = "Tennis Club"
        email = "integration@mergington.edu"
        
        # Verify precondition: not registered
        initial_response = client.get("/activities")
        assert email not in initial_response.json()[activity]["participants"]
        
        # Act - signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify registered
        registered_response = client.get("/activities")
        assert email in registered_response.json()[activity]["participants"]
        
        # Act - unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        
        # Verify unregistered
        final_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert email not in final_response.json()[activity]["participants"]
    
    def test_participant_count_increases_on_signup(self, client):
        """Verify participant count reflects new signup."""
        # Arrange
        activity = "Tennis Club"
        email = "availability@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        max_capacity = initial_response.json()[activity]["max_participants"]
        
        # Act
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        
        # Assert
        assert signup_response.status_code == 200
        assert final_count == initial_count + 1
        assert final_count <= max_capacity
    
    def test_participant_count_decreases_on_unregister(self, client):
        """Verify participant count reflects removal."""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Act
        unregister_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        
        # Assert
        assert unregister_response.status_code == 200
        assert final_count == initial_count - 1
