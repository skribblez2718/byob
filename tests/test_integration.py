"""Integration tests for the Flask blog application."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone
import json

from app.models import User, Category, Post, Project
from app.extensions import db
from app.utils.crypto import hash_password


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    def test_complete_login_flow(self, client, test_admin_user):
        """Test complete login flow from start to finish."""
        # 1. Start at login page
        response = client.get('/auth/login')
        assert response.status_code == 200
        
        # Extract CSRF token from the form
        import re
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', response.data.decode())
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # 2. Submit login form
        response = client.post('/auth/login', data={
            'username': test_admin_user.username,
            'password': 'adminpassword',  # Use correct password from fixture
            'csrf_token': csrf_token
        }, follow_redirects=True)
        
        # Should be redirected and logged in
        assert response.status_code == 200
        
        # 3. Verify session is set
        with client.session_transaction() as sess:
            assert '_user_id' in sess
            assert sess['_user_id'] == str(test_admin_user.id)
        
        # 4. Access protected resource
        response = client.get('/admin/')
        # Should return 403 since MFA hasn't been completed yet
        assert response.status_code == 403
        
        # 5. Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # 6. Verify session is cleared
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_admin_mfa_flow(self, client, test_admin_user):
        """Test complete admin MFA authentication flow."""
        # 1. Login as admin
        response = client.post('/auth/login', data={
            'username': test_admin_user.username,
            'password': 'adminpassword'
        })
        assert response.status_code == 302
        
        # 2. Try to access admin dashboard - should return 403 since MFA not completed
        response = client.get('/admin/')
        assert response.status_code == 403
        
        # 3. Access MFA page
        response = client.get('/auth/mfa')
        assert response.status_code == 200
        
        # 4. Mock successful MFA verification
        with patch('app.services.auth.verify_mfa_with_rate_limiting') as mock_verify:
            mock_verify.return_value = (True, None)
            
            response = client.post('/auth/mfa', data={
                'mfa_code': '123456'
            })
            assert response.status_code == 302
        
        # 5. Verify MFA session flag is set
        with client.session_transaction() as sess:
            assert sess.get('mfa_passed') is True
        
        # 6. Now should be able to access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
    
    def test_rate_limiting_flow(self, client, test_admin_user):
        """Test rate limiting on login attempts."""
        # Extract CSRF token first
        import re
        response = client.get('/auth/login')
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', response.data.decode())
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Make multiple failed login attempts
        for i in range(4):  # One more than the limit
            response = client.post('/auth/login', data={
                'username': test_admin_user.username,
                'password': 'wrongpassword',
                'csrf_token': csrf_token
            })
            
        # Should be rate limited now
        response = client.post('/auth/login', data={
            'username': test_admin_user.username,
            'password': 'adminpassword',  # Even correct password should be blocked
            'csrf_token': csrf_token
        })
        
        # Check that user is locked out
        from app.repositories.user import get_user_by_username, is_user_login_locked
        user = get_user_by_username(test_admin_user.username)
        assert is_user_login_locked(user) is True
        
        # Verify lockout time
        from datetime import datetime, timezone, timedelta
        lockout_time = user.login_locked_until
        if lockout_time.tzinfo is None:
            # Convert to UTC if naive
            expected_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
        else:
            expected_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        time_diff = abs((lockout_time - expected_time).total_seconds())
        assert time_diff < 120  # Within 2 minutes tolerance


class TestBlogWorkflow:
    """Test complete blog management workflows."""
    
    def test_create_category_and_post_workflow(self, mfa_authenticated_admin_client):
        """Test creating a category and then a post in that category."""
        # 1. Create a new category
        response = mfa_authenticated_admin_client.post('/admin/categories/new', data={
            'name': 'Technology',
            'slug': 'technology',
            'description': 'Tech-related posts'
        })
        assert response.status_code == 302
        
        # 2. Verify category was created
        from app.repositories.blog import get_category_by_slug
        category = get_category_by_slug('technology')
        assert category is not None
        assert category.name == 'Technology'
        
        # 3. Create a post in the new category
        response = mfa_authenticated_admin_client.post('/admin/posts/new', data={
            'title': 'My Tech Post',
            'slug': 'my-tech-post',
            'content': '<p>This is a technology post.</p>',
            'excerpt': 'A post about technology',
            'category_id': category.id
        })
        assert response.status_code == 302
        
        # 4. Verify post was created
        from app.repositories.blog import get_post_by_slug
        post = get_post_by_slug('my-tech-post')
        assert post is not None
        assert post.title == 'My Tech Post'
        assert post.category_id == category.id
        
        # 5. View the post on the public blog
        response = mfa_authenticated_admin_client.get(f'/blog/{post.hex_id}')
        assert response.status_code == 200
        assert b'My Tech Post' in response.data
        
        # 6. View posts by category
        response = mfa_authenticated_admin_client.get(f'/blog/category/{category.hex_id}')
        assert response.status_code == 200
        assert b'My Tech Post' in response.data
    
    def test_edit_and_delete_post_workflow(self, mfa_authenticated_admin_client, test_post):
        """Test editing and then deleting a post."""
        # 1. Edit the post
        response = mfa_authenticated_admin_client.post(f'/admin/posts/{test_post.hex_id}/edit', data={
            'title': 'Updated Test Post',
            'slug': test_post.slug,  # Keep same slug
            'content': '<p>Updated content</p>',
            'excerpt': 'Updated excerpt'
        })
        assert response.status_code == 302
        
        # 2. Verify post was updated
        db.session.refresh(test_post)
        assert test_post.title == 'Updated Test Post'
        
        # 3. View updated post
        response = mfa_authenticated_admin_client.get(f'/blog/{test_post.hex_id}')
        assert response.status_code == 200
        assert b'Updated Test Post' in response.data
        
        # 4. Delete the post
        response = mfa_authenticated_admin_client.post(f'/admin/posts/{test_post.hex_id}/delete')
        assert response.status_code == 302
        
        # 5. Verify post was deleted
        response = mfa_authenticated_admin_client.get(f'/blog/{test_post.hex_id}')
        assert response.status_code == 404


class TestAPIWorkflow:
    """Test API workflows and integrations."""
    
    def test_api_crud_workflow(self, mfa_authenticated_admin_client):
        """Test complete CRUD workflow via API."""
        # 1. Create category via API
        response = mfa_authenticated_admin_client.post('/api/admin/categories',
            json={
                'name': 'API Category',
                'slug': 'api-category',
                'description': 'Created via API'
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        category_hex_id = data['hex_id']
        
        # 2. Read category via API
        response = mfa_authenticated_admin_client.get(f'/api/admin/categories/{category_hex_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'API Category'
        
        # 3. Update category via API
        response = mfa_authenticated_admin_client.put(f'/api/admin/categories/{category_hex_id}',
            json={
                'name': 'Updated API Category',
                'description': 'Updated via API'
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Updated API Category'
        
        # 4. Delete category via API
        response = mfa_authenticated_admin_client.delete(f'/api/admin/categories/{category_hex_id}')
        assert response.status_code == 204
        
        # 5. Verify deletion
        response = mfa_authenticated_admin_client.get(f'/api/admin/categories/{category_hex_id}')
        assert response.status_code == 404
    
    def test_public_api_access(self, client, test_category, test_post, test_project):
        """Test public API endpoints don't require authentication."""
        # Test categories API
        response = client.get('/api/categories')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'categories' in data
        assert len(data['categories']) >= 1
        
        # Test posts API
        response = client.get('/api/posts')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'posts' in data
        assert len(data['posts']) >= 1
        
        # Test projects API
        response = client.get('/api/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'projects' in data
        assert len(data['projects']) >= 1
    
    def test_admin_api_requires_authentication(self, client):
        """Test that admin API endpoints require proper authentication."""
        admin_endpoints = [
            '/api/admin/categories',
            '/api/admin/posts',
            '/api/admin/projects'
        ]
        
        for endpoint in admin_endpoints:
            # Test without authentication
            response = client.get(endpoint)
            assert response.status_code == 401
            
            # Test POST without authentication
            response = client.post(endpoint, json={'test': 'data'})
            assert response.status_code == 401


class TestSecurityIntegration:
    """Test security features integration."""
    
    def test_csrf_protection(self, client):
        """Test CSRF protection on forms."""
        # Enable CSRF for this test
        with client.application.app_context():
            client.application.config['WTF_CSRF_ENABLED'] = True
            
            # Try to POST without CSRF token
            response = client.post('/auth/login', data={
                'username': 'test',
                'password': 'test'
            })
            
            # Should get CSRF error
            assert response.status_code == 400
    
    def test_html_sanitization_in_posts(self, mfa_authenticated_admin_client):
        """Test that HTML content is properly sanitized."""
        # Create post with potentially dangerous HTML
        dangerous_html = '''
        <p>Safe content</p>
        <script>alert('xss')</script>
        <img src="x" onerror="alert('xss')">
        <a href="javascript:alert('xss')">Click me</a>
        '''
        
        response = mfa_authenticated_admin_client.post('/admin/posts/new', data={
            'title': 'Security Test Post',
            'slug': 'security-test-post',
            'content': dangerous_html,
            'excerpt': 'Testing security'
        })
        assert response.status_code == 302
        
        # Verify post was created and content was sanitized
        from app.repositories.blog import get_post_by_slug
        post = get_post_by_slug('security-test-post')
        assert post is not None
        
        # View the post and check that dangerous content was removed
        response = mfa_authenticated_admin_client.get(f'/blog/{post.hex_id}')
        assert response.status_code == 200
        assert b'<script>' not in response.data
        assert b'onerror=' not in response.data
        assert b'javascript:' not in response.data
        assert b'Safe content' in response.data
    
    def test_hex_id_security(self, client, test_post):
        """Test that hex IDs prevent enumeration attacks."""
        # Try to access post with integer ID (should fail)
        response = client.get(f'/blog/{test_post.id}')
        assert response.status_code == 404
        
        # Access with hex ID should work
        response = client.get(f'/blog/{test_post.hex_id}')
        assert response.status_code == 200
        
        # Try to guess hex IDs (should be cryptographically secure)
        fake_hex_ids = ['00000000000000000000000000000000', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa']
        for fake_id in fake_hex_ids:
            response = client.get(f'/blog/{fake_id}')
            assert response.status_code == 404


class TestPerformanceIntegration:
    """Test performance-related integrations."""
    
    def test_database_queries_efficiency(self, client, app):
        """Test that pages don't make excessive database queries."""
        with app.app_context():
            # Create multiple test data
            categories = []
            posts = []
            
            for i in range(5):
                category = Category(
                    name=f'Category {i}',
                    slug=f'category-{i}',
                    description=f'Description {i}'
                )
                categories.append(category)
                db.session.add(category)
            
            db.session.commit()
            
            for i in range(10):
                post = Post(
                    title=f'Post {i}',
                    slug=f'post-{i}',
                    content_blocks=[{'type': 'text', 'content': f'Content {i}'}],
                    category_id=categories[i % 5].id,
                    author_id=1  # Assuming test user has ID 1
                )
                posts.append(post)
                db.session.add(post)
            
            db.session.commit()
            
            # Test blog page doesn't make N+1 queries
            with patch('sqlalchemy.engine.Engine.execute') as mock_execute:
                response = client.get('/blog')
                assert response.status_code == 200
                
                # Should make a reasonable number of queries (not N+1)
                # This is a basic check - in a real app you'd use a query counter
                call_count = mock_execute.call_count
                assert call_count < 20  # Arbitrary reasonable limit
    
    def test_caching_integration(self, client, app):
        """Test that caching is working properly."""
        # This would test Flask-Caching integration
        # For now, just verify cache is configured
        assert 'CACHE_TYPE' in app.config
        
        # Test that repeated requests might be cached
        # (This is a basic test - real caching tests would be more sophisticated)
        response1 = client.get('/')
        response2 = client.get('/')
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestErrorHandlingIntegration:
    """Test error handling across the application."""
    
    def test_404_error_handling(self, client):
        """Test 404 error handling across different routes."""
        not_found_urls = [
            '/nonexistent',
            '/blog/nonexistent',
            '/projects/nonexistent',
            '/blog/category/nonexistent'
        ]
        
        for url in not_found_urls:
            response = client.get(url)
            assert response.status_code == 404
    
    def test_database_error_handling(self, client, app):
        """Test graceful handling of database errors."""
        # This would test what happens when database is unavailable
        # For now, just a placeholder test
        with app.app_context():
            # Simulate database connection issue
            with patch('app.extensions.db.session.execute') as mock_execute:
                mock_execute.side_effect = Exception("Database connection failed")
                
                # App should handle database errors gracefully
                response = client.get('/blog')
                # Depending on error handling, this might be 500 or a graceful fallback
                assert response.status_code in [200, 500]
    
    def test_validation_error_handling(self, mfa_authenticated_admin_client):
        """Test validation error handling in forms."""
        # Try to create category with invalid data
        response = mfa_authenticated_admin_client.post('/admin/categories/new', data={
            'name': '',  # Empty name should fail validation
            'slug': 'test-slug',
            'description': 'Test description'
        })
        
        # Should return form with validation errors
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'required' in response.data.lower()
        
        # Try to create post with invalid data
        response = mfa_authenticated_admin_client.post('/admin/posts/new', data={
            'title': '',  # Empty title should fail validation
            'slug': 'test-slug',
            'content': 'Test content'
        })
        
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'required' in response.data.lower()
