"""
Chat Interface Component for Travin Canvas

This module provides the chat interface component for the Travin Canvas application.
It handles all user interactions with the LLM, including text input, speech-to-text,
text-to-speech capabilities, and research commands. The component creates a
conversational experience that integrates with the markdown canvas.

Key features:
- Text-based chat with OpenAI's GPT models
- Speech-to-text input using OpenAI's Whisper API
- Text-to-speech responses using OpenAI's TTS API
- Support for research commands via n8n webhooks
- Document-aware conversations with context management

Dependencies:
- streamlit: For UI components
- utils.llm_utils: For LLM interactions
- utils.audio_utils: For speech processing
- utils.webhook_utils: For external integrations
"""

import os
import time
import streamlit as st
from utils.llm_utils import LLMManager
from utils.audio_utils import AudioProcessor
from utils.webhook_utils import WebhookManager

class ChatInterface:
    """
    Implements the chat interface for the Travin Canvas application.
    
    This class manages the entire chat experience, including:
    - Conversation history storage and rendering
    - User input handling (text and speech)
    - LLM response generation and playback
    - Research command processing
    - Document edit suggestions and confirmations
    
    The interface is rendered in the Streamlit sidebar and maintains
    its state between application reruns using session state.
    """
    
    def __init__(self, on_research_request=None):
        """
        Initialize the chat interface.
        
        Args:
            on_research_request (callable, optional): Callback for research requests
        """
        self.llm_manager = LLMManager()
        self.audio_processor = AudioProcessor()
        self.webhook_manager = WebhookManager(verify_ssl=False)  # Disable SSL verification
        self.on_research_request = on_research_request
        
        # Initialize session state for chat history if not exists
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        if "recording" not in st.session_state:
            st.session_state.recording = False
            
        if "audio_file" not in st.session_state:
            st.session_state.audio_file = None
            
        if "pending_edit" not in st.session_state:
            st.session_state.pending_edit = None
            
        if "edit_confirmed" not in st.session_state:
            st.session_state.edit_confirmed = False
            
        # Add system message to inform the LLM about document editing capabilities
        self.add_system_message("""
        You can help the user with their document in a natural, conversational way.
        
        When the user asks you to create, format, edit, or modify their document:
        1. Understand what changes they want to make
        2. Generate the appropriate content or modifications
        3. Use the phrase "I'll update the document with:" followed by the content
        
        For example, if a user says "Create a document about making a PB&J sandwich",
        you should respond with something like:
        
        "I'll update the document with:
        
        # How to Make a PB&J Sandwich
        
        ## Ingredients
        - 2 slices of bread
        - Peanut butter
        - Jelly or jam
        
        ## Instructions
        1. Lay out the bread slices
        2. Spread peanut butter on one slice
        3. Spread jelly on the other slice
        4. Press the slices together
        5. Enjoy your sandwich!"
        
        The system will detect this pattern and update the document automatically.
        """)
    
    def render(self):
        """Render the chat interface."""
        st.sidebar.title("Chat Interface")
        
        # Display chat messages
        for message in st.session_state.chat_history:
            with st.sidebar.chat_message(message["role"]):
                st.write(message["content"])
                
                # If this is the last assistant message and there's a pending edit, show confirmation buttons
                if (message["role"] == "assistant" and 
                    st.session_state.pending_edit is not None and 
                    message == st.session_state.chat_history[-1]):
                    self._render_edit_confirmation_buttons()
        
        # Chat input
        user_input = st.sidebar.chat_input("Type your message here")
        
        # Voice input controls
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎤 Start Recording", disabled=st.session_state.recording):
                st.session_state.recording = True
                st.session_state.audio_file = None
                st.rerun()
                
        with col2:
            if st.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
                st.session_state.recording = False
                st.rerun()
        
        # Handle recording
        if st.session_state.recording:
            st.sidebar.info("Recording... Speak now")
            audio_file = self.audio_processor.start_recording(max_seconds=10)
            st.session_state.audio_file = audio_file
            st.session_state.recording = False
            st.rerun()
            
        # Process audio file if exists
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
            transcript = self.audio_processor.transcribe_audio(st.session_state.audio_file)
            if transcript:
                user_input = transcript
                # Clean up the audio file
                try:
                    os.remove(st.session_state.audio_file)
                except:
                    pass
                st.session_state.audio_file = None
        
        # Text-to-speech toggle
        st.sidebar.divider()
        tts_enabled = st.sidebar.checkbox("Enable Text-to-Speech", value=False)
        
        if tts_enabled:
            voice_options = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            selected_voice = st.sidebar.selectbox("Select Voice", voice_options)
        else:
            selected_voice = "alloy"  # Default voice
        
        # Process user input
        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Check for research commands (keeping this explicit command for research)
            if user_input.lower().startswith("/research"):
                query = user_input[9:].strip()
                if query and self.on_research_request:
                    # Call the research request handler and get the response
                    response = self.on_research_request(query)
                    
                    # If no response was returned, provide a default message
                    if not response:
                        response = f"Researching: {query}"
                else:
                    response = "Please provide a research query after /research"
            else:
                # For document editing, we'll analyze the user's intent
                # Get current document content to provide context to the LLM
                current_document = self._get_current_document()
                
                # Add document context as a system message before generating response
                self.llm_manager.add_message("system", f"""
                Current document content:
                ```
                {current_document}
                ```
                
                If the user is asking to create, view, format, edit, or modify the document,
                respond with "I'll update the document with:" followed by the complete content.
                """)
                
                # Generate LLM response
                response = self.llm_manager.generate_response(prompt=user_input)
                
                # Check if the response contains document update indicator
                if "I'll update the document with:" in response:
                    # Extract the content after the indicator
                    parts = response.split("I'll update the document with:", 1)
                    if len(parts) > 1:
                        # Get the content part
                        content_part = parts[1].strip()
                        
                        # Store the pending edit
                        st.session_state.pending_edit = content_part
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Text-to-speech if enabled
            if tts_enabled:
                audio_file = self.audio_processor.text_to_speech(response, voice=selected_voice)
                if audio_file:
                    self.audio_processor.play_audio(audio_file)
                    # Clean up the audio file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
            
            st.rerun()
    
    def _render_edit_confirmation_buttons(self):
        """Render confirmation buttons for document edits."""
        st.markdown("**Document update ready to apply:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Apply Changes", key="apply_changes_inline"):
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
            if st.button("❌ Cancel", key="cancel_changes_inline"):
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
        """Clear the chat history."""
        st.session_state.chat_history = []
        self.llm_manager.clear_conversation_history()
    
    def add_system_message(self, content):
        """
        Add a system message to the conversation.
        
        Args:
            content (str): The content of the system message
        """
        self.llm_manager.add_message("system", content) 