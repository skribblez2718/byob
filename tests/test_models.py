"""Tests for database models."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Category, Post, Project, generate_hex_id
from app.utils.crypto import hash_password


class TestUser:
    """Test cases for User model."""
    
    def test_admin_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='newuser',
                email='newuser@example.com',
                password_hash=hash_password('password123'),
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.hex_id is not None
            assert len(user.hex_id) == 32
            assert user.username == 'newuser'
            assert user.email == 'newuser@example.com'
            assert user.is_admin is False
            assert user.mfa_passed is False
            assert user.mfa_setup_completed is False
            assert user.failed_login_attempts == 0
            assert user.failed_mfa_attempts == 0
            assert user.login_locked_until is None
            assert user.mfa_locked_until is None
            assert user.created_at is not None
    
    def test_admin_user_unique_constraints(self, app):
        """Test that username and email must be unique."""
        with app.app_context():
            # Create first user
            user1 = User(
                username='testuser1',
                email='test1@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user1)
            db.session.commit()
            
            # Try to create user with same username
            user2 = User(
                username='testuser1',  # Same username
                email='different@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
            
            db.session.rollback()
            
            # Try to create user with same email
            user3 = User(
                username='differentuser',
                email='test1@example.com',  # Same email
                password_hash=hash_password('password123')
            )
            db.session.add(user3)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_admin_user_hex_id_unique(self, app):
        """Test that hex_id is unique."""
        with app.app_context():
            user1 = User(
                username='user1',
                email='user1@example.com',
                password_hash=hash_password('password123')
            )
            user2 = User(
                username='user2',
                email='user2@example.com',
                password_hash=hash_password('password123')
            )
            
            db.session.add_all([user1, user2])
            db.session.commit()
            
            assert user1.hex_id != user2.hex_id
    
    def test_admin_user_get_id(self, app):
        """Test Flask-Login get_id method."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.get_id() == str(user.id)


