# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive modification package for the DGT Centaur electronic chessboard. It replaces the standard firmware with an enhanced system that adds WiFi connectivity, web interface, plugin architecture, and integration with multiple chess engines. The software runs on a Raspberry Pi Zero 2 W inside the board and is distributed as a Debian package.

## Build and Deployment

### Building the Debian Package

```bash
# Build the complete .deb package for deployment
make package
```

This creates `releases/DGTCentaurMods_A.alpha-ON<version>.deb` which can be installed on the board.

### Development Workflow

The project has nested Makefiles:

```bash
# Clean build artifacts (runs recursively through subdirectories)
make clean

# Deep clean including config files, databases, and Python cache
make distclean
```

**Web UI Development:**

```bash
cd DGTCentaurMods/opt/DGTCentaurMods/web/client

# Install dependencies
npm install

# Run development server with hot reload (configure proxy in vite.config.js first)
npm run dev

# Build production bundle
npm run build  # or just 'make'
```

For development, configure the Vite proxy in `vite.config.js` to point to your board (e.g., `ws://centaur.local`) to work with a live backend.

### On-Device Commands

When SSH'd into the board:

```bash
# Restart main application service
sudo systemctl restart DGTCentaurMods.service

# Restart web interface service
sudo systemctl restart DGTCentaurModsWeb.service

# View application logs
journalctl -u DGTCentaurMods.service -f

# View web service logs
journalctl -u DGTCentaurModsWeb.service -f
```

The main application runs from `/opt/DGTCentaurMods/main.py` and the web server from `/opt/DGTCentaurMods/web/app.py` (Flask).

## Architecture

### Core Application Structure

**Entry Point:** `DGTCentaurMods/opt/DGTCentaurMods/main.py`
- Initializes hardware (board, screen, socket connection)
- Implements the main menu system
- Dynamically loads plugins from the `plugins/` directory
- Handles navigation and module launching

**Hardware Abstraction Layer (`classes/`):**

- **`CentaurBoard.py`**: Complete interface to the physical board
  - LED control (`leds_on()`, `led_from_to()`, `leds_off()`)
  - Piece detection and move recognition
  - Button press handling
  - FEN position reading

- **`CentaurScreen.py`**: E-paper display management
  - Text rendering with multiple fonts
  - Board position drawing
  - Custom graphics and layouts
  - Double-buffering for updates

- **`ChessEngine.py`**: UCI chess engine wrapper
  - Async move calculation
  - Position evaluation
  - ELO configuration
  - Multiple engine support (Stockfish, Maia, CT800, etc.)

- **`Plugin.py`**: Base class for all game modes
  - Defines callback interface (7 callbacks)
  - Provides `Centaur` static API for hardware access
  - Handles lifecycle (start/stop/cleanup)

- **`GameFactory.py`**: Core game engine managing chess logic
  - Move validation
  - PGN recording
  - Undo/redo functionality
  - Game state management

- **`SocketClient.py`**: WebSocket communication with web UI
  - Bidirectional real-time messaging
  - Board state synchronization
  - Remote control capability

### Plugin System

**Location:** `DGTCentaurMods/opt/DGTCentaurMods/plugins/`

**Critical Rule:** Filename MUST match class name exactly (e.g., `RandomBot.py` → `class RandomBot(Plugin)`)

**Plugin Lifecycle:**
1. Plugin inherits from `Plugin` base class
2. Implements callbacks: `splash_screen()`, `on_start_callback()`, `key_callback()`, `event_callback()`, `move_callback()`, `undo_callback()`, `field_callback()`
3. Uses `Centaur` static API to interact with hardware
4. Main application auto-discovers and loads all valid plugins

**Key Plugin Callbacks:**
- `event_callback()`: Handles game state changes (PLAY, QUIT, TERMINATION)
- `move_callback()`: Validates player moves before acceptance
- `key_callback()`: Responds to physical button presses (HELP, PLAY, etc.)

See `plugins/README.md` and `plugins/README.es.md` for complete plugin development documentation with examples.

### Web Architecture

**Backend:** Flask server (`web/app.py`)
- Socket.io server for real-time communication
- Serves static files
- Handles API requests
- Communicates with main application via local socket

**Frontend:** Vue 3 + Vite (`web/client/`)
- Pinia for state management
- DaisyUI + Tailwind CSS for styling
- Chessboard.js for board rendering
- Stockfish.js for client-side analysis
- CodeMirror for code editing

**WebSocket API:**
- Main channel: `'request'` - Commands and data requests
- Secondary channel: `'web_message'` - Lightweight messages, chat, LED control
- See `WEBSOCKET_API.md` for complete protocol documentation

### Module System

**Location:** `DGTCentaurMods/opt/DGTCentaurMods/modules/`

