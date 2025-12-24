#!/usr/bin/env python3
"""
Kickbox Email Verification Module
Provides email verification functionality using Kickbox API
"""

import requests
import json
import time
from typing import Dict, Tuple, Optional

class KickboxEmailVerifier:
    def __init__(self, api_key: str):
        """
        Initialize the Kickbox email verifier
        
        Args:
            api_key (str): Your Kickbox API key
        """
        self.api_key = api_key
        self.base_url = "https://api.kickbox.io/v1"
        self.session = requests.Session()
        
    def verify_email(self, email: str) -> Tuple[bool, str, Dict]:
        """
        Verify an email address using Kickbox API
        
        Args:
            email (str): Email address to verify
            
        Returns:
            Tuple[bool, str, Dict]: (is_valid, status_message, api_response)
        """
        if not self._is_valid_email_format(email):
            return False, "Invalid email format", {}
            
        try:
            url = f"{self.base_url}/verify"
            params = {
                'email': email,
                'apikey': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process the response
            result = self._process_response(data)
            return result
            
        except requests.exceptions.RequestException as e:
            return False, f"API request failed: {str(e)}", {}
        except json.JSONDecodeError as e:
            return False, f"Invalid API response: {str(e)}", {}
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", {}
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _process_response(self, data: Dict) -> Tuple[bool, str, Dict]:
        """
        Process Kickbox API response
        
        Args:
            data (Dict): API response data
            
        Returns:
            Tuple[bool, str, Dict]: (is_valid, status_message, full_response)
        """
        # Common result codes from Kickbox
        result_codes = {
            200: ("valid", "Email is valid and deliverable"),
            201: ("deliverable", "Email is deliverable"),
            202: ("undeliverable", "Email is undeliverable"),
            203: ("risky", "Email is risky"),
            204: ("unknown", "Email verification status unknown"),
            250: ("invalid", "Email format is invalid"),
            400: ("error", "Bad request"),
            401: ("error", "Unauthorized"),
            403: ("error", "Forbidden"),
            429: ("error", "Rate limit exceeded"),
            500: ("error", "Server error")
        }
        
        # Extract result code and message
        result_code = data.get('result', 250)
        reason = data.get('reason', 'Unknown')
        role = data.get('role', False)
        free = data.get('free', False)
        disposable = data.get('disposable', False)
        
        # Determine if email is acceptable
        is_valid = result_code in [200, 201]  # valid or deliverable
        
        # Create status message
        status_message = self._get_status_message(result_code, reason, role, free, disposable)
        
        return is_valid, status_message, data
    
    def _get_status_message(self, result_code: int, reason: str, role: bool, 
                          free: bool, disposable: bool) -> str:
        """Generate user-friendly status message"""
        
        if result_code == 200:
            return "✅ Email is valid and deliverable"
        elif result_code == 201:
            return "✅ Email is deliverable"
        elif result_code == 202:
            return "❌ Email is undeliverable"
        elif result_code == 203:
            return "⚠️ Email is risky (may cause delivery issues)"
        elif result_code == 204:
            return "❓ Email verification status unknown"
        elif result_code == 250:
            return "❌ Invalid email format"
        elif result_code == 429:
            return "⏳ Rate limit exceeded, please try again later"
        else:
            return f"❌ Error: {reason}"
    
    def verify_email_batch(self, emails: list, delay: float = 0.1) -> Dict[str, Tuple[bool, str, Dict]]:
        """
        Verify multiple emails with rate limiting
        
        Args:
            emails (list): List of email addresses to verify
            delay (float): Delay between requests in seconds
            
        Returns:
            Dict: Results for each email
        """
        results = {}
        
        for i, email in enumerate(emails):
            print(f"Verifying email {i+1}/{len(emails)}: {email}")
            
            is_valid, message, response = self.verify_email(email)
            results[email] = (is_valid, message, response)
            
            # Rate limiting - don't overwhelm the API
            if i < len(emails) - 1:  # Don't delay after the last request
                time.sleep(delay)
        
        return results
    
    def get_verification_summary(self, results: Dict[str, Tuple[bool, str, Dict]]) -> Dict:
        """Get summary statistics of verification results"""
        summary = {
            'total': len(results),
            'valid': 0,
            'invalid': 0,
            'risky': 0,
            'unknown': 0,
            'errors': 0
        }
        
        for email, (is_valid, message, _) in results.items():
            if 'valid' in message.lower() or 'deliverable' in message.lower():
                summary['valid'] += 1
            elif 'risky' in message.lower():
                summary['risky'] += 1
            elif 'undeliverable' in message.lower() or 'invalid' in message.lower():
                summary['invalid'] += 1
            elif 'unknown' in message.lower():
                summary['unknown'] += 1
            else:
                summary['errors'] += 1
        
        return summary

# Global instance (will be initialized with the API key)
kickbox_verifier = None

def initialize_kickbox(api_key: str) -> KickboxEmailVerifier:
    """Initialize the global Kickbox verifier instance"""
    global kickbox_verifier
    kickbox_verifier = KickboxEmailVerifier(api_key)
    return kickbox_verifier

def verify_email_address(email: str) -> Tuple[bool, str, Dict]:
    """
    Verify an email address using the global Kickbox instance
    
    Args:
        email (str): Email address to verify
        
    Returns:
        Tuple[bool, str, Dict]: (is_valid, status_message, api_response)
    """
    if kickbox_verifier is None:
        return False, "Kickbox not initialized", {}
    
    return kickbox_verifier.verify_email(email)

def get_verification_status_message(result_code: int, reason: str = "") -> str:
    """Get a user-friendly status message for verification result"""
    messages = {
        200: "✅ Email is valid and deliverable",
        201: "✅ Email is deliverable", 
        202: "❌ Email is undeliverable",
        203: "⚠️ Email is risky - may cause delivery issues",
        204: "❓ Email verification status unknown",
        250: "❌ Invalid email format",
        429: "⏳ Rate limit exceeded - please try again later",
        500: "❌ Server error during verification"
    }
    
    return messages.get(result_code, f"❌ Verification failed: {reason}")

# Example usage and testing
if __name__ == "__main__":
    # Test with a sample API key
    api_key = "test_9e152477679a24e7d8ac0df16467a2f180d3167203fe3789f876db691b8b4c0d"
    
    # Initialize verifier
    verifier = initialize_kickbox(api_key)
    
    # Test emails
    test_emails = [
        "test@gmail.com",
        "user@example.com",
        "invalid-email",
        "test@kickbox.com"
    ]
    
    print("=== Email Verification Test ===")
    for email in test_emails:
        print(f"\nVerifying: {email}")
        is_valid, message, response = verify_email_address(email)
        print(f"Result: {message}")
        if response:
            print(f"API Response: {json.dumps(response, indent=2)}")
        print("-" * 50)