class TestCategory:
    """Test cases for Category model."""
    
    def test_category_creation(self, app):
        """Test creating a new category."""
        with app.app_context():
            category = Category(
                name='Technology',
                slug='technology',
                description='Tech-related posts',
                display_order=1
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.id is not None
            assert category.hex_id is not None
            assert len(category.hex_id) == 32
            assert category.name == 'Technology'
            assert category.slug == 'technology'
            assert category.description == 'Tech-related posts'
            assert category.display_order == 1
            assert category.created_at is not None
    
    def test_category_slug_unique(self, app):
        """Test that category slug must be unique."""
        with app.app_context():
            # Create first category
            category1 = Category(
                name='Technology',
                slug='technology',
                description='Tech posts'
            )
            db.session.add(category1)
            db.session.commit()
            
            # Try to create category with same slug
            category2 = Category(
                name='Different Name',
                slug='technology',  # Same slug
                description='Different description'
            )
            db.session.add(category2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_category_posts_relationship(self, app):
        """Test category-posts relationship."""
        with app.app_context():
            # Create user and category
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            category = Category(
                name='Test Category',
                slug='test-category',
                description='A test category'
            )
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create post
            post = Post(
                title='Test Post',
                slug='test-post-cat',
                content_blocks=[{'type': 'text', 'content': 'Test content'}],
                category_id=category.id,
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            
            # Refresh category to get updated relationship
            db.session.refresh(category)
            assert len(category.posts) == 1
            assert category.posts[0].title == 'Test Post'


class TestPost:
    """Test cases for Post model."""
    
    def test_post_creation(self, app):
        """Test creating a new post."""
        with app.app_context():
            # Create user and category
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            category = Category(
                name='Test Category',
                slug='test-category',
                description='A test category'
            )
            db.session.add_all([user, category])
            db.session.commit()
            
            content_blocks = [
                {'type': 'paragraph', 'content': 'First paragraph'},
                {'type': 'heading', 'content': 'Section Title', 'level': 2}
            ]
            
            post = Post(
                title='My Blog Post',
                slug='my-blog-post',
                content_blocks=content_blocks,
                excerpt='This is an excerpt',
                category_id=category.id,
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            
            assert post.id is not None
            assert post.hex_id is not None
            assert len(post.hex_id) == 32
            assert post.title == 'My Blog Post'
            assert post.slug == 'my-blog-post'
            assert post.content_blocks == content_blocks
            assert post.excerpt == 'This is an excerpt'
            assert post.category_id == category.id
            assert post.author_id == user.id
            assert post.created_at is not None
    
    def test_post_slug_unique(self, app):
        """Test that post slug must be unique."""
        with app.app_context():
            # Create user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            # Create first post
            post1 = Post(
                title='First Post',
                slug='test-post',
                content_blocks=[{'type': 'text', 'content': 'First content'}],
                author_id=user.id
            )
            db.session.add(post1)
            db.session.commit()
            
            # Try to create post with same slug
            post2 = Post(
                title='Different Title',
                slug='test-post',  # Same slug
                content_blocks=[{'type': 'text', 'content': 'Different content'}],
                author_id=user.id
            )
            db.session.add(post2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_post_relationships(self, app):
        """Test post relationships with user and category."""
        with app.app_context():
            # Create user and category
            user = User(
                username='testadmin',
                email='admin@example.com',
                password_hash=hash_password('password123')
            )
            category = Category(
                name='Test Category',
                slug='test-category',
                description='A test category'
            )
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create post
            post = Post(
                title='Test Post',
                slug='test-post-rel',
                content_blocks=[{'type': 'text', 'content': 'Test content'}],
                category_id=category.id,
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            
            # Refresh to get relationships
            db.session.refresh(post)
            
            assert post.author is not None
            assert post.author.username == 'testadmin'
            assert post.category is not None
            assert post.category.name == 'Test Category'
    
    def test_post_with_image(self, app):
        """Test post with image data."""
        with app.app_context():
            # Create user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            image_data = b'fake_image_data'
            post = Post(
                title='Post with Image',
                slug='post-with-image',
                content_blocks=[{'type': 'text', 'content': 'Post content'}],
                image_data=image_data,
                image_mime='image/jpeg',
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            
            assert post.image_data == image_data
            assert post.image_mime == 'image/jpeg'
    
    def test_post_without_category(self, app):
        """Test post creation without category (category_id can be null)."""
        with app.app_context():
            # Create user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            post = Post(
                title='Uncategorized Post',
                slug='uncategorized-post',
                content_blocks=[{'type': 'text', 'content': 'Content'}],
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            
            assert post.category_id is None
            assert post.category is None


class TestProject:
    """Test cases for Project model."""
    
    def test_project_creation(self, app):
        """Test creating a new project."""
        with app.app_context():
            # Create user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            project = Project(
                project_title='My Project',
                project_description='A cool project',
                project_url='https://github.com/user/project',
                project_image_url='https://example.com/image.jpg',
                user_id=user.id,
                display_order=1
            )
            db.session.add(project)
            db.session.commit()
            
            assert project.id is not None
            assert project.hex_id is not None
            assert len(project.hex_id) == 32
            assert project.project_title == 'My Project'
            assert project.project_description == 'A cool project'
            assert project.project_url == 'https://github.com/user/project'
            assert project.project_image_url == 'https://example.com/image.jpg'
            assert project.display_order == 1
            assert project.created_at is not None
    
    def test_project_optional_fields(self, app):
        """Test project with only required fields."""
        with app.app_context():
            # Create user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hash_password('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            project = Project(
                project_title='Minimal Project',
                project_description='Basic project',
                user_id=user.id
            )
            db.session.add(project)
            db.session.commit()
            
            assert project.project_image_url is None
            assert project.project_url is None
            assert project.display_order == 0  # default value


class TestGenerateHexId:
    """Test cases for hex ID generation."""
    
    def test_generate_hex_id_default_length(self):
        """Test generating hex ID with default length."""
        hex_id = generate_hex_id()
        assert len(hex_id) == 32
        assert all(c in '0123456789abcdef' for c in hex_id)
    
    def test_generate_hex_id_custom_length(self):
        """Test generating hex ID with custom length."""
        hex_id = generate_hex_id(16)
        assert len(hex_id) == 16
        assert all(c in '0123456789abcdef' for c in hex_id)
    
    def test_generate_hex_id_uniqueness(self):
        """Test that generated hex IDs are unique."""
        ids = [generate_hex_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All should be unique
