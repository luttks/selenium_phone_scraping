"""
Simple Google OAuth configuration for frontend
Frontend will handle OAuth popup flow to get email
"""
import os

def get_google_oauth_config():
    """
    Return Google OAuth configuration for frontend
    """
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", ""),
        "scope": "openid email profile"
    }
