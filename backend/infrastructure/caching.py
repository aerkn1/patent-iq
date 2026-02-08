import os
import time
import requests
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("uvicorn")


def _repo_root() -> Path:
    # caching.py -> backend/infrastructure/caching.py
    return Path(__file__).resolve().parents[2]


class CacheManager:
    # Use a stable path so running the backend from different working directories
    # does not create multiple caches (e.g. ./data_cache vs backend/data_cache)
    CACHE_DIR = (_repo_root() / "data_cache").absolute()

    @classmethod
    def ensure_cache(cls, registry: Dict[str, str]) -> Dict[str, str]:
        """
        Ensures all files in the registry are cached locally.
        Checks for updates via ETag/Content-Length if file exists.
        Returns a new registry dict with local file paths.
        Uses ThreadPoolExecutor for parallel processing.
        """
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        local_registry = {}
        total_files = len(registry)
        
        print(f"Checking data cache for {total_files} files (Parallel)...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Function to process a single item
        def process_item(key, url):
            filename = url.split("/")[-1]
            local_path = cls.CACHE_DIR / filename
            meta_path = local_path.with_suffix(".meta")
            
            needs_download = False
            remote_etag = None
            
            try:
                # Check remote headers slightly aggressively to ensure freshness
                head = requests.head(url, allow_redirects=True, timeout=10)
                remote_etag = head.headers.get("ETag") or head.headers.get("Content-Length")
                
                if not local_path.exists():
                    needs_download = True
                    # print(f"Missing: {filename}")
                else:
                    # Check staleness
                    local_etag = None
                    if meta_path.exists():
                        local_etag = meta_path.read_text().strip()
                    
                    if remote_etag and local_etag != remote_etag:
                        needs_download = True
                        print(f"Update available: {filename}")
                    
            except Exception as e:
                print(f"Warning: Could not check remote status for {filename}: {e}")
                # Fallback: if local exists, use it. If not, we must crash or fail.
                if not local_path.exists():
                    raise RuntimeError(f"Critical: {filename} missing and remote unreachable.") from e
            
            if needs_download:
                print(f"Downloading {filename}...")
                start_ts = time.time()
                try:
                    cls._download_file(url, local_path)
                    elapsed = time.time() - start_ts
                    print(f"Downloaded {filename} in {elapsed:.1f}s")
                    
                    if remote_etag:
                        meta_path.write_text(remote_etag)
                except Exception as e:
                    # Clean up partials
                    if local_path.exists():
                        local_path.unlink()
                    raise RuntimeError(f"Failed to download {filename}: {e}") from e
            
            return key, str(local_path)

        # Run in parallel
        # Verify max_workers based on network capabilities, 5-8 is usually good for default
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_file = {executor.submit(process_item, k, u): k for k, u in registry.items()}
            
            for future in as_completed(future_to_file):
                try:
                    key, path = future.result()
                    local_registry[key] = path
                except Exception as exc:
                    print(f"Cache update failed: {exc}")
                    raise exc

        print("Data cache verification complete.")
        return local_registry

    @staticmethod
    def _download_file(url: str, dest: Path):
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
