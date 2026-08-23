"""
example_usage.py - Example usage of the Robert unified control system
Demonstrates how to use ServiceManager and UnifiedAPIClient
"""

from ServiceManager import get_service_manager
from UnifiedAPIClient import get_api_client
import time


def example_1_basic_service_control():
    """Example 1: Basic service control"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Service Control")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start all services
    print("\nStarting all services...")
    sm.start_all()
    time.sleep(2)
    
    # Get status
    print("\nService Status:")
    status = sm.get_all_status()
    for service_name, svc_status in status['services'].items():
        print(f"  {service_name}: {'Running' if svc_status['is_running'] else 'Stopped'}")
    
    # Stop all services
    print("\nStopping all services...")
    sm.stop_all()


def example_2_health_monitoring():
    """Example 2: Health monitoring setup"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Health Monitoring")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    
    # Enable health monitoring
    print("Enabling health monitoring...")
    sm.start_monitoring(check_interval=5)
    
    # Run for 15 seconds
    print("Monitoring for 15 seconds...")
    for i in range(3):
        time.sleep(5)
        print(f"\nStatus check {i+1}:")
        status = sm.get_all_status()
        for name, svc in status['services'].items():
            health = svc['health_status']
            print(f"  {name}: {health}")
    
    # Stop monitoring
    sm.stop_monitoring()
    sm.stop_all()


def example_3_api_communication():
    """Example 3: Using unified API client"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Unified API Communication")
    print("="*60)
    
    sm = get_service_manager()
    client = get_api_client()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # Health check
    print("\nChecking service health...")
    health = client.health_check_all()
    for service, is_healthy in health.items():
        print(f"  {service}: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    # Get world state
    print("\nGetting world state...")
    try:
        world_state = client.get_world_state()
        print(f"  Available parameters: {world_state}")
    except Exception as e:
        print(f"  Could not retrieve world state: {e}")
    
    # Stop services
    print("\nStopping services...")
    sm.stop_all()


def example_4_event_broadcasting():
    """Example 4: Broadcasting events"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Event Broadcasting")
    print("="*60)
    
    sm = get_service_manager()
    client = get_api_client()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # Broadcast an event
    print("\nBroadcasting event...")
    event = {
        'type': 'system_event',
        'source': 'example',
        'data': {
            'message': 'Test event from example script',
            'timestamp': time.time()
        }
    }
    
    try:
        result = client.broadcast_event(event)
        print(f"  Broadcast result: {result}")
    except Exception as e:
        print(f"  Broadcast failed: {e}")
    
    # Stop services
    print("\nStopping services...")
    sm.stop_all()


def example_5_individual_service_control():
    """Example 5: Individual service control"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Individual Service Control")
    print("="*60)
    
    sm = get_service_manager()
    
    # List services
    print("\nAvailable services:")
    services = sm.get_service_names()
    for i, name in enumerate(services, 1):
        print(f"  {i}. {name}")
    
    # Start specific services in order
    print("\nStarting services individually...")
    for service in ['CognitiveManager', 'InputManager', 'EventManager', 'AI', 'ToolManager']:
        print(f"  Starting {service}...", end='')
        if sm.start_service(service):
            print(" ✓")
        else:
            print(" ✗")
        time.sleep(1)
    
    # Check status
    print("\nStatus of all services:")
    status = sm.get_all_status()
    for name, svc in status['services'].items():
        uptime = svc['uptime']
        print(f"  {name}: {svc['health_status']} (uptime: {uptime})")
    
    # Stop all
    print("\nStopping all services...")
    sm.stop_all()


def example_6_export_status():
    """Example 6: Export status data"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Export Status Data")
    print("="*60)
    
    sm = get_service_manager()
    
    # Start services
    print("\nStarting services...")
    sm.start_all()
    time.sleep(2)
    
    # Export status
    print("\nExporting status to JSON...")
    sm.export_status_json('example_status.json')
    print("  Status exported to 'example_status.json'")
    
    # Read and display
    import json
    try:
        with open('example_status.json', 'r') as f:
            data = json.load(f)
            print(f"\n  Services in export: {len(data['services'])}")
            print(f"  Timestamp: {data['timestamp']}")
    except Exception as e:
        print(f"  Error reading export: {e}")
    
    # Stop services
    print("\nStopping services...")
    sm.stop_all()


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Robert Unified Control System - Examples")
    print("="*60)
    
    examples = [
        ("Basic Service Control", example_1_basic_service_control),
        ("Health Monitoring", example_2_health_monitoring),
        ("Unified API Communication", example_3_api_communication),
        ("Event Broadcasting", example_4_event_broadcasting),
        ("Individual Service Control", example_5_individual_service_control),
        ("Export Status Data", example_6_export_status),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRun specific examples or modify this script to run selected examples.")
    print("\nTo run an example, uncomment its call at the bottom of this file.")


if __name__ == '__main__':
    # Uncomment any example to run it
    main()
    
    # Run specific examples:
    # example_1_basic_service_control()
    # example_2_health_monitoring()
    # example_3_api_communication()
    # example_4_event_broadcasting()
    # example_5_individual_service_control()
    # example_6_export_status()
