# Robert Unified Control System

A comprehensive system for controlling, monitoring, and managing all Robert services from a single central hub.

## Overview

The unified control system consists of three main components:

### 1. **ServiceManager.py** - Core Service Management
- Starts, stops, and restarts services
- Monitors health and automatically restarts failed services
- Manages service dependencies
- Provides comprehensive status reporting

### 2. **main.py** - Central Command Hub
- Interactive command-line interface for controlling Robert
- Real-time status monitoring
- Service health tracking
- Logging and status export

### 3. **UnifiedAPIClient.py** - Unified Communication Interface
- Single client for communicating with all services
- Broadcast events across services
- Query world state and AI
- Execute tools through ToolManager

## Getting Started

### Web Dashboard Sign-in

The control hub starts an authenticated web dashboard at `http://127.0.0.1:8080`.
Set the dashboard credentials before launching Robert:

```bash
export ROBERT_ADMIN_USERNAME="your-username"
export ROBERT_ADMIN_PASSWORD="your-password"
export ROBERT_DASHBOARD_SECRET="a-long-random-secret"
python main.py
```

The dashboard is local-only by default. It provides service status, recent logs,
start/stop/restart controls, monitoring controls, and the live debug-output toggle.
Use `ROBERT_DASHBOARD_PORT` to change the port. Do not expose it beyond localhost
unless you also put it behind HTTPS and a trusted network boundary.

### Starting Robert

Simply run the main control hub:

```bash
cd /home/asherevan/robert
python main.py
```

This launches an interactive console where you can control all services.

## Available Commands

### Service Control

**Start Services**
```
start all                    # Start all services in dependency order
start CognitiveManager       # Start a specific service
```

**Stop Services**
```
stop all                     # Stop all services
stop EventManager            # Stop a specific service
```

**Restart Services**
```
restart all                  # Restart all services
restart InputManager         # Restart a specific service
```

### Monitoring & Status

**View Status**
```
status                       # Show status of all services
status CognitiveManager      # Show status of specific service
```

**Health Monitoring**
```
monitor start                # Start health monitoring (10s interval)
monitor start 30             # Start monitoring with 30s interval
monitor stop                 # Stop health monitoring
monitor 15                   # Shortcut to start with 15s interval
```

**Detailed Information**
```
info CognitiveManager        # Get detailed info about a service
```

### System Management

**List Services**
```
list                         # Show all registered services
```

**Export Status**
```
export                       # Export status to 'system_status.json'
export my_status.json        # Export to custom filename
```

**Get Help**
```
help                         # Show all available commands
help start                   # Show help for specific command
```

**Shutdown**
```
quit                         # Gracefully shutdown Robert
exit                         # Alias for quit
```

## Service Architecture

```
Robert Control Hub (main.py)
    │
    ├── ServiceManager
    │   ├── CognitiveManager (port 5000)
    │   ├── EventManager (port 5001)
    │   ├── InputManager (port 5002)
    │   ├── AI (port 5003)
    │   └── ToolManager (port 5004)
    │
    └── UnifiedAPIClient
        ├── CognitiveManagerClient
        ├── EventManagerClient
        ├── InputManagerClient
        ├── AIClient
        └── ToolManagerClient
```

## Using UnifiedAPIClient Programmatically

You can use the UnifiedAPIClient in your own Python scripts:

```python
from UnifiedAPIClient import get_api_client

# Get the global API client
client = get_api_client()

# Check health of all services
health = client.health_check_all()

# Get world state
world_state = client.get_world_state()

# Update input values
client.update_input('temperature', 25.5, group='sensors')

# Update world state
client.update_world_state('current_mode', 'auto')

# Broadcast an event
event = {'type': 'sensor_alert', 'sensor': 'temperature', 'value': 35.0}
client.broadcast_event(event)

# Query the AI
response = client.query_ai("What is the current status?")

# Call a tool
result = client.call_tool('send_notification', {'message': 'Test'})
```

## Service Ports

- **CognitiveManager**: Port 5000 - Central world state management
- **EventManager**: Port 5001 - Event processing and distribution
- **InputManager**: Port 5002 - Input management and monitoring
- **AI**: Port 5003 - AI processing and response generation
- **ToolManager**: Port 5004 - Tool execution interface

## Status Output Example

```
============================================================
  ROBERT SYSTEM STATUS
============================================================

Timestamp: 2024-01-15 14:23:45

Service              Status       Health       Port   Restarts
----------------------------------------------------------------------
AI                   ✓ Running    ✓ healthy    5003   0
CognitiveManager     ✓ Running    ✓ healthy    5000   0
EventManager         ✓ Running    ✓ healthy    5001   0
InputManager         ✓ Running    ✓ healthy    5002   0
ToolManager          ✓ Running    ✓ healthy    5004   1

✓ = Healthy/Running | ✗ = Failed/Stopped | ? = Unknown
```

## Features

### Automatic Health Monitoring
- Periodic health checks of all services
- Automatic restart of failed services
- Detailed error logging

### Dependency Management
- Services automatically respect dependencies
- Dependent services start in correct order
- Parent services stop before dependent services

### Comprehensive Logging
- All events logged with timestamps
- Error tracking and reporting
- Service uptime tracking

### Status Persistence
- Export system status to JSON format
- Track restart history
- Historical health data

## Troubleshooting

### Service won't start
1. Check logs: `status <service_name>`
2. Verify port is not in use: `lsof -i :5000`
3. Try manual restart: `restart <service_name>`

### Health check failing
- Service may be overloaded
- Check network connectivity
- Verify service is properly initialized

### Monitoring overhead
- Adjust monitoring interval: `monitor 30` (for 30 seconds)
- Disable monitoring: `monitor stop`

## Integration Points

Services communicate through:
1. **Flask REST API** - Service-to-service HTTP communication
2. **Event Broadcasting** - Multi-service event distribution
3. **Shared State** - CognitiveManager world state

## Next Steps

1. Start all services: `start all`
2. Monitor health: `monitor start`
3. View real-time status: `status`
4. Use UnifiedAPIClient for programmatic access

## Notes

- Services are started with automatic dependency resolution
- Health checks run every 10 seconds (configurable)
- Failed services are automatically restarted
- All status data is logged with timestamps
