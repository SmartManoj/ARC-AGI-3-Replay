from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from typing import Any
import os
from pathlib import Path
import uuid
import logging
from datetime import datetime
from recording_fetcher import RecordingFetcher
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment configuration
is_cloud = os.getenv('IS_CLOUD', '1') == '1'
debug_mode = os.getenv('DEBUG', '0') == '1'

class FrameVisualizer:
    def __init__(self):
        # Initialize recording fetcher
        self.recording_fetcher = RecordingFetcher()
        
        # Default recording info
        self.default_game_id = "ft09-16726c5b26ff"
        self.default_recording_id = "1ed47a81-fda5-4524-afd5-751d3ec30479"
        
        # Sample data from the JSON
        self.frame_data = [[[]]]
        self.game_id = self.default_game_id
        self.state = "NOT_FINISHED"
        self.score = 0
        self.current_frame_index = 0
        self.frames = []
        self.session_id = str(uuid.uuid4())
        self.level = 1
        
        # Color mapping for grid values
        self.color_map = self.create_color_map()
        
        # Performance tracking
        self.load_times = []
        self.last_load_time = None
    
    def create_color_map(self):
        """Create color mapping for grid values"""
        return {
            0: ("#FFFFFFFF", 'White'),
            1: ("#CCCCCCFF", 'Light gray'),
            2: ("#999999FF", 'Gray'),
            3: ("#666666FF", 'Dark gray'),
            4: ("#333333FF", 'Charcoal'),
            5: ("#000000FF", 'Black'),
            6: ("#E53AA3FF", 'Pink'),
            7: ("#FF7BCCFF", 'Light pink'),
            8: ("#F93C31FF", 'Red'),
            9: ("#1E93FFFF", 'Blue'),
            10: ("#88D8F1FF", 'Light blue'),
            11: ("#FFDC00FF", 'Yellow'),
            12: ("#FF851BFF", 'Orange'),
            13: ("#921231FF", 'Dark red'),
            14: ("#4FCC30FF", 'Green'),
            15: ("#A356D6FF", 'Purple'),
        }
    
    def load_recording(self, game_id: str = None, recording_id: str = None) -> dict:
        """Load recording from API and cache it with enhanced error handling"""
        start_time = datetime.now()
        
        try:
            if game_id is None:
                game_id = self.default_game_id
            if recording_id is None:
                recording_id = self.default_recording_id
            
            logger.info(f"Loading recording: {game_id}/{recording_id}")
            
            # Fetch and cache the recording
            jsonl_path = self.recording_fetcher.fetch_and_cache_recording(game_id, recording_id)
            
            if jsonl_path:
                result = self.load_file(jsonl_path)
                if 'error' not in result:
                    self.last_load_time = datetime.now() - start_time
                    self.load_times.append(self.last_load_time.total_seconds())
                    logger.info(f"Recording loaded successfully in {self.last_load_time.total_seconds():.2f}s")
                return result
            else:
                return {"error": "Failed to fetch recording from API"}
                
        except Exception as e:
            logger.error(f"Error loading recording: {str(e)}")
            return {"error": f"Error loading recording: {str(e)}"}
    
    def load_file(self, filepath: str) -> dict:
        """Load frames from JSONL file"""
        if not filepath or not os.path.exists(filepath):
            return {"error": "File not found"}
        
        try:
            self.frames = []
            frame_count = 0
            error_count = 0
            
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if 'data' in data and 'frame' in data['data']:
                                self.frames.append(data)
                                frame_count += 1
                            else:
                                error_count += 1
                                logger.warning(f"Invalid frame structure at line {line_num}")
                        except json.JSONDecodeError as e:
                            error_count += 1
                            logger.warning(f"JSON decode error at line {line_num}: {e}")
            
            logger.info(f"Loaded {frame_count} frames, {error_count} errors")
            
            if self.frames:
                self.current_frame_index = 0
                return self.load_current_frame()
            else:
                return {"error": "No valid frame data found in file"}
                
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            return {"error": f"Error loading file: {str(e)}"}
    
    def load_current_frame(self) -> dict:
        """Load the current frame data"""
        if 0 <= self.current_frame_index < len(self.frames):
            frame_data = self.frames[self.current_frame_index]
            
            # Update game info
            data = frame_data.get('data', {})
            self.game_id = data.get('game_id', 'Unknown')
            self.state = data.get('state', 'Unknown')
            self.score = data.get('score', 0)
            self.frame_data = data.get('frame', [[[]]])
            
            # Extract additional metadata
            action_input = data.get('action_input', {})
            reasoning = action_input.get('reasoning', {})
            
            # Get action information
            action_chosen = reasoning.get('action_chosen', 'None') if reasoning else 'None'
            agent_type = reasoning.get('agent_type', 'None') if reasoning else 'None'
            model = reasoning.get('model', 'None') if reasoning else 'None'
            
            return {
                "game_id": self.game_id,
                "state": self.state,
                "score": self.score,
                "action_chosen": action_chosen,
                "agent_type": agent_type,
                "model": model,
                "frame_index": self.current_frame_index + 1,
                "total_frames": len(self.frames),
                "frame_data": self.frame_data,
                "reasoning": reasoning,
                "session_id": self.session_id,
                "level": self.level,
                "color_map": self.color_map,
            }
        return {"error": "Invalid frame index"}
    
    def go_to_frame(self, frame_index: int) -> dict:
        """Go to specific frame"""
        if 0 <= frame_index < len(self.frames):
            self.current_frame_index = frame_index
            return self.load_current_frame()
        return {"error": f"Invalid frame index: {frame_index}; total frames: {len(self.frames)}"}
    