Modules are standalone Python scripts that can be executed by the main application:
- `uci_module.py`: Play against UCI engines
- `lichess_module.py`: Online play on Lichess.org
- Others for specific game modes

Launched via: `{"execute": "module_name.py args..."}`

### System Services

Three systemd services:
1. **DGTCentaurMods.service**: Main application
   - Runs `python3 main.py` as user `pi`
   - Working directory: `/opt/DGTCentaurMods`
   - Depends on web service

2. **DGTCentaurModsWeb.service**: Web interface
   - Runs Flask server
   - Working directory: `/opt/DGTCentaurMods/web`
   - Always restarts on failure

3. **DGTCentaurModsUpdate.service**: Auto-updater
   - Checks for new releases from GitHub
   - Applies updates automatically

## Important Conventions

### Plugin Development
- File name = Class name (case-sensitive)
- Always call `super().start()` and `super().stop()`
- Handle `Enums.Event.QUIT` in `event_callback()`
- Clean up resources (chess engines, timers) in `stop()`
- Use async callbacks for engine operations (`request_chess_engine_move()`, `request_chess_engine_evaluation()`)

### Hardware Interaction
- Access board via `Centaur` static API, never directly
- Turn off LEDs when done: `Centaur.lights_off()`
- Clear screen before drawing: `Centaur.clear_screen()`
- Use appropriate sounds for feedback: `Centaur.sound(Enums.Sound.CORRECT_MOVE)`

### WebSocket Communication
- Board → Web: Send via `SOCKET.send_web_message(dict)`
- Web → Board: Listen in plugin's `on_socket_request(data)`
- Always validate incoming data from web interface
- Use structured messages (see WEBSOCKET_API.md)

### Code Organization
- All imports should use absolute paths from `DGTCentaurMods`
- Hardware classes are singletons (use `.get()` method)
- Enums are in `DGTCentaurMods.consts.Enums`
- Constants in `DGTCentaurMods.consts.consts`

## Testing

```bash
cd DGTCentaurMods/opt/DGTCentaurMods

# Run tests (if pytest is installed)
pytest test/

# Individual test files
python3 -m pytest test/test_common.py
python3 -m pytest test/test_chess.py
```

Tests are minimal - focus is on integration testing on actual hardware.

## Python Environment

- **Python Version:** 3.x (Debian default)
- **Key Dependencies:**
  - python-chess: Chess logic and UCI
  - Pillow: Image processing for e-paper
  - Flask + flask-socketio: Web server
  - berserk: Lichess API client
  - wpa-pyfi: WiFi configuration

Environment variable required: `PYTHONPATH=/opt`

## Common Patterns

### Creating a Simple Bot Plugin

1. Create file: `plugins/MyBot.py`
2. Inherit from `Plugin`
3. Implement `event_callback()` to handle PLAY event
4. Use `Centaur.request_chess_engine_move()` for async move calculation
5. Call `Centaur.play_computer_move(uci_move)` to execute move

### Accessing Board State

```python
# In plugin methods:
self.chessboard              # Current chess.Board object
self.chessboard.turn         # Current player (chess.WHITE or chess.BLACK)
self.chessboard.legal_moves  # Legal moves
self.chessboard.fen()        # Current position
```

### Displaying Information

```python
Centaur.clear_screen()
Centaur.print("Title", font=fonts.DIGITAL_FONT, row=2)
Centaur.print("Line 1")  # Auto-increments row
Centaur.header("Player W")  # Game header
```

### LED Control

```python
Centaur.flash("e4")              # Flash single square
Centaur.light_move("e2e4")       # Show move
Centaur.light_moves(("e2e4", "d2d4"))  # Multiple moves
Centaur.lights_off()             # Turn all off
```

## Live Script System

Scripts in `DGTCentaurMods/opt/DGTCentaurMods/scripts/` can automate board interaction:
- Access via `LiveScript.get()`
- Can push buttons, select menus, play moves
- Useful for testing and automation
- Execute via web interface or `{"live_script": "code"}`

## Deployment Notes

- Package is built on Linux (requires `dpkg-deb`)
- Version comes from git tags
- Installation scripts in `DEBIAN/` handle service setup
- Default user is `pi` (Raspberry Pi standard)
- Configuration stored in `/opt/DGTCentaurMods/config/centaur.ini`
- Database at `/opt/DGTCentaurMods/db/centaur.db`

## Additional Documentation

- **Plugin Development:** See `plugins/README.md` (English) or `plugins/README.es.md` (Spanish)
- **WebSocket API:** See `WEBSOCKET_API.md` for complete protocol
- **Project Summary:** See `PROJECT_SUMMARY.md` for architecture overview
- **Main README:** See `README.md` for features and installation
