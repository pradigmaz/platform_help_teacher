"""
AES-256-GCM encryption for backup files.
Uses cryptography library (already in deps via PyJWT[crypto]).

Format v1: [version:1][salt:16][nonce:12][ciphertext][tag:16]
- version: Format version byte for future compatibility
- Supports chunked encryption for large files (streaming)
- Key rotation via key_id in metadata
"""
import os
import logging
import struct
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

# Format constants
FORMAT_VERSION = 1
VERSION_SIZE = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256 bits
TAG_SIZE = 16
ITERATIONS = 480000  # OWASP recommendation for PBKDF2-SHA256

# Streaming: 1MB chunks (balance between memory and performance)
CHUNK_SIZE = 1024 * 1024

# Header size for v1 format
HEADER_SIZE = VERSION_SIZE + SALT_SIZE + NONCE_SIZE


class BackupEncryption:
    """
    AES-256-GCM encryption with PBKDF2 key derivation.
    
    Supports:
    - Format versioning for future algorithm changes
    - Chunked encryption for large files (streaming)
    - Key rotation via multiple keys
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
    
    @property
    def key_id(self) -> str:
        """Get current key identifier for audit logging."""
        return self._key_id
    
    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
        )
        return kdf.derive(self._master_key)
    
    def encrypt_file(self, input_path: Path, output_path: Path) -> None:
        """
        Encrypt file using AES-256-GCM with chunked processing.
        
        Format v1: [version:1][salt:16][nonce:12][chunk1][chunk2]...[chunkN]
        Each chunk: [chunk_ciphertext][tag:16]
        
        For files < CHUNK_SIZE, behaves like single-chunk encryption.
        For larger files, processes in CHUNK_SIZE chunks to avoid OOM.
        """
        salt = os.urandom(SALT_SIZE)
        key = self._derive_key(salt)
        
        file_size = input_path.stat().st_size
        
        with open(output_path, 'wb') as out_f:
            # Write header
            out_f.write(struct.pack('B', FORMAT_VERSION))
            out_f.write(salt)
            
            with open(input_path, 'rb') as in_f:
                chunk_num = 0
                while True:
                    chunk = in_f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Unique nonce per chunk: base_nonce + chunk_number
                    # Using 8 bytes random + 4 bytes counter
                    if chunk_num == 0:
                        base_nonce = os.urandom(8)
                        out_f.write(base_nonce)  # Store base nonce in header
                    
                    # Construct chunk nonce: base_nonce (8) + chunk_num (4)
                    chunk_nonce = base_nonce + struct.pack('>I', chunk_num)
                    
                    aesgcm = AESGCM(key)
                    ciphertext = aesgcm.encrypt(chunk_nonce, chunk, None)
                    out_f.write(ciphertext)
                    
                    chunk_num += 1
        
        logger.info(
            f"Encrypted {input_path.name} -> {output_path.name} "
            f"({file_size} bytes, {chunk_num} chunks, key_id={self._key_id})"
        )
    
    def decrypt_file(self, input_path: Path, output_path: Path) -> None:
        """
        Decrypt AES-256-GCM encrypted file with chunked processing.
        
        Raises:
            ValueError: If format version is unsupported
            InvalidTag: If tampered or wrong key
        """
        with open(input_path, 'rb') as in_f:
            # Read header
            version = struct.unpack('B', in_f.read(VERSION_SIZE))[0]
            
            if version != FORMAT_VERSION:
                # Try legacy format (no version byte)
                if version in range(SALT_SIZE):  # Likely old format salt byte
                    in_f.seek(0)
                    self._decrypt_legacy(in_f, output_path)
                    return
                raise ValueError(f"Unsupported encryption format version: {version}")
            
            salt = in_f.read(SALT_SIZE)
            base_nonce = in_f.read(8)  # Only 8 bytes, rest is counter
            
            key = self._derive_key(salt)
            aesgcm = AESGCM(key)
            
            with open(output_path, 'wb') as out_f:
                chunk_num = 0
                remaining = in_f.read()
                pos = 0
                
                while pos < len(remaining):
                    # Each chunk is CHUNK_SIZE + TAG_SIZE (except possibly last)
                    chunk_ciphertext_size = min(
                        CHUNK_SIZE + TAG_SIZE, 
                        len(remaining) - pos
                    )
                    chunk_ciphertext = remaining[pos:pos + chunk_ciphertext_size]
                    
                    chunk_nonce = base_nonce + struct.pack('>I', chunk_num)
                    plaintext = aesgcm.decrypt(chunk_nonce, chunk_ciphertext, None)
                    out_f.write(plaintext)
                    
                    pos += chunk_ciphertext_size
                    chunk_num += 1
        
        logger.info(f"Decrypted {input_path.name} -> {output_path.name}")
    
    def _decrypt_legacy(self, file_handle, output_path: Path) -> None:
        """
        Decrypt legacy format (v0): [salt:16][nonce:12][ciphertext][tag:16]
        For backward compatibility with existing backups.
        """
        salt = file_handle.read(SALT_SIZE)
        nonce = file_handle.read(NONCE_SIZE)
        ciphertext = file_handle.read()
        
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        output_path.write_bytes(plaintext)
        
        logger.info(f"Decrypted legacy format -> {output_path.name}")
    
    def verify_file(self, encrypted_path: Path) -> bool:
        """Verify encrypted file header integrity."""
        try:
            with open(encrypted_path, 'rb') as f:
                version = struct.unpack('B', f.read(VERSION_SIZE))[0]
                
                if version == FORMAT_VERSION:
                    salt = f.read(SALT_SIZE)
                    base_nonce = f.read(8)
                    if len(salt) != SALT_SIZE or len(base_nonce) != 8:
                        return False
                else:
                    # Legacy format check
                    f.seek(0)
                    salt = f.read(SALT_SIZE)
                    nonce = f.read(NONCE_SIZE)
                    if len(salt) != SALT_SIZE or len(nonce) != NONCE_SIZE:
                        return False
                
                # Check minimum size
                f.seek(0, 2)
                size = f.tell()
                min_size = VERSION_SIZE + SALT_SIZE + 8 + TAG_SIZE
                if size < min_size:
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def get_file_version(self, encrypted_path: Path) -> int:
        """Get encryption format version of a file."""
        with open(encrypted_path, 'rb') as f:
            version = struct.unpack('B', f.read(VERSION_SIZE))[0]
            if version == FORMAT_VERSION:
                return version
            return 0  # Legacy format
