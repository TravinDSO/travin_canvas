"""
Markdown Canvas Component for Travin Canvas

This module provides the canvas component for the Travin Canvas application.
It implements a collaborative markdown editor with real-time preview,
formatting tools, and document management features to support
document drafting and refinement.

Key features:
- Split-view markdown editor with real-time preview
- Document enhancement tools powered by LLM
- Document history with undo capability
- File import and export functionality
- Table of contents generation

Dependencies:
- streamlit: For UI components
- utils.markdown_utils: For markdown processing
- utils.llm_utils: For LLM-powered enhancements
"""

import os
import json
import streamlit as st
from utils.markdown_utils import MarkdownProcessor
from utils.llm_utils import LLMManager

class MarkdownCanvas:
    """
    Implements the markdown canvas for the Travin Canvas application.
    
    This class manages the document editing experience, including:
    - Markdown editing with syntax highlighting
    - Real-time preview rendering
    - Document enhancement tools (grammar, clarity, etc.)
    - Document history management with undo capability
    - File operations (save, load, download)
    
    The canvas is rendered in the main content area and maintains
    its state between application reruns using session state.
    """
    
    def __init__(self, on_content_change=None):
        """
        Initialize the markdown canvas.
        
        Args:
            on_content_change (callable, optional): Callback for content changes
        """
        self.markdown_processor = MarkdownProcessor()
        self.llm_manager = LLMManager()
        self.on_content_change = on_content_change
        
        # Initialize session state for markdown content if not exists
        if "markdown_content" not in st.session_state:
            st.session_state.markdown_content = ""
            
        if "show_preview" not in st.session_state:
            st.session_state.show_preview = True
            
        if "current_file" not in st.session_state:
            st.session_state.current_file = None
            
        # Initialize undo history
        if "undo_history" not in st.session_state:
            st.session_state.undo_history = []
            
        if "max_history" not in st.session_state:
            st.session_state.max_history = 10
    
    def render(self):
        """Render the markdown canvas."""
        st.title("Markdown Canvas")
        
        # File operations
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("New Document"):
                # Save current state to history before clearing
                self._save_to_history()
                st.session_state.markdown_content = ""
                st.session_state.current_file = None
                st.rerun()
                
        with col2:
            uploaded_file = st.file_uploader("Upload Markdown", type=["md", "txt"], label_visibility="collapsed")
            if uploaded_file:
                # Save current state to history before loading new file
                self._save_to_history()
                st.session_state.markdown_content = uploaded_file.getvalue().decode("utf-8")
                st.session_state.current_file = uploaded_file.name
                st.rerun()
                
        with col3:
            if st.button("Download Markdown"):
                self._download_markdown()
                
        with col4:
            if st.button("Undo", disabled=len(st.session_state.undo_history) == 0):
                self._undo_last_change()
        
        # Display current file name
        if st.session_state.current_file:
            st.caption(f"Current file: {st.session_state.current_file}")
        
        # Toggle preview mode
        st.session_state.show_preview = st.checkbox("Show Preview", value=st.session_state.show_preview)
        
        # Editor and preview
        if st.session_state.show_preview:
            edit_col, preview_col = st.columns(2)
            
            with edit_col:
                self._render_editor()
                
            with preview_col:
                self._render_preview()
        else:
            self._render_editor()
        
        # Enhancement tools
        st.divider()
        st.subheader("Enhancement Tools")
        
        enhancement_col1, enhancement_col2 = st.columns(2)
        
        with enhancement_col1:
            if st.button("Generate Table of Contents"):
                # Save current state to history before generating TOC
                self._save_to_history()
                toc = self.markdown_processor.generate_table_of_contents(st.session_state.markdown_content)
                if toc:
                    st.session_state.markdown_content = toc + "\n\n" + st.session_state.markdown_content
                    if self.on_content_change:
                        self.on_content_change(st.session_state.markdown_content)
                    st.rerun()
                    
            if st.button("Format Document"):
                # Save current state to history before formatting
                self._save_to_history()
                st.session_state.markdown_content = self.markdown_processor.format_markdown(st.session_state.markdown_content)
                if self.on_content_change:
                    self.on_content_change(st.session_state.markdown_content)
                st.rerun()
                
        with enhancement_col2:
            enhancement_type = st.selectbox(
                "Enhancement Type",
                ["grammar", "clarity", "conciseness", "expansion"],
                index=0
            )
            
            if st.button("Enhance with AI"):
                # Save current state to history before enhancing
                self._save_to_history()
                with st.spinner("Enhancing document..."):
                    enhanced_content = self.llm_manager.enhance_markdown(
                        st.session_state.markdown_content,
                        enhancement_type=enhancement_type
                    )
                    if enhanced_content:
                        st.session_state.markdown_content = enhanced_content
                        if self.on_content_change:
                            self.on_content_change(st.session_state.markdown_content)
                        st.rerun()
    
    def _render_editor(self):
        """Render the markdown editor."""
        st.subheader("Editor")
        
        # Markdown editor
        new_content = st.text_area(
            "Edit your document here",
            value=st.session_state.markdown_content,
            height=400,
            label_visibility="collapsed"
        )
        
        # Update content if changed
        if new_content != st.session_state.markdown_content:
            # Save current state to history before updating
            self._save_to_history()
            st.session_state.markdown_content = new_content
            if self.on_content_change:
                self.on_content_change(new_content)
    
    def _render_preview(self):
        """Render the markdown preview."""
        st.subheader("Preview")
        
        # Create a container with styling to ensure proper markdown rendering
        preview_container = st.container()
        
        with preview_container:
            if st.session_state.markdown_content:
                # Add custom CSS to ensure proper markdown rendering
                st.markdown("""
                <style>
                .preview-markdown {
                    border: 1px solid #eee;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: white;
                    overflow-y: auto;
                    max-height: 400px;
                }
                .preview-markdown h1 { margin-top: 0.5em; }
                .preview-markdown h2 { margin-top: 0.5em; }
                .preview-markdown h3 { margin-top: 0.5em; }
                .preview-markdown ul { margin-bottom: 1em; }
                .preview-markdown ol { margin-bottom: 1em; }
                </style>
                """, unsafe_allow_html=True)
                
                # Render the markdown content with proper formatting
                st.markdown('<div class="preview-markdown">', unsafe_allow_html=True)
                st.markdown(st.session_state.markdown_content, unsafe_allow_html=False)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Your document preview will appear here.")
    
    def _download_markdown(self):
        """Generate a download link for the markdown content."""
        if not st.session_state.markdown_content:
            st.warning("No content to download.")
            return
            
        filename = st.session_state.current_file or "document.md"
        st.download_button(
            label="Download",
            data=st.session_state.markdown_content,
            file_name=filename,
            mime="text/markdown",
            key="download_button"
        )
    
    def _save_to_history(self):
        """Save current content to undo history."""
        if st.session_state.markdown_content:
            # Add current content to history
            st.session_state.undo_history.append(st.session_state.markdown_content)
            
            # Limit history size
            if len(st.session_state.undo_history) > st.session_state.max_history:
                st.session_state.undo_history.pop(0)
    
    def _undo_last_change(self):
        """Restore the previous state from history."""
        if st.session_state.undo_history:
            # Get the last state from history
            previous_content = st.session_state.undo_history.pop()
            st.session_state.markdown_content = previous_content
            if self.on_content_change:
                self.on_content_change(previous_content)
            st.rerun()
    
    def get_content(self):
        """
        Get the current markdown content.
        
        Returns:
            str: The current markdown content
        """
        return st.session_state.markdown_content
    
    def set_content(self, content, save_history=True):
        """
        Set the markdown content.
        
        Args:
            content (str): The markdown content to set
            save_history (bool): Whether to save current content to history
        """
        if save_history:
            self._save_to_history()
            
        st.session_state.markdown_content = content
        if self.on_content_change:
            self.on_content_change(content) 