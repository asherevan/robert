"""
Robert Main Control Hub
- Central command interface for all Robert services
- Start, stop, monitor, and control all components from one place
- Real-time health monitoring and auto-restart capabilities
- Comprehensive logging and status reporting
"""

from dotenv import load_dotenv

load_dotenv()

import sys
import traceback
import time
import json
from datetime import datetime
from ServiceManager import get_service_manager
import os
import logging
import threading
from dashboard import create_dashboard

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'control_hub.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Robert.ControlHub')

service_manager = get_service_manager()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text):
    """Print a formatted section header"""
    print(f"\n--- {text} ---")


def help_cmd(command=None):
    """Show help for commands. Usage: `help [command]`"""
    if command:
        if command in commands:
            doc = commands[command].__doc__
            if doc:
                print(doc)
            else:
                print(f"No help available for '{command}'")
        else:
            print(f"Command '{command}' not found")
    else:
        print_header("ROBERT CONTROL HUB - HELP")
        print("\nAvailable Commands:")
        for cmd_name, cmd_func in sorted(commands.items()):
            doc = cmd_func.__doc__ or "No description"
            first_line = doc.split('\n')[0].strip()
            print(f"  {cmd_name:20} - {first_line}")
        print("\nType 'help <command>' for detailed help on a command")
        print("\nLogging & Output:")
        print("  • All output is logged to 'logs/' directory")
        print("  • System log: logs/robert_system.log")
        print("  • Service logs: logs/<service_name>.log")
        print("  • Control hub: logs/control_hub.log")


def start_cmd(*args):
    """Start services. Usage: `start [service_name]` or `start all`
    
    Examples:
      start all           - Start all services
      start CognitiveManager - Start specific service
    """
    if not args or args[0].lower() == 'all':
        print_section("Starting all services...")
        logger.info("User command: start all")
        service_manager.start_all()
        print("✓ All services started")
        logger.info("All services started successfully")
    else:
        service_name = ' '.join(args)
        print_section(f"Starting {service_name}...")
        logger.info(f"User command: start {service_name}")
        if service_manager.start_service(service_name):
            print(f"✓ {service_name} started successfully")
            logger.info(f"{service_name} started successfully")
        else:
            print(f"✗ Failed to start {service_name}")
            logger.error(f"Failed to start {service_name}")


def stop_cmd(*args):
    """Stop services. Usage: `stop [service_name]` or `stop all`
    
    Examples:
      stop all            - Stop all services
      stop CognitiveManager - Stop specific service
    """
    if not args or args[0].lower() == 'all':
        print_section("Stopping all services...")
        logger.info("User command: stop all")
        service_manager.stop_all()
        print("✓ All services stopped")
        logger.info("All services stopped successfully")
    else:
        service_name = ' '.join(args)
        print_section(f"Stopping {service_name}...")
        logger.info(f"User command: stop {service_name}")
        if service_manager.stop_service(service_name):
            print(f"✓ {service_name} stopped successfully")
            logger.info(f"{service_name} stopped successfully")
        else:
            print(f"✗ Failed to stop {service_name}")
            logger.error(f"Failed to stop {service_name}")


def restart_cmd(*args):
    """Restart services. Usage: `restart [service_name]` or `restart all`
    
    Examples:
      restart all         - Restart all services
      restart CognitiveManager - Restart specific service
    """
    if not args or args[0].lower() == 'all':
        print_section("Restarting all services...")
        logger.info("User command: restart all")
        service_manager.restart_all()
        print("✓ All services restarted")
        logger.info("All services restarted successfully")
    else:
        service_name = ' '.join(args)
        print_section(f"Restarting {service_name}...")
        logger.info(f"User command: restart {service_name}")
        if service_manager.restart_service(service_name):
            print(f"✓ {service_name} restarted successfully")
            logger.info(f"{service_name} restarted successfully")
        else:
            print(f"✗ Failed to restart {service_name}")
            logger.error(f"Failed to restart {service_name}")


