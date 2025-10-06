# Documentación de la API de WebSockets del DGTCentaur

La comunicación en tiempo real entre el frontend y el backend se realiza a través de WebSockets, basado en eventos sobre una conexión persistente.

## A. Eventos que el Servidor Escucha (Cliente -> Servidor)

Estos son los mensajes que el cliente puede enviar al servidor.

### **Canal Principal: `'request'`**

Usado para solicitar datos o ejecutar comandos en el sistema.

| Acción                        | Payload (Ejemplo en JSON)                                                                   | Descripción                                                                                                                                                           |
| :---------------------------- | :------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pedir Menú Web**            | `{"web_menu": true}`                                                                      | Solicita la estructura completa de menús para la interfaz web. El servidor responde con un evento `update_menu`.                                                    |
| **Pedir Datos Específicos**   | `{"data": "previous_games"}` <br> `{"data": "sounds_settings"}`                     | Pide un conjunto de datos concreto. Valores conocidos: `previous_games`, `sounds_settings`, `game_moves`.                                                              |
| **Ejecutar Módulo/Comando**   | `{"execute": "uci_module.py white stockfish \"1400\""}`                               | Ejecuta un módulo del sistema (`.py` de la carpeta `modules`) con argumentos. Se usa para iniciar partidas, etc.                                                    |
| **Ejecutar Plugin**           | `{"plugin_execute": "RandomBot"}`                                                       | Ejecuta un plugin de la carpeta `plugins` por su nombre de clase.                                                                                                     |
| **Ejecutar Script Vivo**      | `{"live_script": "print('Hola')"}`                                                     | Ejecuta un fragmento de código Python directamente en el servidor.                                                                                                    |
| **Simular Botón Físico**      | `{"web_button": "OK"}`                                                                  | Simula la pulsación de un botón físico del tablero. Valores: `OK`, `BACK`, `UP`, `DOWN`, `PLAY`.                                                                       |
| **Enviar Jugada (source/target)** | `{"web_move": {"source": "e2", "target": "e4"}}`                                     | Informa al servidor de una jugada realizada en la interfaz web para su validación. Es el método preferido para enviar jugadas desde una UI.                           |
| **Comandos de Sistema**       | `{"sys": "restart_service"}` <br> `{"sys": "shutdown"}` <br> `{"sys": "log_events"}` | Ejecuta un comando de sistema. Valores: `restart_service`, `restart_web_service`, `shutdown`, `log_events`, `homescreen`.                                            |
| **Leer Archivo**              | `{"read": {"id": "uci", "file": "stockfish"}}`                                      | Lee el contenido de un archivo de configuración. `id` puede ser `plugin`, `uci`, `famous_pgn`, `conf`.                                                               |
| **Escribir Archivo**          | `{"write": {"id": "uci", "file": "stockfish", "text": "..."}}`                  | Escribe contenido en un archivo de configuración, permitiendo cambiar la fuerza de un motor, por ejemplo.                                                           |

### **Canal Secundario: `'web_message'`**

Usado para comunicación más ligera, chat y comandos directos al tablero.

| Acción                  | Payload (Ejemplo en JSON)                                                                   | Descripción                                                                                                                                                         |
| :---------------------- | :------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Enviar Mensaje de Chat**  | `{"chat_message": {"author": "Mandy", "message": "Hola"}}`                           | Envía un mensaje al sistema de chat.                                                                                                                                |
| **Enviar Jugada (FEN)**     | `{"fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"}`                  | Envía una nueva posición FEN al servidor. Útil para sincronizar tableros, aunque `web_move` es preferido para jugadas.                                             |
| **Control de LEDs**         | `{"leds": "e2e4"}` <br> `{"leds_off": ""}` <br> `{"flash": "d4d5"}`                | Permite encender, apagar o hacer parpadear los LEDs de las casillas.                                                                                                |
| **Reproducir Sonido**       | `{"sound": "move"}`                                                                     | Pide al servidor que reproduzca un sonido predefinido. La lista de sonidos se puede obtener con `{"data": "sounds_settings"}`.                                     |

---

## B. Eventos que el Servidor Emite (Servidor -> Cliente)

Estos son los mensajes que el cliente puede recibir del servidor, la mayoría por el canal `web_message`.

| Campo en el JSON      | Ejemplo de Payload                                            | Descripción                                                                                                                     |
| :-------------------- | :------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------ |
| `update_menu`         | `{"update_menu": [{"id": "play", "label": "Play", ...}]}` | Envía la estructura completa de menús dinámicos, incluyendo la lista de motores y plugins.                                    |
| `sounds_settings`     | `{"sounds_settings": {"move": "Move sound", ...}}`         | Envía un diccionario con los sonidos disponibles y sus descripciones.                                                           |
| `fen`                 | `{"fen": "rnbqkb1r/..."}`                                 | Contiene la posición actual del tablero en notación FEN. Se envía tras una jugada o al conectar.                                |
| `uci_move`            | `{"uci_move": "e2e4"}`                                    | Informa de la última jugada realizada en formato UCI.                                                                           |
| `computer_uci_move`   | `{"computer_uci_move": "d2d4"}`                           | Informa de la jugada realizada por el motor.                                                                                    |
| `tip_uci_moves`       | `{"tip_uci_moves": ["g1f3", "d2d4"]}`                   | Envía una lista de jugadas sugeridas.                                                                                           |
| `checkers`            | `{"checkers": ["f7"], "kings": ["e8", "e1"]}`        | Indica qué piezas están dando jaque y la posición de los reyes.                                                                 |
| `centaur_screen`      | `{"centaur_screen": [80, 78, ... ]}`                         | Envía el buffer de la pantalla e-Paper del Centaur como un array de bytes para ser renderizado en la web.                       |
| `loading_screen`      | `{"loading_screen": true}`                                  | Indica al cliente que muestre una pantalla de carga, por ejemplo, mientras se inicia un plugin.                                |
| `popup`               | `{"popup": "Action completed!"}`                          | Pide al cliente que muestre un mensaje corto en una ventana emergente.                                                          |
| `log_events`          | `{"log_events": "..."}`                                   | La respuesta a la petición de logs.                                                                                             |
| `editor`              | `{"editor": {"text": "..."}}`                           | La respuesta a una petición de lectura de archivo, para ser mostrada en un editor.                                              |
| `previous_games`      | `{"previous_games": [...]}`                                 | La lista de partidas guardadas.                                                                                                 |
