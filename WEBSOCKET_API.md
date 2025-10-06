# Documentación de la API de WebSockets del DGTCentaur

La comunicación en tiempo real entre el frontend (la página web) y el backend (el servidor en el Centaur) se realiza a través de **WebSockets**, utilizando la librería `Flask-SocketIO`.

La comunicación se basa en **eventos** sobre una conexión persistente. En lugar de hacer peticiones a endpoints HTTP, el cliente y el servidor emiten y escuchan mensajes en diferentes "canales" o "eventos".

## A. Eventos que el Servidor Escucha (Cliente -> Servidor)

Estos son los mensajes que puedes enviar al servidor para que realice acciones.

### **Canal Principal: `'request'`**

Este es el canal más potente, usado para solicitar datos o ejecutar comandos en el sistema.

| Acción                  | Payload (Ejemplo en JSON)                                                                            | Descripción                                                                                                                                                                 |
| :---------------------- | :--------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Obtener Logs**        | `{ "sys": "log_events" }`                                                                            | Pide las últimas 500 líneas del log. El servidor responde en `'web_message'` con `{"log_events": "..."}`.                                                                   |
| **Reiniciar Servicio**  | `{ "sys": "restart_service" }`                                                                       | Reinicia el servicio principal de DGTCentaurMods.                                                                                                                           |
| **Reiniciar Web**       | `{ "sys": "restart_web_service" }`                                                                   | Reinicia este mismo servidor web.                                                                                                                                           |
| **Apagar**              | `{ "sys": "shutdown" }`                                                                              | Apaga completamente el DGT Centaur.                                                                                                                                         |
| **Leer Archivo**        | `{ "read": { "id": "plugin", "file": "HandAndBrain" } }`                                             | Lee el contenido de un archivo. `id` puede ser `plugin`, `uci`, `famous_pgn`, `conf`. `file` es el nombre sin extensión. Responde en `'web_message'` con `{"editor": ...}`. |
| **Escribir Archivo**    | `{ "write": { "id": "plugin", "file": "HandAndBrain", "new_file": "HandAndBrain", "text": "..." } }` | Escribe contenido en un archivo. `text` es el nuevo contenido.                                                                                                              |
| **Eliminar Archivo**    | `{ "write": { "id": "famous_pgn", "file": "MyGame", "new_file": "__delete__" } }`                    | Elimina un archivo (solo permitido para ciertos tipos como PGNs).                                                                                                           |
| **Obtener Partidas**    | `{ "data": "previous_games" }`                                                                       | Pide la lista de todas las partidas guardadas en la base de datos. Responde en `'web_message'` con `{"previous_games": [...]}`.                                             |
| **Obtener Movimientos** | `{ "data": "game_moves", "id": 123 }`                                                                | Pide la lista de movimientos para una partida específica por su `id`. Responde en `'web_message'` con `{"game_moves": "..."}`.                                              |
| **Eliminar Partida**    | `{ "data": "remove_game", "id": 123 }`                                                               | Elimina una partida de la base de datos por su `id`.                                                                                                                        |
| **Ejecutar Script**     | `{ "script": "update" }`                                                                             | Ejecuta un script de la carpeta `/scripts` por su nombre. Responde en `'web_message'` con `{"script_output": "..."}`.                                                       |

### **Canal Secundario: `'web_message'`**

Usado principalmente para la comunicación entre diferentes tableros (chat) y para enviar comandos directos al tablero.

| Acción                  | Payload (Ejemplo en JSON)                                                 | Descripción                                                                         |
| :---------------------- | :------------------------------------------------------------------------ | :---------------------------------------------------------------------------------- |
| **Comando de Bot**      | `{ "bot_message": ["@username", "MyUser"] }`                              | Envía un comando al bot interno (ej: para cambiar el nombre de usuario de Lichess). |
| **Enviar Jugada (FEN)** | `{ "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1" }` | Envía una nueva posición FEN al servidor para actualizar el estado del juego.       |
| **Encender LED**        | `{ "leds": "e4" }` o `{ "leds": "e2e4" }`                                 | Enciende los LEDs de las casillas indicadas.                                        |
| **Apagar LEDs**         | `{ "leds_off": "" }`                                                      | Apaga todos los LEDs del tablero.                                                   |
| **Mostrar Flash**       | `{ "flash": "e2e4" }`                                                     | Hace un parpadeo rápido en las casillas de un movimiento.                           |

## B. Eventos que el Servidor Emite (Servidor -> Cliente)

Estos son los mensajes que recibirás del servidor. La mayoría llegan por el canal `'web_message'`.

| Campo en el JSON | Ejemplo                                               | Descripción                                                        |
| :--------------- | :---------------------------------------------------- | :----------------------------------------------------------------- |
| `fen`            | `{"fen": "rnbqkb1r/..."}`                             | Contiene la posición actual del tablero en notación FEN.           |
| `log_events`     | `{"log_events": "..."}`                               | La respuesta a la petición de logs.                                |
| `editor`         | `{"editor": {"text": "...", "file": "..."}}`          | La respuesta a una petición de lectura de archivo.                 |
| `popup`          | `{"popup": "Action completed!"}`                      | Un mensaje corto para mostrar al usuario en una ventana emergente. |
| `previous_games` | `{"previous_games": [{"id":1, "date":"..."}, ...]}`   | La lista de partidas guardadas.                                    |
| `script_output`  | `{"script_output": "..."}`                            | El resultado de la ejecución de un script.                         |
| `chat_message`   | `{"chat_message": {"author":"...", "message":"..."}}` | Un mensaje de chat.                                                |
