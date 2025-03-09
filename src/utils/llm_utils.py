"""
LLM Utilities for Travin Canvas

This module provides utilities for interacting with Large Language Models (LLMs).
It handles chat completions, prompt formatting, and context management to enable
intelligent conversations in the Travin Canvas application.

Key features:
- OpenAI API integration for chat completions with function calling
- Perplexity AI integration for research and information gathering
- Conversation history management
- Specialized prompt templates for document operations
- Document summarization and enhancement capabilities
- Error handling and retry logic

Dependencies:
- openai: For API access to OpenAI models
- httpx: For custom HTTP client configuration
- dotenv: For environment variable management
- tools.perplexity: For Perplexity AI integration
"""

import os
import json
import httpx
from typing import Optional, List, Dict, Any
from openai import OpenAI
from openai import AzureOpenAI
from dotenv import load_dotenv
from tools.perplexity import PerplexityTool

# Load environment variables
load_dotenv()

# Initialize Azure configuration if USE_AZURE is True
use_azure = os.getenv("USE_AZURE", "false").lower() == "true"
if use_azure:
    azure_api_key = os.getenv("AZURE_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION") #"2024-12-01-preview"
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_model = os.getenv("AZURE_MODEL")
    print(f"API Version from env: '{azure_api_version}'")
else:
    # Initialize OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")



# Initialize Perplexity configuration
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
# Strip any comments from the model names
perplexity_model = os.getenv("PERPLEXITY_MODEL", "sonar-reasoning")
if perplexity_model and "#" in perplexity_model:
    perplexity_model = perplexity_model.split("#")[0].strip()
    
perplexity_research_model = os.getenv("PERPLEXITY_RESEARCH_MODEL", "sonar-deep-research")
if perplexity_research_model and "#" in perplexity_research_model:
    perplexity_research_model = perplexity_research_model.split("#")[0].strip()
    
if not perplexity_api_key:
    print("Warning: PERPLEXITY_API_KEY environment variable is not set")

# Create a custom httpx client without proxies
http_client = httpx.Client()

if use_azure:
    # Initialize Azure client with the custom httpx client
    client = AzureOpenAI(api_key=azure_api_key,api_version=azure_api_version,azure_endpoint=azure_endpoint,http_client=http_client)
else:
    # Initialize OpenAI client with the custom httpx client
    # This avoids the 'proxies' parameter issue in the newer OpenAI SDK
    client = OpenAI(api_key=openai_api_key, http_client=http_client)

# Define function schemas for OpenAI function calling
PERPLEXITY_SEARCH_FUNCTION = {
    "type": "function",
    "function": {
        "name": "search_with_perplexity",
        "description": "Search the internet for current information, news, events, or facts using Perplexity AI. Use this for any questions about current events, news, or information that might be outdated in your training data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find information about"
                }
            },
            "required": ["query"]
        }
    }
}

PERPLEXITY_RESEARCH_FUNCTION = {
    "type": "function",
    "function": {
        "name": "research_with_perplexity",
        "description": "Perform deep research on a topic using Perplexity AI's specialized research model. Use this for comprehensive analysis, detailed explanations, or when citations are needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research query to investigate in depth"
                }
            },
            "required": ["query"]
        }
    }
}

