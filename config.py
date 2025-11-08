import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AppConfig:
    """Application configuration"""
    
    # Database settings
    MAX_CONNECTIONS: int = 10
    CONNECTION_TIMEOUT: int = 30
    QUERY_TIMEOUT: int = 60
    
    # Schema discovery settings
    MONGODB_SAMPLE_SIZE: int = 100
    MAX_FIELD_ANALYSIS_DEPTH: int = 5
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create config from environment variables"""
        return cls(
            MAX_CONNECTIONS=int(os.getenv('MAX_CONNECTIONS', '10')),
            CONNECTION_TIMEOUT=int(os.getenv('CONNECTION_TIMEOUT', '30')),
            QUERY_TIMEOUT=int(os.getenv('QUERY_TIMEOUT', '60')),
            MONGODB_SAMPLE_SIZE=int(os.getenv('MONGODB_SAMPLE_SIZE', '100')),
            MAX_FIELD_ANALYSIS_DEPTH=int(os.getenv('MAX_FIELD_ANALYSIS_DEPTH', '5')),
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
            LOG_FORMAT=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

# Global config instance
config = AppConfig.from_env()