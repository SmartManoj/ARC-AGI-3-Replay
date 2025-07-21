# ARC-AGI-3 Replay

A modern web-based visualization tool for analyzing ARC (Abstraction and Reasoning Corpus) agent recordings. This application provides an enhanced interface for stepping through recorded frames and viewing detailed reasoning logs from AI agents solving grid-based puzzles.

## 🎯 Core Functionality

### Frame Navigation
- **Visual Grid Representation**: High-quality grid visualization with color-coded cells
- **Smooth Navigation**: Step through frames with keyboard shortcuts or UI controls
- **Frame Slider**: Quick navigation to any frame with visual slider

### Reasoning Analysis
- **Detailed Logs**: Comprehensive reasoning data from AI agents
- **Collapsible Entries**: Expandable reasoning sections for better organization
- **Export Capability**: Download reasoning logs as JSON files

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `←` `→` | Navigate between frames |
| `Home`/`End` | Jump to first/last frame |
| `Space` | Toggle playback |
| `H` | Toggle help tooltip |
| `R` | Refresh recordings list |
| `S` | Show performance statistics |


## 🚀 Getting Started

### Prerequisites
- Python 3.8+

### Installation
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
1. Start the Flask server:
   ```bash
   python run_app.py
   ```
2. Open your web browser and go to: `http://localhost:5000`

### Environment Variables
- `IS_CLOUD=1`: Enable cloud mode (default: 0)
- `DEBUG=1`: Enable debug mode (default: 1)

## 📊 API Endpoints

### Core Endpoints
- `GET /`: Main application page
- `POST /api/load_recording`: Load recording from API
- `POST /api/load_file`: Load local recording file
- `GET /api/go_to_frame/<index>`: Navigate to specific frame
- `GET /api/list_recordings`: List available recordings
- `GET /api/health`: Health check endpoint


## 🛠️ Development

### Project Structure
```
Temp/
├── app.py                 # Main Flask application
├── recording_fetcher.py   # Enhanced recording fetcher
├── run_app.py            # Application entry point
├── requirements.txt      # Updated dependencies
├── templates/
│   └── index.html       # Modern web interface
└── static/
    └── style.css        # Enhanced styling
```

## 🔍 Troubleshooting

### Debug Mode
Enable debug mode for detailed logging:
```bash
DEBUG=1 python run_app.py
```


## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
