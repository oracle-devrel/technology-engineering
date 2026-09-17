"""Service for interacting with OCI Object Storage buckets."""

import asyncio
import logging
import threading
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class OCIObjectStorageError(Exception):
    """Exception raised for OCI Object Storage errors."""

    pass


class OCIObjectStorageService:
    """Service for listing and downloading objects from OCI Object Storage."""

    def __init__(self) -> None:
        self._client = None
        self._lock = threading.Lock()

    async def _run(self, function, *args, **kwargs):
        def call():
            with self._lock:
                return function(*args, **kwargs)

        return await asyncio.to_thread(call)

    async def test_connection(self, **kwargs):
        return await self._run(self._test_connection, **kwargs)

    async def list_objects(self, **kwargs):
        return await self._run(self._list_objects, **kwargs)

    async def download_object(self, **kwargs):
        return await self._run(self._download_object, **kwargs)

    async def upload_object(self, **kwargs):
        return await self._run(self._upload_object, **kwargs)

    def _get_client(self):
        """Lazily initialize the OCI Object Storage client."""
        if self._client is not None:
            return self._client

        try:
            import oci

            config_file = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
            profile = os.getenv("OCI_PROFILE", "DEFAULT")

            # Try config file auth first, fall back to instance principal
            try:
                config = oci.config.from_file(config_file, profile)
                self._client = oci.object_storage.ObjectStorageClient(config)
                logger.info("OCI client initialized with config file auth")
            except Exception:
                logger.info("Config file auth failed, trying instance principal")
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                self._client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
                logger.info("OCI client initialized with instance principal auth")

            return self._client

        except ImportError:
            raise OCIObjectStorageError("OCI SDK not installed. Install with: pip install oci")
        except Exception as e:
            raise OCIObjectStorageError(f"Failed to initialize OCI client: {e}")

    def _test_connection(
        self, namespace: str, bucket_name: str, compartment_id: str, region: str
    ) -> dict:
        """Test connectivity to an OCI Object Storage bucket.

        Returns:
            Dict with connection status and bucket info.
        """
        try:
            client = self._get_client()
            client.base_client.set_region(region)

            bucket = client.get_bucket(namespace, bucket_name).data
            return {
                "status": "connected",
                "bucket_name": bucket.name,
                "compartment_id": bucket.compartment_id,
                "created_by": bucket.created_by,
                "time_created": str(bucket.time_created),
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _list_objects(
        self,
        namespace: str,
        bucket_name: str,
        region: str,
        prefix: str | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        """List objects in a bucket.

        Returns:
            List of dicts with name, size, time_created, md5 keys.
        """
        try:
            client = self._get_client()
            client.base_client.set_region(region)

            kwargs = {
                "namespace_name": namespace,
                "bucket_name": bucket_name,
                "limit": limit,
                "fields": "name,size,timeCreated,md5",
            }
            if prefix:
                kwargs["prefix"] = prefix

            objects = []
            while True:
                response = client.list_objects(**kwargs)
                for obj in response.data.objects:
                    objects.append(
                        {
                            "name": obj.name,
                            "size": obj.size,
                            "time_created": str(obj.time_created) if obj.time_created else None,
                            "md5": obj.md5,
                        }
                    )
                next_start = response.data.next_start_with
                if not next_start:
                    break
                kwargs["start"] = next_start

            return objects

        except Exception as e:
            logger.error(f"Failed to list objects: {e}")
            raise OCIObjectStorageError(f"Failed to list objects: {e}")

    def _download_object(
        self,
        namespace: str,
        bucket_name: str,
        object_name: str,
        region: str,
        dest_dir: str | None = None,
    ) -> Path:
        """Download an object from a bucket to a local file.

        Args:
            namespace: OCI namespace.
            bucket_name: Bucket name.
            object_name: Object key/name.
            region: OCI region.
            dest_dir: Optional destination directory. Uses temp dir if not specified.

        Returns:
            Path to the downloaded file.
        """
        try:
            client = self._get_client()
            client.base_client.set_region(region)

            response = client.get_object(namespace, bucket_name, object_name)

            if dest_dir:
                dest_path = Path(dest_dir)
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                dest_path = Path(tempfile.mkdtemp())

            # Use just the filename part of the object name
            file_name = Path(object_name).name
            file_path = dest_path / file_name

            with open(file_path, "wb") as f:
                for chunk in response.data.raw.stream(1024 * 1024):
                    f.write(chunk)

            logger.info(f"Downloaded {object_name} to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to download {object_name}: {e}")
            raise OCIObjectStorageError(f"Failed to download {object_name}: {e}")

    def _upload_object(
        self,
        namespace: str,
        bucket_name: str,
        object_name: str,
        data: bytes | str,
        region: str,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload an object to an OCI Object Storage bucket.

        Args:
            namespace: OCI namespace.
            bucket_name: Bucket name.
            object_name: Object key/name to store as.
            data: The file content as bytes or a UTF-8 string.
            region: OCI region.
            content_type: MIME type of the object (default application/octet-stream).

        Returns:
            Dict with status, object_name, bucket_name, and namespace.
        """
        try:
            client = self._get_client()
            client.base_client.set_region(region)

            # Convert string data to bytes if needed
            if isinstance(data, str):
                data = data.encode("utf-8")

            client.put_object(namespace, bucket_name, object_name, data, content_type=content_type)

            logger.info(f"Uploaded {object_name} to {bucket_name}/{namespace}")
            return {
                "status": "uploaded",
                "object_name": object_name,
                "bucket_name": bucket_name,
                "namespace": namespace,
            }

        except Exception as e:
            logger.error(f"Failed to upload {object_name}: {e}")
            raise OCIObjectStorageError(f"Failed to upload {object_name}: {e}")
