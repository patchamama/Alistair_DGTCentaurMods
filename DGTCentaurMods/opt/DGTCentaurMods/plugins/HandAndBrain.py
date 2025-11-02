# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

import chess

from DGTCentaurMods.classes.Plugin import Plugin, Centaur, TPlayResult, TAnalyseResult
from DGTCentaurMods.consts import Enums, fonts

from typing import Optional, Tuple, Dict

HUMAN_COLOR = chess.WHITE

# Difficulty levels with ELO ratings
DIFFICULTIES = {
    "Easy": 1200,
    "Medium": 1600,
    "Hard": 2000,
    "Expert": 2400
}

class HandBrain(Plugin):
    """
    Advanced Hand and Brain chess variant with multiple features.

    Game Modes:
    - Normal: Brain decides piece type, Hand chooses move
    - Training: Shows the Brain's suggested best move as a hint

    Features:
    - Configurable difficulty level (Easy to Expert)
    - Multiple chess engine selection for Brain
    - Statistics tracking (which pieces Brain prefers)
    - Training mode with hints
    - Visual feedback with LED highlighting

    In this mode:
    - The "Brain" (chess engine) decides WHAT TYPE of piece to move
    - The "Hand" (human player) decides WHERE to move that piece
    - Opponent is a chess engine
    """

    def __init__(self, id: str):
        super().__init__(id)

        # Game state
        self._waiting_for_hand = False
        self._brain_piece_type = None
        self._valid_moves = []
        self._brain_suggested_move = None
        self._in_config = True

        # Configuration
        self._difficulty_index = 1  # Default: Medium
        self._difficulty_names = list(DIFFICULTIES.keys())
        self._brain_engine_index = 0
        self._available_engines = []
        self._training_mode = False
        self._config_option = 0  # 0=difficulty, 1=engine, 2=training, 3=start

        # Statistics
        self._piece_stats: Dict[int, int] = {
            chess.PAWN: 0,
            chess.KNIGHT: 0,
            chess.BISHOP: 0,
            chess.ROOK: 0,
            chess.QUEEN: 0,
            chess.KING: 0
        }
        self._total_moves = 0

    def start(self):
        super().start()

        # Get available engines
        engines = Centaur.get_chess_engines()
        self._available_engines = [e['name'] for e in engines]

        if not self._available_engines:
            self._available_engines = ["stockfish"]

    def stop(self):
        # Show final statistics before stopping
        if self._total_moves > 0:
            self._show_statistics()
            Centaur.delayed_call(lambda: super(HandBrain, self).stop(), 5000)
        else:
            super().stop()

    def _show_statistics(self):
        """Display final statistics about piece choices."""
        Centaur.clear_screen()

        Centaur.print("STATISTICS", font=fonts.DIGITAL_FONT, row=1)
        Centaur.print(f"Total moves: {self._total_moves}", row=3)

        row = 5
        piece_names = {
            chess.PAWN: "Pawns",
            chess.KNIGHT: "Knights",
            chess.BISHOP: "Bishops",
            chess.ROOK: "Rooks",
            chess.QUEEN: "Queens",
            chess.KING: "Kings"
        }

        # Sort by frequency
        sorted_pieces = sorted(
            self._piece_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for piece_type, count in sorted_pieces:
            if count > 0:
                percentage = int(count * 100 / self._total_moves)
                Centaur.print(
                    f"{piece_names[piece_type]}: {count} ({percentage}%)",
                    row=row,
                    font=fonts.SMALL_MAIN_FONT
                )
                row += 0.8

    def key_callback(self, key: Enums.Btn):
        # Configuration mode
        if self._in_config:
            return self._handle_config_keys(key)

        # Game mode
        if key == Enums.Btn.HELP:
            if self._waiting_for_hand:
                if self._training_mode and self._brain_suggested_move:
                    # Show the Brain's suggested move
                    Centaur.light_move(str(self._brain_suggested_move), web=True)
                    Centaur.sound(Enums.Sound.VERY_GOOD_MOVE)
                elif self._valid_moves:
                    # Show all valid moves for the piece type
                    Centaur.light_moves(tuple(self._valid_moves), web=True)
                    Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            return True

        return False

    def _handle_config_keys(self, key: Enums.Btn) -> bool:
        """Handle key presses during configuration."""

        if key == Enums.Btn.UP:
            self._config_option = (self._config_option - 1) % 4
            self._show_config()
            Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            return True

        elif key == Enums.Btn.DOWN:
            self._config_option = (self._config_option + 1) % 4
            self._show_config()
            Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            return True

        elif key == Enums.Btn.TICK:
            # Modify selected option
            if self._config_option == 0:  # Difficulty
                self._difficulty_index = (self._difficulty_index + 1) % len(self._difficulty_names)
            elif self._config_option == 1:  # Engine
                self._brain_engine_index = (self._brain_engine_index + 1) % len(self._available_engines)
            elif self._config_option == 2:  # Training mode
                self._training_mode = not self._training_mode

            self._show_config()
            Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            return True

        return False

    def _show_config(self):
        """Display configuration screen."""
        Centaur.clear_screen()

        Centaur.print("HAND+BRAIN", font=fonts.DIGITAL_FONT, row=1)
        Centaur.print("CONFIG", font=fonts.MEDIUM_MAIN_FONT, row=3)

        # Difficulty
        prefix = ">" if self._config_option == 0 else " "
        difficulty_name = self._difficulty_names[self._difficulty_index]
        elo = DIFFICULTIES[difficulty_name]
        Centaur.print(f"{prefix}Level: {difficulty_name} ({elo})", row=5)

        # Engine
        prefix = ">" if self._config_option == 1 else " "
        engine_name = self._available_engines[self._brain_engine_index]
        Centaur.print(f"{prefix}Brain: {engine_name}", row=6.5)

        # Training mode
        prefix = ">" if self._config_option == 2 else " "
        mode_text = "ON" if self._training_mode else "OFF"
        Centaur.print(f"{prefix}Training: {mode_text}", row=8)

        # Start
        prefix = ">" if self._config_option == 3 else " "
        Centaur.print(f"{prefix}START GAME", row=9.5, font=fonts.MEDIUM_MAIN_FONT)

        Centaur.print("TICK: Change", row=12, font=fonts.SMALL_MAIN_FONT)
        Centaur.print("UP/DOWN: Navigate", row=13, font=fonts.SMALL_MAIN_FONT)

    def event_callback(self, event: Enums.Event, outcome: Optional[chess.Outcome]):
        if event == Enums.Event.QUIT:
            self.stop()

        if event == Enums.Event.TERMINATION:
            if outcome.winner == HUMAN_COLOR:
                Centaur.sound(Enums.Sound.VICTORY)
            else:
                Centaur.sound(Enums.Sound.GAME_LOST)

        if event == Enums.Event.PLAY:
            turn = self.chessboard.turn

            if turn == HUMAN_COLOR:
                # Human's turn: Brain decides piece type
                current_player = "Hand+Brain"
                Centaur.header(
                    text=f"{current_player} W",
                    web_text="turn → Hand+Brain (WHITE)"
                )

                # Ask the Brain (engine) what to play
                self._ask_brain()
            else:
                # Opponent's turn
                Centaur.header(
                    text="Engine B",
                    web_text="turn → Engine (BLACK)"
                )

                def on_opponent_move(result: TPlayResult):
                    Centaur.play_computer_move(str(result.move))

                difficulty_name = self._difficulty_names[self._difficulty_index]
                opponent_elo = DIFFICULTIES[difficulty_name]
                Centaur.request_chess_engine_move(on_opponent_move, time=3)

    def _ask_brain(self):
        """Ask the Brain (engine) what piece type to move."""

        def on_brain_decision(result: TPlayResult):
            # Brain has decided which move it wants
            brain_move = result.move
            self._brain_suggested_move = brain_move

            # Get the piece type from the move
            from_square = brain_move.from_square
            piece = self.chessboard.piece_at(from_square)

            if piece:
                self._brain_piece_type = piece.piece_type
                piece_name = chess.piece_name(self._brain_piece_type).upper()

                # Update statistics
                self._piece_stats[self._brain_piece_type] += 1
                self._total_moves += 1

                # Find all legal moves with this piece type
                self._valid_moves = []
                for move in self.chessboard.legal_moves:
                    piece_at_from = self.chessboard.piece_at(move.from_square)
                    if piece_at_from and piece_at_from.piece_type == self._brain_piece_type:
                        self._valid_moves.append(str(move))

                # Display instruction to player
                Centaur.clear_screen()
                Centaur.print("HAND+BRAIN", font=fonts.DIGITAL_FONT, row=2)
                Centaur.print(f"Brain says:", row=5)
                Centaur.print(f"Move a {piece_name}", font=fonts.MEDIUM_MAIN_FONT, row=6)
                Centaur.print(f"({len(self._valid_moves)} options)", row=8)

                if self._training_mode:
                    Centaur.print("HELP: Best move", row=10, font=fonts.SMALL_MAIN_FONT)
                else:
                    Centaur.print("HELP: Show moves", row=10, font=fonts.SMALL_MAIN_FONT)

                # Light up all destination squares for this piece type
                self._highlight_valid_moves()

                self._waiting_for_hand = True

        # Request the Brain's decision
        Centaur.print("Brain thinking...", row=5)

        # Use the selected brain engine
        brain_engine_name = self._available_engines[self._brain_engine_index]
        brain_engine = Centaur.add_chess_engine(brain_engine_name)

        difficulty_name = self._difficulty_names[self._difficulty_index]
        brain_elo = DIFFICULTIES[difficulty_name]

        # Configure brain engine difficulty
        Centaur.configure_chess_engine(brain_engine_name.upper(), "UCI_Elo")

        Centaur.request_chess_engine_move(
            on_brain_decision,
            time=2,
            engine_name=brain_engine_name.upper()
        )

    def _highlight_valid_moves(self):
        """Light up all valid destination squares for the piece type."""
        if not self._valid_moves:
            return

        # Light up all the moves
        Centaur.light_moves(tuple(self._valid_moves), web=True)

    def move_callback(self, uci_move: str, san_move: str, color: chess.Color, field_index: chess.Square):
        """Validate that the Hand is moving the correct piece type."""

        if color != HUMAN_COLOR:
            return True

        if not self._waiting_for_hand:
            # Normal move validation
            return True

        # Check if the move uses the correct piece type
        move = chess.Move.from_uci(uci_move)
        piece = self.chessboard.piece_at(move.from_square)

        if piece and piece.piece_type == self._brain_piece_type:
            # Correct piece type!
            Centaur.lights_off()

            # Check if it's the best move in training mode
            if self._training_mode and self._brain_suggested_move:
                if str(move) == str(self._brain_suggested_move):
                    Centaur.sound(Enums.Sound.VERY_GOOD_MOVE)
                    Centaur.print("Best move!", row=12, font=fonts.SMALL_MAIN_FONT)
                else:
                    Centaur.sound(Enums.Sound.CORRECT_MOVE)
                    Centaur.print("Good move!", row=12, font=fonts.SMALL_MAIN_FONT)
            else:
                Centaur.sound(Enums.Sound.CORRECT_MOVE)

            self._waiting_for_hand = False
            self._brain_piece_type = None
            self._valid_moves = []
            self._brain_suggested_move = None
            return True
        else:
            # Wrong piece type
            Centaur.sound(Enums.Sound.WRONG_MOVE)

            # Show feedback
            piece_name = chess.piece_name(self._brain_piece_type).upper() if self._brain_piece_type else "???"
            Centaur.print(f"Must move {piece_name}!", row=12, font=fonts.SMALL_MAIN_FONT)

            # Re-highlight valid moves
            Centaur.delayed_call(lambda: self._highlight_valid_moves(), 1000)

            return False

    def on_start_callback(self, key: Enums.Btn) -> bool:
        """Handle configuration navigation and game start."""

        if self._in_config:
            if self._config_option == 3 and key == Enums.Btn.PLAY:
                # Start the game
                self._in_config = False

                # Set up engines with selected difficulty
                difficulty_name = self._difficulty_names[self._difficulty_index]
                opponent_elo = DIFFICULTIES[difficulty_name]

                Centaur.set_main_chess_engine("stockfish")
                Centaur.configure_main_chess_engine({"UCI_Elo": opponent_elo})

                Centaur.start_game(
                    white="Hand+Brain",
                    black="Engine",
                    event=f"Hand+Brain {difficulty_name}",
                    flags=Enums.BoardOption.CAN_UNDO_MOVES
                )
                return True

        return False

    def splash_screen(self) -> bool:
        """Show configuration screen instead of simple splash."""
        self._show_config()
        return True
