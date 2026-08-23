"""
ServiceManager.py - Central service management system for Robert
Handles starting, stopping, monitoring, and restarting all services
"""

import subprocess
import threading
import time
import requests
import json
import os
import signal
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import logging
from collections import deque

# Create logs directory if it doesn't exist
LOGS_DIR = 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'robert_system.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Service:
    """Represents a single service that can be started/stopped"""
    
    def __init__(self, name: str, script: str, port: int = None,
                 depends_on: List[str] = None, health_check_url: str = None,
                 source: bool = False):
        self.name = name
        self.script = script
        self.port = port
        self.depends_on = depends_on or []
        self.health_check_url = health_check_url or (f'http://127.0.0.1:{port}' if port else None)
        self.source = source
        
        self.process = None
        self.manager = None
        self.is_running = False
        self.last_health_check = None
        self.health_status = 'unknown'
        self.start_time = None
        self.restart_count = 0
        self.last_error = None
        self.paused = False
        
        # Logging setup
        self.logger = logging.getLogger(f'Robert.{self.name}')
        log_file = os.path.join(LOGS_DIR, f'{self.name}.log')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Output buffer for recent logs
        self.output_buffer = deque(maxlen=100)  # Keep last 100 lines
        self.output_lock = threading.Lock()
        
        self.output_thread = None
        self.capture_output = False
        
    def _capture_service_output(self):
        """Continuously capture service stdout/stderr"""
        if not self.process:
            return
        
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    formatted_line = f"[{timestamp}] {line.rstrip()}"
                    
                    with self.output_lock:
                        self.output_buffer.append(formatted_line)
                    
                    self.logger.info(f"OUTPUT: {line.rstrip()}")
                    if self.manager and self.manager.debug_output:
                        print(f"  [{self.name}] {line.rstrip()}")
        except Exception as e:
            self.logger.error(f"Error capturing output: {e}")
    
    def get_recent_output(self, lines: int = 20) -> List[str]:
        """Get recent output lines from service"""
        with self.output_lock:
            return list(self.output_buffer)[-lines:]
        
    def start(self) -> bool:
        """Start the service"""
        if self.paused:
            self.logger.info("Start skipped because service is paused")
            return False
        try:
            self.logger.info(f"Starting service: {self.name}")
            logger.info(f"Starting service: {self.name}")
            
            self.process = subprocess.Popen(
                ['python', self.script],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.is_running = True
            self.start_time = datetime.now()
            self.last_error = None
            
            # Start output capture thread
            self.capture_output = True
            self.output_thread = threading.Thread(
                target=self._capture_service_output,
                daemon=True
            )
            self.output_thread.start()
            
            self.logger.info(f"Service {self.name} started with PID {self.process.pid}")
            logger.info(f"Service {self.name} started with PID {self.process.pid}")
            return True
        except Exception as e:
            self.is_running = False
            self.last_error = str(e)
            self.logger.error(f"Failed to start {self.name}: {e}")
            logger.error(f"Failed to start {self.name}: {e}")
            return False
            self.is_running = True
            self.start_time = datetime.now()
            self.last_error = None
            logger.info(f"Service {self.name} started with PID {self.process.pid}")
            return True
        except Exception as e:
            self.is_running = False
            self.last_error = str(e)
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the service"""
        try:
            if self.process and self.is_running:
                self.logger.info(f"Stopping service: {self.name}")
                logger.info(f"Stopping service: {self.name}")
                
                self.capture_output = False
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Service {self.name} did not stop gracefully, killing...")
                    logger.warning(f"Service {self.name} did not stop gracefully, killing...")
                    self.process.kill()
                    self.process.wait()
                self.is_running = False
                self.logger.info(f"Service {self.name} stopped")
                logger.info(f"Service {self.name} stopped")
                return True
        except Exception as e:
            self.logger.error(f"Error stopping {self.name}: {e}")
            logger.error(f"Error stopping {self.name}: {e}")
            self.last_error = str(e)
        return False
    
    def restart(self) -> bool:
        """Restart the service"""
        self.logger.info(f"Restarting service: {self.name}")
        logger.info(f"Restarting service: {self.name}")
        self.stop()
        time.sleep(1)
        success = self.start()
        if success:
            self.restart_count += 1
        return success
    
    def check_health(self) -> bool:
        """Check if service is healthy"""
        if not self.health_check_url:
            return self.is_running
        
        try:
            response = requests.get(self.health_check_url, timeout=2)
            healthy = response.status_code == 200
            self.health_status = 'healthy' if healthy else 'unhealthy'
            self.last_health_check = datetime.now()
            return healthy
        except Exception as e:
            self.health_status = 'unreachable'
            self.last_error = str(e)
            return False
    
    def get_status(self) -> Dict:
        """Get current status of service"""
        return {
            'name': self.name,
            'is_running': self.is_running,
            'health_status': self.health_status,
            'port': self.port,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else 'N/A',
            'restart_count': self.restart_count,
            'last_error': self.last_error,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else 'N/A'
            , 'source': self.source,
            'paused': self.paused
        }


class ServiceManager:
    """Central manager for all Robert services"""
    
    def __init__(self):
        self.services: Dict[str, Service] = {}
        self.debug_output = True
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.RLock()
        
        self._register_default_services()

    def set_debug_output(self, enabled: bool) -> bool:
        """Enable or disable live service output in the control hub."""
        with self.lock:
            self.debug_output = enabled
            logger.info("Live service output %s", "enabled" if enabled else "disabled")
            for service in self.services.values():
                service.logger.info(
                    "Live service output %s", "enabled" if enabled else "disabled"
                )
            return self.debug_output

    def is_debug_output_enabled(self) -> bool:
        """Return whether live service output is displayed."""
        with self.lock:
            return self.debug_output
    
    def _register_default_services(self):
        """Register all default services"""
        # Define all services with correct ports from actual code
        # CognitiveManager: 5000, AI: 5001, ToolManager: 5002
        services_config = [
            Service('CognitiveManager', 'CognitiveManager.py', port=5000,
                   health_check_url='http://127.0.0.1:5000/'),
            Service('AI', 'AI.py', port=5001,
                   depends_on=['CognitiveManager'],
                   health_check_url='http://127.0.0.1:5001/'),
            Service('ToolManager', 'ToolManager.py', port=5002,
                   health_check_url='http://127.0.0.1:5002/'),
        ]
        
        for service in services_config:
            self.register_service(service)

        source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources')
        if os.path.isdir(source_dir):
            for filename in sorted(os.listdir(source_dir)):
                if filename.endswith('.py') and filename != '__init__.py':
                    name = f"source:{filename[:-3]}"
                    self.register_service(Service(name, os.path.join('sources', filename), source=True))
    
    def register_service(self, service: Service):
        """Register a new service"""
        with self.lock:
            service.manager = self
            self.services[service.name] = service
            logger.info(f"Registered service: {service.name}")
    
    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        with self.lock:
            if service_name not in self.services:
                logger.error(f"Service {service_name} not found")
                return False
            
            service = self.services[service_name]
            
            # Check dependencies
            for dep in service.depends_on:
                if dep in self.services:
                    dep_service = self.services[dep]
                    if not dep_service.is_running:
                        logger.info(f"Starting dependency {dep} for {service_name}")
                        self.start_service(dep)
            
            return service.start()
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        with self.lock:
            if service_name not in self.services:
                logger.error(f"Service {service_name} not found")
                return False
            return self.services[service_name].stop()
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        with self.lock:
            if service_name not in self.services:
                logger.error(f"Service {service_name} not found")
                return False
            return self.services[service_name].restart()
    
    def start_all(self):
        """Start all services in dependency order"""
        logger.info("Starting all services...")
        # Simple dependency resolution: start services without dependencies first
        started = set()
        max_iterations = 10
        iteration = 0
        
        services = {name: service for name, service in self.services.items() if not service.source}
        while len(started) < len(services) and iteration < max_iterations:
            for name, service in services.items():
                if name not in started:
                    if all(dep in started or dep not in self.services for dep in service.depends_on):
                        self.start_service(name)
                        started.add(name)
            iteration += 1
        
        logger.info("All services started")

    def start_sources(self, source_name: str = 'all') -> bool:
        """Start one source or all non-paused sources."""
        with self.lock:
            sources = {name: service for name, service in self.services.items() if service.source}
            if source_name != 'all':
                service = sources.get(source_name) or sources.get(f'source:{source_name}')
                return bool(service and self.start_service(service.name))
            results = [self.start_service(name) for name, service in sources.items() if not service.paused]
            return all(results) if results else True

    def stop_sources(self, source_name: str = 'all') -> bool:
        """Stop one source or all sources without pausing them."""
        with self.lock:
            sources = {name: service for name, service in self.services.items() if service.source}
            if source_name != 'all':
                service = sources.get(source_name) or sources.get(f'source:{source_name}')
                return bool(service and self.stop_service(service.name))
            results = [self.stop_service(name) for name in sources]
            return all(results) if results else True

    def restart_source(self, source_name: str) -> bool:
        """Restart one source unless it is paused."""
        with self.lock:
            service = self.services.get(source_name) or self.services.get(f'source:{source_name}')
            if not service or not service.source or service.paused:
                return False
            return service.restart()

    def pause_source(self, source_name: str) -> bool:
        """Stop a source and mark it paused."""
        with self.lock:
            if source_name == 'all':
                sources = [service.name for service in self.services.values() if service.source]
                return all(self.pause_source(name) for name in sources)
            service = self.services.get(source_name) or self.services.get(f'source:{source_name}')
            if not service or not service.source:
                return False
            service.paused = True
            service.stop()
            logger.info("Paused source: %s", service.name)
            return True

    def resume_source(self, source_name: str) -> bool:
        """Allow a source to run again without starting it automatically."""
        with self.lock:
            if source_name == 'all':
                sources = [service.name for service in self.services.values() if service.source]
                return all(self.resume_source(name) for name in sources)
            service = self.services.get(source_name) or self.services.get(f'source:{source_name}')
            if not service or not service.source:
                return False
            service.paused = False
            logger.info("Resumed source: %s", service.name)
            return True

    def send_event(self, event: Dict) -> Tuple[bool, str]:
        """Send a manually supplied event to CognitiveManager."""
        try:
            response = requests.post('http://127.0.0.1:5000/submit', json=event, timeout=3)
            response.raise_for_status()
            return True, response.text
        except requests.RequestException as error:
            logger.error("Manual event failed: %s", error)
            return False, str(error)

    def run_tool(self, name: str, args: Dict) -> Tuple[bool, str]:
        """Run a tool through ToolManager without managing its lifecycle."""
        try:
            response = requests.post('http://127.0.0.1:5002/run', json={'name': name, 'args': args}, timeout=30)
            response.raise_for_status()
            return True, response.text
        except requests.RequestException as error:
            logger.error("Tool %s failed: %s", name, error)
            return False, str(error)

    def list_tools(self) -> Tuple[bool, List[str]]:
        """List tools currently registered with ToolManager."""
        try:
            response = requests.get('http://127.0.0.1:5002/tools', timeout=3)
            response.raise_for_status()
            return True, response.json().get('tools', [])
        except (requests.RequestException, ValueError) as error:
            logger.error("Tool listing failed: %s", error)
            return False, []
    
    def stop_all(self):
        """Stop all services"""
        logger.info("Stopping all services...")
        with self.lock:
            for service in self.services.values():
                service.stop()
        logger.info("All services stopped")
    
    def restart_all(self):
        """Restart all services"""
        self.stop_all()
        time.sleep(1)
        self.start_all()
    
    def start_monitoring(self, check_interval: int = 10):
        """Start health monitoring of all services"""
        if self.monitoring:
            logger.warning("Monitoring already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Service monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Service monitoring stopped")
    
    def _monitor_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            with self.lock:
                for service in self.services.values():
                    if service.is_running:
                        healthy = service.check_health()
                        if not healthy and service.is_running:
                            logger.warning(f"Service {service.name} health check failed, restarting...")
                            service.restart()
            time.sleep(check_interval)
    
    def get_status(self, service_name: str = None) -> Dict:
        """Get status of service(s)"""
        with self.lock:
            if service_name:
                if service_name in self.services:
                    return self.services[service_name].get_status()
                else:
                    return {'error': f'Service {service_name} not found'}
            else:
                return {
                    'services': {name: service.get_status() 
                               for name, service in self.services.items()},
                    'timestamp': datetime.now().isoformat()
                }
    
    def get_service_names(self) -> List[str]:
        """Get list of all registered service names"""
        with self.lock:
            return list(self.services.keys())
    
    def get_all_status(self) -> Dict:
        """Get status of all services"""
        return self.get_status()
    
    def export_status_json(self, filename: str = 'system_status.json'):
        """Export system status to JSON file"""
        status = self.get_all_status()
        with open(filename, 'w') as f:
            json.dump(status, f, indent=2)
        logger.info(f"Status exported to {filename}")
    
    def get_service_output(self, service_name: str) -> Tuple[str, str]:
        """Get recent output from a service"""
        with self.lock:
            if service_name not in self.services:
                return ('', f'Service {service_name} not found')
            
            service = self.services[service_name]
            return ('\n'.join(service.get_recent_output()), '')
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> List[str]:
        """Get recent logs from service buffer"""
        with self.lock:
            if service_name not in self.services:
                return [f'Service {service_name} not found']
            
            service = self.services[service_name]
            return service.get_recent_output(lines)
    
    def read_log_file(self, service_name: str = None) -> str:
        """Read log file for a service or system log"""
        try:
            if service_name:
                log_file = os.path.join(LOGS_DIR, f'{service_name}.log')
            else:
                log_file = os.path.join(LOGS_DIR, 'robert_system.log')
            
            if not os.path.exists(log_file):
                return f'Log file not found: {log_file}'
            
            with open(log_file, 'r') as f:
                return f.read()
        except Exception as e:
            return f'Error reading log file: {e}'
    
    def get_recent_log_lines(self, service_name: str = None, lines: int = 30) -> List[str]:
        """Get recent lines from log file"""
        try:
            if service_name:
                log_file = os.path.join(LOGS_DIR, f'{service_name}.log')
            else:
                log_file = os.path.join(LOGS_DIR, 'robert_system.log')
            
            if not os.path.exists(log_file):
                return [f'Log file not found: {log_file}']
            
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
            
            return [line.rstrip('\n') for line in all_lines[-lines:]]
        except Exception as e:
            return [f'Error reading log file: {e}']
    
    def get_all_logs_summary(self) -> Dict[str, List[str]]:
        """Get summary of recent logs from all services"""
        summary = {}
        
        # System logs
        summary['robert_system'] = self.get_recent_log_lines(None, 10)
        
        # Service logs
        with self.lock:
            for name in self.services.keys():
                summary[name] = self.get_recent_log_lines(name, 10)
        
        return summary


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager
