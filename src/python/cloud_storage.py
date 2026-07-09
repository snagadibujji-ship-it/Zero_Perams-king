#!/usr/bin/env python3
"""
Cloud Storage Connector — Google Drive Integration for Vision Training

Connects to user's Google Drive (up to 5TB) to:
  - Authenticate via OAuth2 or Service Account
  - List/search image files across folders
  - Stream images for training without downloading entire drive
  - Download batches for local training cache
  - Track sync state (what's been processed)

Supports: JPEG, PNG, WEBP, BMP, TIFF, GIF (first frame)
"""
import os
import io
import json
import time
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Google API imports (installed via: pip install google-api-python-client google-auth-oauthlib)
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# ═══ Constants ═══
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
IMAGE_MIMETYPES = {
    'image/jpeg', 'image/png', 'image/webp',
    'image/bmp', 'image/tiff', 'image/gif'
}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif'}

DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'image_cache')
DEFAULT_CREDENTIALS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'credentials')
SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'drive_sync_state.json')

# Max images per batch stream
DEFAULT_BATCH_SIZE = 50
# Max concurrent download threads
MAX_WORKERS = 4


@dataclass
class DriveFile:
    """Represents an image file on Google Drive."""
    id: str
    name: str
    mime_type: str
    size: int  # bytes
    folder_path: str  # reconstructed path
    created_time: str
    modified_time: str
    md5_checksum: str = ""
    thumbnail_link: str = ""
    labels: List[str] = field(default_factory=list)
    processed: bool = False

    @property
    def extension(self) -> str:
        return Path(self.name).suffix.lower()

    @property
    def size_mb(self) -> float:
        return round(self.size / (1024 * 1024), 2)


@dataclass
class SyncState:
    """Tracks what has been indexed/processed from Drive."""
    last_sync: str = ""
    total_files_indexed: int = 0
    total_size_bytes: int = 0
    folders_scanned: List[str] = field(default_factory=list)
    page_token: str = ""  # For resuming large listings
    processed_ids: List[str] = field(default_factory=list)


