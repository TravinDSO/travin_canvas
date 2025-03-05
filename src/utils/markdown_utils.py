"""
Markdown Processing Utilities for Travin Canvas

This module provides utilities for processing and manipulating markdown content.
It handles parsing, formatting, and transforming markdown text to support
the collaborative document editing features of the Travin Canvas application.

Key features:
- Header-based document splitting and navigation
- Table of contents generation
- Markdown formatting and standardization
- Code block extraction and processing
- Document structure analysis

Dependencies:
- langchain_text_splitters: For semantic document splitting
- re: For regular expression pattern matching
"""

import re
from langchain_text_splitters import MarkdownHeaderTextSplitter

class MarkdownProcessor:
    """
    Processes and manipulates markdown content.
    
    This class provides a comprehensive set of utilities for working with
    markdown documents, including:
    - Document structure analysis and navigation
    - Header extraction and hierarchy management
    - Table of contents generation
    - Markdown formatting and standardization
    - Code block extraction and processing
    
    The processor is designed to support the document editing features
    of the Travin Canvas application, enabling intelligent document
    manipulation and enhancement.
    """
    
    def __init__(self):
        """Initialize the markdown processor."""
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
                ("#####", "Header 5"),
                ("######", "Header 6"),
            ]
        )
    
    def split_by_headers(self, markdown_text):
        """
        Split markdown text by headers.
        
        Args:
            markdown_text (str): The markdown text to split
            
        Returns:
            list: A list of document chunks split by headers
        """
        if not markdown_text.strip():
            return []
            
        try:
            return self.header_splitter.split_text(markdown_text)
        except Exception as e:
            print(f"Error splitting markdown by headers: {e}")
            return [{"content": markdown_text}]
    
    def extract_headers(self, markdown_text):
        """
        Extract headers from markdown text.
        
        Args:
            markdown_text (str): The markdown text to process
            
        Returns:
            list: A list of headers with their levels and text
        """
        header_pattern = r'^(#{1,6})\s+(.+)$'
        headers = []
        
        for line in markdown_text.split('\n'):
            match = re.match(header_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append({
                    "level": level,
                    "text": text
                })
                
        return headers
    
    def generate_table_of_contents(self, markdown_text):
        """
        Generate a table of contents from markdown text.
        
        Args:
            markdown_text (str): The markdown text to process
            
        Returns:
            str: A markdown-formatted table of contents
        """
        headers = self.extract_headers(markdown_text)
        if not headers:
            return ""
            
        toc = ["# Table of Contents\n"]
        
        for header in headers:
            # Skip the title (H1) if it's the first header
            if header["level"] == 1 and headers.index(header) == 0:
                continue
                
            indent = "  " * (header["level"] - 1)
            link_text = header["text"]
            link_target = header["text"].lower().replace(" ", "-")
            toc.append(f"{indent}- [{link_text}](#{link_target})")
            
        return "\n".join(toc)
    
    def format_markdown(self, markdown_text):
        """
        Format markdown text for consistent styling.
        
        Args:
            markdown_text (str): The markdown text to format
            
        Returns:
            str: The formatted markdown text
        """
        # Ensure consistent newlines
        formatted_text = markdown_text.replace('\r\n', '\n')
        
        # Ensure headers have space after #
        header_pattern = r'^(#{1,6})([^ #])'
        formatted_text = re.sub(header_pattern, r'\1 \2', formatted_text, flags=re.MULTILINE)
        
        # Ensure lists have space after bullet
        list_pattern = r'^(\s*[-*+])([^ ])'
        formatted_text = re.sub(list_pattern, r'\1 \2', formatted_text, flags=re.MULTILINE)
        
        # Ensure consistent spacing between sections
        section_pattern = r'(\n#{1,6} .+\n)([^\n])'
        formatted_text = re.sub(section_pattern, r'\1\n\2', formatted_text)
        
        return formatted_text
    
    def extract_code_blocks(self, markdown_text):
        """
        Extract code blocks from markdown text.
        
        Args:
            markdown_text (str): The markdown text to process
            
        Returns:
            list: A list of code blocks with language and content
        """
        code_block_pattern = r'```(\w*)\n(.*?)```'
        code_blocks = []
        
        for match in re.finditer(code_block_pattern, markdown_text, re.DOTALL):
            language = match.group(1) or "text"
            content = match.group(2)
            code_blocks.append({
                "language": language,
                "content": content
            })
            
        return code_blocks