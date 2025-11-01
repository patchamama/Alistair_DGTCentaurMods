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

from DGTCentaurMods.classes.Plugin import Plugin, Centaur, TPlayResult
from DGTCentaurMods.consts import Enums, fonts

from typing import Optional

HUMAN_COLOR = chess.WHITE

class HandBrain(Plugin):
    """
    Hand and Brain chess variant.

    In this mode:
    - The "Brain" (chess engine) decides WHAT TYPE of piece to move (pawn, knight, etc.)
    - The "Hand" (human player) decides WHERE to move that piece
    - Opponent is a chess engine

    This creates an interesting collaboration where the engine provides strategic
    direction and the human executes tactically.
    """

    def __init__(self, id: str):
        super().__init__(id)
        self._waiting_for_hand = False
        self._brain_piece_type = None
        self._valid_moves = []

    def start(self):
        super().start()

        # Set up the chess engine as opponent
        Centaur.set_main_chess_engine("stockfish")
        Centaur.configure_main_chess_engine({"UCI_Elo": 1800})

    def key_callback(self, key: Enums.Btn):
        if key == Enums.Btn.HELP:
            if self._waiting_for_hand and self._valid_moves:
                # Show all valid moves for the piece type
                for move_uci in self._valid_moves:
                    Centaur.light_move(move_uci, web=False)
                Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            return True

        return False

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

                Centaur.request_chess_engine_move(on_opponent_move, time=3)

    def _ask_brain(self):
        """Ask the Brain (engine) what piece type to move."""

        def on_brain_decision(result: TPlayResult):
            # Brain has decided which move it wants
            brain_move = result.move

            # Get the piece type from the move
            from_square = brain_move.from_square
            piece = self.chessboard.piece_at(from_square)

            if piece:
                self._brain_piece_type = piece.piece_type
                piece_name = chess.piece_name(self._brain_piece_type).upper()

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
                Centaur.print("HELP: Show moves", row=10)

                # Light up all destination squares for this piece type
                self._highlight_valid_moves()

                self._waiting_for_hand = True

        # Request the Brain's decision
        Centaur.print("Brain thinking...", row=5)
        Centaur.request_chess_engine_move(on_brain_decision, time=2)

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
            self._waiting_for_hand = False
            self._brain_piece_type = None
            self._valid_moves = []
            Centaur.sound(Enums.Sound.CORRECT_MOVE)
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
        """Start the game when PLAY is pressed."""

        if key == Enums.Btn.PLAY:
            Centaur.start_game(
                white="Hand+Brain",
                black="Engine",
                event="Hand and Brain Challenge",
                flags=Enums.BoardOption.CAN_UNDO_MOVES
            )
            return True

        return False

    def splash_screen(self) -> bool:
        """Show initial splash screen."""
        Centaur.clear_screen()

        Centaur.print("HAND", font=fonts.DIGITAL_FONT, row=2)
        Centaur.print("& BRAIN", font=fonts.DIGITAL_FONT, row=4)

        Centaur.print("Brain: Engine", row=7)
        Centaur.print("decides piece")

        Centaur.print("Hand: You", row=10)
        Centaur.print("choose move")

        Centaur.print("Push PLAY", row=13)
        Centaur.print("to start!")

        return True