class GoogleDriveConnector:
    """
    Connects to Google Drive for streaming images to the vision training pipeline.
    
    Usage:
        connector = GoogleDriveConnector()
        connector.authenticate()  # First time: opens browser for OAuth
        
        # List all images
        images = connector.list_images(folder_id="root", recursive=True)
        
        # Stream images for training
        for image_data, metadata in connector.stream_images(batch_size=50):
            train_on_image(image_data, metadata)
        
        # Download specific images to cache
        connector.download_batch(image_ids, cache_dir="./image_cache/")
    """

    def __init__(self, credentials_dir: str = None, cache_dir: str = None):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google API libraries not installed. Run:\n"
                "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2\n"
                "Then run: python src/python/setup_drive.py"
            )
        
        self.credentials_dir = credentials_dir or DEFAULT_CREDENTIALS_DIR
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.creds: Optional[Credentials] = None
        self.service = None
        self.sync_state = self._load_sync_state()
        self._folder_cache: Dict[str, str] = {}  # id -> path mapping
        
        # Ensure directories exist
        os.makedirs(self.credentials_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    # ═══ AUTHENTICATION ═══

    def authenticate(self, method: str = "oauth") -> bool:
        """
        Authenticate with Google Drive.
        
        Args:
            method: "oauth" for user login, "service_account" for server-side
            
        Returns:
            True if authentication successful
        """
        token_path = os.path.join(self.credentials_dir, 'token.json')
        client_secret_path = os.path.join(self.credentials_dir, 'client_secret.json')
        service_account_path = os.path.join(self.credentials_dir, 'service_account.json')

        if method == "service_account":
            return self._auth_service_account(service_account_path)

        # OAuth2 flow
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = None

            if not self.creds:
                if not os.path.exists(client_secret_path):
                    print(f"\n  ERROR: No credentials found at {client_secret_path}")
                    print("  Run: python src/python/setup_drive.py  for setup instructions\n")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(token_path, 'w') as f:
                f.write(self.creds.to_json())

        self.service = build('drive', 'v3', credentials=self.creds)
        print("  [OK] Google Drive authenticated successfully")
        return True

    def _auth_service_account(self, key_path: str) -> bool:
        """Authenticate using service account JSON key."""
        if not os.path.exists(key_path):
            print(f"\n  ERROR: Service account key not found at {key_path}")
            return False

        self.creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=SCOPES
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        print("  [OK] Google Drive authenticated (service account)")
        return True

    @property
    def is_authenticated(self) -> bool:
        return self.service is not None and self.creds is not None

    # ═══ FILE LISTING & SEARCH ═══

    def list_images(self, folder_id: str = "root", recursive: bool = True,
                    max_results: int = 10000) -> List[DriveFile]:
        """
        List all image files in a Drive folder.
        
        Args:
            folder_id: Google Drive folder ID ("root" for top-level)
            recursive: Scan subfolders
            max_results: Maximum files to return
            
        Returns:
            List of DriveFile objects
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        images = []
        self._list_folder_recursive(folder_id, "", images, recursive, max_results)
        
        # Update sync state
        self.sync_state.total_files_indexed = len(images)
        self.sync_state.total_size_bytes = sum(f.size for f in images)
        self.sync_state.last_sync = datetime.now().isoformat()
        self._save_sync_state()

        return images

    def _list_folder_recursive(self, folder_id: str, path: str,
                                results: List[DriveFile], recursive: bool,
                                max_results: int):
        """Recursively list images in Drive folders."""
        if len(results) >= max_results:
            return

        page_token = None
        while True:
            # Query for images in this folder
            query = f"'{folder_id}' in parents and trashed = false"
            
            try:
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, createdTime, '
                           'modifiedTime, md5Checksum, thumbnailLink)',
                    pageToken=page_token,
                    pageSize=min(1000, max_results - len(results))
                ).execute()
            except Exception as e:
                print(f"  [WARN] Error listing {path}: {e}")
                return

            files = response.get('files', [])
            
            for f in files:
                if len(results) >= max_results:
                    return

                mime = f.get('mimeType', '')
                name = f.get('name', '')
                
                # If it's a folder and recursive, descend
                if mime == 'application/vnd.google-apps.folder':
                    if recursive:
                        subfolder_path = f"{path}/{name}" if path else name
                        self._folder_cache[f['id']] = subfolder_path
                        self._list_folder_recursive(
                            f['id'], subfolder_path, results, recursive, max_results
                        )
                
                # If it's an image, add to results
                elif mime in IMAGE_MIMETYPES or Path(name).suffix.lower() in IMAGE_EXTENSIONS:
                    drive_file = DriveFile(
                        id=f['id'],
                        name=name,
                        mime_type=mime,
                        size=int(f.get('size', 0)),
                        folder_path=path,
                        created_time=f.get('createdTime', ''),
                        modified_time=f.get('modifiedTime', ''),
                        md5_checksum=f.get('md5Checksum', ''),
                        thumbnail_link=f.get('thumbnailLink', ''),
                    )
                    results.append(drive_file)

            page_token = response.get('nextPageToken')
            if not page_token:
                break

    def search_images(self, query: str = "", folder_id: str = None,
                      min_size_mb: float = 0, max_size_mb: float = 100,
                      after_date: str = None) -> List[DriveFile]:
        """
        Search for images with filters.
        
        Args:
            query: Text to search in filename
            folder_id: Limit to specific folder
            min_size_mb: Minimum file size in MB
            max_size_mb: Maximum file size in MB
            after_date: Only files created after this date (ISO format)
            
        Returns:
            Filtered list of DriveFile objects
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Build Drive API query
        q_parts = ["trashed = false"]
        
        # Image MIME types
        mime_queries = [f"mimeType = '{m}'" for m in IMAGE_MIMETYPES]
        q_parts.append(f"({' or '.join(mime_queries)})")
        
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")
        
        if query:
            q_parts.append(f"name contains '{query}'")
        
        if after_date:
            q_parts.append(f"createdTime > '{after_date}'")

        full_query = " and ".join(q_parts)
        
        results = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=full_query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, size, createdTime, '
                       'modifiedTime, md5Checksum, thumbnailLink, parents)',
                pageToken=page_token,
                pageSize=1000
            ).execute()

            for f in response.get('files', []):
                size = int(f.get('size', 0))
                size_mb = size / (1024 * 1024)
                
                if size_mb < min_size_mb or size_mb > max_size_mb:
                    continue

                drive_file = DriveFile(
                    id=f['id'],
                    name=f['name'],
                    mime_type=f.get('mimeType', ''),
                    size=size,
                    folder_path=self._resolve_path(f.get('parents', [])),
                    created_time=f.get('createdTime', ''),
                    modified_time=f.get('modifiedTime', ''),
                    md5_checksum=f.get('md5Checksum', ''),
                    thumbnail_link=f.get('thumbnailLink', ''),
                )
                results.append(drive_file)

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return results

    def _resolve_path(self, parent_ids: List[str]) -> str:
        """Resolve folder path from parent IDs."""
        if not parent_ids:
            return ""
        parent_id = parent_ids[0]
        if parent_id in self._folder_cache:
            return self._folder_cache[parent_id]
        return f"folder:{parent_id}"

    # ═══ IMAGE STREAMING (for training) ═══

    def stream_images(self, file_list: List[DriveFile] = None,
                      folder_id: str = "root",
                      batch_size: int = DEFAULT_BATCH_SIZE,
                      target_size: Tuple[int, int] = (224, 224),
                      skip_processed: bool = True) -> Generator[Tuple[bytes, DriveFile], None, None]:
        """
        Stream images from Drive for training. Yields (image_bytes, metadata) tuples.
        
        Memory-efficient: downloads one batch at a time, processes, then moves on.
        
        Args:
            file_list: Specific files to stream (or None to list from folder)
            folder_id: Folder to stream from if file_list is None
            batch_size: How many to buffer at once
            target_size: Resize images to this (width, height) for training
            skip_processed: Skip files already in processed_ids
            
        Yields:
            (image_bytes, DriveFile) tuples
        """
        if file_list is None:
            file_list = self.list_images(folder_id=folder_id)

        for drive_file in file_list:
            # Skip already processed
            if skip_processed and drive_file.id in self.sync_state.processed_ids:
                continue

            try:
                image_bytes = self._download_file_bytes(drive_file.id)
                if image_bytes:
                    yield (image_bytes, drive_file)
                    
                    # Mark as processed
                    self.sync_state.processed_ids.append(drive_file.id)
                    
            except Exception as e:
                print(f"  [WARN] Failed to stream {drive_file.name}: {e}")
                continue

        # Save state after streaming
        self._save_sync_state()

    def _download_file_bytes(self, file_id: str) -> Optional[bytes]:
        """Download a file from Drive into memory."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            return buffer.getvalue()
        except Exception as e:
            print(f"  [ERR] Download failed for {file_id}: {e}")
            return None

    # ═══ BATCH DOWNLOAD (for local cache) ═══

    def download_batch(self, files: List[DriveFile], 
                       category: str = "uncategorized",
                       max_per_batch: int = 100) -> List[str]:
        """
        Download a batch of images to local cache for training.
        
        Args:
            files: List of DriveFile objects to download
            category: Subdirectory name for organization
            max_per_batch: Maximum files per batch
            
        Returns:
            List of local file paths
        """
        category_dir = os.path.join(self.cache_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        downloaded = []
        
        for i, drive_file in enumerate(files[:max_per_batch]):
            local_path = os.path.join(category_dir, drive_file.name)
            
            # Skip if already cached (check hash)
            if os.path.exists(local_path):
                if drive_file.md5_checksum:
                    with open(local_path, 'rb') as f:
                        local_hash = hashlib.md5(f.read()).hexdigest()
                    if local_hash == drive_file.md5_checksum:
                        downloaded.append(local_path)
                        continue
                else:
                    downloaded.append(local_path)
                    continue

            # Download
            image_bytes = self._download_file_bytes(drive_file.id)
            if image_bytes:
                with open(local_path, 'wb') as f:
                    f.write(image_bytes)
                downloaded.append(local_path)
                
                if (i + 1) % 10 == 0:
                    print(f"  [{i+1}/{min(len(files), max_per_batch)}] Downloaded to {category}/")

        print(f"  [OK] {len(downloaded)} images cached in {category_dir}")
        return downloaded

    # ═══ DRIVE INFO & STATS ═══

    def get_drive_info(self) -> Dict:
        """Get information about the connected Drive."""
        if not self.is_authenticated:
            return {"error": "Not authenticated"}

        try:
            about = self.service.about().get(fields="user, storageQuota").execute()
            quota = about.get('storageQuota', {})
            user = about.get('user', {})
            
            total = int(quota.get('limit', 0))
            used = int(quota.get('usage', 0))
            
            return {
                'user': user.get('displayName', 'Unknown'),
                'email': user.get('emailAddress', ''),
                'total_storage_gb': round(total / (1024**3), 1),
                'used_storage_gb': round(used / (1024**3), 1),
                'free_storage_gb': round((total - used) / (1024**3), 1),
                'usage_percent': round(used / max(total, 1) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_index_stats(self) -> Dict:
        """Get stats about what's been indexed."""
        return {
            'total_indexed': self.sync_state.total_files_indexed,
            'total_size_gb': round(self.sync_state.total_size_bytes / (1024**3), 2),
            'total_processed': len(self.sync_state.processed_ids),
            'last_sync': self.sync_state.last_sync,
            'folders_scanned': len(self.sync_state.folders_scanned),
        }

    # ═══ FOLDER MANAGEMENT ═══

    def list_folders(self, parent_id: str = "root") -> List[Dict]:
        """List top-level folders in Drive (useful for selecting training sources)."""
        if not self.is_authenticated:
            return []

        query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
        results = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, createdTime)',
                pageToken=page_token,
                pageSize=100
            ).execute()

            for f in response.get('files', []):
                results.append({
                    'id': f['id'],
                    'name': f['name'],
                    'created': f.get('createdTime', ''),
                })

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return sorted(results, key=lambda x: x['name'])

    # ═══ SYNC STATE PERSISTENCE ═══

    def _load_sync_state(self) -> SyncState:
        """Load sync state from disk."""
        if os.path.exists(SYNC_STATE_FILE):
            try:
                with open(SYNC_STATE_FILE, 'r') as f:
                    data = json.load(f)
                return SyncState(**data)
            except Exception:
                pass
        return SyncState()

    def _save_sync_state(self):
        """Save sync state to disk."""
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
        with open(SYNC_STATE_FILE, 'w') as f:
            json.dump(asdict(self.sync_state), f, indent=2)

    def reset_sync_state(self):
        """Reset all sync/processing state (re-process everything)."""
        self.sync_state = SyncState()
        self._save_sync_state()
        print("  [OK] Sync state reset. All images will be re-processed.")


