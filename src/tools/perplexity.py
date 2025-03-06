"""
Perplexity API Tool for Travin Canvas

This module provides a tool for interacting with the Perplexity AI API.
It handles chat completions and question answering capabilities to enable
intelligent responses in the Travin Canvas application.

Key features:
- Integration with Perplexity AI's chat completion API
- Question answering with citations
- Customizable model parameters
- Error handling and response formatting

Dependencies:
- requests: For API communication
"""

import requests
from typing import Optional, Dict, Any

class PerplexityTool:
    """
    Tool for interacting with Perplexity AI's API.
    
    This class provides a comprehensive interface for working with the Perplexity AI API,
    handling all aspects of the interaction including:
    - API authentication
    - Question answering with citations
    - Response formatting and error handling
    - Customizable model parameters
    
    The tool is designed to work seamlessly with the chat interface
    to enable AI-powered question answering capabilities.
    
    Available models:
    - sonar-reasoning (best for research and analysis)
    - sonar-reasoning-pro (enhanced research capabilities)
    - sonar-deep-research (specialized for in-depth research)
    - sonar-small (faster, less detailed)
    - sonar-medium (balanced performance)
    - sonar-large (most comprehensive)
    """
    
    # Available models and their descriptions
    AVAILABLE_MODELS = {
        "sonar-reasoning": "Best for research and analysis",
        "sonar-reasoning-pro": "Enhanced research capabilities with improved reasoning",
        "sonar-deep-research": "Specialized for in-depth research with comprehensive citations",
        "sonar-small": "Faster, less detailed responses",
        "sonar-medium": "Balanced performance and detail",
        "sonar-large": "Most comprehensive responses"
    }
    
    def __init__(self, api_key: str, default_model: str = "sonar-reasoning"):
        """
        Initialize the Perplexity API tool.
        
        Args:
            api_key (str): Your API key for authenticating requests
            default_model (str, optional): Default model to use. Defaults to "sonar-reasoning"
        
        Raises:
            ValueError: If api_key is empty or default_model is not in AVAILABLE_MODELS
        """
        if not api_key:
            raise ValueError("Perplexity API key is required")
            
        if default_model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model. Available models: {', '.join(self.AVAILABLE_MODELS.keys())}")
            
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
    def ask_question(self, question: str, model: Optional[str] = None) -> Optional[str]:
        """
        Send a question to the Perplexity AI API and get a response.
        
        Args:
            question (str): The question to ask
            model (str, optional): The model to use for the response. 
                                 If not provided, uses the default model.
            
        Returns:
            Optional[str]: The formatted response with answer and citations, or None if an error occurs
            
        Raises:
            ValueError: If model is provided but not in AVAILABLE_MODELS
        """
        if not question.strip():
            print("Error: Question cannot be empty")
            return None
            
        if model and model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model. Available models: {', '.join(self.AVAILABLE_MODELS.keys())}")
            
        payload = self._build_payload(question, model or self.default_model)
        headers = self._get_headers()
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return self._format_response(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Perplexity API: {e}")
            return None
            
    def _build_payload(self, question: str, model: str) -> Dict[str, Any]:
        """
        Build the payload for the API request.
        
        Args:
            question (str): The question to ask
            model (str): The model to use
            
        Returns:
            Dict[str, Any]: The formatted payload
        """
        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Be precise and concise."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.2,
            "top_p": 0.9,
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "month",
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1
        }
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for the API request.
        
        Returns:
            Dict[str, str]: The request headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def _format_response(self, response_data: Dict[str, Any]) -> str:
        """
        Format the API response into a readable string.
        
        Args:
            response_data (Dict[str, Any]): The raw API response
            
        Returns:
            str: The formatted response string
        """
        formatted_text = "Answer:\n"
        
        # Add the main response
        for choice in response_data.get('choices', []):
            if message := choice.get('message', {}):
                formatted_text += message.get('content', '')
                
        # Add citations if available
        if citations := response_data.get('citations', []):
            formatted_text += "\n\nCitations:\n"
            for citation in citations:
                formatted_text += f"- {citation}\n"
                
        return formatted_text

# Example Usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("Error: PERPLEXITY_API_KEY environment variable not set")
    else:
        # Initialize tool with API key and optional model
        perplexity = PerplexityTool(
            api_key=api_key,
            default_model=os.getenv("PERPLEXITY_MODEL", "sonar-reasoning")
        )
        
        # Ask a question
        result = perplexity.ask_question("What is the capital of France?")
        if result:
            print(result)