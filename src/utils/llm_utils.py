"""
LLM Utilities for Travin Canvas

This module provides utilities for interacting with Large Language Models (LLMs).
It handles chat completions, prompt formatting, and context management to enable
intelligent conversations in the Travin Canvas application.

Key features:
- OpenAI API integration for chat completions
- Conversation history management
- Specialized prompt templates for document operations
- Document summarization and enhancement capabilities
- Error handling and retry logic

Dependencies:
- openai: For API access to OpenAI models
- httpx: For custom HTTP client configuration
- dotenv: For environment variable management
"""

import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Create a custom httpx client without proxies
http_client = httpx.Client()

# Initialize OpenAI client with the custom httpx client
# This avoids the 'proxies' parameter issue in the newer OpenAI SDK
client = OpenAI(api_key=api_key, http_client=http_client)

class LLMManager:
    """
    Manages interactions with Large Language Models.
    
    This class provides a comprehensive interface for working with LLMs,
    handling all aspects of the interaction including:
    - Conversation history management
    - Message formatting and prompt engineering
    - API calls with error handling
    - Response processing and parsing
    
    It supports both general chat completions and specialized document
    operations like summarization, enhancement, and editing.
    """
    
    def __init__(self, model="o3-mini"):
        """
        Initialize the LLM manager with the specified model.
        
        Args:
            model (str): The LLM model to use
        """
        self.model = model
        self.conversation_history = []
        
    def add_message(self, role, content):
        """
        Add a message to the conversation history.
        
        Args:
            role (str): The role of the message sender (user, assistant, system)
            content (str): The content of the message
        """
        self.conversation_history.append({"role": role, "content": content})
        
    def get_conversation_history(self):
        """
        Get the current conversation history.
        
        Returns:
            list: The conversation history
        """
        return self.conversation_history
        
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        
    def generate_response(self, prompt=None, system_prompt=None):
        """
        Generate a response from the LLM based on the conversation history.
        
        Args:
            prompt (str, optional): A new user prompt to add to the conversation
            system_prompt (str, optional): A system prompt to add to the conversation
            
        Returns:
            str: The generated response
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add new prompt if provided
        if prompt:
            messages.append({"role": "user", "content": prompt})
            
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            response_text = response.choices[0].message.content
            
            # Add the new messages to the conversation history
            if prompt:
                self.add_message("user", prompt)
            self.add_message("assistant", response_text)
            
            return response_text
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return f"Error: {str(e)}"
    
    def generate_markdown_summary(self, markdown_text):
        """
        Generate a summary of markdown content.
        
        Args:
            markdown_text (str): The markdown text to summarize
            
        Returns:
            str: A summary of the markdown content
        """
        prompt = f"""
        Please summarize the following markdown document:
        
        {markdown_text}
        
        Provide a concise summary that captures the main points and structure.
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating markdown summary: {e}")
            return f"Error: {str(e)}"
    
    def enhance_markdown(self, markdown_text, enhancement_type="grammar"):
        """
        Enhance markdown content based on the specified enhancement type.
        
        Args:
            markdown_text (str): The markdown text to enhance
            enhancement_type (str): The type of enhancement to apply
                (grammar, clarity, conciseness, expansion)
                
        Returns:
            str: The enhanced markdown content
        """
        enhancement_prompts = {
            "grammar": "Improve the grammar and spelling of the following markdown content while preserving its structure and formatting:",
            "clarity": "Improve the clarity of the following markdown content, making it easier to understand while preserving its structure and formatting:",
            "conciseness": "Make the following markdown content more concise while preserving its key information, structure, and formatting:",
            "expansion": "Expand on the following markdown content with additional relevant details while preserving its structure and formatting:"
        }
        
        prompt = f"""
        {enhancement_prompts.get(enhancement_type, enhancement_prompts["grammar"])}
        
        {markdown_text}
        
        Return only the enhanced markdown content without additional comments.
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error enhancing markdown: {e}")
            return markdown_text
    
    def edit_document(self, document_content, edit_instruction):
        """
        Edit a document based on the provided instruction.
        
        Args:
            document_content (str): The current document content
            edit_instruction (str): Instructions for how to edit the document
            
        Returns:
            str: The edited document content
        """
        system_prompt = """
        You are a document editing assistant. Your task is to edit the provided document 
        according to the user's instructions. Maintain the document's original structure 
        and formatting unless explicitly instructed to change it. Return the complete 
        edited document with all changes applied.
        """
        
        user_prompt = f"""
        # Original Document:
        ```
        {document_content}
        ```
        
        # Edit Instructions:
        {edit_instruction}
        
        Please return the complete edited document with all changes applied.
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            edited_content = response.choices[0].message.content
            
            # Extract the document content if it's wrapped in markdown code blocks
            if "```" in edited_content:
                # Try to extract content between code blocks
                import re
                code_blocks = re.findall(r'```(?:markdown)?\n(.*?)```', edited_content, re.DOTALL)
                if code_blocks:
                    edited_content = code_blocks[0]
            
            return edited_content
        except Exception as e:
            print(f"Error editing document: {e}")
            return document_content 