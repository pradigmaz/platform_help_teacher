"""
AES-256-GCM encryption for backup files.

Format v3 (portable, current):
[magic:3][version:1][key_fingerprint:8]
[master_salt:16][master_nonce:12][wrapped_data_key_by_master:48]
[recovery_salt:16][recovery_nonce:12][wrapped_data_key_by_recovery:48]
[payload_base_nonce:8]
[chunk1][chunk2]...[chunkN]

Format v2 (portable, legacy header without magic):
[version:1]
[master_salt:16][master_nonce:12][wrapped_data_key_by_master:48]
[recovery_salt:16][recovery_nonce:12][wrapped_data_key_by_recovery:48]
[payload_base_nonce:8]
[chunk1][chunk2]...[chunkN]

Format v1 (legacy current):
[version:1][salt:16][payload_base_nonce:8][chunk1][chunk2]...[chunkN]

Format v0 (legacy oldest):
[salt:16][nonce:12][ciphertext][tag:16]
"""

import hashlib
import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Format constants
BACKUP_FILE_MAGIC = b"BKP"
MAGIC_SIZE = len(BACKUP_FILE_MAGIC)
FORMAT_VERSION_V1 = 1
FORMAT_VERSION_V2 = 2
FORMAT_VERSION_V3 = 3
CURRENT_FORMAT_VERSION = FORMAT_VERSION_V3
VERSION_SIZE = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256 bits
TAG_SIZE = 16
ITERATIONS = 480000  # OWASP recommendation for PBKDF2-SHA256

# Streaming: 1MB chunks (balance between memory and performance)
CHUNK_SIZE = 1024 * 1024

PAYLOAD_BASE_NONCE_SIZE = 8
WRAPPED_KEY_SIZE = KEY_SIZE + TAG_SIZE
KEY_FINGERPRINT_SIZE = 8

# Header sizes
HEADER_SIZE_V1 = VERSION_SIZE + SALT_SIZE + PAYLOAD_BASE_NONCE_SIZE
HEADER_SIZE_V2 = (
    VERSION_SIZE
    + SALT_SIZE
    + NONCE_SIZE
    + WRAPPED_KEY_SIZE
    + SALT_SIZE
    + NONCE_SIZE
    + WRAPPED_KEY_SIZE
    + PAYLOAD_BASE_NONCE_SIZE
)
HEADER_SIZE_V3 = (
    MAGIC_SIZE
    + VERSION_SIZE
    + KEY_FINGERPRINT_SIZE
    + SALT_SIZE
    + NONCE_SIZE
    + WRAPPED_KEY_SIZE
    + SALT_SIZE
    + NONCE_SIZE
    + WRAPPED_KEY_SIZE
    + PAYLOAD_BASE_NONCE_SIZE
)
LEGACY_MIN_SIZE = SALT_SIZE + NONCE_SIZE + TAG_SIZE


@dataclass(frozen=True)
class BackupFileInfo:
    """Static metadata that can be read from backup file headers."""

    format_version: int
    portable: bool
    key_fingerprint: str | None = None
    trusted_header: bool = False


class RecoveryCodeRequiredError(Exception):
    """Raised when portable backup requires recovery code on a different machine."""


class InvalidRecoveryCodeError(Exception):
    """Raised when provided recovery code cannot decrypt portable backup key."""


def _normalize_recovery_code(recovery_code: str) -> str:
    normalized = "".join(ch for ch in recovery_code.lower() if ch.isalnum())
    if len(normalized) < 16:
        raise ValueError("Recovery code is too short")
    return normalized


def generate_recovery_code() -> str:
    token = os.urandom(16).hex()
    return "-".join(token[i : i + 4] for i in range(0, len(token), 4))


def _fingerprint_secret(secret: bytes) -> bytes:
    return hashlib.sha256(secret).digest()[:KEY_FINGERPRINT_SIZE]


