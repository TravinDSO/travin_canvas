"""
Chat Interface Component for Travin Canvas

This module provides the chat interface component for the Travin Canvas application.
It handles all user interactions with the LLM, including text input and research commands.
The component creates a conversational experience that integrates with the markdown canvas.

Key features:
- Text-based chat with OpenAI's GPT models using function calling
- Integration with Perplexity AI for search and research capabilities
- Support for research commands via n8n webhooks
- Document-aware conversations with context management

Dependencies:
- streamlit: For UI components
- utils.llm_utils: For LLM interactions
- utils.webhook_utils: For external integrations
"""

import os
import time
import streamlit as st
from utils.llm_utils import LLMManager
from utils.webhook_utils import WebhookManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access global configuration
use_azure = os.getenv("USE_AZURE", "false").lower() == "true"
use_n8n = os.getenv("USE_N8N", "false").lower() == "true"
use_perplexity = os.getenv("USE_PERPLEXITY", "false").lower() == "true"
azure_model = os.getenv("AZURE_MODEL", "")
openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

class ChatInterface:
    """
    Implements the chat interface for the Travin Canvas application.
    
    This class manages the entire chat experience, including:
    - Conversation history storage and rendering
    - User input handling
    - LLM response generation
    - Research command processing
    - Document edit suggestions and confirmations
    
    The interface is rendered in the Streamlit sidebar and maintains
    its state between application reruns using session state.
    """
    
    def __init__(self, on_research_request=None, use_perplexity=False):
        """
        Initialize the chat interface.
        
        Args:
            on_research_request (callable, optional): Callback for research requests
            use_perplexity (bool, optional): Whether Perplexity AI integration is enabled
        """
        self.llm_manager = LLMManager()
        self.webhook_manager = WebhookManager(verify_ssl=False)  # Disable SSL verification
        self.on_research_request = on_research_request
        self.use_perplexity = use_perplexity
        
        # Initialize session state for chat history if not exists
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
            # Add configuration information as the first message
            self._add_config_info_message()
            
        if "pending_edit" not in st.session_state:
            st.session_state.pending_edit = None
            
        if "edit_confirmed" not in st.session_state:
            st.session_state.edit_confirmed = False
            
        # Add system message to inform the LLM about its capabilities
        if self.use_perplexity:
            self.add_system_message("""
            You are an AI assistant with two main capabilities:
            
            1. Document Editing:
               When the user asks you to create, format, edit, or modify their document:
               - Understand what changes they want to make
               - Generate the appropriate content or modifications
               - Use the phrase "I'll update the document with:" followed by the content
            
            2. Information Retrieval:
               You have access to two special functions for retrieving information:
               - search_with_perplexity: Use this to search the internet for general information and current events
               - research_with_perplexity: Use this for in-depth research with comprehensive citations
            
            EXTREMELY IMPORTANT INSTRUCTIONS:
            
            When the user asks ANY question about:
            - News or current events
            - Recent developments or updates
            - Facts that might have changed since your training
            - "What is X" or "Tell me about X" questions
            - Any topic where up-to-date information would be valuable
            
            You MUST use one of your search functions rather than responding from your training data.
            DO NOT try to answer these questions directly - ALWAYS use the appropriate function.
            
            Examples of when to use search_with_perplexity:
            - "What are today's top headlines?"
            - "Tell me about recent developments in AI"
            - "What is the current situation in Ukraine?"
            - "Who is the current CEO of Apple?"
            - "What's the weather like in New York today?"
            
            Examples of when to use research_with_perplexity:
            - "I need detailed research on climate change impacts"
            - "Provide a comprehensive analysis of quantum computing"
            - "Give me an in-depth literature review on cancer treatments"
            - "What are the scholarly perspectives on consciousness?"
            """)
        else:
            self.add_system_message("""
            You are an AI assistant focused on document editing.
            
            When the user asks you to create, format, edit, or modify their document:
            - Understand what changes they want to make
            - Generate the appropriate content or modifications
            - Use the phrase "I'll update the document with:" followed by the content
            """)
    
    def _add_config_info_message(self):
        """Add a message with the current configuration information to the chat history."""
        # Determine LLM provider and model
        if use_azure:
            llm_provider = "Azure OpenAI"
            llm_model = azure_model
        else:
            llm_provider = "OpenAI"
            llm_model = openai_model
            
        # Format the configuration information message
        config_info = f"""
        **System Configuration:**
        - **LLM Provider:** {llm_provider}
        - **Model:** {llm_model}
        - **N8N Integration:** {'Enabled' if use_n8n else 'Disabled'}
        - **Perplexity Integration:** {'Enabled' if use_perplexity else 'Disabled'}
        """
        
        # Add the message to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": config_info
        })
    
    def render(self):
        """Render the chat interface in the Streamlit sidebar."""
        with st.sidebar:
            # Display chat history
            st.write("### Chat History")
            chat_container = st.container(height=400)
            
            with chat_container:
                for i, message in enumerate(st.session_state.chat_history):
                    role = message["role"]
                    content = message["content"]
                    
                    if role == "user":
                        st.markdown(f"**You:** {content}")
                    elif role == "assistant":
                        st.markdown(f"**Assistant:** {content}")
                        
                        # Check if this is an edit suggestion
                        if "I'll update the document with:" in content:
                            # Only show edit confirmation if not already confirmed
                            if not st.session_state.edit_confirmed:
                                # Extract the content after the marker
                                marker = "I'll update the document with:"
                                marker_index = content.find(marker)
                                if marker_index != -1:
                                    edit_content = content[marker_index + len(marker):].strip()
                                    st.session_state.pending_edit = edit_content
                                    # Pass the message index to create unique keys
                                    self._render_edit_confirmation_buttons(message_index=i)
            
            # User input area
            st.write("### Your Message")
            
            # Initialize the widget key counter if it doesn't exist
            if "widget_key_counter" not in st.session_state:
                st.session_state.widget_key_counter = 0
                
            # Generate a key for the text area that changes when we want to clear it
            textarea_key = f"user_input_{st.session_state.widget_key_counter}"
            
            # Text input widget with the dynamic key
            user_input = st.text_area(
                "Type your message", 
                key=textarea_key,
                height=100
            )
            
            # Button row
            col1, col2 = st.columns(2)
            
            with col2:
                if st.button("🧹 Clear Chat", use_container_width=True):
                    self.clear_chat_history()
                    # Re-add the configuration message after clearing
                    self._add_config_info_message()
                    st.rerun()
            
            # Send button
            if st.button("Send", use_container_width=True, type="primary"):
                if user_input and user_input.strip():
                    # Process the user input
                    self.process_user_input(user_input)
                    
                    # Increment the counter to change the text area's key on next render
                    st.session_state.widget_key_counter += 1
                    
                    # Force a rerun to update the UI with the new key
                    st.rerun()
    
    def _render_edit_confirmation_buttons(self, message_index=0):
        """
        Render confirmation buttons for document edits.
        
        Args:
            message_index (int): Index of the message to create unique keys
        """
        st.markdown("**Document update ready to apply:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Apply Changes", key=f"apply_changes_inline_{message_index}"):
                # Apply the changes to the document
                if "markdown_canvas" in st.session_state:
                    st.session_state.markdown_content = st.session_state.pending_edit
                    
                    # Add confirmation message to chat
                    st.session_state.chat_history.append({
                        "role": "system", 
                        "content": "✅ Document has been updated successfully."
                    })
                    
                    # Clear the pending edit
                    st.session_state.pending_edit = None
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_changes_inline_{message_index}"):
                # Add cancellation message to chat
                st.session_state.chat_history.append({
                    "role": "system", 
                    "content": "❌ Document update was cancelled."
                })
                
                # Clear the pending edit
                st.session_state.pending_edit = None
                st.rerun()
    
    def _get_current_document(self):
        """
        Get the current document content.
        
        Returns:
            str: The current document content or an empty string if not available
        """
        if "markdown_content" in st.session_state:
            return st.session_state.markdown_content
        return ""
    
    def clear_chat_history(self):
        """
        Clear the chat history but keep system configuration information.
        
        This method resets the conversation history but preserves the
        system configuration information message at the start of the chat.
        """
        # Clear the session state chat history
        st.session_state.chat_history = []
        
        # Clear the LLM manager conversation history
        self.llm_manager.clear_conversation_history()
    
    def add_system_message(self, content):
        """
        Add a system message to the conversation.
        
        Args:
            content (str): The content of the system message
        """
        self.llm_manager.add_message("system", content)
    
    def _should_use_research_mode(self, user_input: str) -> bool:
        """
        Determine if research mode should be used for the given input.
        
        This method analyzes the user's input to determine if it requires
        in-depth research rather than just a simple search. It looks for patterns
        that suggest a need for comprehensive analysis.
        
        Args:
            user_input (str): The user's input message
            
        Returns:
            bool: Whether research mode should be used
        """
        # With function calling, we let the LLM decide when to use search vs research
        # But we can still force research mode for certain queries
        
        research_indicators = [
            "research",
            "in-depth",
            "comprehensive",
            "detailed analysis",
            "thorough investigation",
            "deep dive",
            "academic",
            "scholarly",
            "literature review",
            "systematic review",
            "meta-analysis",
            "citations",
            "references",
            "bibliography",
            "peer-reviewed",
            "journal",
            "publication"
        ]
        
        # Convert input to lowercase for case-insensitive matching
        lower_input = user_input.lower()
        
        # Check for research indicators that suggest deep research
        for indicator in research_indicators:
            if indicator in lower_input:
                print(f"Enabling research mode due to indicator: {indicator}")
                return True
                
        return False
        
    def process_user_input(self, user_input):
        """
        Process user input and generate a response.
        
        This method handles all user input, including:
        - Regular text-based questions and requests
        - Research commands (prefixed with '/research')
        - Document editing requests
        
        It updates the chat history with the user input and the generated response,
        and handles any special actions needed based on the response content.
        
        Args:
            user_input (str): The text input from the user
        """
        # Check if this is a research command
        if user_input.startswith("/research "):
            research_query = user_input[len("/research "):].strip()
            if self.on_research_request and research_query:
                # Reset any pending edits
                st.session_state.pending_edit = None
                
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"Research: {research_query}"
                })
                
                # Add temporary assistant message
                temp_idx = len(st.session_state.chat_history)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Researching... please wait."
                })
                
                try:
                    # Call the research handler with the query
                    result = self.on_research_request(research_query)
                    
                    # Update the temporary message with the result
                    st.session_state.chat_history[temp_idx]["content"] = result
                except Exception as e:
                    # Update temporary message with error
                    st.session_state.chat_history[temp_idx]["content"] = f"Error during research: {str(e)}"
                
                return
        
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Determine if we should use research mode based on the query
        research_mode = False
        if self.use_perplexity:
            research_mode = self._should_use_research_mode(user_input)
            
        # Get current document content to provide context to the LLM
        current_document = self._get_current_document()
        
        # Set up system prompt with document context if available
        if current_document:
            system_prompt = f"""
            You are a helpful AI assistant that helps the user work with documents.
            
            The current document content is:
            ```
            {current_document}
            ```
            
            For document editing:
            - When asked to edit, summarize or add to the document, provide the exact text to be added or modified
            - Begin your response with "I'll update the document with:" followed by the content
            - Use markdown formatting as appropriate
            
            For general questions:
            - Answer clearly and concisely
            - If relevant to the document, reference specific sections
            - For information that might be outdated in your training data, use the available functions
            
            For current events or information retrieval:
            - For general information or current events, use the search_with_perplexity function
            - For in-depth research questions, use the research_with_perplexity function
            """
        else:
            system_prompt = """
            You are a helpful AI assistant. The user is working on a new document.
            
            When the user asks you to create or draft content:
            - Generate appropriate markdown content based on their request
            - Begin your response with "I'll update the document with:" followed by the content
            - Use markdown formatting for headings, lists, emphasis, etc.
            
            For general questions:
            - Answer clearly and concisely
            - If asked about creating document structure, suggest markdown formats
            - For information that might be outdated in your training data, use the available functions
            
            For current events or information retrieval:
            - For general information or current events, use the search_with_perplexity function
            - For in-depth research questions, use the research_with_perplexity function
            """
            
        # Add temporary assistant message
        temp_idx = len(st.session_state.chat_history)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Thinking..."
        })
        
        # Generate LLM response with the appropriate system prompt
        try:
            # Pass research_mode when Perplexity is enabled
            if self.use_perplexity:
                response = self.llm_manager.generate_response(
                    prompt=user_input,
                    system_prompt=system_prompt,
                    research_mode=research_mode
                )
                # For compatibility with older code
                if isinstance(response, dict):
                    response_text = response.get("content", "")
                else:
                    response_text = response
            else:
                # Regular response without Perplexity
                response = self.llm_manager.generate_response(
                    prompt=user_input,
                    system_prompt=system_prompt
                )
                # For compatibility with older code
                if isinstance(response, dict):
                    response_text = response.get("content", "")
                else:
                    response_text = response
                
            # Check if this is a document edit request
            if response_text.startswith("I'll update the document with:"):
                # Extract the content after the prefix
                content_start = response_text.find("I'll update the document with:")
                if content_start >= 0:
                    content_start += len("I'll update the document with:")
                    new_content = response_text[content_start:].strip()
                    
                    # Store the edit suggestion in session state
                    st.session_state.pending_edit = new_content
                    
                    # Add the full response with our custom edit buttons
                    st.session_state.chat_history[temp_idx]["content"] = response_text
                    st.session_state.chat_history[temp_idx]["has_edit"] = True
                    
                    # The callback will handle the rerun
                    return
                    
            # Update the temporary message with the final response
            st.session_state.chat_history[temp_idx]["content"] = response_text
            
        except Exception as e:
            # Update the temporary message with error information
            st.session_state.chat_history[temp_idx]["content"] = f"Error generating response: {str(e)}"
            print(f"Error in process_user_input: {e}")
        
        # We don't need to rerun here as the callback function will handle it 