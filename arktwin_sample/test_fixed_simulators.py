#!/usr/bin/env python3
"""
Test script to verify the fixed simulators work correctly
"""

import subprocess
import time
import sys
import os
import signal

def run_test():
    """Run a quick test of both simulators"""
    print("=== ArkTwin Fixed Simulators Test ===")
    
    # Start vehicle simulator in background
    print("Starting vehicle simulator...")
    vehicle_proc = subprocess.Popen(
        [sys.executable, "vehicle_simulator.py"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a bit for vehicle simulator to start
    time.sleep(3)
    
    # Start pedestrian simulator in background  
    print("Starting pedestrian simulator...")
    pedestrian_proc = subprocess.Popen(
        [sys.executable, "pedestrian_simulator.py"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Let them run for 10 seconds
        print("Running simulators for 10 seconds...")
        time.sleep(10)
        
        # Get output from vehicle simulator
        print("\n=== Vehicle Simulator Output ===")
        vehicle_proc.terminate()
        vehicle_stdout, vehicle_stderr = vehicle_proc.communicate(timeout=5)
        print(vehicle_stdout)
        if vehicle_stderr:
            print("STDERR:", vehicle_stderr)
        
        # Get output from pedestrian simulator
        print("\n=== Pedestrian Simulator Output ===")
        pedestrian_proc.terminate()
        pedestrian_stdout, pedestrian_stderr = pedestrian_proc.communicate(timeout=5)
        print(pedestrian_stdout)
        if pedestrian_stderr:
            print("STDERR:", pedestrian_stderr)
            
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Clean up processes
        try:
            vehicle_proc.terminate()
            vehicle_proc.wait(timeout=2)
        except:
            try:
                vehicle_proc.kill()
            except:
                pass
                
        try:
            pedestrian_proc.terminate()
            pedestrian_proc.wait(timeout=2)
        except:
            try:
                pedestrian_proc.kill()
            except:
                pass
        
        print("Test completed")

if __name__ == "__main__":
    run_test()