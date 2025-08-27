import pytest
from app import create_app, db
from app.models import User, ServiceApiKey
from werkzeug.security import generate_password_hash

TEST_ADMIN_USER = "admin"
TEST_ADMIN_PASS = "adminpass"
TEST_API_KEY = "testkey123"


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing."""
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    return app


@pytest.fixture(scope="function", autouse=True)
def app_context(app):
    """Push an app context for each test and reset the database."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        # seed admin + one service API key
        admin = User(username=TEST_ADMIN_USER,
             password=generate_password_hash(TEST_ADMIN_PASS),
             is_admin=True)
        db.session.add(admin)
        db.session.add(ServiceApiKey(key=TEST_API_KEY, description="test key"))
        db.session.commit()

        yield


@pytest.fixture
def client(app, app_context):
    """Return a Flask test client within an app context."""
    return app.test_client()
