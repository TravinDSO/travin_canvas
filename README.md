# Travin Canvas

A web application that combines an LLM-powered chat interface with a collaborative markdown editor and integration with n8n webhooks and Perplexity AI.

![Screenshot of Travin Canvas](./images/gui.png?raw=true)

## Features

### Chat Interface (Left Panel)
- **AI-Powered Conversations**: Interact with OpenAI's GPT models for intelligent assistance
- **Research Commands**: Trigger external n8n workflows with the `/research` command
- **Document Awareness**: The AI assistant maintains awareness of your document content
- **Perplexity AI Integration**: Access to Perplexity AI's research capabilities through OpenAI function calls

### Canvas (Right Panel)
- **Markdown Editor**: Collaborative markdown editor with syntax highlighting
- **Real-time Preview**: Instant rendering of markdown content
- **Toggle View**: Switch between editor and preview modes to maximize workspace
- **Optimized View Mode**: Clean document preview with no excessive whitespace
- **Version History**: Undo capability to revert to previous versions
- **Minimalist Interface**: Clean, distraction-free design with essential controls
- **Document Import**: Support for uploading and converting Word documents (.docx) and PDFs to text

### Integration Capabilities
- **n8n Webhooks**: Connect to external workflows for research and data enrichment via the `/research` command
- **Context-Aware Research**: Include document context with research requests
- **Dynamic LLM Prompting**: Enhance LLM prompts with external knowledge
- **Perplexity AI Research**: Access Perplexity AI for advanced research and question answering through OpenAI function calls

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
    ├── tools/            # External API integrations
    │   └── perplexity.py # Perplexity AI integration
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
- OpenAI API key
- Perplexity AI API key (for research capabilities)
- n8n instance with configured webhooks (optional, for `/research` command)

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
PERPLEXITY_API_KEY=your_perplexity_api_key
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
2. **Research Command**: Type `/research` followed by a query to send to your configured n8n webhook
3. **Clear Chat**: Use the "Clear Chat" button to start a new conversation
4. **Perplexity Research**: Ask research questions directly in chat - the AI will automatically use Perplexity when needed through function calling

### Using the Markdown Canvas

The markdown canvas is located in the main content area:

1. **Document Controls**: Use the toolbar to create new documents, undo changes, or upload files
2. **Toggle View**: Switch between "Edit" and "View" modes using the toggle buttons
3. **Editing**: Write or edit markdown content in the editor mode
4. **Preview**: View the rendered markdown in the preview mode
5. **Download**: Download your document from the preview mode
6. **File Import**: Upload and convert Word documents (.docx) and PDFs to text in the editor

### Document Import Feature

The canvas supports importing various document formats:

1. **Supported Formats**:
   - Markdown (.md)
   - Text files (.txt)
   - Word documents (.docx)
   - PDF files (.pdf)

2. **Import Process**:
   - Click the file upload button in the canvas toolbar
   - Select a file from your computer
   - The file will be processed and its content will be extracted
   - For Word documents, both paragraph text and table content are extracted
   - For PDFs, text is extracted from all pages
   - The extracted content is placed in the editor for further editing

## Configuration

You can configure the application by modifying the following files:

- `.env`: API keys and external service URLs
- `src/main.py`: Application layout and global settings
- `src/components/chat.py`: Chat interface behavior
- `src/components/canvas.py`: Markdown canvas behavior
- `src/tools/perplexity.py`: Perplexity AI integration settings

## Development

### Project Structure

- **components/**: UI components for the application
  - `chat.py`: Implements the chat interface
  - `canvas.py`: Implements the markdown canvas with optimized view mode
- **tools/**: External API integrations
  - `perplexity.py`: Implements Perplexity AI integration for research capabilities
- **utils/**: Utility modules for various functionalities
  - `audio_utils.py`: Audio recording and processing
  - `llm_utils.py`: LLM interactions and prompt management
  - `markdown_utils.py`: Markdown parsing and formatting
  - `webhook_utils.py`: n8n webhook integration

### Integration Details

- **OpenAI Function Calling**: The chat interface uses OpenAI's function calling capability to automatically invoke Perplexity AI for research when needed
- **n8n Webhook**: The `/research` command sends requests to an external n8n workflow for processing
- **Perplexity Integration**: Perplexity AI is integrated as a tool that can be called by the LLM to search for information and perform research

### UI Implementation Notes

- **View Mode**: The document preview uses Streamlit's native expander component for optimal layout
- **CSS Management**: Custom CSS is minimized to avoid conflicts with Streamlit's built-in styling
- **Component Design**: UI components are designed to work with Streamlit's rendering lifecycle

### Adding New Features

1. **New UI Components**: Add new components to the `components/` directory
2. **New Utilities**: Add new utility modules to the `utils/` directory
3. **New Tools**: Add new external API integrations to the `tools/` directory
4. **Integration**: Update `main.py` to integrate new components and tools

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
- [Perplexity AI](https://www.perplexity.ai/) for research capabilities
- [n8n](https://n8n.io/) for workflow automation
- [python-docx](https://python-docx.readthedocs.io/) for Word document processing
- [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing

## Recent Updates

### Integration Improvements
- **Perplexity AI**: Integrated with OpenAI function calling for automatic research capabilities
- **Multiple Research Models**: Support for various Perplexity AI models including sonar-reasoning, sonar-deep-research, and more
- **n8n Webhook**: Enhanced `/research` command to send queries to external n8n workflows

### UI Improvements
- **Fixed View Mode Whitespace**: Eliminated excessive whitespace in the document preview mode
- **Improved Layout Consistency**: Enhanced the document viewing experience with better container management
- **Streamlined CSS**: Reduced CSS complexity for better performance and maintainability 

### New Features
- **Document Import**: Added support for uploading and converting Word documents (.docx) and PDFs to text
- **Enhanced File Processing**: Implemented robust extraction of text from various document formats 