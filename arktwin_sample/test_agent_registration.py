#!/usr/bin/env python3
"""
Test script to verify agent registration and ID tracking
"""

import requests
import json

def test_vehicle_registration():
    """Test vehicle agent registration"""
    edge_url = "http://127.0.0.1:2237"
    
    # Test agent registration
    agents = [
        {"agentIdPrefix": "vehicle-001", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-002", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-003", "kind": "vehicle", "status": {}, "assets": {}}
    ]
    
    try:
        response = requests.post(
            f"{edge_url}/api/edge/agents",
            json=agents,
            timeout=5
        )
        response.raise_for_status()
        
        response_data = response.json()
        print("Registration response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract agent ID mappings
        registered_agent_ids = {}
        if "agents" in response_data:
            for agent_data in response_data["agents"]:
                agent_id = agent_data["agentId"]
                # Find matching prefix
                for prefix in ["vehicle-001", "vehicle-002", "vehicle-003"]:
                    if agent_id.startswith(prefix):
                        registered_agent_ids[prefix] = agent_id
                        print(f"Vehicle {prefix} -> Agent ID: {agent_id}")
                        break
        
        return registered_agent_ids
        
    except requests.RequestException as e:
        print(f"Registration error: {e}")
        return {}

def test_pedestrian_registration():
    """Test pedestrian agent registration"""
    edge_url = "http://127.0.0.1:2238"
    
    # Test agent registration
    agents = [
        {"agentIdPrefix": "pedestrian-001", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-002", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-003", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-004", "kind": "pedestrian", "status": {}, "assets": {}}
    ]
    
    try:
        response = requests.post(
            f"{edge_url}/api/edge/agents",
            json=agents,
            timeout=5
        )
        response.raise_for_status()
        
        response_data = response.json()
        print("Registration response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract agent ID mappings
        registered_agent_ids = {}
        if "agents" in response_data:
            for agent_data in response_data["agents"]:
                agent_id = agent_data["agentId"]
                # Find matching prefix
                for prefix in ["pedestrian-001", "pedestrian-002", "pedestrian-003", "pedestrian-004"]:
                    if agent_id.startswith(prefix):
                        registered_agent_ids[prefix] = agent_id
                        print(f"Pedestrian {prefix} -> Agent ID: {agent_id}")
                        break
        
        return registered_agent_ids
        
    except requests.RequestException as e:
        print(f"Registration error: {e}")
        return {}

if __name__ == "__main__":
    print("=== Testing Vehicle Registration ===")
    vehicle_ids = test_vehicle_registration()
    
    print("\n=== Testing Pedestrian Registration ===")
    pedestrian_ids = test_pedestrian_registration()
    
    print(f"\nVehicle IDs: {vehicle_ids}")
    print(f"Pedestrian IDs: {pedestrian_ids}")