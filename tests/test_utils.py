"""Tests for utility functions."""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from PIL import Image
import io

from app.utils.html_sanitizer import sanitize_html, ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from app.utils.crypto import (
    hash_password, verify_password, encrypt_bytes, decrypt_bytes,
    hash_backup_code, verify_backup_code
)
from app.utils.slug import slugify
from app.utils.markdown import render_markdown
from app.utils.image import validate_image, rewrite_image


class TestHTMLSanitizer:
    """Test cases for HTML sanitization."""
    
    def test_sanitize_basic_html(self):
        """Test sanitizing basic allowed HTML."""
        html = '<p>This is a <strong>test</strong> paragraph.</p>'
        result = sanitize_html(html)
        assert result == html
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        html = '<p>Safe content</p><script>alert("xss")</script>'
        result = sanitize_html(html)
        assert '<script>' not in result
        assert 'alert("xss")' not in result
        assert '<p>Safe content</p>' in result
    
    def test_sanitize_removes_dangerous_attributes(self):
        """Test that dangerous attributes are removed."""
        html = '<p onclick="alert(\'xss\')">Click me</p>'
        result = sanitize_html(html)
        assert 'onclick' not in result
        assert '<p>Click me</p>' == result
    
    def test_sanitize_allows_safe_attributes(self):
        """Test that safe attributes are preserved."""
        html = '<a href="https://example.com" title="Example">Link</a>'
        result = sanitize_html(html)
        assert 'href="https://example.com"' in result
        assert 'title="Example"' in result
    
    def test_sanitize_removes_disallowed_tags(self):
        """Test that disallowed tags are removed."""
        html = '<p>Safe</p><iframe src="evil.com"></iframe>'
        result = sanitize_html(html)
        assert '<iframe>' not in result
        assert '<p>Safe</p>' in result
    
    def test_sanitize_preserves_formatting(self):
        """Test that formatting tags are preserved."""
        html = '<h1>Title</h1><p>Text with <em>emphasis</em> and <strong>bold</strong>.</p>'
        result = sanitize_html(html)
        assert '<h1>Title</h1>' in result
        assert '<em>emphasis</em>' in result
        assert '<strong>bold</strong>' in result
    
    def test_sanitize_preserves_lists(self):
        """Test that list tags are preserved."""
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = sanitize_html(html)
        assert '<ul>' in result
        assert '<li>Item 1</li>' in result
        assert '<li>Item 2</li>' in result
    
    def test_sanitize_empty_input(self):
        """Test sanitizing empty input."""
        assert sanitize_html('') == ''
        assert sanitize_html(None) == ''
    
    def test_allowed_tags_configuration(self):
        """Test that allowed tags are properly configured."""
        expected_tags = {
            'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
        }
        assert set(ALLOWED_TAGS) >= expected_tags
    
    def test_allowed_attributes_configuration(self):
        """Test that allowed attributes are properly configured."""
        assert 'href' in ALLOWED_ATTRIBUTES.get('a', [])
        assert 'title' in ALLOWED_ATTRIBUTES.get('a', [])