def status_cmd(*args):
    """Show service status. Usage: `status [service_name]`
    
    Examples:
      status              - Show all services status
      status CognitiveManager - Show specific service status
    """
    if args:
        service_name = ' '.join(args)
        logger.info(f"User command: status {service_name}")
        status = service_manager.get_status(service_name)
        print_section(f"Status of {service_name}")
        if 'error' in status:
            print(f"✗ {status['error']}")
        else:
            print(json.dumps(status, indent=2))
    else:
        logger.info("User command: status all")
        print_header("ROBERT SYSTEM STATUS")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        status = service_manager.get_all_status()
        services_status = status.get('services', {})
        
        # Print table header
        print(f"{'Service':<20} {'Status':<12} {'Health':<12} {'Port':<6} {'Restarts':<8}")
        print("-" * 70)
        
        # Print each service
        for service_name, svc_status in sorted(services_status.items()):
            status_str = "Running" if svc_status['is_running'] else "Stopped"
            health = svc_status['health_status']
            port = str(svc_status['port']) if svc_status['port'] else "N/A"
            restarts = str(svc_status['restart_count'])
            
            status_indicator = "✓" if svc_status['is_running'] else "✗"
            health_indicator = "✓" if health == 'healthy' else "✗" if health == 'unreachable' else "?"
            
            print(f"{service_name:<20} {status_indicator} {status_str:<10} {health_indicator} {health:<10} {port:<6} {restarts:<8}")
        
        print("\n✓ = Healthy/Running | ✗ = Failed/Stopped | ? = Unknown")


def monitor_cmd(*args):
    """Start/stop health monitoring. Usage: `monitor [start|stop|interval]`
    
    Examples:
      monitor start       - Start monitoring with default interval (10s)
      monitor stop        - Stop monitoring
      monitor 30          - Start monitoring with 30s interval
    """
    if not args or args[0].lower() == 'start':
        interval = 10
        if len(args) > 1:
            try:
                interval = int(args[1])
            except ValueError:
                print("Invalid interval. Using default (10s)")
        print_section(f"Starting monitoring (interval: {interval}s)...")
        logger.info(f"User command: monitor start with interval {interval}s")
        service_manager.start_monitoring(check_interval=interval)
        print(f"✓ Monitoring started. Services will be health-checked every {interval} seconds")
        logger.info(f"Monitoring started with {interval}s interval")
        
        # Optional: show monitoring loop with logs
        try:
            print("\nMonitoring in progress... (Press Ctrl+C to stop)")
            while service_manager.monitoring:
                time.sleep(interval)
                status = service_manager.get_all_status()
                services_status = status.get('services', {})
                
                # Print compact status
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status check:")
                for svc_name, svc_status in sorted(services_status.items()):
                    health = "✓" if svc_status['health_status'] == 'healthy' else "✗"
                    print(f"  {health} {svc_name}: {svc_status['health_status']}")
        except KeyboardInterrupt:
            print("\n\nStopping monitoring...")
            service_manager.stop_monitoring()
            logger.info("Monitoring stopped by user")
    elif args[0].lower() == 'stop':
        print_section("Stopping monitoring...")
        logger.info("User command: monitor stop")
        service_manager.stop_monitoring()
        print("✓ Monitoring stopped")
        logger.info("Monitoring stopped successfully")
    else:
        try:
            interval = int(args[0])
            print_section(f"Starting monitoring (interval: {interval}s)...")
            logger.info(f"User command: monitor {interval}s")
            service_manager.start_monitoring(check_interval=interval)
            print(f"✓ Monitoring started")
            logger.info(f"Monitoring started with {interval}s interval")
        except ValueError:
            print("Invalid command. Use: monitor [start|stop|interval]")
            logger.warning("Invalid monitor command")


def list_cmd(*args):
    """List all registered services. Usage: `list`"""
    print_section("Registered Services")
    logger.info("User command: list")
    services = service_manager.get_service_names()
    for i, service in enumerate(services, 1):
        print(f"  {i}. {service}")


def export_cmd(*args):
    """Export system status to JSON file. Usage: `export [filename]`
    
    Examples:
      export              - Export to 'system_status.json'
      export my_status.json - Export to specified file
    """
    filename = args[0] if args else 'system_status.json'
    try:
        logger.info(f"User command: export to {filename}")
        service_manager.export_status_json(filename)
        print(f"✓ Status exported to {filename}")
        logger.info(f"Status successfully exported to {filename}")
    except Exception as e:
        print(f"✗ Error exporting status: {e}")
        logger.error(f"Error exporting status: {e}")


