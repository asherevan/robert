#!/usr/bin/env python3
"""
logging_examples.py - Examples of using the Robert logging system
"""

from ServiceManager import get_service_manager
import time

def example_1_view_logs():
    """Example 1: View system and service logs"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Viewing Logs")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # View system logs
    print("\n--- System Logs (last 5 lines) ---")
    system_logs = sm.get_recent_log_lines(None, 5)
    for line in system_logs:
        print(line)
    
    # View service logs
    print("\n--- CognitiveManager Logs (last 5 lines) ---")
    service_logs = sm.get_recent_log_lines('CognitiveManager', 5)
    for line in service_logs:
        print(line)
    
    # Stop services
    sm.stop_all()


def example_2_service_output_buffer():
    """Example 2: Access service output buffer"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Service Output Buffer")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start a service
    print("\nStarting CognitiveManager...")
    sm.start_service('CognitiveManager')
    time.sleep(2)
    
    # Get recent output
    print("\n--- Recent Output (last 10 lines) ---")
    output = sm.get_service_logs('CognitiveManager', 10)
    for line in output:
        print(line)
    
    # Stop service
    sm.stop_service('CognitiveManager')


def example_3_log_file_content():
    """Example 3: Read complete log files"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Reading Log Files")
    print("="*60)
    
    sm = get_service_manager()
    
    # Read system log
    print("\n--- System Log File (all content) ---")
    sys_log = sm.read_log_file()
    lines = sys_log.split('\n')
    print(f"Total lines in system log: {len(lines)}")
    print("Last 5 lines:")
    for line in lines[-5:]:
        if line:
            print(line)
    
    # Read service log
    print("\n--- CognitiveManager Log File ---")
    svc_log = sm.read_log_file('CognitiveManager')
    lines = svc_log.split('\n')
    print(f"Total lines: {len(lines)}")


def example_4_all_logs_summary():
    """Example 4: Get summary of all logs"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Logs Summary")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # Get summary
    print("\n--- Logs Summary (last 5 lines from each service) ---")
    summary = sm.get_all_logs_summary()
    
    for service_name, logs in sorted(summary.items()):
        print(f"\n{service_name}:")
        for log_line in logs[-3:]:  # Show last 3 lines
            print(f"  {log_line}")
    
    # Stop services
    sm.stop_all()


def example_5_monitoring_with_logs():
    """Example 5: Monitor services with log output"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Monitoring with Logs")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # Enable monitoring
    print("\nEnabling monitoring for 20 seconds...")
    sm.start_monitoring(check_interval=5)
    
    # Run monitoring loop
    for i in range(4):
        time.sleep(5)
        
        # Get current status
        status = sm.get_all_status()
        print(f"\n[Check {i+1}] Service Status:")
        
        for name, svc_status in sorted(status['services'].items()):
            health = svc_status['health_status']
            indicator = "✓" if health == 'healthy' else "✗"
            print(f"  {indicator} {name}: {health}")
    
    # Stop monitoring
    sm.stop_monitoring()
    sm.stop_all()


def example_6_search_logs():
    """Example 6: Search logs for specific content"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Searching Logs")
    print("="*60)
    
    sm = get_service_manager()
    
    # Get system log
    sys_log = sm.read_log_file()
    
    # Search for ERROR
    print("\n--- Searching for ERROR in system log ---")
    error_lines = [line for line in sys_log.split('\n') if 'ERROR' in line]
    print(f"Found {len(error_lines)} ERROR entries")
    if error_lines:
        for line in error_lines[:5]:  # Show first 5
            print(f"  {line}")
    else:
        print("  No errors found")
    
    # Search for START
    print("\n--- Searching for START in system log ---")
    start_lines = [line for line in sys_log.split('\n') if 'start' in line.lower()]
    print(f"Found {len(start_lines)} START entries")
    if start_lines:
        for line in start_lines[:5]:
            print(f"  {line}")


def main():
    """Run examples"""
    print("\n" + "="*60)
    print("Robert Logging System - Examples")
    print("="*60)
    
    examples = [
        ("View Logs", example_1_view_logs),
        ("Service Output Buffer", example_2_service_output_buffer),
        ("Log File Content", example_3_log_file_content),
        ("Logs Summary", example_4_all_logs_summary),
        ("Monitoring with Logs", example_5_monitoring_with_logs),
        ("Search Logs", example_6_search_logs),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nUncomment an example at the bottom to run it")


if __name__ == '__main__':
    main()
    
    # Uncomment to run examples:
    # example_1_view_logs()
    # example_2_service_output_buffer()
    # example_3_log_file_content()
    # example_4_all_logs_summary()
    # example_5_monitoring_with_logs()
    # example_6_search_logs()
