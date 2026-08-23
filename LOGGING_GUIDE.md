# Robert System Logging Guide

Complete logging system for the Robert control hub and all services. All output is captured, logged, and can be viewed in real-time.

## Logging Architecture

### Log Files Location
All logs are stored in the `logs/` directory:

```
logs/
├── robert_system.log          # Main system log
├── control_hub.log            # Control hub commands and actions
├── CognitiveManager.log       # CognitiveManager service output
├── EventManager.log           # EventManager service output
├── InputManager.log           # InputManager service output
├── AI.log                     # AI service output
└── ToolManager.log            # ToolManager service output
```

### Automatic Log Creation
- Logs are automatically created when services start
- Logs are created when you run `main.py`
- All service output is captured in real-time

## Viewing Logs

### View System Logs
```
logs                    # Show system log (last 20 lines)
logs system 50          # Show system log (last 50 lines)
```

### View Service Logs
```
logs CognitiveManager    # Show service log (last 20 lines)
logs InputManager 50     # Show service log (last 50 lines)
```

### View Recent Service Output
```
output CognitiveManager   # Show recent output (last 20 lines)
output InputManager 50    # Show recent output (last 50 lines)
```

### Toggle Live Output
```
debug off                # Hide live service output in the control hub
debug on                 # Show live service output again
debug status             # Show the current setting
```

The toggle affects only output printed live by service processes. Output continues
to be written to log files and kept in the recent-output buffer.

## Log Format

Each log entry follows this format:
```
YYYY-MM-DD HH:MM:SS - LoggerName - LEVEL - Message
2024-01-15 14:23:45 - Robert.CognitiveManager - INFO - Starting service: CognitiveManager
```

### Log Levels
- **INFO** - Informational messages (normal operations)
- **WARNING** - Warning messages (issues that don't prevent operation)
- **ERROR** - Error messages (serious issues)
- **DEBUG** - Debug messages (when enabled)

## What Gets Logged

### System Logging
- Service start/stop/restart events
- Health check results
- Auto-restart operations
- User commands
- System events and errors

### Service Logging
- Service startup with PID
- All service output (stdout/stderr)
- Health check status
- Restart events
- Error messages

### Control Hub Logging
- All user commands entered
- Command execution results
- Export operations
- Monitoring start/stop events

## Monitoring with Logs

When you run `monitor start`, the system:
1. Starts health monitoring
2. Performs periodic health checks
3. Logs all health check results
4. Shows compact status updates with timestamps
5. Logs any automatic restarts

Example monitoring output:
```
[14:23:45] Status check:
  ✓ AI: healthy
  ✓ CognitiveManager: healthy
  ✓ EventManager: healthy
  ✓ InputManager: healthy
  ✓ ToolManager: healthy
```

## Exporting Logs

Export current status (which includes log references):
```
export                    # Export to 'system_status.json'
export my_export.json     # Export to specific file
```

## Reading Log Files Directly

View raw log files from command line:
```bash
# View last 50 lines of system log
tail -50 logs/robert_system.log

# View all logs for a service
cat logs/CognitiveManager.log

# Search logs for errors
grep ERROR logs/robert_system.log

# Watch logs in real-time
tail -f logs/robert_system.log
```

## Log Rotation (Best Practices)

For long-running systems, consider rotating logs:
```bash
# Compress old logs
gzip logs/*.log

# Move old logs to archive
mkdir -p logs/archive
mv logs/*.log.gz logs/archive/
```

## Troubleshooting with Logs

### Service won't start?
1. Check service log: `logs ServiceName`
2. Check system log: `logs`
3. Look for error messages with ERROR level

### Service crashes repeatedly?
1. View service output: `output ServiceName 100`
2. Check restart count: `status ServiceName`
3. Review logs for patterns in failures

### Network/connectivity issues?
1. Search logs for "unreachable": `grep unreachable logs/*.log`
2. Check health check failures: `logs`
3. Verify ports in use: `lsof -i :5000`

## Log Size Management

Logs grow over time. Monitor and manage:
```bash
# Check log file sizes
du -sh logs/*

# Clean logs older than 7 days
find logs -name "*.log" -mtime +7 -delete

# Compress logs to save space
find logs -name "*.log" -exec gzip {} \;
```

## Real-time Log Streaming

Monitor logs while monitoring runs:
```bash
# Terminal 1: Start monitoring
python main.py
> monitor start

# Terminal 2: Watch logs in real-time
tail -f logs/robert_system.log
```

## Integration with External Tools

Export logs for analysis:
```bash
# Export all logs to single file
cat logs/*.log > robert_all_logs.txt

# Export with timestamps
tail -f logs/robert_system.log | tee monitoring.log

# Send to syslog
logger -t robert < logs/robert_system.log
```

## Performance Impact

Logging overhead is minimal:
- ~2% CPU impact from log writing
- ~100KB per 1000 log entries
- Buffer size: 100 lines per service
- Doesn't block service operations

## Recommended Usage

1. **Daily**: Check logs for errors
   ```
   logs
   logs system 50
   ```

2. **During Monitoring**: Watch service output
   ```
   monitor start
   output ServiceName
   ```

3. **Weekly**: Export status and archive
   ```
   export status.json
   gzip logs/*.log
   ```

4. **On Issues**: Search logs for specific errors
   ```
   logs ServiceName 200
   tail -f logs/robert_system.log
   ```
