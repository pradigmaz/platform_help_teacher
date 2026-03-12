"""
Tests for backup encryption module.
"""

import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.backup.encryption import (
    BackupEncryption,
    InvalidRecoveryCodeError,
    RecoveryCodeRequiredError,
)


class TestBackupEncryption:
    """Test AES-256-GCM encryption."""

    @pytest.fixture
    def encryption(self):
        """Create encryption instance with test key."""
        return BackupEncryption("test_master_key_32_chars_minimum!")

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_encrypt_decrypt_roundtrip(self, encryption, temp_dir):
        """Test that encrypt -> decrypt returns original data."""
        # Create test file
        original_data = b"Hello, this is test data for encryption!"
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"
        decrypted_file = temp_dir / "decrypted.txt"

        input_file.write_bytes(original_data)

        # Encrypt
        encryption.encrypt_file(input_file, encrypted_file)
        assert encrypted_file.exists()
        assert encrypted_file.read_bytes() != original_data

        # Decrypt
        encryption.decrypt_file(encrypted_file, decrypted_file)
        assert decrypted_file.exists()
        assert decrypted_file.read_bytes() == original_data
        file_info = encryption.inspect_file(encrypted_file)
        assert encryption.get_file_version(encrypted_file) == 3
        assert file_info.format_version == 3
        assert file_info.portable is True
        assert file_info.key_fingerprint == encryption.key_fingerprint
        assert file_info.trusted_header is True

    def test_encrypted_file_is_different(self, encryption, temp_dir):
        """Test that encrypted content differs from original."""
        original_data = b"Secret data that should be encrypted"
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"

        input_file.write_bytes(original_data)
        encryption.encrypt_file(input_file, encrypted_file)

        encrypted_data = encrypted_file.read_bytes()
        assert original_data not in encrypted_data

    def test_different_machine_requires_recovery_code_for_portable_backup(self, temp_dir):
        """Portable backups require recovery code when master key changes."""
        original_data = b"Data encrypted with one key"
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"
        decrypted_file = temp_dir / "decrypted.txt"

        input_file.write_bytes(original_data)

        # Encrypt with key 1
        enc1 = BackupEncryption("first_key_32_characters_minimum!")
        enc1.encrypt_file(input_file, encrypted_file)

        # Try decrypt with a different machine key and no recovery code
        enc2 = BackupEncryption("second_key_32_characters_minimum")
        with pytest.raises(RecoveryCodeRequiredError):
            enc2.decrypt_file(encrypted_file, decrypted_file)

    def test_recovery_code_restores_portable_backup_on_different_machine(self, temp_dir):
        """Portable backups can be restored on another machine with recovery code."""
        original_data = b"Portable restore payload"
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"
        decrypted_file = temp_dir / "decrypted.txt"

        input_file.write_bytes(original_data)

        enc1 = BackupEncryption("first_key_32_characters_minimum!")
        recovery_code = enc1.encrypt_file(input_file, encrypted_file)

        enc2 = BackupEncryption("second_key_32_characters_minimum")
        enc2.decrypt_file(encrypted_file, decrypted_file, recovery_code)

        assert decrypted_file.read_bytes() == original_data

    def test_wrong_recovery_code_fails_portable_decryption(self, temp_dir):
        """Portable backups reject an incorrect recovery code."""
        original_data = b"Portable restore payload"
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"
        decrypted_file = temp_dir / "decrypted.txt"

        input_file.write_bytes(original_data)

        enc1 = BackupEncryption("first_key_32_characters_minimum!")
        enc1.encrypt_file(input_file, encrypted_file)

        enc2 = BackupEncryption("second_key_32_characters_minimum")
        with pytest.raises(InvalidRecoveryCodeError):
            enc2.decrypt_file(encrypted_file, decrypted_file, "dead-beef-dead-beef")

    def test_verify_valid_file(self, encryption, temp_dir):
        """Test verification of valid encrypted file."""
        input_file = temp_dir / "original.txt"
        encrypted_file = temp_dir / "encrypted.enc"

        input_file.write_bytes(b"Test data")
        encryption.encrypt_file(input_file, encrypted_file)

        assert encryption.verify_file(encrypted_file) is True

    def test_verify_invalid_file(self, encryption, temp_dir):
        """Test verification of invalid file."""
        invalid_file = temp_dir / "invalid.enc"
        invalid_file.write_bytes(b"not encrypted data")

        assert encryption.verify_file(invalid_file) is False

    def test_verify_nonexistent_file(self, encryption, temp_dir):
        """Test verification of nonexistent file."""
        nonexistent = temp_dir / "nonexistent.enc"
        assert encryption.verify_file(nonexistent) is False

    def test_decrypt_legacy_format_fallback(self, encryption, temp_dir):
        """Test that decrypt_file detects and decrypts legacy v0 files."""
        original_data = b"legacy backup payload"
        legacy_file = temp_dir / "legacy.enc"
        decrypted_file = temp_dir / "legacy.txt"

        salt = b"\x0f1234567890abcde"
        nonce = b"legacy_nonce"
        key = encryption._derive_key(salt)
        ciphertext = AESGCM(key).encrypt(nonce, original_data, None)
        legacy_file.write_bytes(salt + nonce + ciphertext)

        encryption.decrypt_file(legacy_file, decrypted_file)

        assert encryption.get_file_version(legacy_file) == 0
        assert encryption.verify_file(legacy_file) is True
        assert decrypted_file.read_bytes() == original_data

    @pytest.mark.parametrize("leading_byte", [1, 2])
    def test_decrypt_legacy_format_with_v1_v2_collision(self, encryption, temp_dir, leading_byte):
        """Legacy backups remain decryptable even when the first byte collides with v1/v2 markers."""
        original_data = b"legacy backup payload with colliding first byte"
        legacy_file = temp_dir / f"legacy_{leading_byte}.enc"
        decrypted_file = temp_dir / f"legacy_{leading_byte}.txt"

        salt = bytes([leading_byte]) + b"1234567890abcde"
        nonce = b"legacy_nonce"
        key = encryption._derive_key(salt)
        ciphertext = AESGCM(key).encrypt(nonce, original_data, None)
        legacy_file.write_bytes(salt + nonce + ciphertext)

        encryption.decrypt_file(legacy_file, decrypted_file)

        assert encryption.verify_file(legacy_file) is True
        assert decrypted_file.read_bytes() == original_data

    def test_short_key_rejected(self):
        """Test that short keys are rejected."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            BackupEncryption("short_key")

    def test_large_file_encryption(self, encryption, temp_dir):
        """Test encryption of larger file (1MB)."""
        large_data = b"x" * (1024 * 1024)  # 1MB
        input_file = temp_dir / "large.bin"
        encrypted_file = temp_dir / "large.enc"
        decrypted_file = temp_dir / "large_dec.bin"

        input_file.write_bytes(large_data)
        encryption.encrypt_file(input_file, encrypted_file)
        encryption.decrypt_file(encrypted_file, decrypted_file)

        assert decrypted_file.read_bytes() == large_data