class LLMManager:
    """
    Manages interactions with Large Language Models.
    
    This class provides a comprehensive interface for working with LLMs,
    handling all aspects of the interaction including:
    - Conversation history management
    - Message formatting and prompt engineering
    - API calls with error handling and function calling
    - Response processing and parsing
    - Research and information gathering via Perplexity AI
    
    It supports both general chat completions and specialized document
    operations like summarization, enhancement, and editing.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the LLM manager with the specified model.
        
        Args:
            model (str, optional): The LLM model to use. If not provided, uses OPENAI_MODEL from env
        """
        if use_azure:
            self.model = azure_model
        else:
            self.model = model or openai_model
        self.conversation_history = []
        self.perplexity = None
        if perplexity_api_key:
            self.perplexity = PerplexityTool(
                api_key=perplexity_api_key,
                default_model=perplexity_model
            )
            # Store the research model name for later use
            self.perplexity_research_model = perplexity_research_model
        
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
        
    def search_with_perplexity(self, query: str) -> Optional[str]:
        """
        Search for information using Perplexity AI's standard model.
        
        Args:
            query (str): The search query
            
        Returns:
            Optional[str]: The search results with citations, or None if unavailable
        """
        if not self.perplexity:
            print("Warning: Perplexity AI not available - PERPLEXITY_API_KEY not set")
            return None
            
        try:
            return self.perplexity.ask_question(query, model=self.perplexity.default_model)
        except Exception as e:
            print(f"Error searching with Perplexity: {e}")
            return None
            
    def research_with_perplexity(self, query: str) -> Optional[str]:
        """
        Perform deep research using Perplexity AI's research model.
        
        Args:
            query (str): The research query to investigate in depth
            
        Returns:
            Optional[str]: The research results with citations, or None if unavailable
        """
        if not self.perplexity:
            print("Warning: Perplexity AI not available - PERPLEXITY_API_KEY not set")
            return None
            
        try:
            return self.perplexity.ask_question(query, model=self.perplexity_research_model)
        except Exception as e:
            print(f"Error researching with Perplexity: {e}")
            return None
    
    def research_topic(self, query: str) -> Optional[str]:
        """
        Research a topic using Perplexity AI.
        
        This method uses Perplexity AI to gather detailed information and citations
        about a specific topic or question. It's particularly useful when the LLM
        needs additional context or up-to-date information.
        
        Args:
            query (str): The research query or topic to investigate
            
        Returns:
            Optional[str]: The research results with citations, or None if unavailable
        """
        if not self.perplexity:
            print("Warning: Perplexity AI not available - PERPLEXITY_API_KEY not set")
            return None
            
        try:
            # Use the deep research model for comprehensive results
            return self.perplexity.ask_question(query, model=self.perplexity_research_model)
        except Exception as e:
            print(f"Error researching topic: {e}")
            return None
            
    def generate_response(self, prompt=None, system_prompt=None, research_mode=False):
        """
        Generate a response from the LLM based on the conversation history.
        
        Args:
            prompt (str, optional): A new user prompt to add to the conversation
            system_prompt (str, optional): A system prompt to add to the conversation
            research_mode (bool, optional): Whether to use Perplexity AI for research
            
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
            # Check if this is a document editing request
            is_document_request = False
            if system_prompt and any(phrase in system_prompt for phrase in [
                "summarize or add the content", 
                "add to the document", 
                "update the document"
            ]):
                is_document_request = True
                print("Detected document editing request")
            
            # Define available tools based on Perplexity availability
            tools = []
            if self.perplexity and not is_document_request:
                tools = [PERPLEXITY_SEARCH_FUNCTION, PERPLEXITY_RESEARCH_FUNCTION]
            
            # Default to auto tool choice
            tool_choice = "auto"
            
            # Check if the prompt contains keywords that suggest using search
            if prompt and self.perplexity and tools and not is_document_request:
                search_keywords = ["news", "latest", "current", "recent", "today", "headlines", "what is", "who is", "where is", "when did", "how to", "tell me about"]
                lower_prompt = prompt.lower()
                
                for keyword in search_keywords:
                    if keyword in lower_prompt:
                        # Force the model to use the search function
                        tool_choice = {
                            "type": "function",
                            "function": {"name": "search_with_perplexity"}
                        }
                        print(f"Forcing search function for keyword: {keyword}")
                        break
            
            # If research mode is enabled, override and force research function
            if research_mode and self.perplexity and not is_document_request:
                tool_choice = {
                    "type": "function",
                    "function": {"name": "research_with_perplexity"}
                }
                print("Forcing research function due to research_mode=True")
            
            print(f"Using tool_choice: {tool_choice}")
            
            # Make the initial API call with function calling enabled
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice=tool_choice if tools else None
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call a function
            if response_message.tool_calls:
                print(f"Model decided to use function: {response_message.tool_calls[0].function.name}")
                
                # Process each tool call
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Executing {function_name} with query: {function_args.get('query')}")
                    
                    # Execute the appropriate function
                    function_response = None
                    if function_name == "search_with_perplexity":
                        function_response = self.search_with_perplexity(function_args.get("query"))
                    elif function_name == "research_with_perplexity":
                        function_response = self.research_with_perplexity(function_args.get("query"))
                    
                    # Add the function response to messages
                    if function_response:
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": function_name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            ]
                        })
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": function_response
                        })
                
                # Make a second API call to get the final response
                second_response = client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                
                response_text = second_response.choices[0].message.content
            else:
                print("Model did not use any functions")
                # If no function was called, use the original response
                response_text = response_message.content
            
            # Add the new messages to the conversation history
            if prompt:
                self.add_message("user", prompt)
            self.add_message("assistant", response_text)
            
            return response_text
        except Exception as e:
            print(f"Error generating LLM response: Use Azure={use_azure}|Model={self.model}|Error={e}")
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