class BackupEncryption:
    """
    AES-256-GCM encryption with PBKDF2 key derivation.

    Supports:
    - Format versioning for future algorithm changes
    - Chunked encryption for large files (streaming)
    - Key rotation diagnostics via stored key fingerprint
    """

    def __init__(self, master_key: str, key_id: str = "default"):
        """
        Initialize with master key from config.

        Args:
            master_key: At least 32 character encryption key
            key_id: Identifier for key rotation (stored in logs, not in file)
        """
        if len(master_key) < 32:
            raise ValueError("Master key must be at least 32 characters")
        self._master_key = master_key.encode()
        self._key_id = key_id
        self._key_fingerprint_bytes = _fingerprint_secret(self._master_key)
        self._key_fingerprint = self._key_fingerprint_bytes.hex()

    @property
    def key_id(self) -> str:
        """Get current key identifier for audit logging."""
        return self._key_id

    @property
    def key_fingerprint(self) -> str:
        """Stable fingerprint of the current master key."""
        return self._key_fingerprint

    @property
    def current_format_version(self) -> int:
        """Current encryption format version for newly created backups."""
        return CURRENT_FORMAT_VERSION

    def _derive_key_from_secret(self, secret: bytes, salt: bytes) -> bytes:
        """Derive encryption key from an arbitrary secret using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
        )
        return kdf.derive(secret)

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key using PBKDF2."""
        return self._derive_key_from_secret(self._master_key, salt)

    def _derive_recovery_key(self, recovery_code: str, salt: bytes) -> bytes:
        """Derive wrapping key from operator-managed recovery code."""
        normalized = _normalize_recovery_code(recovery_code)
        return self._derive_key_from_secret(normalized.encode(), salt)

    def encrypt_file(self, input_path: Path, output_path: Path) -> str:
        """
        Encrypt file using portable v3 format with chunked payload encryption.

        Returns:
            Recovery code that can decrypt this backup on another machine.
        """
        recovery_code = generate_recovery_code()
        payload_key = AESGCM.generate_key(bit_length=KEY_SIZE * 8)
        master_salt = os.urandom(SALT_SIZE)
        master_nonce = os.urandom(NONCE_SIZE)
        recovery_salt = os.urandom(SALT_SIZE)
        recovery_nonce = os.urandom(NONCE_SIZE)
        payload_base_nonce = os.urandom(PAYLOAD_BASE_NONCE_SIZE)

        master_wrap_key = self._derive_key(master_salt)
        recovery_wrap_key = self._derive_recovery_key(recovery_code, recovery_salt)
        wrapped_payload_key_by_master = AESGCM(master_wrap_key).encrypt(master_nonce, payload_key, None)
        wrapped_payload_key_by_recovery = AESGCM(recovery_wrap_key).encrypt(recovery_nonce, payload_key, None)

        file_size = input_path.stat().st_size

        with open(output_path, "wb") as out_f:
            out_f.write(BACKUP_FILE_MAGIC)
            out_f.write(struct.pack("B", CURRENT_FORMAT_VERSION))
            out_f.write(self._key_fingerprint_bytes)
            out_f.write(master_salt)
            out_f.write(master_nonce)
            out_f.write(wrapped_payload_key_by_master)
            out_f.write(recovery_salt)
            out_f.write(recovery_nonce)
            out_f.write(wrapped_payload_key_by_recovery)
            out_f.write(payload_base_nonce)

            with open(input_path, "rb") as in_f:
                chunk_num = 0
                while True:
                    chunk = in_f.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    chunk_nonce = payload_base_nonce + struct.pack(">I", chunk_num)
                    ciphertext = AESGCM(payload_key).encrypt(chunk_nonce, chunk, None)
                    out_f.write(ciphertext)
                    chunk_num += 1

        logger.info(
            "Encrypted %s -> %s (%s bytes, %s chunks, key_id=%s, format=v%s)",
            input_path.name,
            output_path.name,
            file_size,
            chunk_num,
            self._key_id,
            CURRENT_FORMAT_VERSION,
        )
        return recovery_code

    def inspect_file(self, encrypted_path: Path) -> BackupFileInfo:
        """Inspect backup header without decrypting payload."""
        with open(encrypted_path, "rb") as in_f:
            prefix = in_f.read(MAGIC_SIZE)
            if prefix == BACKUP_FILE_MAGIC:
                version_raw = in_f.read(VERSION_SIZE)
                if len(version_raw) != VERSION_SIZE:
                    raise ValueError("Backup header is truncated")
                version = struct.unpack("B", version_raw)[0]
                if version != FORMAT_VERSION_V3:
                    raise ValueError(f"Unsupported backup format version: {version}")
                fingerprint = in_f.read(KEY_FINGERPRINT_SIZE)
                if len(fingerprint) != KEY_FINGERPRINT_SIZE:
                    raise ValueError("Backup fingerprint header is truncated")
                return BackupFileInfo(
                    format_version=version,
                    portable=True,
                    key_fingerprint=fingerprint.hex(),
                    trusted_header=True,
                )

            if len(prefix) < MAGIC_SIZE:
                raise ValueError("Backup header is truncated")

            first_byte = prefix[0]
            if first_byte == FORMAT_VERSION_V2:
                return BackupFileInfo(format_version=FORMAT_VERSION_V2, portable=True)
            if first_byte == FORMAT_VERSION_V1:
                return BackupFileInfo(format_version=FORMAT_VERSION_V1, portable=False)
            return BackupFileInfo(format_version=0, portable=False)

    def decrypt_file(self, input_path: Path, output_path: Path, recovery_code: str | None = None) -> None:
        """
        Decrypt AES-256-GCM encrypted file with chunked processing.

        Raises:
            ValueError: If format version is unsupported
            InvalidTag: If tampered or wrong key
        """
        with open(input_path, "rb") as in_f:
            prefix = in_f.read(MAGIC_SIZE)

            if prefix == BACKUP_FILE_MAGIC:
                version_raw = in_f.read(VERSION_SIZE)
                if len(version_raw) != VERSION_SIZE:
                    raise ValueError("Backup header is truncated")
                version = struct.unpack("B", version_raw)[0]
                if version != FORMAT_VERSION_V3:
                    raise ValueError(f"Unsupported backup format version: {version}")
                fingerprint = in_f.read(KEY_FINGERPRINT_SIZE)
                if len(fingerprint) != KEY_FINGERPRINT_SIZE:
                    raise ValueError("Backup fingerprint header is truncated")
                self._decrypt_portable(
                    file_handle=in_f, output_path=output_path, recovery_code=recovery_code, version=version
                )
                return

            if not prefix:
                raise ValueError("Backup file is empty")

            in_f.seek(0)
            version = struct.unpack("B", in_f.read(VERSION_SIZE))[0]

            if version == FORMAT_VERSION_V1:
                self._decrypt_with_legacy_fallback(in_f, output_path, lambda: self._decrypt_v1(in_f, output_path))
                return

            if version == FORMAT_VERSION_V2:
                self._decrypt_with_legacy_fallback(
                    in_f,
                    output_path,
                    lambda: self._decrypt_portable(in_f, output_path, recovery_code, version),
                )
                return

            in_f.seek(0)
            self._decrypt_legacy(in_f, output_path)

    def _decrypt_with_legacy_fallback(self, file_handle, output_path: Path, decrypt_candidate) -> None:
        candidate_error: Exception | None = None
        try:
            decrypt_candidate()
            return
        except (InvalidTag, InvalidRecoveryCodeError, RecoveryCodeRequiredError, ValueError, struct.error) as exc:
            candidate_error = exc

        file_handle.seek(0)
        try:
            self._decrypt_legacy(file_handle, output_path)
        except Exception:
            if candidate_error is not None:
                raise candidate_error
            raise

    def _decrypt_chunks(self, file_handle, output_path: Path, payload_key: bytes, payload_base_nonce: bytes) -> None:
        aesgcm = AESGCM(payload_key)

        with open(output_path, "wb") as out_f:
            chunk_num = 0
            encrypted_chunk_size = CHUNK_SIZE + TAG_SIZE

            while True:
                chunk_ciphertext = file_handle.read(encrypted_chunk_size)
                if not chunk_ciphertext:
                    break

                chunk_nonce = payload_base_nonce + struct.pack(">I", chunk_num)
                plaintext = aesgcm.decrypt(chunk_nonce, chunk_ciphertext, None)
                out_f.write(plaintext)
                chunk_num += 1

    def _decrypt_v1(self, file_handle, output_path: Path) -> None:
        salt = file_handle.read(SALT_SIZE)
        payload_base_nonce = file_handle.read(PAYLOAD_BASE_NONCE_SIZE)
        if len(salt) != SALT_SIZE or len(payload_base_nonce) != PAYLOAD_BASE_NONCE_SIZE:
            raise ValueError("Backup header is truncated")
        key = self._derive_key(salt)
        self._decrypt_chunks(file_handle, output_path, key, payload_base_nonce)
        logger.info("Decrypted v1 backup")

    def _decrypt_portable(
        self,
        file_handle,
        output_path: Path,
        recovery_code: str | None = None,
        version: int = FORMAT_VERSION_V2,
    ) -> None:
        master_salt = file_handle.read(SALT_SIZE)
        master_nonce = file_handle.read(NONCE_SIZE)
        wrapped_payload_key_by_master = file_handle.read(WRAPPED_KEY_SIZE)
        recovery_salt = file_handle.read(SALT_SIZE)
        recovery_nonce = file_handle.read(NONCE_SIZE)
        wrapped_payload_key_by_recovery = file_handle.read(WRAPPED_KEY_SIZE)
        payload_base_nonce = file_handle.read(PAYLOAD_BASE_NONCE_SIZE)

        header_fields = (
            master_salt,
            master_nonce,
            wrapped_payload_key_by_master,
            recovery_salt,
            recovery_nonce,
            wrapped_payload_key_by_recovery,
            payload_base_nonce,
        )
        if any(not field for field in header_fields) or len(payload_base_nonce) != PAYLOAD_BASE_NONCE_SIZE:
            raise ValueError("Backup header is truncated")

        try:
            master_wrap_key = self._derive_key(master_salt)
            payload_key = AESGCM(master_wrap_key).decrypt(master_nonce, wrapped_payload_key_by_master, None)
        except InvalidTag as master_exc:
            if not recovery_code:
                raise RecoveryCodeRequiredError(
                    "This portable backup was created on a different machine. Provide recovery code to restore it."
                ) from master_exc

            try:
                recovery_wrap_key = self._derive_recovery_key(recovery_code, recovery_salt)
                payload_key = AESGCM(recovery_wrap_key).decrypt(
                    recovery_nonce,
                    wrapped_payload_key_by_recovery,
                    None,
                )
            except (InvalidTag, ValueError) as recovery_exc:
                raise InvalidRecoveryCodeError("Recovery code is invalid or backup is corrupted") from recovery_exc

        self._decrypt_chunks(file_handle, output_path, payload_key, payload_base_nonce)
        logger.info("Decrypted portable v%s backup", version)

    def _decrypt_legacy(self, file_handle, output_path: Path) -> None:
        """
        Decrypt legacy format (v0): [salt:16][nonce:12][ciphertext][tag:16]
        For backward compatibility with existing backups.
        """
        salt = file_handle.read(SALT_SIZE)
        nonce = file_handle.read(NONCE_SIZE)
        ciphertext = file_handle.read()

        if len(salt) != SALT_SIZE or len(nonce) != NONCE_SIZE or len(ciphertext) < TAG_SIZE:
            raise ValueError("Legacy backup header is truncated")

        key = self._derive_key(salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        output_path.write_bytes(plaintext)

        logger.info("Decrypted legacy format -> %s", output_path.name)

    def verify_file(self, encrypted_path: Path) -> bool:
        """Verify encrypted file header integrity."""
        try:
            info = self.inspect_file(encrypted_path)
            size = encrypted_path.stat().st_size

            if info.format_version == FORMAT_VERSION_V3:
                return size >= HEADER_SIZE_V3 + TAG_SIZE
            if info.format_version == FORMAT_VERSION_V2:
                return size >= HEADER_SIZE_V2 + TAG_SIZE or size >= LEGACY_MIN_SIZE
            if info.format_version == FORMAT_VERSION_V1:
                return size >= HEADER_SIZE_V1 + TAG_SIZE or size >= LEGACY_MIN_SIZE
            return size >= LEGACY_MIN_SIZE
        except Exception as exc:
            logger.error("Verification failed: %s", exc)
            return False

    def get_file_version(self, encrypted_path: Path) -> int:
        """Get encryption format version of a file."""
        return self.inspect_file(encrypted_path).format_version
