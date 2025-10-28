"""
Utility Functions

Common utility functions used across the crypto value checker.
"""

import json
import os
from datetime import datetime, timedelta
import hashlib

def load_json(filepath):
    """
    Load JSON data from file.
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        dict: Loaded JSON data
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json(data, filepath):
    """
    Save data to JSON file.
    
    Args:
        data (dict): Data to save
        filepath (str): Path to save file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def normalize_crypto_name(crypto_name):
    """
    Normalize cryptocurrency name for consistent processing.
    
    Args:
        crypto_name (str): Raw crypto name
        
    Returns:
        str: Normalized crypto name
    """
    # TODO: Implement name normalization
    # Handle variations like "Bitcoin" vs "BTC", "Ethereum" vs "ETH", etc.
    return crypto_name.lower().strip()

def is_cache_valid(filepath, max_age_minutes=5):
    """
    Check if cached file is still valid.
    
    Args:
        filepath (str): Path to cached file
        max_age_minutes (int): Maximum age in minutes
        
    Returns:
        bool: True if cache is valid
    """
    if not os.path.exists(filepath):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
    age = datetime.now() - file_time
    return age < timedelta(minutes=max_age_minutes)

def generate_cache_key(crypto_name, data_type):
    """
    Generate a cache key for storing data.
    
    Args:
        crypto_name (str): Name of cryptocurrency
        data_type (str): Type of data (market, historical, etc.)
        
    Returns:
        str: Cache key
    """
    key_string = f"{crypto_name}_{data_type}_{datetime.now().strftime('%Y%m%d_%H')}"
    return hashlib.md5(key_string.encode()).hexdigest()

def format_number(number, precision=2):
    """
    Format large numbers with appropriate suffixes.
    
    Args:
        number (float): Number to format
        precision (int): Decimal precision
        
    Returns:
        str: Formatted number string
    """
    if number >= 1e12:
        return f"{number/1e12:.{precision}f}T"
    elif number >= 1e9:
        return f"{number/1e9:.{precision}f}B"
    elif number >= 1e6:
        return f"{number/1e6:.{precision}f}M"
    elif number >= 1e3:
        return f"{number/1e3:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"

def validate_api_response(response_data, required_fields):
    """
    Validate API response contains required fields.
    
    Args:
        response_data (dict): API response data
        required_fields (list): List of required field names
        
    Returns:
        bool: True if all required fields present
    """
    return all(field in response_data for field in required_fields)