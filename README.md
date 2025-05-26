# nlp-security-audio-agent

**nlp-security-audio-agent** es un agente de procesamiento de audio en tiempo real, basado en modelos `Whisper` (OpenAI) y `Gemini` (Google), diseñado para detectar y clasificar eventos de seguridad y asistencia a partir de grabaciones continuas del micrófono.

---

## 💡 Idea general del proyecto

Este proyecto integra varias piezas:

1. **Recorder**: un módulo que graba continuamente audio del micrófono y almacena archivos (por defecto, en formato `.mp3`) en la carpeta `grabaciones/`.
2. **Transcripción**: cada archivo de audio se transcribe con el modelo `Whisper` para obtener texto en lenguaje natural. Se ha usado Español para el desarrollo de este proyecto pero el modelo de transcripción es capaz de transcribir audio en Inglés, Francés, Alemán...
3. **Filtro de validación**: se descartan transcripciones vacías o irrelevantes (silencios, ruidos, repeticiones).
4. **Ventana de contexto**: el texto válido se añade a un buffer (deque) que mantiene los últimos **N** tokens (`MAX_TOKENS`), para dotar de contexto al modelo.
5. **Clasificador LLM**: un prompt maestro que determina a qué categoría pertenece la situación escuchada. En este proyecto las categorías posibles implementadas son:
   * `robo_banco`
   * `robo_casa`
   * `asistencia_mayor`
   * `ninguna`
6. **Agente LLM**: según la categoría, se envía un segundo prompt específico para generar una respuesta detallada o alerta. En base a la respuesta JSON obtenida por este prompt, el sistema será capaz de tomar decisiones como mandar un aviso a la policía o avisar a un familiar en el caso de asistencia.

---

## 🔧 Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/raulpg1/nlp-security-audio-agent.git
   cd nlp-security-audio-agent
   ```
2. Crear un entorno Conda o virtualenv e instalar dependencias:

   ```bash
   conda create -n audio-agent python=3.10
   conda activate audio-agent
   pip install -r requirements.txt
   ```
3. Configurar variables de entorno en `keys.env`:

   ```dotenv
   RECORD_FOLDER=grabaciones
   DESTINATION_FOLDER=procesadas
   MAX_TOKENS=150
   AUDIO_DURATION=10
   MAX_SILENT_ITERS=5
   WHISPER_MODEL=medium
   MODEL_NAME=gemini-2.0-flash
   GOOGLE_API_KEY=tu_api_key
   ```

---

## 🚀 Uso

1. Iniciar el recorder (grabador continuo):

   ```bash
   python scripts/recorder.py
   ```
2. Ejecutar el analizador en tiempo real:

   ```bash
   python src/main.py
   ```

---

## ⚙️ Arquitectura y detalles de implementación

### 1. Recorder

* Graba audio en bloques de 10 segundos (ajustable con `AUDIO_DURATION`).
* Nombra los archivos con timestamp y los guarda en `RECORD_FOLDER`.

### 2. Procesamiento en `real_time_analyzer()`

* **Bucle infinito** (`while True`): lista y procesa nuevos archivos `.mp3`.
* Transcribe con `whisper.load_model(WHISPER_MODEL)`.
* Mueve el archivo al directorio procesado (`DESTINATION_FOLDER`).
* Valida texto con `es_texto_valido()` (descarta silencios y ruido).

### 3. Ventana de contexto (context window)

* Se almacenan tokens en un `collections.deque` de tamaño máximo `MAX_TOKENS`.
* Cada texto válido se tokeniza (`WhisperTokenizer`) y se añade:

  * Si **nuevo\_texto** > `MAX_TOKENS`, se reinicia contexto a solo esos tokens. Por defecto, el límite de tokens se ha fijado en 150 ya que debería ser suficiente para tratar audios de 10 segundos manteniendo el contexto de los anteriores.
  * Si cabe, se añaden y eliminan tokens antiguos para respetar el límite.
* **Vida de contexto**: si ocurren `MAX_SILENT_ITERS` transcripciones vacías seguidas, se eliminan gradualmente tokens antiguos (por ejemplo, 10 por iteración) para "envejecer" el contexto.

### 4. Clasificador maestro

* Prompt que categoriza el texto en una de cuatro categorías.
* Se envía a Gemini vía `gemini_api_llm()`.
* El JSON de salida dicta si se procede con un prompt específico o se descarta.

### 5. Agente de respuesta

* Para `robo_banco`, `robo_casa` o `asistencia_mayor`, existe un prompt dedicado en `./prompts/`.
* Se envía a Gemini y se imprime respuesta para alertas o logs. Según el resultado obtenido, se puede desencadenar una acción concreta, como activar una alarma sonora en caso de detección de robo o enviar una notificación a un familiar en situaciones de asistencia a personas mayores.

---

## 🌐 Ejemplos de aplicaciones adicionales

El sistema es altamente adaptable: al modificar los prompts utilizados tanto en el clasificador como en los agentes de respuesta, se puede orientar el análisis hacia cualquier dominio de interés. Esto permite construir aplicaciones que van más allá del ámbito de seguridad o asistencia, explorando desde usos médicos hasta contextos industriales, educativos o comerciales.

* **Detección de violencia en eventos masivos**: monitorizar megáfonos o transmisiones en directo para identificar amenazas.
* **Soporte en call centers**: analizar llamadas para detectar clientes en crisis o situaciones críticas.
* **Detección de intrusos en vehículos**: grabar y procesar audio en cabinas de transporte público.
* **Monitoreo de pacientes**: alertar si un paciente en casa emite señales de dolor o llamada de auxilio.
* **Control de ambientes industriales**: detectar sonidos de alarmas o indicaciones de falla en maquinaria.

---

## 🔮 Futuras mejoras

* Integrar reconocimiento de hablantes (speaker diarization).
* Añadir geolocalización de eventos.
* Dashboard web en tiempo real con mapas y estadísticas.
* Modularizar componentes en microservicios.

---

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

---

*Desarrollado por raulpg1*
