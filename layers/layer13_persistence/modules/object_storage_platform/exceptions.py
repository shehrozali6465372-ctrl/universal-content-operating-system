"""Exceptions for object storage platform."""
from __future__ import annotations

class StorageError(Exception): """Base storage error."""
class ConnectionError(StorageError): """Connection failed."""
class UploadError(StorageError): """Upload failed."""
class DownloadError(StorageError): """Download failed."""
class EncryptionError(StorageError): """Encryption failed."""
class CompressionError(StorageError): """Compression failed."""
class IntegrityError(StorageError): """Data integrity error."""
class AccessError(StorageError): """Access denied."""
class QuotaError(StorageError): """Quota exceeded."""
