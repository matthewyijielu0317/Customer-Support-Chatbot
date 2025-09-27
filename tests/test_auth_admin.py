from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api.main import create_app
from src.config.settings import settings


def test_admin_login_bypasses_database():
    app = create_app()
    client = TestClient(app)

    with patch('src.persistence.postgres.queries.verify_user_credentials') as mock_verify:
        mock_verify.return_value = None

        original_email = settings.admin_email
        original_passcode = settings.admin_passcode
        settings.admin_email = 'admin@example.com'
        settings.admin_passcode = 'letmein'
        try:
            response = client.post('/v1/auth/login', json={
                'email': 'admin@example.com',
                'passcode': 'letmein',
            })
            assert response.status_code == 200
            payload = response.json()
            assert payload['success'] is True
            assert payload['user']['email'] == 'admin@example.com'
            mock_verify.assert_not_called()
        finally:
            settings.admin_email = original_email
            settings.admin_passcode = original_passcode
