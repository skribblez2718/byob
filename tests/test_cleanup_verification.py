#!/usr/bin/env python3
"""
Test to verify that test users are properly cleaned up after tests complete.
This ensures no test data persists in the database.
"""

import pytest
from sqlalchemy import text

from app.extensions import db
from app.models import User, Category, Post, Project


class TestDatabaseCleanup:
    """Test cases to verify database cleanup after tests."""
    
    def test_database_starts_empty(self, app):
        """Verify database starts empty for each test."""
        with app.app_context():
            # Check that all tables are empty
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            category_count = db.session.execute(text("SELECT COUNT(*) FROM categories")).scalar()
            post_count = db.session.execute(text("SELECT COUNT(*) FROM posts")).scalar()
            project_count = db.session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
            
            assert user_count == 0, f"Users table should be empty, found {user_count} records"
            assert category_count == 0, f"Categories table should be empty, found {category_count} records"
            assert post_count == 0, f"Posts table should be empty, found {post_count} records"
            assert project_count == 0, f"Projects table should be empty, found {project_count} records"
    
    def test_create_and_verify_cleanup(self, app):
        """Test that data created in test is cleaned up."""
        with app.app_context():
            # Create test data
            user = User(
                username='cleanup_test_user',
                email='cleanup@example.com',
                password_hash='test_hash'
            )
            db.session.add(user)
            db.session.commit()
            
            # Verify data exists
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert user_count == 1
            
            # The cleanup will happen automatically after this test
            # The next test should verify the database is clean again
    
    def test_database_cleaned_after_previous_test(self, app):
        """Verify database was cleaned after the previous test."""
        with app.app_context():
            # Check that all tables are empty again
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert user_count == 0, "Database should be cleaned between tests"
    
    def test_admin_user_fixture_cleanup(self, app, test_admin_user):
        """Test that admin user fixture is properly cleaned up."""
        with app.app_context():
            # Verify the fixture user exists
            assert test_admin_user.username == 'testadmin'
            assert test_admin_user.is_admin is True
            
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert user_count == 1
            
            # After this test, the user should be cleaned up
    
    def test_no_admin_user_persists(self, app):
        """Verify admin user from previous test was cleaned up."""
        with app.app_context():
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert user_count == 0, "Admin user fixture should be cleaned up"
            
            # Also verify no user with admin username exists
            admin_user = db.session.execute(
                text("SELECT * FROM users WHERE username = 'testadmin'")
            ).fetchone()
            assert admin_user is None, "No admin user should persist in database"
