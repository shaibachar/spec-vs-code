"""
Ollama Client Integration
"""
import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama LLM server"""
    
    def __init__(self):
        self.host = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'codellama:7b-instruct')
        self.timeout = 30
        self.max_retries = 3
    
    def health_check(self) -> dict:
        """
        Check if Ollama is accessible and healthy
        
        Returns:
            Dict with status and model information
        """
        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            return {
                'status': 'connected',
                'models_loaded': len(models),
                'primary_model_available': self.model in model_names,
                'available_models': model_names
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'error': 'Cannot connect to Ollama server'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate(self, prompt: str, temperature: float = 0.1, 
                max_tokens: int = 2000) -> Optional[str]:
        """
        Generate completion from Ollama
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.host}/api/generate",
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': temperature,
                            'num_predict': max_tokens
                        }
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get('response', '')
                
            except requests.exceptions.Timeout:
                logger.warning(f"Ollama request timed out (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    continue
                raise Exception("Ollama request timed out")
            
            except requests.exceptions.ConnectionError:
                logger.error("Cannot connect to Ollama server")
                raise Exception("Ollama server unavailable")
            
            except Exception as e:
                logger.error(f"Ollama request failed: {e}")
                raise
        
        return None
    
    def chat(self, messages: list, temperature: float = 0.1) -> Optional[str]:
        """
        Chat completion with Ollama
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Response text or None if failed
        """
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    'model': self.model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'temperature': temperature
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
            
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return None
    
    def ensure_model_loaded(self) -> bool:
        """
        Ensure the model is pulled and loaded
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            # Check if model exists
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            models = [m['name'] for m in response.json().get('models', [])]
            
            if self.model in models:
                logger.info(f"Model {self.model} is already loaded")
                return True
            
            # Pull model
            logger.info(f"Pulling model {self.model}...")
            response = requests.post(
                f"{self.host}/api/pull",
                json={'name': self.model},
                timeout=600  # 10 minutes for model download
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure model is loaded: {e}")
            return False
