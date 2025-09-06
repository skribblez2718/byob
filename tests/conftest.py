"""Test configuration and fixtures for Flask blog application."""

import os
import tempfile
from datetime import datetime, timezone
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db
from app.models import User, Category, Post, Project
from app.utils.crypto import hash_password


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create and configure a test Flask application."""
    # Use in-memory SQLite for each test
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'poolclass': StaticPool,
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False}
        },
        'SECRET_KEY': 'test-secret-key',
        'ENCRYPTION_KEY': b'test-encryption-key-32-bytes-long',
        'TOTP_ISSUER': 'test-blog',
        'RATELIMIT_ENABLED': False,  # Disable rate limiting for tests
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 300,
    }
    
    # Create app with test config
    app = create_app(test_config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def db_session(app: Flask):
    """Create a clean database session for each test."""
    with app.app_context():
        yield db.session


@pytest.fixture
def test_admin_user(app: Flask):
    """Create a test admin user (matching the application's single admin user pattern)."""
    with app.app_context():
        admin_user = User(
            username='testadmin',
            email='admin@example.com',
            password_hash=hash_password('adminpassword'),
            is_admin=True,
            mfa_setup_completed=True,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(admin_user)
        db.session.commit()
        
        # Refresh to ensure object is bound to current session
        db.session.refresh(admin_user)
        yield admin_user




@pytest.fixture
def test_category(app: Flask):
    """Create a test category."""
    with app.app_context():
        category = Category(
            name='Test Category',
            slug='test-category',
            description='A test category',
            display_order=1,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        yield category


@pytest.fixture
def test_post(app: Flask, test_category: Category, test_admin_user: User):
    """Create a test blog post."""
    with app.app_context():
        post = Post(
            title='Test Post',
            slug='test-post',
            content_blocks=[
                {'type': 'paragraph', 'content': 'This is a test post content.'}
            ],
            excerpt='Test post excerpt',
            category_id=test_category.id,
            author_id=test_admin_user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(post)
        db.session.commit()
        db.session.refresh(post)
        yield post


@pytest.fixture
def test_project(app: Flask, test_admin_user: User):
    """Create a test project."""
    with app.app_context():
        project = Project(
            project_title='Test Project',
            project_description='A test project description',
            project_url='https://github.com/test/project',
            project_image_url='https://demo.example.com/image.jpg',
            user_id=test_admin_user.id,
            display_order=1,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(project)
        db.session.commit()
        db.session.refresh(project)
        yield project


@pytest.fixture
def authenticated_client(client: FlaskClient, test_admin_user: User) -> FlaskClient:
    """Create a client with an authenticated user session."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_admin_user.id)
        sess['_fresh'] = True
    return client




@pytest.fixture
def mfa_authenticated_admin_client(client: FlaskClient, test_admin_user: User) -> FlaskClient:
    """Create a client with an authenticated admin user who has passed MFA."""
    # Set MFA passed on the user object
    test_admin_user.mfa_passed = True
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_admin_user.id)
        sess['_fresh'] = True
    return client


class AuthActions:
    """Helper class for authentication actions in tests."""
    
    def __init__(self, client: FlaskClient):
        self._client = client
    
    def login(self, username: str = 'testuser', password: str = 'testpassword'):
        """Login a user."""
        return self._client.post('/auth/login', data={
            'username': username,
            'password': password
        })
    
    def logout(self):
        """Logout the current user."""
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client: FlaskClient) -> AuthActions:
    """Authentication helper fixture."""
    return AuthActions(client)
