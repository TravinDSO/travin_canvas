"""
Test script for verifying the n8n webhook integration.

This script tests the connection to the n8n webhook and verifies
that the webhook is properly configured and responding.
"""

import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv

def test_webhook_connection(verify_ssl=False):
    """
    Test the connection to the n8n webhook.
    
    Args:
        verify_ssl (bool): Whether to verify SSL certificates
    """
    # Load environment variables
    load_dotenv()
    
    # Get the webhook URL and remove quotes if present
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = webhook_url.strip('"\'')
    
    if not webhook_url:
        print("Error: N8N_WEBHOOK_URL environment variable is not set.")
        return False
    
    print(f"Testing connection to webhook: {webhook_url}")
    print(f"SSL Verification: {'Enabled' if verify_ssl else 'Disabled'}")
    
    # Create a test payload
    payload = {
        "type": "test",
        "message": "This is a test message from Travin Canvas"
    }
    
    # Print request details for debugging
    print("\nRequest details:")
    print(f"URL: {webhook_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {{'Content-Type': 'application/json'}}")
    
    try:
        # Send a test request to the webhook
        print("\nSending request...")
        response = requests.post(
            webhook_url, 
            json=payload, 
            timeout=10,
            headers={'Content-Type': 'application/json'},
            verify=verify_ssl  # Control SSL verification
        )
        
        # Check if the request was successful
        print(f"Response received. Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Connection successful!")
            
            # Try to parse the response as JSON
            try:
                response_json = response.json()
                print("Response JSON:", json.dumps(response_json, indent=2))
                return True
            except json.JSONDecodeError:
                print("Response is not JSON. Response text:", response.text)
                return True  # Still consider it a success if we got a 200 response
        else:
            print("Connection failed with status code:", response.status_code)
            print("Response headers:", dict(response.headers))
            print("Response text:", response.text)
            return False
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        if verify_ssl:
            print("Try running the test with verify_ssl=False")
        return False
    except requests.exceptions.Timeout:
        print("Error: Request timed out. The webhook took too long to respond.")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the webhook. Connection error: {e}")
        print("Please check the URL, your internet connection, and any proxy settings.")
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return False

def manual_test_webhook(verify_ssl=False):
    """
    Test the webhook using a manual HTTP request approach.
    
    Args:
        verify_ssl (bool): Whether to verify SSL certificates
    """
    import http.client
    import ssl
    
    # Load environment variables
    load_dotenv()
    
    # Get the webhook URL and remove quotes if present
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = webhook_url.strip('"\'')
    
    if not webhook_url:
        print("Error: N8N_WEBHOOK_URL environment variable is not set.")
        return False
    
    print(f"\nTrying alternative connection method to: {webhook_url}")
    print(f"SSL Verification: {'Enabled' if verify_ssl else 'Disabled'}")
    
    # Parse the URL
    parts = urllib.parse.urlparse(webhook_url)
    host = parts.netloc
    path = parts.path
    if parts.query:
        path += f"?{parts.query}"
    
    # Create payload
    payload = json.dumps({
        "type": "test",
        "message": "This is a test message from Travin Canvas (manual test)"
    })
    
    print(f"Host: {host}")
    print(f"Path: {path}")
    
    try:
        # Create connection
        if parts.scheme == 'https':
            context = ssl.create_default_context()
            if not verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(host, context=context)
        else:
            conn = http.client.HTTPConnection(host)
        
        # Send request
        headers = {'Content-Type': 'application/json'}
        print("Sending manual request...")
        conn.request("POST", path, payload, headers)
        
        # Get response
        response = conn.getresponse()
        print(f"Response status: {response.status} {response.reason}")
        
        # Read response data
        data = response.read().decode()
        print(f"Response data: {data}")
        
        conn.close()
        return response.status == 200
    except Exception as e:
        print(f"Manual test error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing webhook connection using requests library ===")
    print("First trying with SSL verification disabled...")
    success = test_webhook_connection(verify_ssl=False)
    
    if not success:
        print("\n=== Trying alternative connection method ===")
        alt_success = manual_test_webhook(verify_ssl=False)
        if alt_success:
            print("\nAlternative webhook test completed successfully!")
        else:
            print("\nAll webhook tests failed. Please check the webhook configuration.")
    else:
        print("\nWebhook test completed successfully!") 