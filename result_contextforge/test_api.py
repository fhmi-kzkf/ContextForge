import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_predict_valid_payload():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Mocking a payload based on detected args
        payload = {
            
            
            "X": 0, # Mock value
            
            
        }
        response = await ac.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_predict_missing_field():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Empty payload to trigger 422
        response = await ac.post("/api/v1/predict", json={})
    # If the function has required arguments, FastAPI returns 422
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_predict_wrong_type():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Passing a string where maybe a number is expected (FastAPI validation)
        payload = {
            
            
            "X": "should_be_number_maybe", 
            
            
        }
        response = await ac.post("/api/v1/predict", json=payload)
    # This might return 200 if type is Any, but we'll try to trigger validation
    # For a robust template, we'll just check if it handles bad inputs
    assert response.status_code in [200, 422]

@pytest.mark.asyncio
async def test_score_valid_payload():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Mocking a payload based on detected args
        payload = {
            
            
            "X": 0, # Mock value
            
            
            
            "y": 0, # Mock value
            
            
            
            "sample_weight": 0, # Mock value
            
            
        }
        response = await ac.post("/api/v1/score", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_score_missing_field():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Empty payload to trigger 422
        response = await ac.post("/api/v1/score", json={})
    # If the function has required arguments, FastAPI returns 422
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_score_wrong_type():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Passing a string where maybe a number is expected (FastAPI validation)
        payload = {
            
            
            "X": "should_be_number_maybe", 
            
            
            
            "y": "should_be_number_maybe", 
            
            
            
            "sample_weight": "should_be_number_maybe", 
            
            
        }
        response = await ac.post("/api/v1/score", json=payload)
    # This might return 200 if type is Any, but we'll try to trigger validation
    # For a robust template, we'll just check if it handles bad inputs
    assert response.status_code in [200, 422]
