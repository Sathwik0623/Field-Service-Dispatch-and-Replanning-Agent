from app.core.config import settings


def test_settings_load_defaults():
    assert settings.PROJECT_NAME == "Field Service Dispatch and Replanning Agent"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert settings.DATABASE_URL is not None
