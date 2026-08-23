"""
UnifiedAPIClient.py - Unified API client for all Robert services
Provides a single interface to communicate with all services across the system
"""

import requests
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    pass


class ServiceClient:
    """Base client for communicating with a service"""
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 5):
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make a GET request to the service"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Try to parse as JSON, fall back to text
            try:
                return response.json()
            except:
                return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {endpoint} failed: {e}")
            raise APIError(f"{self.service_name}: {str(e)}")
    
    def post(self, endpoint: str, data: Dict[str, Any] = None, 
             params: Dict[str, Any] = None) -> Any:
        """Make a POST request to the service"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.post(url, json=data, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            try:
                return response.json()
            except:
                return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {endpoint} failed: {e}")
            raise APIError(f"{self.service_name}: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if service is accessible"""
        try:
            self.get('/')
            return True
        except:
            return False


class CognitiveManagerClient(ServiceClient):
    """Client for CognitiveManager service"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        super().__init__('CognitiveManager', f'http://{host}:{port}')
    
    def get_param(self, name: str) -> Any:
        """Get a parameter from world state"""
        return self.get('/get', params={'name': name})
    
    def set_param(self, name: str, value: Any) -> str:
        """Set a parameter in world state"""
        return self.post('/update', params={'name': name, 'value': value})
    
    def get_available_params(self) -> List[str]:
        """Get list of available parameters"""
        return self.get('/get_available')
    
    def submit_event(self, event: Dict[str, Any]) -> str:
        """Submit an event to be processed"""
        return self.post('/submit', data=event)


class EventManagerClient(ServiceClient):
    """Client for EventManager service"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5001):
        super().__init__('EventManager', f'http://{host}:{port}')
    
    def submit_event(self, event: Dict[str, Any]) -> str:
        """Submit an event for processing"""
        return self.post('/submit', data=event)


class InputManagerClient(ServiceClient):
    """Client for InputManager service"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5002):
        super().__init__('InputManager', f'http://{host}:{port}')
    
    def set_parameter(self, name: str, value: Any, group: str = None) -> str:
        """Set an input parameter"""
        params = {'name': name, 'value': str(value)}
        if group:
            params['group'] = group
        return self.post('/set', params=params)
    
    def get_status(self, group: str = None, name: str = None) -> Any:
        """Get status/parameters"""
        params = {}
        if group:
            params['group'] = group
        if name:
            params['name'] = name
        return self.get('/get', params=params)


class AIClient(ServiceClient):
    """Client for AI service"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5003):
        super().__init__('AI', f'http://{host}:{port}')
    
    def process_request(self, prompt: str, context: Dict = None) -> str:
        """Send a request to the AI"""
        data = {'prompt': prompt}
        if context:
            data['context'] = context
        return self.post('/process', data=data)


class ToolManagerClient(ServiceClient):
    """Client for ToolManager service"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5004):
        super().__init__('ToolManager', f'http://{host}:{port}')
    
    def execute_tool(self, tool_name: str, params: Dict = None) -> Any:
        """Execute a tool"""
        data = {'tool': tool_name}
        if params:
            data['params'] = params
        return self.post('/execute', data=data)
    
    def list_tools(self) -> List[str]:
        """List available tools"""
        return self.get('/tools')


class UnifiedAPIClient:
    """Unified client for all Robert services"""
    
    def __init__(self, host: str = '127.0.0.1'):
        self.host = host
        
        # Initialize service clients
        self.cognitive = CognitiveManagerClient(host)
        self.events = EventManagerClient(host)
        self.inputs = InputManagerClient(host)
        self.ai = AIClient(host)
        self.tools = ToolManagerClient(host)
    
    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services"""
        return {
            'CognitiveManager': self.cognitive.health_check(),
            'EventManager': self.events.health_check(),
            'InputManager': self.inputs.health_check(),
            'AI': self.ai.health_check(),
            'ToolManager': self.tools.health_check(),
        }
    
    def broadcast_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Send an event to all applicable services"""
        results = {}
        
        # Send to event manager
        try:
            results['EventManager'] = self.events.submit_event(event)
        except APIError as e:
            results['EventManager'] = str(e)
        
        # Send to cognitive manager
        try:
            results['CognitiveManager'] = self.cognitive.submit_event(event)
        except APIError as e:
            results['CognitiveManager'] = str(e)
        
        return results
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get the current world state from CognitiveManager"""
        try:
            return self.cognitive.get_available_params()
        except APIError as e:
            logger.error(f"Failed to get world state: {e}")
            return {}
    
    def update_input(self, name: str, value: Any, group: str = None) -> str:
        """Update an input value"""
        return self.inputs.set_parameter(name, value, group)
    
    def update_world_state(self, name: str, value: Any) -> str:
        """Update world state in cognitive manager"""
        return self.cognitive.set_param(name, value)
    
    def query_ai(self, prompt: str, context: Dict = None) -> str:
        """Query the AI with optional context"""
        try:
            return self.ai.process_request(prompt, context)
        except APIError as e:
            logger.error(f"AI query failed: {e}")
            return None
    
    def call_tool(self, tool_name: str, params: Dict = None) -> Any:
        """Call a tool through ToolManager"""
        return self.tools.execute_tool(tool_name, params)
    
    def get_all_tools(self) -> List[str]:
        """Get list of all available tools"""
        try:
            return self.tools.list_tools()
        except APIError as e:
            logger.error(f"Failed to list tools: {e}")
            return []


# Global instance
_api_client: Optional[UnifiedAPIClient] = None


def get_api_client(host: str = '127.0.0.1') -> UnifiedAPIClient:
    """Get or create the global API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = UnifiedAPIClient(host)
    return _api_client


if __name__ == '__main__':
    # Example usage
    client = get_api_client()
    
    # Check health
    print("Health Status:")
    health = client.health_check_all()
    for service, status in health.items():
        print(f"  {service}: {'✓' if status else '✗'}")
    
    # Get world state
    print("\nWorld State:")
    try:
        world_state = client.get_world_state()
        print(f"  Available parameters: {world_state}")
    except Exception as e:
        print(f"  Error: {e}")
