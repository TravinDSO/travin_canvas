"""
Test script for checking network connectivity and proxy settings.

This script tests basic network connectivity to common services
and checks if there are any proxy settings that might be affecting
the webhook connection.
"""

import os
import sys
import socket
import requests
import urllib.parse
from dotenv import load_dotenv

def check_dns(hostname):
    """Check if a hostname can be resolved via DNS."""
    try:
        print(f"Resolving {hostname}...")
        ip = socket.gethostbyname(hostname)
        print(f"  Success! Resolved to {ip}")
        return True
    except socket.gaierror as e:
        print(f"  Failed to resolve {hostname}: {e}")
        return False

def check_connection(url):
    """Check if a connection can be established to a URL."""
    try:
        print(f"Testing connection to {url}...")
        response = requests.get(url, timeout=5)
        print(f"  Success! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"  Failed to connect to {url}: {e}")
        return False

def check_proxy_settings():
    """Check if there are any proxy settings that might affect connections."""
    print("\nChecking proxy settings:")
    
    # Check environment variables
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy']
    found_proxy = False
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            found_proxy = True
            print(f"  {var} = {value}")
    
    if not found_proxy:
        print("  No proxy environment variables found.")
    
    # Check requests library proxy settings
    print("\nRequests library proxy settings:")
    print(f"  Current proxies: {requests.utils.getproxies()}")
    
    return found_proxy

def check_webhook_url():
    """Check if the webhook URL is valid and can be parsed."""
    load_dotenv()
    
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = webhook_url.strip('"\'')
    
    if not webhook_url:
        print("Error: N8N_WEBHOOK_URL environment variable is not set.")
        return False
    
    print(f"\nAnalyzing webhook URL: {webhook_url}")
    
    try:
        parts = urllib.parse.urlparse(webhook_url)
        print(f"  Scheme: {parts.scheme}")
        print(f"  Netloc: {parts.netloc}")
        print(f"  Path: {parts.path}")
        print(f"  Params: {parts.params}")
        print(f"  Query: {parts.query}")
        print(f"  Fragment: {parts.fragment}")
        
        # Check if the hostname can be resolved
        hostname = parts.netloc
        if ':' in hostname:
            hostname = hostname.split(':')[0]
            
        return check_dns(hostname)
    except Exception as e:
        print(f"  Error parsing webhook URL: {e}")
        return False

def main():
    """Run network connectivity tests."""
    print("=== Network Connectivity Test ===\n")
    
    # Check DNS resolution for common services
    print("Testing DNS resolution:")
    dns_checks = [
        check_dns("google.com"),
        check_dns("microsoft.com"),
        check_dns("github.com")
    ]
    
    # Check connection to common services
    print("\nTesting HTTP connections:")
    conn_checks = [
        check_connection("https://www.google.com"),
        check_connection("https://www.microsoft.com"),
        check_connection("https://www.github.com")
    ]
    
    # Check proxy settings
    has_proxy = check_proxy_settings()
    
    # Check webhook URL
    webhook_valid = check_webhook_url()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"DNS resolution: {'All passed' if all(dns_checks) else 'Some failed'}")
    print(f"HTTP connections: {'All passed' if all(conn_checks) else 'Some failed'}")
    print(f"Proxy settings: {'Found' if has_proxy else 'None detected'}")
    print(f"Webhook URL: {'Valid' if webhook_valid else 'Invalid or cannot be resolved'}")
    
    if not all(dns_checks) or not all(conn_checks):
        print("\nThere may be network connectivity issues affecting the webhook connection.")
        
    if has_proxy:
        print("\nProxy settings were detected which might be affecting the webhook connection.")
        print("Try temporarily disabling the proxy or adding the webhook domain to the NO_PROXY list.")
        
    if not webhook_valid:
        print("\nThe webhook URL could not be properly resolved. Please check the URL.")

if __name__ == "__main__":
    main() 