# Plugin Development Guide for DGT Centaur Mods

[🇪🇸 Versión en Español](README.es.md)

## Table of Contents
1. [Introduction](#introduction)
2. [Basic Structure](#basic-structure)
3. [Available Callbacks](#available-callbacks)
4. [Centaur API](#centaur-api)
5. [Complete Examples](#complete-examples)
6. [Best Practices](#best-practices)
7. [Testing Your Plugin](#testing-your-plugin)

---

## Introduction

Plugins for DGT Centaur Mods allow you to extend the functionality of the DGT Centaur chess board. Each plugin inherits from the `Plugin` base class and can implement chess variants, educational games, custom bots, and more.

### Prerequisites
- Basic Python knowledge
- Familiarity with the `python-chess` library
- Understanding of the DGT Centaur system

---

## Basic Structure

### 1. File Structure

All plugins must be located in the directory:
```
DGTCentaurMods/opt/DGTCentaurMods/plugins/
```

**Important rule**: The file name must exactly match the class name.
- File: `MyPlugin.py`
- Class: `class MyPlugin(Plugin):`

### 2. Basic Template

```python
# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
# [Include full GPL v3 license header]

import chess
from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts
from typing import Optional

class MyPlugin(Plugin):
    """
    Description of what your plugin does.
    """

    def __init__(self, id: str):
        """Plugin constructor."""
        super().__init__(id)
        # Initialize plugin variables here
        self.my_variable = None

    def start(self):
        """
        Automatically invoked when the user launches the plugin.
        """
        super().start()
        # Initial setup here

    def stop(self):
        """
        Automatically invoked when the user stops the plugin.
        """
        super().stop()
        # Resource cleanup here

    def splash_screen(self) -> bool:
        """
        Initial screen shown when starting the plugin.
        Returns True if you want to activate the splash screen.
        """
        Centaur.clear_screen()
        Centaur.print("MY PLUGIN", font=fonts.DIGITAL_FONT, row=2)
        Centaur.print("Push PLAY", row=5)
        Centaur.print("to start!")
        return True

    def on_start_callback(self, key: Enums.Btn) -> bool:
        """
        Invoked after splash screen when a button is pressed.
        Returns True to indicate the game has started.
        """
        if key == Enums.Btn.PLAY:
            # Start the game
            return True
        return False
```

---

## Available Callbacks

### 1. `splash_screen() -> bool`

Shows an initial screen when the plugin is launched.

**Return:**
- `True`: Activates splash screen (user must press a button to continue)
- `False`: Skips directly to the game

**Example:**
```python
def splash_screen(self) -> bool:
    Centaur.clear_screen()
    Centaur.print("RANDOM BOT", row=2)
    Centaur.print("Push PLAY to start", row=5)
    return True
```

---

### 2. `on_start_callback(key: Enums.Btn) -> bool`

Invoked when the user presses a button after the splash screen.

**Parameters:**
- `key`: The button pressed (Enums.Btn.PLAY, UP, DOWN, TICK, etc.)

**Return:**
- `True`: The game has started
- `False`: Wait for more user actions

**Example:**
```python
def on_start_callback(self, key: Enums.Btn) -> bool:
    if key == Enums.Btn.UP:
        self.HUMAN_COLOR = chess.WHITE
    elif key == Enums.Btn.DOWN:
        self.HUMAN_COLOR = chess.BLACK
        Centaur.reverse_board()
    else:
        return False  # Wait for color choice

    # Start game
    Centaur.start_game(
        white="You",
        black="Bot",
        event="My Event",
        flags=Enums.BoardOption.CAN_UNDO_MOVES
    )
    return True
```

---

### 3. `key_callback(key: Enums.Btn) -> bool`

Invoked each time the user presses a button (except BACK, which is handled automatically).

**Parameters:**
- `key`: The button pressed

**Return:**
- `True`: The key has been handled by the plugin
- `False`: The key can be handled by the game engine

**Available buttons:**
```python
Enums.Btn.HELP    # Help button
Enums.Btn.TICK    # Tick/confirmation button
Enums.Btn.UP      # Up button
Enums.Btn.DOWN    # Down button
Enums.Btn.PLAY    # Play button
```

**Example:**
```python
def key_callback(self, key: Enums.Btn):
    if key == Enums.Btn.HELP:
        Centaur.hint()  # Show hint using Stockfish
        return True
    return False
```

---

### 4. `event_callback(event: Enums.Event, outcome: Optional[chess.Outcome])`

Invoked when the game engine state changes.

**Available events:**
```python
Enums.Event.NEW_GAME      # New game started
Enums.Event.RESUME_GAME   # Game resumed
Enums.Event.PLAY          # Play turn
Enums.Event.REQUEST_DRAW  # Draw request
Enums.Event.RESIGN_GAME   # Resignation
Enums.Event.QUIT          # Exit plugin
Enums.Event.TERMINATION   # Game ended
```

**Example:**
```python
def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
    if event == Enums.Event.QUIT:
        self.stop()

    if event == Enums.Event.TERMINATION:
        if outcome.winner == chess.WHITE:
            Centaur.sound(Enums.Sound.VICTORY)
        else:
            Centaur.sound(Enums.Sound.GAME_LOST)

    if event == Enums.Event.PLAY:
        turn = self.chessboard.turn
        current_player = "You" if turn == chess.WHITE else "Bot"
        Centaur.header(f"{current_player} {'W' if turn == chess.WHITE else 'B'}")

        if turn == (not self.HUMAN_COLOR):
            # Computer's turn
            self.computer_move()
```

---

### 5. `move_callback(uci_move: str, san_move: str, color: chess.Color, field_index: chess.Square) -> bool`

Invoked when the player physically moves a piece.

**Parameters:**
- `uci_move`: Move in UCI notation (e.g., "e2e4")
- `san_move`: Move in SAN notation (e.g., "e4")
- `color`: Color that moved (chess.WHITE or chess.BLACK)
- `field_index`: Destination square index (0-63)

**Return:**
- `True`: Move accepted
- `False`: Move rejected

**Example:**
```python
def move_callback(self, uci_move: str, san_move: str, color: chess.Color, field_index: chess.Square):
    # Validate custom move
    if color == self.HUMAN_COLOR:
        # Evaluate position after move
        self.evaluate_position()
    return True  # Accept move
```

---

### 6. `undo_callback(uci_move: str, san_move: str, field_index: chess.Square)`

Invoked when the player takes back a move.

**Example:**
```python
def undo_callback(self, uci_move: str, san_move: str, field_index: chess.Square):
    # Re-evaluate the position
    self.evaluate_position()
```

---

### 7. `field_callback(square: str, field_action: Enums.PieceAction, web_move: bool)`

Invoked when the player interacts with a board square.

**Parameters:**
- `square`: Square name (e.g., "e4")
- `field_action`: Action performed (LIFT or PLACE)
- `web_move`: If the move comes from the web interface

**Available actions:**
```python
Enums.PieceAction.LIFT   # Piece lifted
Enums.PieceAction.PLACE  # Piece placed
```

**Example:**
```python
def field_callback(self, square: str, field_action: Enums.PieceAction, web_move: bool):
    if field_action == Enums.PieceAction.PLACE:
        # Check if it's the correct square
        if square == self.target_square:
            Centaur.sound(Enums.Sound.CORRECT_MOVE)
        else:
            Centaur.sound(Enums.Sound.WRONG_MOVE)
```

---

## Centaur API

The `Centaur` class provides a static API to interact with the hardware and system.

### Display (E-paper Screen)

#### `Centaur.clear_screen()`
Clears the e-paper display.

```python
Centaur.clear_screen()
```

#### `Centaur.print(text: str, row: float = -1, font=fonts.MAIN_FONT)`
Prints text on the screen.

**Parameters:**
- `text`: Text to display
- `row`: Row where to display (optional, auto-increments)
- `font`: Font to use

**Available fonts:**
```python
fonts.MAIN_FONT          # Main font
fonts.DIGITAL_FONT       # Large digital font
fonts.SMALL_DIGITAL_FONT # Small digital font
fonts.MEDIUM_MAIN_FONT   # Medium font
fonts.SMALL_MAIN_FONT    # Small font
```

**Example:**
```python
Centaur.print("MY PLUGIN", font=fonts.DIGITAL_FONT, row=2)
Centaur.print("Line 1")
Centaur.print("Line 2")  # Row auto-increments
```

#### `Centaur.header(text: str, web_text: str = None)`
Shows a header during the game.

```python
Centaur.header("You W")
Centaur.header(
    text="You W",
    web_text="turn → You (WHITE)"
)
```

#### `Centaur.messagebox(text_lines: Tuple[str,...], row: float = 8, tick_button: bool = False)`
Shows a message box.

```python
Centaur.messagebox(("Game Over!", "White wins"), row=8)
```

#### `Centaur.print_button_label(button: Enums.Btn, x: int, row: float = -1, text: str = "")`
Shows a button label.

```python
Centaur.print_button_label(Enums.Btn.UP, row=8, x=6, text="Play white")
Centaur.print_button_label(Enums.Btn.DOWN, row=9, x=6, text="Play black")
```

---

### Board LEDs

#### `Centaur.flash(square: str)`
Flashes an LED on a square.

```python
Centaur.flash("e4")
```

#### `Centaur.light_move(uci_move: str, web: bool = True)`
Lights up a move (from → to).

```python
Centaur.light_move("e2e4")
```

#### `Centaur.light_moves(uci_moves: Tuple[str], web: bool = True)`
Lights up multiple moves.

```python
Centaur.light_moves(("e2e4", "d2d4", "g1f3"))
```

#### `Centaur.lights_off()`
Turns off all LEDs.

```python
Centaur.lights_off()
```

---

### Sounds

#### `Centaur.sound(sound: Enums.Sound, override: Optional[Enums.Sound] = None)`
Plays a sound.

**Available sounds:**
```python
Enums.Sound.MUSIC           # Music
Enums.Sound.WRONG_MOVE      # Wrong move
Enums.Sound.CORRECT_MOVE    # Correct move
Enums.Sound.TAKEBACK_MOVE   # Takeback move
Enums.Sound.COMPUTER_MOVE   # Computer move
Enums.Sound.POWER_OFF       # Power off
Enums.Sound.VICTORY         # Victory
Enums.Sound.GAME_LOST       # Game lost
Enums.Sound.VERY_GOOD_MOVE  # Very good move
Enums.Sound.BAD_MOVE        # Bad move
```

**Example:**
```python
Centaur.sound(Enums.Sound.CORRECT_MOVE)
Centaur.sound(Enums.Sound.VICTORY)
```

---

### Chess Engine

#### `Centaur.start_game(...)`
Starts a new game.

```python
Centaur.start_game(
    white="You",              # White player name
    black="Bot",              # Black player name
    event="My Event 2024",    # Event name
    site="",                  # Site (optional)
    flags=Enums.BoardOption.CAN_UNDO_MOVES | Enums.BoardOption.CAN_FORCE_MOVES
)
```

**Board options (flags):**
```python
Enums.BoardOption.CAN_FORCE_MOVES      # Allow forcing moves
Enums.BoardOption.CAN_UNDO_MOVES       # Allow undo
Enums.BoardOption.DB_RECORD_DISABLED   # Disable DB recording
Enums.BoardOption.EVALUATION_DISABLED  # Disable evaluation
Enums.BoardOption.PARTIAL_PGN_DISABLED # Disable partial PGN
Enums.BoardOption.RESUME_DISABLED      # Disable resume
```

You can combine flags using the `|` operator:
```python
flags = Enums.BoardOption.CAN_UNDO_MOVES | Enums.BoardOption.CAN_FORCE_MOVES
```

#### `Centaur.play_computer_move(uci_move: str)`
Executes a computer move.

```python
Centaur.play_computer_move("e2e4")
```

#### `Centaur.hint()`
Shows a hint using the chess engine.

```python
Centaur.hint()
```

#### `Centaur.set_main_chess_engine(engine_name: str)`
Sets the main chess engine.

```python
Centaur.set_main_chess_engine("ct800")     # CT800 engine
Centaur.set_main_chess_engine("stockfish") # Stockfish
```

#### `Centaur.configure_main_chess_engine(options: dict)`
Configures engine options.

```python
Centaur.configure_main_chess_engine({"UCI_Elo": 1800})
```

#### `Centaur.request_chess_engine_move(callback, time: int = 5)`
Requests the engine to calculate a move (asynchronous).

```python
def on_move_calculated(result: TPlayResult):
    Centaur.play_computer_move(str(result.move))

Centaur.request_chess_engine_move(on_move_calculated, time=3)
```

#### `Centaur.request_chess_engine_evaluation(callback, time: int = 2, multipv: int = 1)`
Requests position evaluation (asynchronous).

```python
def on_evaluation(results: Tuple[TAnalyseResult, ...]):
    result = results[0]
    score = result.score.pov(chess.WHITE)
    print(f"Evaluation: {score}")

Centaur.request_chess_engine_evaluation(on_evaluation, time=2)
```

---

### Utilities

#### `Centaur.reverse_board(value: bool = True)`
Reverses the board display.

```python
Centaur.reverse_board()  # Reverse
Centaur.reverse_board(False)  # Normal
```

#### `Centaur.delayed_call(call: callable, delay: int)`
Executes a function after a delay (milliseconds).

```python
def my_function():
    print("Executed after 2 seconds")

Centaur.delayed_call(my_function, 2000)
```

#### `self.chessboard`
Accesses the current chess board (`chess.Board` object).

```python
# View current turn
turn = self.chessboard.turn

# View legal moves
legal_moves = list(self.chessboard.legal_moves)

# View current FEN
fen = self.chessboard.fen()

# Check game over
is_over = self.chessboard.is_game_over()
```

---

## Complete Examples

### Example 1: Simple Bot with Random Moves

```python
import chess, random
from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts
from typing import Optional

HUMAN_COLOR = chess.WHITE

class RandomBot(Plugin):

    def key_callback(self, key: Enums.Btn):
        if key == Enums.Btn.HELP:
            Centaur.hint()
            return True
        return False

    def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
        if event == Enums.Event.QUIT:
            self.stop()

        if event == Enums.Event.PLAY:
            turn = self.chessboard.turn
            current_player = "You" if turn == chess.WHITE else "Random bot"
            Centaur.header(f"{current_player} {'W' if turn == chess.WHITE else 'B'}")

            if turn == (not HUMAN_COLOR):
                # Choose random move
                uci_move = str(random.choice(list(self.chessboard.legal_moves)))
                Centaur.play_computer_move(uci_move)

    def on_start_callback(self, key: Enums.Btn) -> bool:
        Centaur.start_game(
            white="You",
            black="Random bot",
            event="Random Bot Event",
            flags=Enums.BoardOption.CAN_UNDO_MOVES
        )
        return True

    def splash_screen(self) -> bool:
        Centaur.clear_screen()
        Centaur.print("RANDOM", row=2)
        Centaur.print("BOT", font=fonts.DIGITAL_FONT, row=4)
        Centaur.print("Push PLAY", row=8)
        Centaur.print("to start")
        return True
```

---

### Example 2: Educational Game - Squiz (Find the Square)

```python
import chess, random
from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts

QUESTIONS_COUNT = 10

class Squiz(Plugin):

    def __init__(self, id: str):
        super().__init__(id)
        self.initialize()

    def initialize(self):
        self._qindex = 0
        self._bonus = QUESTIONS_COUNT * 3
        Centaur.pause_plugin()

    def game_over(self):
        Centaur.clear_screen()
        Centaur.print("GAME OVER", row=2, font=fonts.DIGITAL_FONT)

        score = int(self._bonus * 100 / (QUESTIONS_COUNT * 3))
        Centaur.print(f"SCORE: {score}%", row=5, font=fonts.DIGITAL_FONT)
        Centaur.print("Press PLAY to retry!", row=8)

        self.initialize()

    def generate_question(self):
        self._qindex += 1

        if self._qindex == QUESTIONS_COUNT + 1:
            self.game_over()
            return

        Centaur.clear_screen()

        # Generate random square
        self._random_square = chess.square_name(random.randint(0, 63))

        Centaur.print(f"Question {self._qindex}", row=2)
        Centaur.print("Place a piece on", row=5)
        Centaur.print(self._random_square, font=fonts.DIGITAL_FONT)

    def key_callback(self, key: Enums.Btn):
        if key == Enums.Btn.HELP:
            Centaur.sound(Enums.Sound.TAKEBACK_MOVE)
            Centaur.flash(self._random_square)

    def field_callback(self, square: str, field_action: Enums.PieceAction, web_move: bool):
        if field_action == Enums.PieceAction.PLACE:
            Centaur.flash(square)

            if self._random_square == square:
                Centaur.sound(Enums.Sound.CORRECT_MOVE)
                self.generate_question()
            else:
                Centaur.sound(Enums.Sound.WRONG_MOVE)
                Centaur.print("WRONG!", row=11)
                self._bonus -= 1

                if self._bonus == 0:
                    self.game_over()

    def on_start_callback(self, key: Enums.Btn) -> bool:
        Centaur.sound(Enums.Sound.COMPUTER_MOVE)
        self.generate_question()
        return True

    def splash_screen(self) -> bool:
        Centaur.clear_screen()
        Centaur.print("SQUIZ", font=fonts.DIGITAL_FONT, row=2)
        Centaur.print("Push PLAY to start!", row=5)
        return True
```

---

### Example 3: Adaptive Bot with Chess Engine

```python
import chess
from DGTCentaurMods.classes.Plugin import Plugin, Centaur, TPlayResult, TAnalyseResult
from DGTCentaurMods.consts import Enums, fonts
from typing import Optional, Tuple

class AdaptiveBot(Plugin):

    def __init__(self, id: str):
        super().__init__(id)
        self.HUMAN_COLOR = chess.WHITE
        self._elo = 1500

    def start(self):
        super().start()
        Centaur.set_main_chess_engine("stockfish")
        self._adjust_engine_level(1500)

    def _adjust_engine_level(self, elo: int):
        if self._elo != elo:
            Centaur.configure_main_chess_engine({"UCI_Elo": elo})
            self._elo = elo

    def _evaluate_and_adjust(self):
        def on_evaluation(results: Tuple[TAnalyseResult, ...]):
            result = results[0]
            score = result.score.pov(self.HUMAN_COLOR)

            # Get evaluation in centipawns
            cp = score.score()
            if cp:
                # Adjust level based on evaluation
                if cp > 200:  # Player winning
                    new_elo = min(2400, self._elo + 100)
                elif cp < -200:  # Player losing
                    new_elo = max(1000, self._elo - 100)
                else:
                    new_elo = 1500

                self._adjust_engine_level(new_elo)

        Centaur.request_chess_engine_evaluation(on_evaluation, time=2)

    def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
        if event == Enums.Event.QUIT:
            self.stop()

        if event == Enums.Event.TERMINATION:
            if outcome.winner == self.HUMAN_COLOR:
                Centaur.sound(Enums.Sound.VICTORY)
            else:
                Centaur.sound(Enums.Sound.GAME_LOST)

        if event == Enums.Event.PLAY:
            turn = self.chessboard.turn
            current_player = "You" if turn == self.HUMAN_COLOR else "Bot"
            Centaur.header(f"{current_player} {'W' if turn == chess.WHITE else 'B'}")

            if turn == (not self.HUMAN_COLOR):
                def on_move(result: TPlayResult):
                    Centaur.play_computer_move(str(result.move))
                    self._evaluate_and_adjust()

                Centaur.request_chess_engine_move(on_move, time=3)

    def move_callback(self, uci_move: str, san_move: str, color: chess.Color, field_index: chess.Square):
        if color == self.HUMAN_COLOR:
            self._evaluate_and_adjust()
        return True

    def on_start_callback(self, key: Enums.Btn) -> bool:
        if key == Enums.Btn.UP:
            self.HUMAN_COLOR = chess.WHITE
        elif key == Enums.Btn.DOWN:
            self.HUMAN_COLOR = chess.BLACK
            Centaur.reverse_board()
        else:
            return False

        Centaur.start_game(
            white="You" if self.HUMAN_COLOR == chess.WHITE else "Adaptive Bot",
            black="Adaptive Bot" if self.HUMAN_COLOR == chess.WHITE else "You",
            event="Adaptive Bot Challenge",
            flags=Enums.BoardOption.CAN_UNDO_MOVES | Enums.BoardOption.CAN_FORCE_MOVES
        )
        return True

    def splash_screen(self) -> bool:
        Centaur.clear_screen()
        Centaur.print("ADAPTIVE BOT", font=fonts.DIGITAL_FONT, row=2)
        Centaur.print_button_label(Enums.Btn.UP, row=6, x=6, text="Play white")
        Centaur.print_button_label(Enums.Btn.DOWN, row=7, x=6, text="Play black")
        return True
```

---

## Best Practices

### 1. Naming Convention
- **File and class must match**: `MyPlugin.py` → `class MyPlugin(Plugin):`
- Use CamelCase for class names
- Descriptive names that indicate functionality

### 2. Resource Management
- Always call `super().start()` and `super().stop()`
- Clean up resources in `stop()` (chess engines, timers, etc.)
- Don't maintain state between different plugin instances

### 3. Event Handling
```python
def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
    # Always handle QUIT
    if event == Enums.Event.QUIT:
        self.stop()

    # Handle TERMINATION for game end
    if event == Enums.Event.TERMINATION:
        # Show result
        pass
```

### 4. Asynchronous Callbacks
When using chess engines, callbacks are asynchronous:

```python
def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
    if event == Enums.Event.PLAY:
        if self.chessboard.turn == computer_turn:
            # Callback will be invoked when engine finishes
            def on_move_ready(result: TPlayResult):
                Centaur.play_computer_move(str(result.move))

            Centaur.request_chess_engine_move(on_move_ready, time=5)
```

### 5. User Feedback
- Use appropriate sounds for each action
- Update display regularly with `Centaur.header()`
- Light up LEDs to guide the user
- Provide visual and audio feedback

### 6. License
Always include the GPL v3 license header at the beginning of the file:

```python
# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
# [...]
```

### 7. Testing
- Test all callbacks
- Verify behavior with illegal moves
- Test BACK button in different states
- Verify resource cleanup on exit

### 8. Documentation
- Document the plugin's purpose in the class docstring
- Comment complex logic
- Include usage examples if the plugin has special configuration

---

## Testing Your Plugin

A comprehensive test script is provided to validate your plugin follows all required conventions and best practices.

### Test Script: `test_plugins.py`

The test script checks for:
- ✓ Correct file extension (.py)
- ✓ GPL license header presence
- ✓ Valid Python syntax
- ✓ Required imports (chess, Plugin, Centaur, Enums)
- ✓ Class name matches filename
- ✓ Class inherits from Plugin
- ✓ Proper __init__ method with super() call
- ✓ Callback methods implementation
- ✓ Class docstring presence

### Running the Tests

#### Test All Plugins

To test all plugins in the plugins directory:

```bash
cd DGTCentaurMods/opt/DGTCentaurMods/plugins/
python test_plugins.py
```

#### Test a Specific Plugin

To test a single plugin:

```bash
python test_plugins.py --plugin MyPlugin.py
```

#### Test Multiple Specific Plugins

```bash
python test_plugins.py --plugin RandomBot.py --plugin Squiz.py
```

#### Test Plugins in a Different Directory

```bash
python test_plugins.py --dir /path/to/plugins
```

### Example Output

```
============================================================
Validating plugin: RandomBot
============================================================

────────────────────────────────────────────────────────────

✓ PASSED CHECKS:
  ✓ File extension is correct (.py)
  ✓ GPL license header found
  ✓ Python syntax is valid
  ✓ Required import found: chess
  ✓ Required import found: Plugin
  ✓ Required import found: Centaur
  ✓ Required import found: Enums
  ✓ Class name matches filename: RandomBot
  ✓ Class inherits from Plugin
  ✓ Callbacks implemented: key_callback, event_callback, on_start_callback, splash_screen

⚠ WARNINGS:
  ⚠ No __init__ method found

────────────────────────────────────────────────────────────

✓ Plugin 'RandomBot' is VALID!
  (1 warning(s))

============================================================
SUMMARY
============================================================

Total plugins tested: 1
✓ Valid: 1
✗ Invalid: 0
```

### Interpreting Results

**✓ PASSED CHECKS**: All validations that passed successfully

**⚠ WARNINGS**: Non-critical issues that should be addressed but don't prevent the plugin from working

**✗ ERRORS**: Critical issues that must be fixed for the plugin to work properly

### Recommended Workflow

1. **Develop your plugin** following the examples and best practices
2. **Run the test** before submitting or deploying
3. **Fix any errors** reported by the test
4. **Address warnings** to improve code quality
5. **Test manually** on the DGT Centaur board

### Continuous Testing

It's recommended to run the test suite:
- After creating a new plugin
- After modifying existing plugins
- Before committing changes to version control
- As part of your CI/CD pipeline (if applicable)

---

## Additional Resources

- **python-chess**: https://python-chess.readthedocs.io/
- **DGTCentaurMods Repository**: https://github.com/Alistair-Crompton/DGTCentaurMods
- **Existing Plugins**: See examples in the `plugins/` directory

---

## Troubleshooting

### Plugin doesn't appear in menu
- Verify that the file name matches the class
- Ensure the class inherits from `Plugin`
- Check for syntax errors in the code

### LEDs don't light up
- Use `Centaur.flash(square)` or `Centaur.light_move(uci_move)`
- Turn off LEDs with `Centaur.lights_off()` when necessary

### Chess engine doesn't work
- Initialize with `Centaur.set_main_chess_engine(engine_name)`
- Verify the engine is available on the system
- Use callbacks correctly for asynchronous operations

### Screen doesn't update
- Call `Centaur.clear_screen()` before drawing
- Use `row` to position text correctly
- Verify text is not too long

---

Happy plugin development! 🎉
