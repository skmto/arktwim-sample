#!/usr/bin/env python3
"""
Test neighbor detection with proper agent IDs
"""

import requests
import json
import math
import time

def test_neighbor_detection():
    """Test the complete neighbor detection flow"""
    
    # Step 1: Register vehicle agents
    print("=== Registering Vehicle Agents ===")
    vehicle_agents = [
        {"agentIdPrefix": "vehicle-001", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-002", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-003", "kind": "vehicle", "status": {}, "assets": {}}
    ]
    
    response = requests.post("http://127.0.0.1:2237/api/edge/agents", json=vehicle_agents)
    response.raise_for_status()
    vehicle_response = response.json()
    print("Vehicle registration response:", json.dumps(vehicle_response, indent=2))
    
    # Extract actual vehicle agent IDs
    vehicle_agent_ids = [agent["agentId"] for agent in vehicle_response]
    print(f"Vehicle agent IDs: {vehicle_agent_ids}")
    
    # Step 2: Register pedestrian agents
    print("\n=== Registering Pedestrian Agents ===")
    pedestrian_agents = [
        {"agentIdPrefix": "pedestrian-001", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-002", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-003", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-004", "kind": "pedestrian", "status": {}, "assets": {}}
    ]
    
    response = requests.post("http://127.0.0.1:2238/api/edge/agents", json=pedestrian_agents)
    response.raise_for_status()
    pedestrian_response = response.json()
    print("Pedestrian registration response:", json.dumps(pedestrian_response, indent=2))
    
    # Extract actual pedestrian agent IDs
    pedestrian_agent_ids = [agent["agentId"] for agent in pedestrian_response]
    print(f"Pedestrian agent IDs: {pedestrian_agent_ids}")
    
    # Step 3: Send position updates using correct agent IDs
    print("\n=== Sending Position Updates ===")
    
    # Vehicle positions (near origin)
    vehicle_positions = [
        (0.0, 0.0, 0.5),   # vehicle-001 at origin
        (5.0, 0.0, 0.5),   # vehicle-002 5m east
        (0.0, 5.0, 0.5),   # vehicle-003 5m north
    ]
    
    # Pedestrian positions (near vehicles)
    pedestrian_positions = [
        (0.0, 0.0, 0.0),    # pedestrian-001 at origin
        (-2.0, 2.0, 0.0),   # pedestrian-002 nearby
        (2.0, -2.0, 0.0),   # pedestrian-003 nearby
        (7.0, 2.0, 0.0),    # pedestrian-004 nearby
    ]
    
    timestamp = {"seconds": int(time.time()), "nanos": 0}
    
    # Send vehicle transforms
    vehicle_transforms = {}
    for i, agent_id in enumerate(vehicle_agent_ids):
        x, y, z = vehicle_positions[i]
        vehicle_transforms[agent_id] = {
            "transform": {
                "parentAgentId": None,
                "globalScale": {"x": 1.0, "y": 1.0, "z": 1.0},
                "localRotation": {"EulerAngles": {"x": 0.0, "y": 0.0, "z": 0.0}},
                "localTranslation": {"x": x, "y": y, "z": z},
                "localTranslationSpeed": {"x": 0.0, "y": 0.0, "z": 0.0}
            },
            "status": {}
        }
    
    vehicle_data = {"timestamp": timestamp, "agents": vehicle_transforms}
    response = requests.put("http://127.0.0.1:2237/api/edge/agents", json=vehicle_data)
    response.raise_for_status()
    print("Vehicle positions sent successfully")
    
    # Send pedestrian transforms
    pedestrian_transforms = {}
    for i, agent_id in enumerate(pedestrian_agent_ids):
        x, y, z = pedestrian_positions[i]
        pedestrian_transforms[agent_id] = {
            "transform": {
                "parentAgentId": None,
                "globalScale": {"x": 1.0, "y": 1.0, "z": 1.0},
                "localRotation": {"EulerAngles": {"x": 0.0, "y": 0.0, "z": 0.0}},
                "localTranslation": {"x": x, "y": y, "z": z},
                "localTranslationSpeed": {"x": 0.0, "y": 0.0, "z": 0.0}
            },
            "status": {}
        }
    
    pedestrian_data = {"timestamp": timestamp, "agents": pedestrian_transforms}
    response = requests.put("http://127.0.0.1:2238/api/edge/agents", json=pedestrian_data)
    response.raise_for_status()
    print("Pedestrian positions sent successfully")
    
    # Step 4: Query neighbors from vehicle perspective
    print("\n=== Querying Neighbors (Vehicle Side) ===")
    query = {
        "timestamp": timestamp,
        "neighborsNumber": 50,
        "changeDetection": True
    }
    
    response = requests.post("http://127.0.0.1:2237/api/edge/neighbors/_query", json=query)
    response.raise_for_status()
    
    neighbors_data = response.json()
    print("Vehicle neighbors response:", json.dumps(neighbors_data, indent=2))
    
    if "neighbors" in neighbors_data:
        neighbors = neighbors_data["neighbors"]
        pedestrian_neighbors = {k: v for k, v in neighbors.items() if k.startswith("pedestrian")}
        print(f"Found {len(pedestrian_neighbors)} pedestrian neighbors from vehicle perspective:")
        for agent_id in pedestrian_neighbors.keys():
            print(f"  - {agent_id}")
    
    # Step 5: Query neighbors from pedestrian perspective
    print("\n=== Querying Neighbors (Pedestrian Side) ===")
    response = requests.post("http://127.0.0.1:2238/api/edge/neighbors/_query", json=query)
    response.raise_for_status()
    
    neighbors_data = response.json()
    print("Pedestrian neighbors response:", json.dumps(neighbors_data, indent=2))
    
    if "neighbors" in neighbors_data:
        neighbors = neighbors_data["neighbors"]
        vehicle_neighbors = {k: v for k, v in neighbors.items() if k.startswith("vehicle")}
        print(f"Found {len(vehicle_neighbors)} vehicle neighbors from pedestrian perspective:")
        for agent_id in vehicle_neighbors.keys():
            print(f"  - {agent_id}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_neighbor_detection()