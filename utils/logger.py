"""
Logging Configuration

Centralized logging setup for the crypto value checker.
"""

import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = f"crypto_checker_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return logging.getLogger(__name__)

def log_analysis_result(crypto_name, recommendation, score, reasoning):
    """
    Log analysis result for tracking.
    
    Args:
        crypto_name (str): Name of analyzed cryptocurrency
        recommendation (str): BUY/HOLD/AVOID recommendation
        score (float): Overall analysis score
        reasoning (list): List of reasoning points
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Analysis completed for {crypto_name}")
    logger.info(f"Recommendation: {recommendation} (Score: {score})")
    logger.info(f"Reasoning: {', '.join(reasoning)}")

def log_api_call(api_name, crypto_name, success=True, error_msg=None):
    """
    Log API call for debugging and monitoring.
    
    Args:
        api_name (str): Name of the API called
        crypto_name (str): Cryptocurrency being queried
        success (bool): Whether the call was successful
        error_msg (str): Error message if call failed
    """
    logger = logging.getLogger(__name__)
    if success:
        logger.info(f"Successful API call to {api_name} for {crypto_name}")
    else:
        logger.error(f"Failed API call to {api_name} for {crypto_name}: {error_msg}")