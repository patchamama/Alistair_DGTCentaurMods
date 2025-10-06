import chess
import time
from classes.Plugin import Plugin
from classes.ChessEngine import ChessEngine
from consts.Enums import Key

class HandAndBrain(Plugin):
    """
    Plugin for the "Hand and Brain" chess variant with engine integration.
    - The user selects an engine and ELO level to act as the "Hand".
    - The "Hand" determines the piece type to be moved.
    - The user, as the "Brain", chooses a legal move with that piece type.
    - The opponent is the default Stockfish engine.
    """
    def __init__(self, centaur_board, centaur_screen, dal, config):
        super().__init__(centaur_board, centaur_screen, dal, config)
        self.name = "Hand+Brain"
        self.description = "Engine Hand, Human Brain."
        
        self.board = None
        self.hand_engine = None
        self.opponent_engine = None
        
        self.running = False
        self.is_configuring = False
        
        # Configuration state
        self.available_engines = ChessEngine.get_engine_names()
        self.selected_engine_index = 0
        self.selected_elo = 1500
        self.config_options = ["Engine", "ELO", "Start"]
        self.selected_config_index = 0

    def on_start_callback(self):
        """Called when the plugin is selected from the menu."""
        self.is_configuring = True
        self.running = False
        self.display_configuration()

    def key_callback(self, key):
        """Handles key presses for configuration and in-game actions."""
        if self.is_configuring:
            self.handle_config_keys(key)
        elif self.running:
            if key == Key.BACK:
                self.undo_callback()

    def undo_callback(self):
        """Handles the undo/takeback action."""
        if self.board and len(self.board.move_stack) >= 2:
            self.centaur_screen.write_text("Undoing move...", 4, 0)
            self.board.pop() # Opponent's move
            self.board.pop() # Player's move
            self.centaur_screen.show_board(self.board)
            self.centaur_board.set_board_from_fen(self.board.fen())

    def event_callback(self, event):
        """Handles system events (not used in this plugin)."""
        pass

    def stop(self):
        """Stops the plugin and cleans up resources."""
        self.running = False
        self.is_configuring = False
        if self.hand_engine:
            self.hand_engine.quit()
        if self.opponent_engine:
            self.opponent_engine.quit()

    def display_configuration(self):
        """Displays the configuration screen on the e-paper display."""
        self.centaur_screen.clear()
        self.centaur_screen.write_text(self.name, 0, 10, center=True)
        
        for i, option in enumerate(self.config_options):
            prefix = "> " if i == self.selected_config_index else "  "
            if option == "Engine":
                text = f"{prefix}Hand Engine: {self.available_engines[self.selected_engine_index]}"
            elif option == "ELO":
                text = f"{prefix}Hand ELO: {self.selected_elo}"
            else: # Start
                text = f"{prefix}{option}"
            self.centaur_screen.write_text(text, i + 2, 10)

    def handle_config_keys(self, key):
        """Logic to handle key presses during configuration."""
        option = self.config_options[self.selected_config_index]
        
        if key == Key.UP:
            self.selected_config_index = (self.selected_config_index - 1) % len(self.config_options)
        elif key == Key.DOWN:
            self.selected_config_index = (self.selected_config_index + 1) % len(self.config_options)
        elif key == Key.LEFT:
            if option == "Engine":
                self.selected_engine_index = (self.selected_engine_index - 1) % len(self.available_engines)
            elif option == "ELO":
                self.selected_elo = max(100, self.selected_elo - 100)
        elif key == Key.RIGHT:
            if option == "Engine":
                self.selected_engine_index = (self.selected_engine_index + 1) % len(self.available_engines)
            elif option == "ELO":
                self.selected_elo = min(3200, self.selected_elo + 100)
        elif key == Key.OK:
            if option == "Start":
                self.is_configuring = False
                self.start() # Transition to the main game
        
        if self.is_configuring:
            self.display_configuration()

    def start(self):
        """Main entry point for the plugin's logic, called after configuration."""
        self.running = True
        
        # --- Engine Setup ---
        hand_engine_name = self.available_engines[self.selected_engine_index]
        self.hand_engine = ChessEngine(hand_engine_name)
        self.hand_engine.set_elo(self.selected_elo)

        self.opponent_engine = ChessEngine("stockfish") # Default opponent
        self.opponent_engine.set_elo(2000) # Set a fixed ELO for the opponent

        # --- Board Setup ---
        self.centaur_screen.clear()
        self.centaur_screen.show_logo()
        self.centaur_screen.write_text(f"Hand: {hand_engine_name} ({self.selected_elo})", 2, 10)
        self.centaur_screen.write_text("Opponent: Stockfish (2000)", 3, 10)
        time.sleep(2)

        try:
            self.board = chess.Board(self.centaur_board.get_fen())
        except ValueError:
            self.centaur_screen.write_text("Invalid board setup", 4, 0)
            self.running = False
            return

        # --- Main Game Loop ---
        while self.running and not self.board.is_game_over(claim_draw=True):
            self.centaur_screen.show_board(self.board)
            
            if self.board.turn == chess.WHITE: # Assuming player is White
                self.player_turn()
            else:
                self.opponent_turn()

        if self.running: # Check if loop was exited gracefully
            result = self.board.result(claim_draw=True)
            self.centaur_screen.write_text(f"Game Over: {result}", 4, 0)
        
        self.stop()

    def player_turn(self):
        """Handles the Hand+Brain player's turn."""
        # 1. "HAND" PHASE: Engine determines the piece type
        self.centaur_screen.write_text("Hand is thinking...", 4, 0)
        best_move = self.hand_engine.get_best_move(self.board.fen())
        piece_to_announce = self.board.piece_at(best_move.from_square).piece_type
        piece_name = chess.piece_name(piece_to_announce).capitalize()
        self.centaur_screen.write_text(f"White: Move {piece_name}", 4, 0)

        # 2. "BRAIN" PHASE: Show possible moves and wait for user
        squares_to_light = []
        for move in self.board.legal_moves:
            if self.board.piece_at(move.from_square).piece_type == piece_to_announce:
                squares_to_light.append(chess.square_name(move.to_square))
        
        self.centaur_board.leds_on(list(set(squares_to_light)))

        # 3. WAIT FOR PLAYER'S MOVE
        valid_move_made = False
        while not valid_move_made:
            user_move_uci = self.centaur_board.get_user_move()
            user_move = chess.Move.from_uci(user_move_uci)

            if user_move in self.board.legal_moves and self.board.piece_at(user_move.from_square).piece_type == piece_to_announce:
                self.board.push(user_move)
                valid_move_made = True
            else:
                self.centaur_board.show_leds_for_move(user_move_uci) # Flash error
                time.sleep(0.5)
                self.centaur_board.leds_off()
                self.centaur_board.leds_on(list(set(squares_to_light))) # Re-light options

        self.centaur_board.leds_off()

    def opponent_turn(self):
        """Handles the opponent engine's turn."""
        self.centaur_screen.write_text("Stockfish is thinking...", 4, 0)
        best_move = self.opponent_engine.get_best_move(self.board.fen())
        
        self.board.push(best_move)
        self.centaur_screen.show_board(self.board)
        self.centaur_screen.write_text(f"Black plays {best_move.uci()}", 4, 0)
        
        # Show move on board and wait for user to physically make it
        self.centaur_board.show_leds_for_move(best_move.uci())
        self.centaur_board.wait_for_move(best_move.uci())
        self.centaur_board.leds_off()