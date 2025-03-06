"""
Travin Canvas - A web application for conversational document creation and editing.

This is the main entry point for the Travin Canvas application, which integrates
a chat interface powered by an LLM with a collaborative markdown editor.
The application supports real-time speech-to-text input, text-to-speech responses,
and integration with n8n webhooks for research and dynamic LLM prompting.

Key components:
- Chat Interface: Manages conversations with the LLM, speech-to-text, and TTS
- Markdown Canvas: Provides document editing, preview, and enhancement tools
- Webhook Integration: Connects to n8n for external research capabilities

The application is built using Streamlit for the front-end interface,
LangChain for managing LLM interactions and markdown processing,
and OpenAI APIs for LLM, speech-to-text, and text-to-speech functionalities.

Author: Travin AI
License: MIT
"""

import os
import streamlit as st
from dotenv import load_dotenv
from components.chat import ChatInterface
from components.canvas import MarkdownCanvas
from utils.webhook_utils import WebhookManager

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Travin Canvas",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Basic layout adjustments */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stSidebar .block-container {
        padding-top: 1rem;
    }
    .stTextArea textarea {
        font-family: monospace;
    }
    
    /* Remove default padding from expanders in view mode */
    .streamlit-expander {
        border: none !important;
        box-shadow: none !important;
    }
    .streamlit-expander .streamlit-expanderContent {
        padding: 0 !important;
        border: 1px solid #eee;
        border-radius: 5px;
        padding: 20px !important;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def handle_research_request(query):
    """
    Handle a research request from the chat interface by sending it to an n8n webhook.
    
    This function processes research queries from the chat interface, sends them to
    an n8n webhook for external processing, and integrates the results back into
    the markdown document. It provides context-aware research capabilities by
    including the current document content with the request.
    
    Args:
        query (str): The research query from the user
        
    Returns:
        str: A message indicating the result of the research operation
    """
    # Initialize WebhookManager with SSL verification disabled
    webhook_manager = WebhookManager(verify_ssl=False)
    
    # Check if webhook URL is configured
    if not webhook_manager.webhook_url:
        return "Error: N8N webhook URL is not configured. Please set the N8N_WEBHOOK_URL environment variable."
    
    # Get current document content for context
    if "markdown_content" in st.session_state:
        document_context = st.session_state.markdown_content
    else:
        document_context = ""
    
    # Show status to user
    with st.sidebar:
        with st.spinner(f"Researching: {query}"):
            # Send research request to n8n
            response = webhook_manager.send_research_request(
                query,
                additional_context={"document": document_context}
            )
            
            # Process response
            processed_response = webhook_manager.process_webhook_response(response)
    
    # Handle the response
    if not processed_response["success"]:
        error_message = processed_response.get("error", "Unknown error occurred")
        return f"Research error: {error_message}"
    
    if processed_response["data"]:
        # Update markdown content with research results
        if "markdown_canvas" in st.session_state and "markdown_content" in st.session_state:
            current_content = st.session_state.markdown_content
            research_content = processed_response["data"].get("content", "")
            
            if research_content:
                new_content = current_content + "\n\n## Research Results\n\n" + research_content
                st.session_state.markdown_content = new_content
                return f"Research complete! Added results to your document."
            else:
                return "Research complete, but no content was returned."
        else:
            return "Research complete, but couldn't update the document."
    else:
        return "Research complete, but no data was returned."

def handle_content_change(content):
    """
    Handle content changes in the markdown canvas and notify the LLM.
    
    This function is called whenever the content in the markdown canvas changes.
    It notifies the LLM about significant document updates, allowing the chat
    interface to maintain awareness of the current document state without
    sending the entire document content with each notification.
    
    Args:
        content (str): The updated markdown content
    """
    # Inform the LLM about the document content change
    if "chat_interface" in st.session_state:
        # Add a system message to inform the LLM about the document update
        chat_interface = st.session_state.chat_interface
        
        # Only send a notification if the content is not empty and has changed significantly
        if content.strip() and len(content) > 20:
            # We don't need to send the entire document as a system message anymore
            # since we're providing it just-in-time when needed
            chat_interface.add_system_message("""
            The document has been updated. You can access the current content when needed.
            """)

def main():
    """
    Main application entry point.
    
    Initializes the application components, sets up the layout, and renders
    the user interface. The application uses a two-panel layout with the
    chat interface in the sidebar and the markdown canvas in the main area.
    
    Components are stored in session state to enable cross-component
    communication and maintain state between Streamlit reruns.
    """
    # Initialize components
    chat_interface = ChatInterface(on_research_request=handle_research_request)
    markdown_canvas = MarkdownCanvas(on_content_change=handle_content_change)
    
    # Store components in session state for access in callbacks
    st.session_state.chat_interface = chat_interface
    st.session_state.markdown_canvas = markdown_canvas
    
    # Set up the layout
    # Chat interface is rendered in the sidebar by the ChatInterface class
    chat_interface.render()
    
    # Main content area for the markdown canvas
    markdown_canvas.render()
    
    # Footer
    st.divider()
    st.caption("Travin Canvas - Powered by Streamlit, LangChain, and OpenAI")

if __name__ == "__main__":
    main()