def quit_cmd(*args):
    """Shutdown Robert and all services. Usage: `quit` or `quit force`"""
    force = len(args) > 0 and args[0].lower() == 'force'
    
    logger.info("User command: quit")
    print_header("SHUTTING DOWN ROBERT")
    print("\nStopping all services...")
    service_manager.stop_all()
    print("✓ All services stopped")
    logger.info("All services stopped. Robert shutting down.")
    print("\nRobert is shutting down. Goodbye!")
    
    sys.exit(0)


def clear_cmd(*args):
    """Clear the screen. Usage: `clear`"""
    os.system('clear' if os.name == 'posix' else 'cls')


def info_cmd(*args):
    """Show system information. Usage: `info [service_name]`"""
    if args:
        service_name = ' '.join(args)
        status = service_manager.get_status(service_name)
        if 'error' not in status:
            print_section(f"Detailed Info - {service_name}")
            print(f"Name:           {status['name']}")
            print(f"Running:        {'Yes' if status['is_running'] else 'No'}")
            print(f"Health:         {status['health_status']}")
            print(f"Port:           {status['port']}")
            print(f"Uptime:         {status['uptime']}")
            print(f"Restart Count:  {status['restart_count']}")
            if status['last_error']:
                print(f"Last Error:     {status['last_error']}")
            print(f"Last Check:     {status['last_health_check']}")
        else:
            print(f"✗ {status['error']}")
    else:
        print("Usage: info <service_name>")


def logs_cmd(*args):
    """View service logs. Usage: `logs [service_name] [lines]`
    
    Examples:
      logs                  - Show system log (last 20 lines)
      logs CognitiveManager  - Show service log (last 20 lines)
      logs CognitiveManager 50 - Show service log (last 50 lines)
      logs system 30        - Show system log (last 30 lines)
    """
    if not args:
        # Show system logs
        print_section("System Logs (last 20 lines)")
        logger.info("User command: logs (system)")
        lines = service_manager.get_recent_log_lines(None, 20)
        for line in lines:
            print(line)
    else:
        if args[0].lower() == 'system':
            num_lines = int(args[1]) if len(args) > 1 else 20
            print_section(f"System Logs (last {num_lines} lines)")
            logger.info(f"User command: logs system {num_lines}")
            lines = service_manager.get_recent_log_lines(None, num_lines)
        else:
            service_name = args[0]
            num_lines = int(args[1]) if len(args) > 1 else 20
            print_section(f"Logs for {service_name} (last {num_lines} lines)")
            logger.info(f"User command: logs {service_name} {num_lines}")
            lines = service_manager.get_recent_log_lines(service_name, num_lines)
        
        for line in lines:
            print(line)


def output_cmd(*args):
    """View recent service output. Usage: `output <service_name> [lines]`
    
    Examples:
      output CognitiveManager   - Show recent output (last 20 lines)
      output InputManager 50    - Show recent output (last 50 lines)
    """
    if not args:
        print("Usage: output <service_name> [lines]")
        logger.info("User command: output (no service specified)")
        return
    
    service_name = args[0]
    num_lines = int(args[1]) if len(args) > 1 else 20
    
    print_section(f"Output for {service_name} (last {num_lines} lines)")
    logger.info(f"User command: output {service_name} {num_lines}")
    
    lines = service_manager.get_service_logs(service_name, num_lines)
    for line in lines:
        print(line)


def sources_cmd(*args):
    """Manage sources. Usage: `sources start|stop|pause|resume [name|all]`"""
    action = args[0].lower() if args else 'status'
    name = args[1] if len(args) > 1 else 'all'
    if action == 'start':
        success = service_manager.start_sources(name)
    elif action == 'stop':
        success = service_manager.stop_sources(name)
    elif action == 'pause':
        success = service_manager.pause_source(name)
    elif action == 'resume':
        success = service_manager.resume_source(name)
    elif action == 'status':
        for source_name, status in service_manager.get_all_status()['services'].items():
            if status['source']:
                print(f"{source_name}: running={status['is_running']} paused={status['paused']}")
        return
    else:
        print("Usage: sources start|stop|pause|resume [name|all]")
        return
    print(f"Source {action} {'succeeded' if success else 'failed'}: {name}")


def event_cmd(*args):
    """Send an event to CognitiveManager. Usage: `event <JSON>`"""
    if not args:
        print('Usage: event {"type":"...","source":"...","data":{}}')
        return
    try:
        event = json.loads(' '.join(args))
        success, response = service_manager.send_event(event)
        print(response if success else f"Event failed: {response}")
    except json.JSONDecodeError as error:
        print(f"Invalid event JSON: {error}")


