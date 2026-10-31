import pytest
from fastapi.testclient import TestClient
from alibi.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'vault')) as client:
        yield client


@pytest.fixture
def case(client):
    response = client.post('/api/investigations', json={'name': 'Test investigation', 'description': 'Synthetic data only'})
    assert response.status_code == 201
    return response.json()['id']
