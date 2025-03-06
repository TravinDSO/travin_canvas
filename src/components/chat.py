"""
Chat Interface Component for Travin Canvas

This module provides the chat interface component for the Travin Canvas application.
It handles all user interactions with the LLM, including text input, speech-to-text,
text-to-speech capabilities, and research commands. The component creates a
conversational experience that integrates with the markdown canvas.

Key features:
- Text-based chat with OpenAI's GPT models using function calling
- Integration with Perplexity AI for search and research capabilities
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
            
        # Add system message to inform the LLM about its capabilities
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
            
            # Text input
            user_input = st.text_area("Type your message", key="user_input", height=100)
            
            # Speech input
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎤 Record", use_container_width=True):
                    st.session_state.recording = True
                    st.rerun()
            
            with col2:
                if st.button("🧹 Clear Chat", use_container_width=True):
                    self.clear_chat_history()
                    st.rerun()
            
            # Handle recording state
            if st.session_state.recording:
                with st.spinner("Recording... (Click Stop when finished)"):
                    if st.button("⏹️ Stop Recording", use_container_width=True):
                        st.session_state.recording = False
                        
                        # Process the audio
                        try:
                            audio_file = self.audio_processor.stop_recording()
                            if audio_file:
                                st.session_state.audio_file = audio_file
                                
                                # Transcribe the audio
                                with st.spinner("Transcribing..."):
                                    transcription = self.audio_processor.transcribe_audio(audio_file)
                                    if transcription:
                                        # Set the transcription as user input
                                        st.session_state.user_input = transcription
                                        st.rerun()
                        except Exception as e:
                            st.error(f"Error processing audio: {e}")
                            st.session_state.recording = False
                    
                    # Start recording if not already started
                    if not self.audio_processor.is_recording():
                        self.audio_processor.start_recording()
            
            # Send button
            if st.button("Send", use_container_width=True, type="primary"):
                if user_input:
                    # Process the user input
                    self.process_user_input(user_input)
                    
                    # Clear the input
                    st.session_state.user_input = ""
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
        """Process user input and generate a response."""
        if not user_input:
            return
            
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Check if this is a research command
        if user_input.startswith("/research"):
            # Extract the research query
            query = user_input[9:].strip()
            if query:
                if self.on_research_request:
                    response = self.on_research_request(query)
                else:
                    response = "Research command handler not configured."
            else:
                response = "Please provide a research query after /research"
                
        else:
            # Get current document content to provide context to the LLM
            current_document = self._get_current_document()
            
            # Check if the user is asking to summarize or use previous content
            summarize_indicators = [
                "summarize", "summary", "generate a summary", "create a summary", 
                "put this in", "add this to", "update the document", "update document",
                "add to document", "add to the document", "put in document", "put in the document",
                "create document", "create a document", "make a document", "make document",
                "edit document", "edit the document", "write document", "write a document",
                "generate document", "generate a document"
            ]
            is_summarize_request = any(indicator in user_input.lower() for indicator in summarize_indicators)
            
            # If this is a summarize request and we have previous messages
            if is_summarize_request and len(st.session_state.chat_history) >= 2:
                # Get the last assistant message
                last_assistant_message = None
                for msg in reversed(st.session_state.chat_history):
                    if msg["role"] == "assistant":
                        last_assistant_message = msg["content"]
                        break
                
                if last_assistant_message:
                    # Create a special system message for summarization
                    system_message = f"""
                    The user wants you to summarize or add the content from your previous response to the document.
                    
                    Here is your previous response that should be summarized or added to the document:
                    ```
                    {last_assistant_message}
                    ```
                    
                    Current document content:
                    ```
                    {current_document}
                    ```
                    
                    IMPORTANT: You MUST respond with "I'll update the document with:" followed by a well-formatted version
                    of the content that should be added to the document. Focus ONLY on the factual content from
                    your previous response, not on system instructions or capabilities.
                    
                    For example, if your previous response contained news headlines, create a well-formatted summary
                    of those headlines. Do NOT include any meta-commentary about your capabilities or functions.
                    
                    The document should be in Markdown format with appropriate headings, bullet points, etc.
                    """
                    
                    # Generate response with the special system message
                    with st.spinner("Thinking..."):
                        response = self.llm_manager.generate_response(
                            prompt=user_input,
                            system_prompt=system_message,
                            research_mode=False
                        )
                else:
                    # Add regular document context as a system message
                    self.llm_manager.add_message("system", f"""
                    Current document content:
                    ```
                    {current_document}
                    ```
                    
                    You have two main responsibilities:
                    
                    1. Help with document editing when the user asks about creating, editing, or modifying the document.
                       When doing this, respond with "I'll update the document with:" followed by the content.
                    
                    2. Answer general questions and provide information using your functions:
                       - For general information or current events, use the search_with_perplexity function
                       - For in-depth research questions, use the research_with_perplexity function
                    
                    If the user is asking about news, current events, or information that requires up-to-date knowledge,
                    ALWAYS use one of your search functions rather than responding from your training data.
                    """)
                    
                    # Check if we should use research mode
                    research_mode = self._should_use_research_mode(user_input)
                    
                    # Generate response with the LLM
                    with st.spinner("Thinking..."):
                        response = self.llm_manager.generate_response(
                            prompt=user_input, 
                            research_mode=research_mode
                        )
            else:
                # Add regular document context as a system message
                self.llm_manager.add_message("system", f"""
                Current document content:
                ```
                {current_document}
                ```
                
                You have two main responsibilities:
                
                1. Help with document editing when the user asks about creating, editing, or modifying the document.
                   When doing this, respond with "I'll update the document with:" followed by the content.
                
                2. Answer general questions and provide information using your functions:
                   - For general information or current events, use the search_with_perplexity function
                   - For in-depth research questions, use the research_with_perplexity function
                
                If the user is asking about news, current events, or information that requires up-to-date knowledge,
                ALWAYS use one of your search functions rather than responding from your training data.
                """)
                
                # Check if we should use research mode
                research_mode = self._should_use_research_mode(user_input)
                
                # Generate response with the LLM
                with st.spinner("Thinking..."):
                    response = self.llm_manager.generate_response(
                        prompt=user_input, 
                        research_mode=research_mode
                    )
            
            # Check if we should play the response as audio
            if "audio_enabled" in st.session_state and st.session_state.audio_enabled:
                try:
                    with st.spinner("Generating audio..."):
                        audio_file = self.audio_processor.text_to_speech(response)
                        if audio_file:
                            st.audio(audio_file)
                except Exception as e:
                    st.error(f"Error generating audio: {e}")
        
        # Add assistant message to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.rerun() 