"""Tests for repository functions."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.extensions import db
from app.models import User
from app.repositories.user import (
    get_user_by_hex_id,
    get_user_by_username,
    increment_failed_login_attempts,
    reset_failed_login_attempts,
    increment_failed_mfa_attempts,
    reset_failed_mfa_attempts,
    is_user_login_locked,
    is_user_mfa_locked,
    clear_all_lockouts
)
from app.repositories.blog import (
    get_category_by_hex_id,
    get_category_by_slug,
    get_post_by_hex_id,
    get_post_by_slug,
    list_posts_by_category,
    list_posts
)
from app.utils.crypto import hash_password


class TestUserRepository:
    """Test cases for user repository functions."""
    
    def test_get_user_by_hex_id(self, app, test_admin_user):
        """Test getting user by hex ID."""
        with app.app_context():
            found_user = get_user_by_hex_id(test_admin_user.hex_id)
            assert found_user is not None
            assert found_user.id == test_admin_user.id
            assert found_user.username == test_admin_user.username
    
    def test_get_user_by_hex_id_not_found(self, app):
        """Test getting user by non-existent hex ID."""
        with app.app_context():
            found_user = get_user_by_hex_id('nonexistent')
            assert found_user is None
    
    def test_get_user_by_username(self, app, test_admin_user):
        """Test getting user by username."""
        with app.app_context():
            found_user = get_user_by_username(test_admin_user.username)
            assert found_user is not None
            assert found_user.id == test_admin_user.id
            assert found_user.email == test_admin_user.email
    
    def test_get_user_by_username_not_found(self, app):
        """Test getting user by non-existent username."""
        with app.app_context():
            found_user = get_user_by_username('nonexistent')
            assert found_user is None
    
    def test_increment_failed_login_attempts(self, app, test_admin_user):
        """Test incrementing failed login attempts."""
        with app.app_context():
            # Get fresh instance from database
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            # Initial state
            assert user.failed_login_attempts == 0
            assert user.login_locked_until is None
            
            # First attempt
            increment_failed_login_attempts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.failed_login_attempts == 1
            assert user.login_locked_until is None
            
            # Second attempt
            increment_failed_login_attempts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.failed_login_attempts == 2
            assert user.login_locked_until is None
            
            # Third attempt - should trigger lockout
            increment_failed_login_attempts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.failed_login_attempts == 3
            assert user.login_locked_until is not None
            
            # Verify lockout time is approximately 15 minutes from now
            lockout_time = user.login_locked_until
            if lockout_time.tzinfo is None:
                # Convert to UTC if naive
                expected_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            else:
                expected_time = datetime.now(timezone.utc) + timedelta(minutes=15)
            time_diff = abs((lockout_time - expected_time).total_seconds())
            assert time_diff < 60  # Within 1 minute tolerance
    
    def test_reset_failed_login_attempts(self, app, test_admin_user):
        """Test resetting failed login attempts."""
        with app.app_context():
            # Get fresh instance and set up failed attempts and lockout
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.failed_login_attempts = 3
            user.login_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            
            # Reset attempts
            reset_failed_login_attempts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            assert user.failed_login_attempts == 0
            assert user.login_locked_until is None
    
    def test_increment_failed_mfa_attempts(self, app, test_admin_user):
        """Test incrementing failed MFA attempts."""
        with app.app_context():
            # Get fresh instance from database
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            # Initial state
            assert user.failed_mfa_attempts == 0
            assert user.mfa_locked_until is None
            
            # Increment to lockout threshold
            for i in range(3):
                increment_failed_mfa_attempts(user)
                user = get_user_by_hex_id(test_admin_user.hex_id)
            
            assert user.failed_mfa_attempts == 3
            assert user.mfa_locked_until is not None
    
    def test_reset_failed_mfa_attempts(self, app, test_admin_user):
        """Test resetting failed MFA attempts."""
        with app.app_context():
            # Get fresh instance and set up failed attempts and lockout
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.failed_mfa_attempts = 3
            user.mfa_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            
            # Reset attempts
            reset_failed_mfa_attempts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            assert user.failed_mfa_attempts == 0
            assert user.mfa_locked_until is None
    
    def test_is_user_login_locked_not_locked(self, app, test_admin_user):
        """Test checking login lock status when not locked."""
        with app.app_context():
            assert is_user_login_locked(test_admin_user) is False
    
    def test_is_user_login_locked_active_lockout(self, app, test_admin_user):
        """Test checking login lock status with active lockout."""
        with app.app_context():
            # Get fresh instance and set lockout in the future
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.login_locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            db.session.commit()
            
            assert is_user_login_locked(user) is True
    
    def test_is_user_login_locked_expired_lockout(self, app, test_admin_user):
        """Test checking login lock status with expired lockout."""
        with app.app_context():
            # Get fresh instance and set lockout in the past
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.login_locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
            user.failed_login_attempts = 3
            db.session.commit()
            
            # Should automatically reset and return False
            assert is_user_login_locked(user) is False
            
            # Verify reset occurred
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.failed_login_attempts == 0
            assert user.login_locked_until is None
    
    def test_is_user_mfa_locked_not_locked(self, app, test_admin_user):
        """Test checking MFA lock status when not locked."""
        with app.app_context():
            assert is_user_mfa_locked(test_admin_user) is False
    
    def test_is_user_mfa_locked_active_lockout(self, app, test_admin_user):
        """Test checking MFA lock status with active lockout."""
        with app.app_context():
            # Get fresh instance and set lockout in the future
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.mfa_locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            db.session.commit()
            
            assert is_user_mfa_locked(user) is True
    
    def test_clear_all_lockouts(self, app, test_admin_user):
        """Test clearing all lockouts."""
        with app.app_context():
            # Get fresh instance and set up both types of lockouts
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.failed_login_attempts = 3
            user.login_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            user.failed_mfa_attempts = 3
            user.mfa_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            
            # Clear all lockouts
            clear_all_lockouts(user)
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            assert user.failed_login_attempts == 0
            assert user.login_locked_until is None
            assert user.failed_mfa_attempts == 0
            assert user.mfa_locked_until is None


class TestBlogRepository:
    """Test cases for blog repository functions."""
    
    def test_get_category_by_hex_id(self, app, test_category):
        """Test getting category by hex ID."""
        with app.app_context():
            found_category = get_category_by_hex_id(test_category.hex_id)
            assert found_category is not None
            assert found_category.id == test_category.id
            assert found_category.name == test_category.name
    
    def test_get_category_by_slug(self, app, test_category):
        """Test getting category by slug."""
        with app.app_context():
            found_category = get_category_by_slug(test_category.slug)
            assert found_category is not None
            assert found_category.id == test_category.id
            assert found_category.name == test_category.name
    
    def test_get_post_by_hex_id(self, app, test_post):
        """Test getting post by hex ID."""
        with app.app_context():
            found_post = get_post_by_hex_id(test_post.hex_id)
            assert found_post is not None
            assert found_post.id == test_post.id
            assert found_post.title == test_post.title
    
    def test_get_post_by_slug(self, app, test_post):
        """Test getting post by slug."""
        with app.app_context():
            found_post = get_post_by_slug(test_post.slug)
            assert found_post is not None
            assert found_post.id == test_post.id
            assert found_post.title == test_post.title
    
    def test_list_posts_by_category(self, app, test_category, test_admin_user):
        """Test getting posts by category."""
        with app.app_context():
            # Create multiple posts in the category
            from app.models import Post
            
            post1 = Post(
                title='Post 1',
                slug='post-1',
                content_blocks=[{'type': 'text', 'content': 'Content 1'}],
                category_id=test_category.id,
                author_id=test_admin_user.id
            )
            post2 = Post(
                title='Post 2',
                slug='post-2',
                content_blocks=[{'type': 'text', 'content': 'Content 2'}],
                category_id=test_category.id,
                author_id=test_admin_user.id
            )
            
            db.session.add_all([post1, post2])
            db.session.commit()
            
            posts, total = list_posts_by_category(test_category.slug)
            assert len(posts) >= 2  # At least our 2 posts (plus any from fixtures)
            assert total >= 2
            
            # Check that all posts belong to the category
            for post in posts:
                assert post.category_id == test_category.id
    
    def test_list_posts(self, app, test_admin_user, test_category):
        """Test getting recent posts."""
        with app.app_context():
            from app.models import Post
            
            # Create posts with different timestamps
            older_post = Post(
                title='Older Post',
                slug='older-post',
                content_blocks=[{'type': 'text', 'content': 'Older content'}],
                author_id=test_admin_user.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
            newer_post = Post(
                title='Newer Post',
                slug='newer-post',
                content_blocks=[{'type': 'text', 'content': 'Newer content'}],
                author_id=test_admin_user.id,
                created_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            
            db.session.add_all([older_post, newer_post])
            db.session.commit()
            
            # Get recent posts (limit 5)
            recent_posts, total = list_posts(per_page=5)
            assert len(recent_posts) >= 2
            assert total >= 2
            
            # Should be ordered by created_at descending
            for i in range(len(recent_posts) - 1):
                assert recent_posts[i].created_at >= recent_posts[i + 1].created_at


class TestProjectRepository:
    """Test cases for project repository functions."""
    
    def test_get_project_by_hex_id(self, app, test_project):
        """Test getting project by hex ID."""
        with app.app_context():
            from app.repositories.project import get_project_by_hex_id
            
            found_project = get_project_by_hex_id(test_project.hex_id)
            assert found_project is not None
            assert found_project.id == test_project.id
            assert found_project.project_title == test_project.project_title
