"""
Travin Canvas - A web application for conversational document creation and editing.

This is the main entry point for the Travin Canvas application, which integrates
a chat interface powered by an LLM with a collaborative markdown editor.
The application supports integration with n8n webhooks for research and dynamic LLM prompting.

Key components:
- Chat Interface: Manages conversations with the LLM
- Markdown Canvas: Provides document editing, preview, and enhancement tools
- Webhook Integration: Connects to n8n for external research capabilities

The application is built using Streamlit for the front-end interface,
LangChain for managing LLM interactions and markdown processing,
and OpenAI APIs for LLM functionalities.

Author: Travin AI
License: MIT
"""

import os
import sys
import time
import streamlit as st
from dotenv import load_dotenv
from components.chat import ChatInterface
from components.canvas import MarkdownCanvas
from utils.webhook_utils import WebhookManager

# Load environment variables
load_dotenv()

# Check if features are enabled
use_n8n = os.getenv("USE_N8N", "false").lower() == "true"
use_perplexity = os.getenv("USE_PERPLEXITY", "false").lower() == "true"

# Set page configuration
st.set_page_config(
    page_title="Travin Canvas",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global flag to track if shutdown is in progress
shutdown_in_progress = False

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
    
    /* Shutdown button styles */
    .shutdown-btn {
        font-size: 0.8em;
        opacity: 0.7;
        height: 1.5rem;
    }
    .shutdown-btn:hover {
        opacity: 1;
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
    # Check if n8n integration is enabled
    if not use_n8n:
        return "Research via n8n is currently disabled. Please enable it by setting USE_N8N=true in your .env file."
    
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

def graceful_shutdown():
    """
    Perform a graceful shutdown of the application.
    
    This function handles proper cleanup and resource release before
    terminating the Streamlit application. It provides a consistent
    shutdown experience when using the Exit button.
    
    The shutdown process:
    1. Displays a shutdown message on the webpage
    2. Prints terminal messages about the shutdown
    3. Terminates the application using os._exit(0)
    """
    global shutdown_in_progress
    
    # Prevent multiple shutdown attempts
    if shutdown_in_progress:
        return
    
    shutdown_in_progress = True
    
    # Display a message to the user about the shutdown
    st.toast("Shutting down Travin Canvas...", icon="🛑")
    
    # Create a full-page shutdown message
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; text-align: center;">
            <h1 style="color: #FF5555;">Application Shutdown</h1>
            <p style="font-size: 1.2rem; margin-top: 20px;">Travin Canvas has been terminated.</p>
            <p style="margin-top: 10px;">You can close this browser tab.</p>
        </div>
        <style>
            /* Hide all other elements */
            header, .stSidebar, .stButton, footer {
                display: none !important;
            }
            .main .block-container {
                max-width: 100% !important;
                padding-top: 0 !important;
                padding-right: 0 !important;
                padding-left: 0 !important;
                padding-bottom: 0 !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Print shutdown messages to terminal
    print("\nStopping...")
    
    # Give the UI a moment to update before exiting
    time.sleep(1)
    
    print("Travin Canvas stopped.")
    
    # Force immediate termination of all processes
    os._exit(0)

def main():
    """
    Main application entry point.
    
    Initializes the application components, sets up the layout, and renders
    the user interface. The application uses a two-panel layout with the
    chat interface in the sidebar and the markdown canvas in the main area.
    
    Components are stored in session state to enable cross-component
    communication and maintain state between Streamlit reruns.
    """
    # Initialize components with feature flags
    chat_interface = ChatInterface(
        on_research_request=handle_research_request,
        use_perplexity=use_perplexity
    )
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
    
    # Footer content with shutdown button in a small container
    footer_cols = st.columns([0.92, 0.08])
    with footer_cols[0]:
        st.caption("Travin Canvas - Powered by Streamlit, LangChain, and OpenAI")
    
    with footer_cols[1]:
        # Apply custom class to the container div
        st.markdown(
            """
            <style>
            div[data-testid="column"]:nth-of-type(2) .stButton {
                text-align: right;
                height: 1.5rem;
            }
            div[data-testid="column"]:nth-of-type(2) .stButton button {
                font-size: 0.7rem;
                padding: 0px 0.5rem;
                line-height: 1.2;
                min-height: 0px;
                height: 1.5rem;
                border-radius: 4px;
                opacity: 0.6;
            }
            div[data-testid="column"]:nth-of-type(2) .stButton button:hover {
                opacity: 1;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        if st.button("⏹️ Exit", key="shutdown_btn", help="Safely shutdown the application", 
                     use_container_width=False, type="secondary", 
                     on_click=graceful_shutdown):
            pass

if __name__ == "__main__":
    main()
