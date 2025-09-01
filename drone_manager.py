import airsim
import time
import numpy as np
import asyncio
import threading

class DroneManager:
    def __init__(self, num_drones=5):  # Default to 5 drones
        self.num_drones = num_drones
        self.drone_names = [f"Drone{i}" for i in range(num_drones)]
        self.client = None
        self.connected_drones = []
        self.formation_positions = []
        
    def connect_drones(self, num_drones=None):
        """Connect to AirSim and initialize drones"""
        if num_drones:
            self.num_drones = num_drones
            self.drone_names = [f"Drone{i}" for i in range(num_drones)]
            
        try:
            print(f"🔌 Connecting to AirSim...")
            self.client = airsim.MultirotorClient()
            self.client.confirmConnection()
            print("✅ Connected to AirSim!")
            
            # First, check which drones are actually available
            print(f"🔍 Checking for available drones...")
            available_drones = []
            
            for drone_name in self.drone_names:
                try:
                    # Test if drone exists by getting its state
                    state = self.client.getMultirotorState(vehicle_name=drone_name)
                    available_drones.append(drone_name)
                    print(f"✅ Found {drone_name} at position: "
                          f"X={state.kinematics_estimated.position.x_val:.1f}, "
                          f"Y={state.kinematics_estimated.position.y_val:.1f}, "
                          f"Z={state.kinematics_estimated.position.z_val:.1f}")
                except Exception:
                    print(f"❌ {drone_name} not found in simulation")
            
            if not available_drones:
                print("❌ No drones found! Check your settings.json")
                return 0
            
            print(f"📊 Found {len(available_drones)} drones in simulation")
            
            # Enable API control for all available drones
            connected_count = 0
            for drone_name in available_drones:
                try:
                    print(f"🚁 Initializing {drone_name}...")
                    self.client.enableApiControl(True, drone_name)
                    self.client.armDisarm(True, drone_name)
                    self.connected_drones.append(drone_name)
                    connected_count += 1
                    print(f"✅ {drone_name} ready!")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"❌ Failed to initialize {drone_name}: {e}")
                    
            print(f"🎯 Successfully connected {connected_count} out of {len(available_drones)} drones")
            
            if connected_count < self.num_drones:
                print(f"⚠️ Warning: Expected {self.num_drones} drones but only connected {connected_count}")
                print("   Check your settings.json and restart AirSim if needed")
            
            return connected_count
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return 0
    
    def takeoff_all(self):
        """Takeoff all connected drones"""
        print("🚀 Taking off all drones...")
        
        for drone_name in self.connected_drones:
            try:
                print(f"🚁 {drone_name} taking off...")
                self.client.takeoffAsync(vehicle_name=drone_name)
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ {drone_name} takeoff failed: {e}")
        
        # Wait for all to stabilize
        print("⏳ Waiting for all drones to stabilize...")
        time.sleep(3)  # Good for 5 drones
        print("✅ All drones airborne!")
    
    def land_all(self):
        """Land all connected drones"""
        print("🛬 Landing all drones...")
        
        for drone_name in self.connected_drones:
            try:
                print(f"🚁 {drone_name} landing...")
                self.client.landAsync(vehicle_name=drone_name)
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ {drone_name} landing failed: {e}")
        
        print("⏳ Waiting for all drones to land...")
        time.sleep(5)
        print("✅ All drones landed!")
    
    def move_to_formation(self, positions, altitude=-10):
        """Move drones to specific formation positions - FIXED VERSION"""
        if not positions:
            print("❌ No positions provided!")
            return False
            
        print(f"📐 Moving {len(self.connected_drones)} drones to formation...")
        print(f"🎯 Formation positions: {positions}")
        
        # Ensure we have enough drones for the formation
        num_positions = len(positions)
        available_drones = len(self.connected_drones)
        
        if available_drones < num_positions:
            print(f"⚠️ Need {num_positions} drones but only {available_drones} available")
            # Use available drones for the first N positions
            positions = positions[:available_drones]
            print(f"🔧 Using first {available_drones} positions: {positions}")
        elif available_drones > num_positions:
            print(f"ℹ️ Have {available_drones} drones for {num_positions} positions")
            print(f"   Extra drones will stay at current position")
        
        # FIXED: Use synchronous movement to avoid Future object issues
        try:
            for i, (drone_name, position) in enumerate(zip(self.connected_drones, positions)):
                try:
                    x, y = position
                    print(f"🚁 Moving {drone_name} to ({x:.2f}, {y:.2f}, {altitude})")
                    
                    # Use synchronous movement - this fixes the Future object error
                    self.client.moveToPositionAsync(
                        x, y, altitude, 
                        velocity=3.0,
                        vehicle_name=drone_name
                    ).join()  # Wait for this movement to complete
                    
                    time.sleep(0.2)  # Small delay between movements
                    
                except Exception as e:
                    print(f"❌ Failed to move {drone_name}: {e}")
            
            print("✅ Formation complete!")
            return True
            
        except Exception as e:
            print(f"❌ Formation movement failed: {e}")
            return False
    
    def get_drone_positions(self):
        """Get current positions of all drones"""
        positions = {}
        for drone_name in self.connected_drones:
            try:
                state = self.client.getMultirotorState(vehicle_name=drone_name)
                pos = state.kinematics_estimated.position
                positions[drone_name] = (pos.x_val, pos.y_val, pos.z_val)
            except Exception as e:
                print(f"❌ Failed to get position for {drone_name}: {e}")
                positions[drone_name] = (0, 0, 0)
        return positions
    
    def print_drone_status(self):
        """Print status of all connected drones"""
        print(f"\n📊 === DRONE STATUS ({len(self.connected_drones)} drones) ===")
        positions = self.get_drone_positions()
        
        for i, drone_name in enumerate(self.connected_drones):
            x, y, z = positions.get(drone_name, (0, 0, 0))
            print(f"🚁 {drone_name}: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
        print("=" * 50)
    
    def reset_all(self):
        """Reset all drones to starting position"""
        print("🔄 Resetting all drones...")
        try:
            self.client.reset()
            time.sleep(3)
            
            # Re-enable API control after reset
            for drone_name in self.connected_drones:
                try:
                    self.client.enableApiControl(True, drone_name)
                    self.client.armDisarm(True, drone_name)
                    time.sleep(0.3)
                except Exception as e:
                    print(f"❌ Failed to reset {drone_name}: {e}")
                
            print("✅ All drones reset!")
        except Exception as e:
            print(f"❌ Reset failed: {e}")
    
    def disconnect(self):
        """Disconnect from AirSim"""
        try:
            if self.client:
                print("🔌 Disconnecting from AirSim...")
                for drone_name in self.connected_drones:
                    try:
                        self.client.enableApiControl(False, drone_name)
                    except Exception as e:
                        print(f"❌ Error disabling {drone_name}: {e}")
                print("✅ Disconnected!")
        except Exception as e:
            print(f"❌ Disconnect error: {e}")

# Test the drone manager
if __name__ == "__main__":
    print("🧪 Testing Drone Manager with 5 Drones...")
    
    # Create drone manager for 5 drones
    dm = DroneManager(num_drones=5)
    
    # Connect to drones
    connected = dm.connect_drones(5)
    
    if connected > 0:
        try:
            # Print current status
            dm.print_drone_status()
            
            # Test takeoff
            dm.takeoff_all()
            
            # Test formation (pentagon for 5 drones)
            print("🔷 Creating pentagon formation...")
            pentagon_positions = []
            center_x, center_y = 0, 0
            radius = 12
            
            for i in range(5):
                angle = 2 * np.pi * i / 5  # 5 equally spaced points
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                pentagon_positions.append((x, y))
            
            print(f"🎯 Pentagon positions: {pentagon_positions}")
            dm.move_to_formation(pentagon_positions)
            
            # Print final positions
            dm.print_drone_status()
            
            # Hold formation
            print("⏳ Holding formation for 5 seconds...")
            time.sleep(5)
            
            # Land
            dm.land_all()
            
        except KeyboardInterrupt:
            print("🛑 Interrupted by user")
        finally:
            dm.disconnect()
    else:
        print("❌ No drones connected. Make sure AirSim is running!")
        print("📋 Troubleshooting steps:")
        print("1. Check if settings.json is in the correct location")
        print("2. Restart AirSim after updating settings.json")
        print("3. Verify all 5 drones appear in the Unreal Engine scene")
        print("4. Run this script to test drone connections")