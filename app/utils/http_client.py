import requests
from flask import current_app, request
from urllib.parse import urljoin

class HTTPClient:
    """HTTP client for making requests within the application."""
    
    def __init__(self, base_url=None):
        """Initialize the HTTP client.
        
        Args:
            base_url (str, optional): Base URL for all requests. Defaults to None.
        """
        self.base_url = base_url
        if self.base_url is None and current_app:
            self.base_url = current_app.config.get('HTTP_CLIENT_BASE_URL', 'http://localhost:8000')
        
        if not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f'http://{self.base_url}'
    
    def _get_headers(self, headers=None):
        """Get default headers, including CSRF token if available."""
        default_headers = {
            'Accept': 'application/json'
        }

        # Add CSRF token from form if available in the current request context
        if request and 'csrf_token' in request.form:
            default_headers['X-CSRFToken'] = request.form['csrf_token']

        if headers:
            default_headers.update(headers)
        return default_headers

    def _get_cookies(self, cookies=None):
        """Get cookies, including from the current request context."""
        default_cookies = {}
        if request:
            default_cookies.update(request.cookies)
        if cookies:
            default_cookies.update(cookies)
        return default_cookies

    def _build_url(self, path):
        """Build the full URL from a path."""
        if path.startswith(('http://', 'https://')):
            return path
        return urljoin(self.base_url, path.lstrip('/'))

    def post(self, path, headers=None, cookies=None, **kwargs):
        """Make a POST request."""
        url = self._build_url(path)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.post(url, headers=headers, cookies=cookies, **kwargs)

    def get(self, path, params=None, headers=None, cookies=None, **kwargs):
        """Make a GET request."""
        url = self._build_url(path)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.get(url, params=params, headers=headers, cookies=cookies, **kwargs)

    def put(self, path, headers=None, cookies=None, **kwargs):
        """Make a PUT request."""
        url = self._build_url(path)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.put(url, headers=headers, cookies=cookies, **kwargs)

    def delete(self, path, headers=None, cookies=None, **kwargs):
        """Make a DELETE request."""
        url = self._build_url(path)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.delete(url, headers=headers, cookies=cookies, **kwargs)

# Create a default instance
http_client = HTTPClient()
