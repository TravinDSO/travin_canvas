# Travin Canvas

A web application that combines an LLM-powered chat interface with a collaborative markdown editor, supporting real-time speech-to-text input, text-to-speech responses, and integration with n8n webhooks.

## Features

### Chat Interface (Left Panel)
- **AI-Powered Conversations**: Interact with OpenAI's GPT models for intelligent assistance
- **Speech Input**: Real-time speech-to-text input using OpenAI's Whisper API
- **Voice Responses**: Text-to-speech responses using OpenAI's TTS API
- **Research Commands**: Trigger external research workflows with the `/research` command
- **Document Awareness**: The AI assistant maintains awareness of your document content

### Canvas (Right Panel)
- **Markdown Editor**: Collaborative markdown editor with syntax highlighting
- **Real-time Preview**: Instant rendering of markdown content
- **Document Enhancement**: AI-powered tools to improve grammar, clarity, and more
- **Version History**: Undo capability to revert to previous versions
- **Export Options**: Download your documents in markdown format

### Integration Capabilities
- **n8n Webhooks**: Connect to external workflows for research and data enrichment
- **Context-Aware Research**: Include document context with research requests
- **Dynamic LLM Prompting**: Enhance LLM prompts with external knowledge

## Architecture

Travin Canvas is built with a modular architecture:

```
travin_canvas/
├── .env                  # Environment variables
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── run.py                # Application launcher
└── src/                  # Source code
    ├── main.py           # Main application entry point
    ├── __init__.py       # Package initialization
    ├── components/       # UI components
    │   ├── __init__.py   # Component package initialization
    │   ├── chat.py       # Chat interface component
    │   └── canvas.py     # Markdown canvas component
    ├── utils/            # Utility modules
    │   ├── __init__.py   # Utilities package initialization
    │   ├── audio_utils.py    # Audio processing utilities
    │   ├── llm_utils.py      # LLM interaction utilities
    │   ├── markdown_utils.py # Markdown processing utilities
    │   └── webhook_utils.py  # n8n webhook utilities
    └── test_*.py         # Test modules
```

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed on your system (for audio processing)
- OpenAI API key
- n8n instance with configured webhooks (optional)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/travin_canvas.git
cd travin_canvas
```

2. Create and activate a virtual environment:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
N8N_WEBHOOK_URL=your_n8n_webhook_url
```

## Usage

### Starting the Application

Run the application using the provided run script:
```bash
python run.py
```

Alternatively, you can run it directly with Streamlit:
```bash
streamlit run src/main.py
```

### Using the Chat Interface

The chat interface is located in the left sidebar:

1. **Text Input**: Type your message in the chat input field and press Enter
2. **Voice Input**: Click the microphone button to record speech input
3. **Text-to-Speech**: Toggle the speaker button to hear responses
4. **Research Command**: Type `/research` followed by a query to trigger research workflows
5. **Clear Chat**: Use the "Clear Chat" button to start a new conversation

### Using the Markdown Canvas

The markdown canvas is located in the main content area:

1. **Editing**: Write or edit markdown content in the editor
2. **Preview**: Toggle the preview to see the rendered markdown
3. **Enhancement Tools**: Use the enhancement tools to improve your document
4. **Undo Changes**: Revert to previous versions with the undo button
5. **Download**: Download your document when finished

## Configuration

You can configure the application by modifying the following files:

- `.env`: API keys and external service URLs
- `src/main.py`: Application layout and global settings
- `src/components/chat.py`: Chat interface behavior
- `src/components/canvas.py`: Markdown canvas behavior

## Development

### Project Structure

- **components/**: UI components for the application
  - `chat.py`: Implements the chat interface
  - `canvas.py`: Implements the markdown canvas
- **utils/**: Utility modules for various functionalities
  - `audio_utils.py`: Audio recording and processing
  - `llm_utils.py`: LLM interactions and prompt management
  - `markdown_utils.py`: Markdown parsing and formatting
  - `webhook_utils.py`: n8n webhook integration

### Adding New Features

1. **New UI Components**: Add new components to the `components/` directory
2. **New Utilities**: Add new utility modules to the `utils/` directory
3. **Integration**: Update `main.py` to integrate new components

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web interface
- [LangChain](https://langchain.com/) for LLM interactions
- [OpenAI](https://openai.com/) for AI models and APIs
- [n8n](https://n8n.io/) for workflow automation 