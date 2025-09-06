"""Tests for service layer functions."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.models import User
from app.services.auth import (
    find_user_by_username,
    authenticate,
    verify_mfa_with_rate_limiting,
    ensure_totp_secret,
    verify_totp_code,
    generate_backup_codes,
    set_backup_codes,
    consume_backup_code
)
from app.utils.crypto import hash_password, encrypt_bytes


class TestAuthService:
    """Test cases for authentication service."""
    
    def test_find_user_by_username(self, app, test_admin_user):
        """Test finding user by username."""
        with app.app_context():
            found_user = find_user_by_username(test_admin_user.username)
            assert found_user is not None
            assert found_user.id == test_admin_user.id
    
    def test_find_user_by_username_not_found(self, app):
        """Test finding non-existent user."""
        with app.app_context():
            found_user = find_user_by_username('nonexistent')
            assert found_user is None
    
    def test_authenticate_success(self, app, test_admin_user):
        """Test successful authentication."""
        with app.app_context():
            user, error = authenticate(test_admin_user.username, 'adminpassword')
            assert user is not None
            assert user.id == test_admin_user.id
            assert error is None
    
    def test_authenticate_invalid_username(self, app):
        """Test authentication with invalid username."""
        with app.app_context():
            user, error = authenticate('nonexistent', 'password')
            assert user is None
            assert error == "Invalid username or password"
    
    def test_authenticate_invalid_password(self, app, test_admin_user):
        """Test authentication with invalid password."""
        with app.app_context():
            user, error = authenticate(test_admin_user.username, 'wrongpassword')
            assert user is None
            assert "Invalid username or password" in error
            assert "2 attempts remaining" in error
    
    def test_authenticate_lockout_after_three_attempts(self, app, test_admin_user):
        """Test account lockout after three failed attempts."""
        with app.app_context():
            # First two attempts
            for i in range(2):
                user, error = authenticate(test_admin_user.username, 'wrongpassword')
                assert user is None
                assert f"{2-i} attempts remaining" in error
            
            # Third attempt should trigger lockout
            user, error = authenticate(test_admin_user.username, 'wrongpassword')
            assert user is None
            assert "Account has been locked for 15 minutes" in error
            
            # Fourth attempt should show lockout message
            user, error = authenticate(test_admin_user.username, 'wrongpassword')
            assert user is None
            assert "Account locked due to 3 failed login attempts" in error
    
    def test_authenticate_locked_user(self, app, test_admin_user):
        """Test authentication with locked user."""
        with app.app_context():
            # Get fresh instance and set user as locked
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.failed_login_attempts = 3
            user.login_locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            from app.extensions import db
            db.session.commit()
            
            user, error = authenticate(test_admin_user.username, 'adminpassword')
            assert user is None
            assert "Account locked due to 3 failed login attempts" in error
    
    def test_authenticate_expired_lockout(self, app, test_admin_user):
        """Test authentication with expired lockout."""
        with app.app_context():
            # Get fresh instance and set user as locked in the past
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            user.failed_login_attempts = 3
            user.login_locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
            from app.extensions import db
            db.session.commit()
            
            # Should succeed and reset lockout
            user, error = authenticate(test_admin_user.username, 'adminpassword')
            assert user is not None
            assert error is None
    
    def test_verify_mfa_with_rate_limiting_no_secret(self, app, test_admin_user):
        """Test MFA verification without TOTP secret."""
        with app.app_context():
            success, error = verify_mfa_with_rate_limiting(test_admin_user, '123456')
            assert success is False
            assert "Invalid MFA code" in error
    
    @patch('app.services.auth.verify_totp_code')
    def test_verify_mfa_with_rate_limiting_success(self, mock_verify, app, test_admin_user):
        """Test successful MFA verification."""
        with app.app_context():
            mock_verify.return_value = True
            
            success, error = verify_mfa_with_rate_limiting(test_admin_user, '123456')
            assert success is True
            assert error is None
    
    @patch('app.services.auth.verify_totp_code')
    def test_verify_mfa_with_rate_limiting_failure(self, mock_verify, app, test_admin_user):
        """Test failed MFA verification with rate limiting."""
        with app.app_context():
            mock_verify.return_value = False
            
            # First two attempts
            for i in range(2):
                success, error = verify_mfa_with_rate_limiting(test_admin_user, '123456')
                assert success is False
                assert f"{2-i} attempts remaining" in error
            
            # Third attempt should trigger lockout
            success, error = verify_mfa_with_rate_limiting(test_admin_user, '123456')
            assert success is False
            assert "MFA has been locked for 15 minutes" in error
    
    def test_verify_mfa_locked_user(self, app, test_admin_user):
        """Test MFA verification with locked user."""
        with app.app_context():
            # Set user as MFA locked
            test_admin_user.failed_mfa_attempts = 3
            test_admin_user.mfa_locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            from app.extensions import db
            db.session.commit()
            
            success, error = verify_mfa_with_rate_limiting(test_admin_user, '123456')
            assert success is False
            assert "MFA locked due to 3 failed attempts" in error
    
    def test_ensure_totp_secret_new_user(self, app, test_admin_user):
        """Test ensuring TOTP secret for user without one."""
        with app.app_context():
            # Get fresh instance to avoid session conflicts
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.totp_secret_encrypted is None
            
            secret, uri = ensure_totp_secret(user)
            
            assert len(secret) == 32  # Base32 secret length
            assert uri.startswith('otpauth://totp/')
            # Email is URL-encoded in the URI
            import urllib.parse
            assert urllib.parse.quote(test_admin_user.email, safe='') in uri
            # Refresh user to check updated field
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.totp_secret_encrypted is not None
    
    def test_ensure_totp_secret_existing_user(self, app, test_admin_user):
        """Test ensuring TOTP secret for user with existing secret."""
        with app.app_context():
            # Get fresh instance and set up existing secret
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            original_secret = 'JBSWY3DPEHPK3PXP'
            user.totp_secret_encrypted = encrypt_bytes(original_secret.encode())
            from app.extensions import db
            db.session.commit()
            
            # Get fresh instance again for the service call
            user = get_user_by_hex_id(test_admin_user.hex_id)
            secret, uri = ensure_totp_secret(user)
            
            assert secret == original_secret
            assert uri.startswith('otpauth://totp/')
    
    @patch('pyotp.TOTP.verify')
    def test_verify_totp_code_success(self, mock_verify, app, test_admin_user):
        """Test successful TOTP code verification."""
        with app.app_context():
            # Set up TOTP secret
            test_admin_user.totp_secret_encrypted = encrypt_bytes('JBSWY3DPEHPK3PXP'.encode())
            from app.extensions import db
            db.session.commit()
            
            mock_verify.return_value = True
            
            result = verify_totp_code(test_admin_user, '123456')
            assert result is True
            mock_verify.assert_called_once_with('123456', valid_window=1)
    
    @patch('pyotp.TOTP.verify')
    def test_verify_totp_code_failure(self, mock_verify, app, test_admin_user):
        """Test failed TOTP code verification."""
        with app.app_context():
            # Set up TOTP secret
            test_admin_user.totp_secret_encrypted = encrypt_bytes('JBSWY3DPEHPK3PXP'.encode())
            from app.extensions import db
            db.session.commit()
            
            mock_verify.return_value = False
            
            result = verify_totp_code(test_admin_user, '123456')
            assert result is False
    
    def test_verify_totp_code_no_secret(self, app, test_admin_user):
        """Test TOTP verification without secret."""
        with app.app_context():
            result = verify_totp_code(test_admin_user, '123456')
            assert result is False
    
    def test_verify_totp_code_invalid_format(self, app, test_admin_user):
        """Test TOTP verification with invalid code format."""
        with app.app_context():
            # Set up TOTP secret
            test_admin_user.totp_secret_encrypted = encrypt_bytes('JBSWY3DPEHPK3PXP'.encode())
            from app.extensions import db
            db.session.commit()
            
            # Test various invalid formats
            invalid_codes = ['', '12345', 'abcdef', '123 456 789', None]
            
            for code in invalid_codes:
                result = verify_totp_code(test_admin_user, code)
                assert result is False
    
    def test_verify_totp_code_normalization(self, app, test_admin_user):
        """Test TOTP code normalization (spaces removed)."""
        with app.app_context():
            # Set up TOTP secret
            test_admin_user.totp_secret_encrypted = encrypt_bytes('JBSWY3DPEHPK3PXP'.encode())
            from app.extensions import db
            db.session.commit()
            
            with patch('pyotp.TOTP.verify') as mock_verify:
                mock_verify.return_value = True
                
                # Code with spaces should be normalized
                result = verify_totp_code(test_admin_user, ' 123 456 ')
                assert result is True
                mock_verify.assert_called_once_with('123456', valid_window=1)
    
    def test_generate_backup_codes(self):
        """Test backup code generation."""
        codes = generate_backup_codes()
        
        assert len(codes) == 8  # Default number
        assert all(len(code) == 8 for code in codes)  # 8 hex chars
        assert len(set(codes)) == 8  # All unique
        
        # Test custom number
        codes = generate_backup_codes(5)
        assert len(codes) == 5
    
    def test_set_backup_codes(self, app, test_admin_user):
        """Test setting backup codes for user."""
        with app.app_context():
            # Get fresh instance to avoid session conflicts
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            codes = ['code1', 'code2', 'code3']
            set_backup_codes(user, codes)
            
            # Refresh user to check updated field
            user = get_user_by_hex_id(test_admin_user.hex_id)
            assert user.backup_codes_hash is not None
            # Should be JSON array of hashed codes
            import json
            hashed_codes = json.loads(user.backup_codes_hash)
            assert len(hashed_codes) == 3
    
    def test_consume_backup_code_success(self, app, test_admin_user):
        """Test successful backup code consumption."""
        with app.app_context():
            # Get fresh instance and set backup codes
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            codes = ['code1', 'code2', 'code3']
            set_backup_codes(user, codes)
            
            # Get fresh instance for consumption
            user = get_user_by_hex_id(test_admin_user.hex_id)
            result = consume_backup_code(user, 'code2')
            assert result is True
            
            # Code should be removed from list
            import json
            user = get_user_by_hex_id(test_admin_user.hex_id)
            remaining_codes = json.loads(user.backup_codes_hash)
            assert len(remaining_codes) == 2
            
            # Same code should not work again
            user = get_user_by_hex_id(test_admin_user.hex_id)
            result = consume_backup_code(user, 'code2')
            assert result is False
    
    def test_consume_backup_code_invalid(self, app, test_admin_user):
        """Test consuming invalid backup code."""
        with app.app_context():
            # Get fresh instance and set backup codes
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            
            codes = ['code1', 'code2', 'code3']
            set_backup_codes(user, codes)
            
            # Get fresh instance and try invalid code
            user = get_user_by_hex_id(test_admin_user.hex_id)
            result = consume_backup_code(user, 'invalid')
            assert result is False
            
            # All codes should still be there
            import json
            user = get_user_by_hex_id(test_admin_user.hex_id)
            remaining_codes = json.loads(user.backup_codes_hash)
            assert len(remaining_codes) == 3
    
    def test_consume_backup_code_no_codes(self, app, test_admin_user):
        """Test consuming backup code when user has no codes."""
        with app.app_context():
            # Get fresh instance
            from app.repositories.user import get_user_by_hex_id
            user = get_user_by_hex_id(test_admin_user.hex_id)
            result = consume_backup_code(user, 'code1')
            assert result is False