# ═══ CLI INTERFACE ═══

def main():
    """Command-line interface for testing the connector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Drive Image Connector")
    parser.add_argument("action", choices=["auth", "info", "list", "folders", "search", "stats"],
                       help="Action to perform")
    parser.add_argument("--folder", default="root", help="Folder ID to scan")
    parser.add_argument("--query", default="", help="Search query")
    parser.add_argument("--limit", type=int, default=100, help="Max results")
    
    args = parser.parse_args()
    
    connector = GoogleDriveConnector()
    
    if args.action == "auth":
        success = connector.authenticate()
        if success:
            info = connector.get_drive_info()
            print(f"\n  Connected to: {info.get('email', 'Unknown')}")
            print(f"  Storage: {info.get('used_storage_gb', 0)} / {info.get('total_storage_gb', 0)} GB")
            print(f"  Free: {info.get('free_storage_gb', 0)} GB\n")
    
    elif args.action == "info":
        connector.authenticate()
        info = connector.get_drive_info()
        for k, v in info.items():
            print(f"  {k}: {v}")
    
    elif args.action == "folders":
        connector.authenticate()
        folders = connector.list_folders(args.folder)
        print(f"\n  Folders in {'root' if args.folder == 'root' else args.folder}:")
        for f in folders:
            print(f"    {f['name']}  (id: {f['id']})")
        print(f"\n  Total: {len(folders)} folders\n")
    
    elif args.action == "list":
        connector.authenticate()
        images = connector.list_images(folder_id=args.folder, max_results=args.limit)
        print(f"\n  Found {len(images)} images:")
        for img in images[:20]:
            print(f"    {img.folder_path}/{img.name}  ({img.size_mb} MB)")
        if len(images) > 20:
            print(f"    ... and {len(images) - 20} more")
        total_gb = sum(i.size for i in images) / (1024**3)
        print(f"\n  Total: {len(images)} images, {total_gb:.2f} GB\n")
    
    elif args.action == "search":
        connector.authenticate()
        results = connector.search_images(query=args.query)
        print(f"\n  Search results for '{args.query}': {len(results)} images")
        for img in results[:10]:
            print(f"    {img.name}  ({img.size_mb} MB)")
    
    elif args.action == "stats":
        stats = connector.get_index_stats()
        print("\n  Index Stats:")
        for k, v in stats.items():
            print(f"    {k}: {v}")
        print()


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════════════
# RCLONE-BASED CONNECTOR (RECOMMENDED — no Google Cloud, no credit card)
# ═══════════════════════════════════════════════════════════════════════



import subprocess
import shutil


class RcloneDriveConnector:
    """
    Google Drive connector using Rclone — NO Google Cloud project needed.
    
    Advantages over GoogleDriveConnector:
      - No credit card / billing profile required
      - Uses rclone's built-in Google API keys
      - Headless authentication (works in cloud sandboxes)
      - Can stream directly to/from Drive (0 local disk for transfers)
      - Battle-tested with 5TB+ drives
    
    Prerequisites:
      - rclone installed (curl https://rclone.org/install.sh | bash)
      - 'gdrive' remote configured (python3 src/python/setup_drive.py)
    
    Usage:
        connector = RcloneDriveConnector()
        
        # List folders
        folders = connector.list_folders()
        
        # List images in a folder
        images = connector.list_images(folder_path="Photos/Vacation")
        
        # Download images for training
        connector.download_folder("TrainingImages/cats", "./user_data/image_cache/cats")
        
        # Stream images for training
        for img_bytes, metadata in connector.stream_images(folder_path="TrainingImages"):
            process(img_bytes)
    """

    REMOTE_NAME = "gdrive"

    def __init__(self, remote_name: str = None, cache_dir: str = None):
        self.remote = remote_name or self.REMOTE_NAME
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.sync_state = self._load_sync_state()
        
        # Verify rclone is available
        if not shutil.which("rclone"):
            raise RuntimeError(
                "Rclone not installed. Run:\n"
                "  curl https://rclone.org/install.sh | bash\n"
                "Then: python3 src/python/setup_drive.py"
            )

    @property
    def is_authenticated(self) -> bool:
        """Check if the remote is configured and accessible."""
        try:
            result = subprocess.run(
                ["rclone", "listremotes"],
                capture_output=True, text=True, timeout=10
            )
            return f"{self.remote}:" in result.stdout
        except Exception:
            return False

    def authenticate(self) -> bool:
        """Verify rclone remote is configured. Returns True if ready."""
        if self.is_authenticated:
            print(f"  [OK] Rclone remote '{self.remote}' is configured")
            return True
        else:
            print(f"  [!] Remote '{self.remote}' not found.")
            print("      Run: python3 src/python/setup_drive.py")
            return False

    # ═══ FILE LISTING ═══

    def list_folders(self, path: str = "") -> List[Dict]:
        """List folders at a given path on Drive."""
        remote_path = f"{self.remote}:{path}"
        try:
            result = subprocess.run(
                ["rclone", "lsjson", remote_path, "--dirs-only"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"  [WARN] Error listing {path}: {result.stderr.strip()}")
                return []
            
            items = json.loads(result.stdout) if result.stdout.strip() else []
            return [
                {
                    'name': item['Name'],
                    'path': f"{path}/{item['Name']}" if path else item['Name'],
                    'modified': item.get('ModTime', ''),
                }
                for item in items
            ]
        except Exception as e:
            print(f"  [ERR] {e}")
            return []

    def list_images(self, folder_path: str = "", recursive: bool = True,
                    max_results: int = 10000) -> List[DriveFile]:
        """
        List all image files in a Drive folder.
        
        Args:
            folder_path: Path on Drive (e.g. "Photos/Vacation")
            recursive: Include subfolders
            max_results: Maximum files to return
            
        Returns:
            List of DriveFile objects
        """
        remote_path = f"{self.remote}:{folder_path}"
        cmd = ["rclone", "lsjson", remote_path, "--no-modtime"]
        
        if recursive:
            cmd.append("--recursive")
        
        # Filter to image files
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'tif', 'gif']:
            cmd.extend(["--include", f"*.{ext}"])
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                print(f"  [WARN] {result.stderr.strip()}")
                return []
            
            items = json.loads(result.stdout) if result.stdout.strip() else []
            
            images = []
            for item in items[:max_results]:
                if item.get('IsDir', False):
                    continue
                
                # Extract folder from path
                item_path = item.get('Path', item['Name'])
                folder = str(Path(item_path).parent) if '/' in item_path else folder_path
                
                drive_file = DriveFile(
                    id=item.get('ID', hashlib.md5(item_path.encode()).hexdigest()),
                    name=item['Name'],
                    mime_type=item.get('MimeType', ''),
                    size=item.get('Size', 0),
                    folder_path=folder,
                    created_time=item.get('ModTime', ''),
                    modified_time=item.get('ModTime', ''),
                    md5_checksum=item.get('Hashes', {}).get('MD5', ''),
                )
                images.append(drive_file)
            
            # Update sync state
            self.sync_state.total_files_indexed = len(images)
            self.sync_state.total_size_bytes = sum(f.size for f in images)
            self.sync_state.last_sync = datetime.now().isoformat()
            self._save_sync_state()
            
            return images
            
        except subprocess.TimeoutExpired:
            print("  [WARN] Listing timed out (very large folder). Try a subfolder.")
            return []
        except Exception as e:
            print(f"  [ERR] {e}")
            return []


    def search_images(self, query: str = "", folder_path: str = "",
                      min_size_mb: float = 0, max_size_mb: float = 100) -> List[DriveFile]:
        """Search for images matching a name pattern."""
        remote_path = f"{self.remote}:{folder_path}"
        cmd = ["rclone", "lsjson", remote_path, "--recursive"]
        
        if query:
            cmd.extend(["--include", f"*{query}*"])
        else:
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                cmd.extend(["--include", f"*.{ext}"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return []
            
            items = json.loads(result.stdout) if result.stdout.strip() else []
            
            images = []
            for item in items:
                if item.get('IsDir', False):
                    continue
                size_mb = item.get('Size', 0) / (1024 * 1024)
                if size_mb < min_size_mb or size_mb > max_size_mb:
                    continue
                
                item_path = item.get('Path', item['Name'])
                drive_file = DriveFile(
                    id=hashlib.md5(item_path.encode()).hexdigest(),
                    name=item['Name'],
                    mime_type=item.get('MimeType', ''),
                    size=item.get('Size', 0),
                    folder_path=str(Path(item_path).parent),
                    created_time=item.get('ModTime', ''),
                    modified_time=item.get('ModTime', ''),
                )
                images.append(drive_file)
            
            return images
        except Exception:
            return []

    # ═══ DOWNLOADING & STREAMING ═══

    def download_folder(self, drive_path: str, local_path: str,
                        max_files: int = None) -> List[str]:
        """
        Download a folder from Drive to local cache.
        
        Args:
            drive_path: Path on Drive (e.g. "TrainingImages/cats")
            local_path: Local destination
            max_files: Maximum files to download (None = all)
            
        Returns:
            List of downloaded local file paths
        """
        os.makedirs(local_path, exist_ok=True)
        remote = f"{self.remote}:{drive_path}"
        
        cmd = ["rclone", "copy", remote, local_path, "--progress",
               "--include", "*.jpg", "--include", "*.jpeg",
               "--include", "*.png", "--include", "*.webp",
               "--include", "*.bmp", "--include", "*.tiff"]
        
        if max_files:
            cmd.extend(["--max-transfer", f"{max_files}"])
        
        print(f"  [..] Downloading {drive_path} → {local_path}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"  [WARN] Some errors: {result.stderr.strip()[:200]}")
        except subprocess.TimeoutExpired:
            print("  [WARN] Download timed out after 10 minutes")
        
        # List downloaded files
        downloaded = []
        image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
        for root, dirs, files in os.walk(local_path):
            for f in files:
                if Path(f).suffix.lower() in image_exts:
                    downloaded.append(os.path.join(root, f))
        
        print(f"  [OK] {len(downloaded)} images in {local_path}")
        return downloaded

    def download_file(self, drive_path: str, local_path: str) -> bool:
        """Download a single file from Drive."""
        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
        remote = f"{self.remote}:{drive_path}"
        
        try:
            result = subprocess.run(
                ["rclone", "copyto", remote, local_path],
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0
        except Exception:
            return False

    def _download_file_bytes(self, file_id_or_path: str) -> Optional[bytes]:
        """
        Download a file into memory (for streaming to trainer).
        
        Args:
            file_id_or_path: Either a Drive file path or a cached reference
            
        Returns:
            Raw file bytes, or None on failure
        """
        # file_id_or_path here is actually the path on drive
        remote = f"{self.remote}:{file_id_or_path}"
        
        try:
            result = subprocess.run(
                ["rclone", "cat", remote],
                capture_output=True, timeout=60
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass
        return None


    def stream_images(self, folder_path: str = "",
                      file_list: List[DriveFile] = None,
                      batch_size: int = DEFAULT_BATCH_SIZE,
                      skip_processed: bool = True) -> Generator[Tuple[bytes, DriveFile], None, None]:
        """
        Stream images from Drive for training.
        
        Uses 'rclone cat' to pipe files directly into memory —
        zero local disk usage per file.
        
        Yields:
            (image_bytes, DriveFile) tuples
        """
        if file_list is None:
            file_list = self.list_images(folder_path=folder_path)

        for drive_file in file_list:
            if skip_processed and drive_file.id in self.sync_state.processed_ids:
                continue

            # Build the full path for rclone cat
            if drive_file.folder_path and drive_file.folder_path != '.':
                full_path = f"{drive_file.folder_path}/{drive_file.name}"
            else:
                full_path = drive_file.name
            
            # Prepend the original folder_path if not already included
            if folder_path and not full_path.startswith(folder_path):
                full_path = f"{folder_path}/{full_path}"

            img_bytes = self._download_file_bytes(full_path)
            if img_bytes:
                yield (img_bytes, drive_file)
                self.sync_state.processed_ids.append(drive_file.id)

        self._save_sync_state()

    def download_batch(self, files: List[DriveFile],
                       category: str = "uncategorized",
                       folder_path: str = "") -> List[str]:
        """Download a batch of specific files to local cache."""
        category_dir = os.path.join(self.cache_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        downloaded = []
        for drive_file in files:
            local_path = os.path.join(category_dir, drive_file.name)
            
            if os.path.exists(local_path):
                downloaded.append(local_path)
                continue
            
            if drive_file.folder_path and drive_file.folder_path != '.':
                full_path = f"{drive_file.folder_path}/{drive_file.name}"
            else:
                full_path = drive_file.name
            
            if folder_path and not full_path.startswith(folder_path):
                full_path = f"{folder_path}/{full_path}"
            
            if self.download_file(full_path, local_path):
                downloaded.append(local_path)
        
        return downloaded

    # ═══ DRIVE INFO ═══

    def get_drive_info(self) -> Dict:
        """Get storage info about the connected Drive."""
        try:
            result = subprocess.run(
                ["rclone", "about", f"{self.remote}:", "--json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                total = data.get('total', 0)
                used = data.get('used', 0)
                free = data.get('free', 0)
                return {
                    'total_storage_gb': round(total / (1024**3), 1),
                    'used_storage_gb': round(used / (1024**3), 1),
                    'free_storage_gb': round(free / (1024**3), 1),
                    'usage_percent': round(used / max(total, 1) * 100, 1),
                }
        except Exception:
            pass
        return {"error": "Could not get drive info"}

    def get_index_stats(self) -> Dict:
        """Get stats about what's been indexed."""
        return {
            'total_indexed': self.sync_state.total_files_indexed,
            'total_size_gb': round(self.sync_state.total_size_bytes / (1024**3), 2),
            'total_processed': len(self.sync_state.processed_ids),
            'last_sync': self.sync_state.last_sync,
        }

    # ═══ STREAMING TO DRIVE (0 local disk) ═══

    def copy_url_to_drive(self, url: str, drive_dest_path: str) -> bool:
        """
        Stream a URL directly to Google Drive — uses 0 local disk.
        
        Perfect for downloading large datasets straight to your 5TB drive.
        
        Args:
            url: Source URL to download from
            drive_dest_path: Destination path on Drive
        """
        remote_dest = f"{self.remote}:{drive_dest_path}"
        print(f"  [..] Streaming {url} → {remote_dest}")
        
        try:
            result = subprocess.run(
                ["rclone", "copyurl", url, remote_dest, "--progress"],
                capture_output=True, text=True, timeout=3600  # 1 hour max
            )
            if result.returncode == 0:
                print(f"  [OK] Saved to Drive: {drive_dest_path}")
                return True
            else:
                print(f"  [ERR] {result.stderr.strip()[:200]}")
                return False
        except subprocess.TimeoutExpired:
            print("  [WARN] Transfer timed out after 1 hour")
            return False

    # ═══ SYNC STATE ═══

    def _load_sync_state(self) -> SyncState:
        """Load sync state from disk."""
        if os.path.exists(SYNC_STATE_FILE):
            try:
                with open(SYNC_STATE_FILE, 'r') as f:
                    data = json.load(f)
                return SyncState(**data)
            except Exception:
                pass
        return SyncState()

    def _save_sync_state(self):
        """Save sync state to disk."""
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
        with open(SYNC_STATE_FILE, 'w') as f:
            json.dump(asdict(self.sync_state), f, indent=2)

    def reset_sync_state(self):
        """Reset processing state."""
        self.sync_state = SyncState()
        self._save_sync_state()
        print("  [OK] Sync state reset.")
