import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import logging
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class RecordingFetcher:
    def __init__(self, storage_dir: str = "recordings_cache", max_retries: int = 3, timeout: int = 30):
        self.base_url = "https://three.arcprize.org/api/recordings"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.max_retries = max_retries
        self.timeout = timeout


    def fetch_recording(self, game_id: str, recording_id: str) -> Optional[List[Dict]]:
        """Fetch a recording from the ARC API with retry logic and progress tracking"""
        url = f"{self.base_url}/{game_id}/{recording_id}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching recording from: {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse NDJSON format (each line is a JSON object)
                frames = []
                lines = response.text.strip().split('\n')
                total_lines = len(lines)
                
                for line_num, line in enumerate(lines, 1):
                    if line.strip():
                        try:
                            frame_data = json.loads(line.strip())
                            frames.append(frame_data)
                            
                            # Log progress for large files
                            if total_lines > 1000 and line_num % 100 == 0:
                                progress = (line_num / total_lines) * 100
                                logger.info(f"Parsing progress: {progress:.1f}% ({line_num}/{total_lines})")
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"Error parsing line {line_num}: {e}")
                            continue
                
                logger.info(f"Successfully parsed {len(frames)} frames from {total_lines} lines")
                return frames
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        logger.error(f"Failed to fetch recording after {self.max_retries} attempts")
        return None
    
    def save_recording(self, game_id: str, recording_id: str, frames: List[Dict]) -> str:
        """Save recording data to local file"""
        filename = f"{game_id}-{recording_id}.jsonl"
        filepath = self.storage_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for frame in frames:
                    f.write(json.dumps(frame) + '\n')
            
            
            logger.info(f"Saved recording to: {filepath} ({len(frames)} frames)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            raise
    
    def get_cached_recording(self, game_id: str, recording_id: str) -> Optional[str]:
        """Check if recording is already cached locally"""
        filename = f"{game_id}-{recording_id}.jsonl"
        filepath = self.storage_dir / filename
        
        if filepath.exists():
            logger.info(f"Found cached recording: {filepath}")
            return str(filepath)
        
        return None
    
    def fetch_and_cache_recording(self, game_id: str, recording_id: str) -> Optional[str]:
        """Fetch recording from API and cache it locally"""
        start_time = datetime.now()
        
        try:
            cached_path = self.get_cached_recording(game_id, recording_id)
            if cached_path:
                return cached_path
            
            frames = self.fetch_recording(game_id, recording_id)
            if frames:
                result_path = self.save_recording(game_id, recording_id, frames)
                load_time = datetime.now() - start_time
                logger.info(f"Recording fetched and cached in {load_time.total_seconds():.2f}s")
                return result_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fetch_and_cache_recording: {e}")
            return None
    
    def list_cached_recordings(self) -> List[Dict]:
        """List all cached recordings"""
        recordings = []
        
        for filepath in self.storage_dir.glob("*.jsonl"):
            try:
                stat = filepath.stat()
                recordings.append({
                    "name": filepath.name,
                    "path": str(filepath),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "game_id": filepath.stem.split('-')[0],
                    "recording_id": '-'.join(filepath.stem.split('-')[1:])
                })
            except Exception as e:
                logger.warning(f"Error reading file {filepath}: {e}")
        
        # Sort by modification time (newest first)
        recordings.sort(key=lambda x: x['modified'], reverse=True)
        return recordings

# Example usage
if __name__ == "__main__":
    fetcher = RecordingFetcher()
    
    # Example recording from your code
    game_id = "ft09-16726c5b26ff"
    recording_id = "1ed47a81-fda5-4524-afd5-751d3ec30479"
    
    # Fetch and cache the recording
    jsonl_path = fetcher.fetch_and_cache_recording(game_id, recording_id)
    
    if jsonl_path:
        print(f"Ready for visualization: {jsonl_path}")
    else:
        print("Failed to fetch recording")
    