# Create global instance
visualizer = FrameVisualizer()

@app.route('/')
def index():
    """Main page with environment info"""
    return render_template('index.html', 
                         is_cloud=is_cloud, 
                         debug_mode=debug_mode)

@app.route('/<game_id>/<recording_id>')
def replay_url(game_id, recording_id):
    """Handle replay URLs in the format /{game_id}/{recording_id}"""
    # Validate lengths
    if len(game_id) != 17:
        return jsonify({"error": f"Invalid game_id length: {len(game_id)}, expected 17"}), 400
    
    if len(recording_id) != 36:
        return jsonify({"error": f"Invalid recording_id length: {len(recording_id)}, expected 36"}), 400
    
    # Construct the three.arcprize.org URL
    arcprize_url = f"https://three.arcprize.org/replay/{game_id}/{recording_id}"
    
    return render_template('index.html', 
                         is_cloud=is_cloud, 
                         debug_mode=debug_mode,
                         game_id=game_id,
                         recording_id=recording_id,
                         arcprize_url=arcprize_url)

@app.route('/api/load_recording', methods=['POST'])
def api_load_recording():
    """API endpoint to load a recording from API"""
    try:
        data = request.get_json()
        game_id = data.get('game_id', visualizer.default_game_id)
        recording_id = data.get('recording_id', visualizer.default_recording_id)
        
        # Validate lengths if provided
        if game_id and len(game_id) != 17:
            return jsonify({"error": f"Invalid game_id length: {len(game_id)}, expected 17"}), 400
        
        if recording_id and len(recording_id) != 36:
            return jsonify({"error": f"Invalid recording_id length: {len(recording_id)}, expected 36"}), 400
        
        result = visualizer.load_recording(game_id, recording_id)
        if 'error' not in result:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in load_recording API: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/load_file', methods=['POST'])
def api_load_file():
    """API endpoint to load a file"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        filepath = data.get('filepath', '')
        if not filepath:
            return jsonify({"error": "No filepath provided"}), 400
        
        result = visualizer.load_file(filepath)
        if 'error' not in result:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in load_file API: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/go_to_frame/<int:frame_index>')
def api_go_to_frame(frame_index):
    """API endpoint to go to specific frame"""
    try:
        result = visualizer.go_to_frame(frame_index)
        if 'error' not in result:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in go_to_frame API: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/upload_file', methods=['POST'])
def api_upload_file():
    """API endpoint to upload and load a recording file"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not file.filename.lower().endswith(('.jsonl')):
            return jsonify({"error": "Only .jsonl files are supported"}), 400
        
        # Create temporary file
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Load the uploaded file
            result = visualizer.load_file(temp_path)
            if 'error' not in result:
                return jsonify(result)
            else:
                return jsonify(result), 400
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_path}: {e}")
            
    except Exception as e:
        logger.error(f"Error in upload_file API: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/list_recordings')
def api_list_recordings():
    """API endpoint to list available recording files"""
    try:
        # for security reasons, we don't want to list recordings if we are not on the cloud;
        # for concerned users: add PR to fetch recordings on client side itself
        if is_cloud:
            return jsonify({"error": "Recordings are not available on this device"}), 403
        else:
            # Get cached recordings from the fetcher
            cached_recordings = visualizer.recording_fetcher.list_cached_recordings()
            
            # Also look for recordings in the ARC-AGI-3-Agents directory
            recordings_dir = Path(r"C:\Users\smart\Desktop\GD\ARC-AGI-3-Agents\recordings")
            local_recordings = []
            
            if recordings_dir.exists():
                for file_path in recordings_dir.glob("*.jsonl"):
                    try:
                        stat = file_path.stat()
                        local_recordings.append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "source": "local"
                        })
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")
            
            # Combine and sort all recordings
            all_recordings = []
            for rec in cached_recordings:
                rec["source"] = "cached"
                all_recordings.append(rec)
            
            for rec in local_recordings:
                all_recordings.append(rec)
            
            # Sort by modification time (newest first)
            all_recordings.sort(key=lambda x: x['modified'], reverse=True)
            
            return jsonify({
                "recordings": all_recordings,
                "cached_directory": str(visualizer.recording_fetcher.storage_dir),
                "local_directory": str(recordings_dir) if recordings_dir.exists() else None,
                "total_recordings": len(all_recordings)
            })
            
    except Exception as e:
        logger.error(f"Error listing recordings: {str(e)}")
        return jsonify({"error": f"Error listing recordings: {str(e)}"}), 500


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "cloud" if is_cloud else "local",
        "debug_mode": debug_mode
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create static directory if it doesn't exist
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    logger.info(f"Starting Frame Visualizer in {'cloud' if is_cloud else 'local'} mode")
    logger.info(f"Debug mode: {debug_mode}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 