class TestCrypto:
    """Test cases for cryptographic functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith('$2b$')  # bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        assert verify_password('wrongpassword', hashed) is False
    
    def test_encrypt_decrypt_bytes(self):
        """Test byte encryption and decryption."""
        data = b'secret data to encrypt'
        encrypted = encrypt_bytes(data)
        
        assert encrypted != data
        assert len(encrypted) > len(data)  # Encrypted data is longer
        
        decrypted = decrypt_bytes(encrypted)
        assert decrypted == data
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        data = 'secret string to encrypt'
        encrypted = encrypt_bytes(data.encode())
        decrypted = decrypt_bytes(encrypted).decode()
        
        assert decrypted == data
    
    def test_hash_backup_code(self):
        """Test backup code hashing."""
        code = 'backup123'
        hashed = hash_backup_code(code)
        
        assert hashed != code
        assert len(hashed) > 50
    
    def test_verify_backup_code_correct(self):
        """Test backup code verification with correct code."""
        code = 'backup123'
        hashed = hash_backup_code(code)
        
        assert verify_backup_code(code, hashed) is True
    
    def test_verify_backup_code_incorrect(self):
        """Test backup code verification with incorrect code."""
        code = 'backup123'
        hashed = hash_backup_code(code)
        
        assert verify_backup_code('wrongcode', hashed) is False


class TestSlug:
    """Test cases for slug generation."""
    
    def test_slugify_basic(self):
        """Test basic slug creation."""
        assert slugify('Hello World') == 'hello-world'
        assert slugify('Test Title') == 'test-title'
    
    def test_slugify_special_characters(self):
        """Test slug creation with special characters."""
        assert slugify('Hello, World!') == 'hello-world'
        assert slugify('Test & Title') == 'test-title'
        assert slugify('Multiple   Spaces') == 'multiple-spaces'
    
    def test_slugify_unicode(self):
        """Test slug creation with unicode characters."""
        assert slugify('Café') == 'cafe'
        assert slugify('Naïve') == 'naive'
    
    def test_slugify_numbers(self):
        """Test slug creation with numbers."""
        assert slugify('Test 123') == 'test-123'
        assert slugify('Version 2.0') == 'version-20'
    
    def test_slugify_empty(self):
        """Test slug creation with empty input."""
        assert slugify('') == ''
        assert slugify('   ') == ''


class TestMarkdown:
    """Test cases for Markdown rendering."""
    
    def test_render_markdown_basic(self):
        """Test basic Markdown rendering."""
        markdown = '# Title\n\nThis is **bold** text.'
        html = render_markdown(markdown)
        
        assert '<h1>Title</h1>' in html
        assert '<strong>bold</strong>' in html
    
    def test_render_markdown_code_blocks(self):
        """Test Markdown code block rendering."""
        markdown = '```python\nprint("hello")\n```'
        html = render_markdown(markdown)
        
        assert '<pre>' in html
        assert '<code' in html
        assert 'print("hello")' in html
    
    def test_render_markdown_links(self):
        """Test Markdown link rendering."""
        markdown = '[Example](https://example.com)'
        html = render_markdown(markdown)
        
        assert '<a href="https://example.com">Example</a>' in html
    
    def test_render_markdown_lists(self):
        """Test Markdown list rendering."""
        markdown = '- Item 1\n- Item 2\n- Item 3'
        html = render_markdown(markdown)
        
        assert '<ul>' in html
        assert '<li>Item 1</li>' in html
        assert '<li>Item 2</li>' in html
    
    def test_render_markdown_empty(self):
        """Test rendering empty Markdown."""
        assert render_markdown('') == ''
        assert render_markdown(None) == ''


class TestImage:
    """Test cases for image utilities."""
    
    def create_test_image(self, width=100, height=100, format='JPEG'):
        """Helper to create a test image."""
        img = Image.new('RGB', (width, height), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_validate_image_valid_jpeg(self):
        """Test validating a valid JPEG image."""
        image_data = self.create_test_image(format='JPEG')
        
        is_valid, error, info = validate_image(image_data)
        assert is_valid is True
        assert error is None
        assert info['format'] == 'JPEG'
    
    def test_validate_image_valid_png(self):
        """Test validating a valid PNG image."""
        image_data = self.create_test_image(format='PNG')
        
        is_valid, error, info = validate_image(image_data)
        assert is_valid is True
        assert error is None
        assert info['format'] == 'PNG'
    
    def test_validate_image_invalid_data(self):
        """Test validating invalid image data."""
        invalid_data = b'not an image'
        
        is_valid, error, info = validate_image(invalid_data)
        assert is_valid is False
        assert error == 'invalid_image'
    
    def test_validate_image_too_large(self):
        """Test validating image that's too large."""
        # Create a large image data
        large_data = b'x' * (6 * 1024 * 1024)  # 6MB of fake data
        
        is_valid, error, info = validate_image(large_data, max_bytes=1024*1024)
        assert is_valid is False
        assert error == 'file_too_large'
    
    def test_rewrite_image(self):
        """Test rewriting an image."""
        original_data = self.create_test_image(width=200, height=150)
        
        rewritten_data, format_str, mime_type = rewrite_image(original_data)
        
        # Should return valid data
        assert len(rewritten_data) > 0
        assert format_str in ['JPEG', 'PNG', 'WEBP']
        assert mime_type.startswith('image/')
        
        # Should still be a valid image
        is_valid, error, info = validate_image(rewritten_data)
        assert is_valid is True
    
    def test_rewrite_image_with_target_format(self):
        """Test rewriting image with specific target format."""
        jpeg_data = self.create_test_image(format='JPEG')
        
        png_data, format_str, mime_type = rewrite_image(jpeg_data, target_format='PNG')
        
        assert format_str == 'PNG'
        assert mime_type == 'image/png'
    
    def test_rewrite_image_invalid_data(self):
        """Test rewriting invalid image data."""
        invalid_data = b'not an image'
        
        with pytest.raises(ValueError, match='invalid_image'):
            rewrite_image(invalid_data)


class TestHttpClient:
    """Test cases for HTTP client utilities."""
    
    @patch('requests.get')
    def test_http_client_get_success(self, mock_get):
        """Test successful HTTP GET request."""
        from app.utils.http_client import make_request
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_response.text = '{"data": "test"}'
        mock_get.return_value = mock_response
        
        result = make_request('GET', 'https://api.example.com/data')
        
        assert result['status_code'] == 200
        assert result['data'] == {'data': 'test'}
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_http_client_get_failure(self, mock_get):
        """Test failed HTTP GET request."""
        from app.utils.http_client import make_request
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_get.return_value = mock_response
        
        result = make_request('GET', 'https://api.example.com/notfound')
        
        assert result['status_code'] == 404
        assert 'error' in result
    
    @patch('requests.post')
    def test_http_client_post_with_data(self, mock_post):
        """Test HTTP POST request with data."""
        from app.utils.http_client import make_request
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1, 'created': True}
        mock_post.return_value = mock_response
        
        data = {'name': 'Test', 'value': 123}
        result = make_request('POST', 'https://api.example.com/create', json=data)
        
        assert result['status_code'] == 201
        assert result['data']['created'] is True
        mock_post.assert_called_once()
    
    def test_http_client_timeout_handling(self):
        """Test HTTP client timeout handling."""
        from app.utils.http_client import make_request
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Request timed out")
            
            result = make_request('GET', 'https://slow.example.com', timeout=1)
            
            assert 'error' in result
            assert 'timeout' in result['error'].lower()
    
    def test_http_client_connection_error(self):
        """Test HTTP client connection error handling."""
        from app.utils.http_client import make_request
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")
            
            result = make_request('GET', 'https://unreachable.example.com')
            
            assert 'error' in result
            assert 'connection' in result['error'].lower()