def tool_cmd(*args):
    """Run a tool through ToolManager. Usage: `tool <name> [JSON args]`"""
    if not args:
        print('Usage: tool <name> {"argument":"value"}')
        return
    try:
        tool_name = args[0]
        tool_args = json.loads(' '.join(args[1:])) if len(args) > 1 else {}
        success, response = service_manager.run_tool(tool_name, tool_args)
        print(response if success else f"Tool failed: {response}")
    except json.JSONDecodeError as error:
        print(f"Invalid tool arguments JSON: {error}")


def tools_cmd(*args):
    """List tools registered with ToolManager. Usage: `tools`"""
    success, tools = service_manager.list_tools()
    if success:
        print('\n'.join(tools) if tools else 'No tools registered.')
    else:
        print('ToolManager is unavailable.')


def debug_cmd(*args):
    """Toggle live service output. Usage: `debug on|off|status`"""
    if not args or args[0].lower() == 'status':
        state = 'on' if service_manager.is_debug_output_enabled() else 'off'
        print(f"Debug output is {state}")
        return

    value = args[0].lower()
    if value not in ('on', 'off'):
        print("Usage: debug on|off|status")
        return

    enabled = value == 'on'
    service_manager.set_debug_output(enabled)
    print(f"Debug output turned {value}")


# Command registry
commands = {
    'help': help_cmd,
    'start': start_cmd,
    'stop': stop_cmd,
    'restart': restart_cmd,
    'status': status_cmd,
    'monitor': monitor_cmd,
    'list': list_cmd,
    'export': export_cmd,
    'info': info_cmd,
    'logs': logs_cmd,
    'output': output_cmd,
    'debug': debug_cmd,
    'sources': sources_cmd,
    'event': event_cmd,
    'tool': tool_cmd,
    'tools': tools_cmd,
    'clear': clear_cmd,
    'quit': quit_cmd,
    'exit': quit_cmd,  # Alias
}


def command_parse(c):
    """Parse user input into command and arguments"""
    parts = c.strip().split(None, 1)
    if not parts:
        return None, []
    
    command = parts[0].lower()
    args = parts[1].split() if len(parts) > 1 else []
    
    return command, args


def main_loop():
    """Main command loop"""
    print_header("WELCOME TO ROBERT CONTROL HUB")
    print("\nType 'help' for available commands")
    print("Type 'help <command>' for command-specific help\n")
    logger.info("Robert Control Hub started")
    
    while True:
        try:
            user_input = input("robert> ").strip()
            
            if not user_input:
                continue
            
            command, args = command_parse(user_input)
            
            if command is None:
                continue
            
            if command not in commands:
                print(f"✗ Unknown command: '{command}'. Type 'help' for available commands.")
                logger.warning(f"Unknown command entered: {command}")
                continue
            
            # Execute command
            commands[command](*args)
            
        except KeyboardInterrupt:
            print("\n\nUse 'quit' to shutdown properly")
            logger.info("Received KeyboardInterrupt")
        except Exception as e:
            print(f"✗ Error: {e}")
            traceback.print_exc()
            logger.error(f"Error executing command: {e}", exc_info=True)


def start_web_dashboard():
    """Start the authenticated dashboard in a background thread."""
    try:
        dashboard = create_dashboard(service_manager)
    except RuntimeError as error:
        logger.error("Web dashboard disabled: %s", error)
        print(f"Web dashboard disabled: {error}")
        return None

    host = os.environ.get('ROBERT_DASHBOARD_HOST', '0.0.0.0')
    port = int(os.environ.get('ROBERT_DASHBOARD_PORT', '8080'))
    thread = threading.Thread(
        target=dashboard.run,
        kwargs={'host': host, 'port': port, 'debug': False, 'use_reloader': False},
        daemon=True,
        name='RobertDashboard'
    )
    thread.start()
    logger.info("Web dashboard started at http://%s:%s", host, port)
    print(f"Web dashboard: http://{host}:{port}")
    return thread


if __name__ == '__main__':
    try:
        start_web_dashboard()
        main_loop()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Shutting down...")
        logger.info("Control Hub interrupted, shutting down services")
        service_manager.stop_all()
        sys.exit(0)