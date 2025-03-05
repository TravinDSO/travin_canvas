"""
Webhook Integration Utilities for Travin Canvas

This module provides utilities for interacting with n8n webhooks.
It handles sending requests to n8n workflows and processing responses
to integrate external data and automation into the Travin Canvas application.

Key features:
- Integration with n8n workflow automation platform
- Research request handling for external data retrieval
- Prompt enhancement for dynamic LLM interactions
- Response processing and error handling
- Context-aware request formatting

Dependencies:
- requests: For HTTP communication with webhooks
- json: For data serialization and deserialization
- dotenv: For environment variable management
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WebhookManager:
    """
    Manages interactions with n8n webhooks for research and dynamic LLM prompting.
    
    This class provides a comprehensive interface for working with n8n webhooks,
    handling all aspects of the integration including:
    - Sending research requests to external data sources
    - Enhancing prompts with external context and knowledge
    - Processing and validating webhook responses
    - Error handling and recovery
    - Context management for document-aware requests
    
    The webhook integration enables the Travin Canvas application to extend
    beyond its local capabilities by leveraging external workflows and services.
    """
    
    def __init__(self, verify_ssl=False):
        """
        Initialize the webhook manager with the webhook URL from environment variables.
        
        Args:
            verify_ssl (bool): Whether to verify SSL certificates. Set to False to bypass SSL verification.
        """
        webhook_url = os.getenv("N8N_WEBHOOK_URL")
        
        # Remove quotes if present
        if webhook_url:
            webhook_url = webhook_url.strip('"\'')
            
        self.webhook_url = webhook_url
        self.verify_ssl = verify_ssl
        
        if not self.webhook_url:
            print("Warning: N8N_WEBHOOK_URL not set in environment variables")
    
    def send_research_request(self, query, additional_context=None):
        """
        Send a research request to n8n for processing.
        
        Args:
            query (str): The research query to process
            additional_context (dict, optional): Additional context for the request
            
        Returns:
            dict: The processed research data from n8n
        """
        if not self.webhook_url:
            return {"error": "N8N_WEBHOOK_URL not configured"}
        
        payload = {
            "query": query,
            "type": "research",
        }
        
        if additional_context:
            payload["context"] = additional_context
            
        print(f"Sending research request to: {self.webhook_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"SSL Verification: {'Enabled' if self.verify_ssl else 'Disabled'}")
            
        try:
            # Add timeout to prevent hanging if the webhook is unreachable
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=30,
                headers=headers,
                verify=self.verify_ssl  # Skip SSL verification if needed
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Timeout error: The request to n8n took too long to complete")
            return {"error": "Request timeout. The n8n webhook took too long to respond."}
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("Consider setting verify_ssl=False if you trust this endpoint.")
            return {"error": f"SSL verification failed: {e}"}
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: Could not connect to the n8n webhook. Error: {e}")
            return {"error": "Connection error. Could not connect to the n8n webhook."}
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: The n8n webhook returned an error status: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.exceptions.RequestException as e:
            print(f"Error sending research request to n8n: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Error: The response from n8n is not valid JSON")
            # Try to return the raw text
            try:
                return {"error": "Invalid JSON response", "raw_response": response.text}
            except:
                return {"error": "Invalid response format from n8n webhook"}
    
    def send_prompt_enhancement_request(self, prompt, document_context=None):
        """
        Send a request to enhance an LLM prompt based on document context.
        
        Args:
            prompt (str): The original prompt to enhance
            document_context (str, optional): The document context to consider
            
        Returns:
            dict: The enhanced prompt data from n8n
        """
        if not self.webhook_url:
            return {"error": "N8N_WEBHOOK_URL not configured"}
        
        payload = {
            "prompt": prompt,
            "type": "prompt_enhancement",
        }
        
        if document_context:
            payload["document_context"] = document_context
            
        print(f"Sending prompt enhancement request to: {self.webhook_url}")
        print(f"Payload type: {type(payload)}")
        print(f"SSL Verification: {'Enabled' if self.verify_ssl else 'Disabled'}")
            
        try:
            # Add timeout to prevent hanging if the webhook is unreachable
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=30,
                headers=headers,
                verify=self.verify_ssl  # Skip SSL verification if needed
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Timeout error: The request to n8n took too long to complete")
            return {"error": "Request timeout. The n8n webhook took too long to respond."}
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("Consider setting verify_ssl=False if you trust this endpoint.")
            return {"error": f"SSL verification failed: {e}"}
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: Could not connect to the n8n webhook. Error: {e}")
            return {"error": "Connection error. Could not connect to the n8n webhook."}
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: The n8n webhook returned an error status: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.exceptions.RequestException as e:
            print(f"Error sending prompt enhancement request to n8n: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Error: The response from n8n is not valid JSON")
            # Try to return the raw text
            try:
                return {"error": "Invalid JSON response", "raw_response": response.text}
            except:
                return {"error": "Invalid response format from n8n webhook"}
    
    def process_webhook_response(self, response_data):
        """
        Process the response data from an n8n webhook.
        
        Args:
            response_data (dict): The response data from n8n
            
        Returns:
            dict: Processed data in a standardized format
        """
        if not response_data:
            return {
                "success": False,
                "error": "Empty response from webhook",
                "data": None
            }
            
        if "error" in response_data:
            return {
                "success": False,
                "error": response_data["error"],
                "data": None
            }
        
        return {
            "success": True,
            "error": None,
            "data": response_data
        } 