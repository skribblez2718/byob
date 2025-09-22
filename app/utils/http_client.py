import requests
import ipaddress
import socket
from flask import current_app, request
from urllib.parse import urljoin, urlparse

class HTTPClient:
    """HTTP client for making requests within the application."""

    # Private IP ranges that should be blocked for SSRF protection
    PRIVATE_IP_RANGES = [
        ipaddress.ip_network('127.0.0.0/8'),      # Loopback
        ipaddress.ip_network('10.0.0.0/8'),       # Private network
        ipaddress.ip_network('172.16.0.0/12'),    # Private network
        ipaddress.ip_network('192.168.0.0/16'),   # Private network
        ipaddress.ip_network('169.254.0.0/16'),   # Link-local (includes metadata endpoint)
        ipaddress.ip_network('::1/128'),          # IPv6 loopback
        ipaddress.ip_network('fc00::/7'),         # IPv6 unique local
        ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
    ]

    # Common cloud metadata endpoints that should be blocked
    BLOCKED_METADATA_HOSTS = [
        '169.254.169.254',  # AWS, Azure, GCP metadata
        'metadata.google.internal',  # GCP metadata
        'metadata.azure.com',  # Azure metadata
    ]

    def __init__(self, base_url=None, allowed_domains=None):
        """Initialize the HTTP client.

        Args:
            base_url (str, optional): Base URL for all requests. Defaults to None.
            allowed_domains (list, optional): List of allowed domains for requests.
                If provided, only these domains will be allowed.
        """
        self.base_url = base_url
        if self.base_url is None and current_app:
            self.base_url = current_app.config.get('HTTP_CLIENT_BASE_URL', 'http://localhost:8000')

        if not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f'http://{self.base_url}'

        # Initialize domain allowlist from config or parameter
        self.allowed_domains = allowed_domains
        if self.allowed_domains is None and current_app:
            # Get allowed domains from config, defaulting to empty list (allow all) if not configured
            self.allowed_domains = current_app.config.get('HTTP_CLIENT_ALLOWED_DOMAINS', [])
    
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

    def _is_private_ip(self, ip_str):
        """Check if an IP address is in a private/restricted range.

        Args:
            ip_str (str): IP address as string

        Returns:
            bool: True if IP is private/restricted, False otherwise
        """
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in network for network in self.PRIVATE_IP_RANGES)
        except ValueError:
            # Not a valid IP address
            return False

    def _validate_url(self, url):
        """Validate URL for SSRF protection.

        Args:
            url (str): URL to validate

        Returns:
            bool: True if URL is safe, False otherwise

        Raises:
            ValueError: If URL is blocked for security reasons
        """
        parsed = urlparse(url)

        # Ensure we only allow HTTP(S) schemes
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"Blocked: Invalid scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed.")

        # Extract hostname
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Blocked: Invalid URL - no hostname found")

        # Block known metadata endpoints
        if hostname.lower() in [h.lower() for h in self.BLOCKED_METADATA_HOSTS]:
            raise ValueError(f"Blocked: Access to metadata endpoint '{hostname}' is not allowed")

        # Check domain allowlist if configured
        if self.allowed_domains:
            # Check if hostname matches any allowed domain (including subdomains)
            hostname_lower = hostname.lower()
            allowed = any(
                hostname_lower == domain.lower() or
                hostname_lower.endswith('.' + domain.lower())
                for domain in self.allowed_domains
            )
            if not allowed:
                raise ValueError(f"Blocked: Domain '{hostname}' is not in the allowed domains list")

        # Resolve hostname to IP addresses and check each one
        try:
            # Get all IP addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None)
            ips = set()
            for info in addr_info:
                # info[4][0] contains the IP address
                ips.add(info[4][0])

            # Check if any resolved IP is private/restricted
            for ip in ips:
                if self._is_private_ip(ip):
                    raise ValueError(
                        f"Blocked: Host '{hostname}' resolves to private/restricted IP {ip}. "
                        "Access to private networks is not allowed for security reasons."
                    )
        except socket.gaierror as e:
            # DNS resolution failed
            raise ValueError(f"Blocked: Failed to resolve hostname '{hostname}': {str(e)}")
        except Exception as e:
            # Other errors during validation
            if "Blocked:" in str(e):
                raise  # Re-raise our own security blocks
            raise ValueError(f"Blocked: Error validating URL: {str(e)}")

        return True

    def _build_url(self, path):
        """Build the full URL from a path."""
        if path.startswith(('http://', 'https://')):
            return path
        return urljoin(self.base_url, path.lstrip('/'))

    def post(self, path, headers=None, cookies=None, **kwargs):
        """Make a POST request with SSRF protection.

        Raises:
            ValueError: If URL fails security validation
        """
        url = self._build_url(path)
        # Validate URL for SSRF protection
        self._validate_url(url)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.post(url, headers=headers, cookies=cookies, **kwargs)

    def get(self, path, params=None, headers=None, cookies=None, **kwargs):
        """Make a GET request with SSRF protection.

        Raises:
            ValueError: If URL fails security validation
        """
        url = self._build_url(path)
        # Validate URL for SSRF protection
        self._validate_url(url)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.get(url, params=params, headers=headers, cookies=cookies, **kwargs)

    def put(self, path, headers=None, cookies=None, **kwargs):
        """Make a PUT request with SSRF protection.

        Raises:
            ValueError: If URL fails security validation
        """
        url = self._build_url(path)
        # Validate URL for SSRF protection
        self._validate_url(url)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.put(url, headers=headers, cookies=cookies, **kwargs)

    def delete(self, path, headers=None, cookies=None, **kwargs):
        """Make a DELETE request with SSRF protection.

        Raises:
            ValueError: If URL fails security validation
        """
        url = self._build_url(path)
        # Validate URL for SSRF protection
        self._validate_url(url)
        headers = self._get_headers(headers)
        cookies = self._get_cookies(cookies)
        return requests.delete(url, headers=headers, cookies=cookies, **kwargs)

# Create a default instance
http_client = HTTPClient()
