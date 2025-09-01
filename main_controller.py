import time
import sys
import os
import threading
import keyboard
import airsim
import math

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from drawing_capture import PreciseCanvasCapture
from drone_manager import DroneManager
from coordinate_scaler import CoordinateScaler

class CameraController:
    def __init__(self):
        self.client = airsim.MultirotorClient()
        self.running = False
        self.camera_thread = None
        self.move_speed = 2.0  # m/s
        self.rotate_speed = 30.0  # degrees/s
        
        # Default camera position
        self.default_position = airsim.Vector3r(0, 0, -20)
        self.default_orientation = airsim.Quaternionr(0, 0, 0, 1)
        
        # Current camera state
        self.current_position = self.default_position
        self.current_yaw = 0
        self.current_pitch = 0
        
    def start(self):
        """Start camera control in background thread"""
        if not self.running:
            self.running = True
            self.camera_thread = threading.Thread(target=self._camera_control_loop, daemon=True)
            self.camera_thread.start()
            print("🎥 Camera control started!")
            self._print_controls()
    
    def stop(self):
        """Stop camera control"""
        self.running = False
        if self.camera_thread:
            self.camera_thread.join(timeout=1)
        print("🎥 Camera control stopped!")
    
    def _print_controls(self):
        """Print camera control instructions"""
        print("\n🎮 === CAMERA CONTROLS ===")
        print("WASD: Move camera horizontally")
        print("Q/E: Move camera up/down") 
        print("Arrow Keys: Rotate camera")
        print("R: Reset camera to default position")
        print("C: Print current camera position")
        print("ESC: Stop camera control")
        print("========================\n")
    
    def _camera_control_loop(self):
        """Main camera control loop"""
        while self.running:
            try:
                # Movement controls
                if keyboard.is_pressed('w'):
                    self._move_forward()
                if keyboard.is_pressed('s'):
                    self._move_backward()
                if keyboard.is_pressed('a'):
                    self._move_left()
                if keyboard.is_pressed('d'):
                    self._move_right()
                if keyboard.is_pressed('q'):
                    self._move_up()
                if keyboard.is_pressed('e'):
                    self._move_down()
                
                # Rotation controls
                if keyboard.is_pressed('up'):
                    self._rotate_pitch_up()
                if keyboard.is_pressed('down'):
                    self._rotate_pitch_down()
                if keyboard.is_pressed('left'):
                    self._rotate_yaw_left()
                if keyboard.is_pressed('right'):
                    self._rotate_yaw_right()
                
                # Special commands
                if keyboard.is_pressed('r'):
                    self._reset_camera()
                    time.sleep(0.5)  # Prevent multiple resets
                
                if keyboard.is_pressed('c'):
                    self._print_position()
                    time.sleep(0.5)  # Prevent spam
                
                if keyboard.is_pressed('esc'):
                    self.stop()
                    break
                
                time.sleep(0.05)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"❌ Camera control error: {e}")
                time.sleep(0.1)
    
    def _move_forward(self):
        """Move camera forward"""
        # Calculate forward direction based on current yaw
        yaw_rad = math.radians(self.current_yaw)
        dx = self.move_speed * 0.1 * math.cos(yaw_rad)
        dy = self.move_speed * 0.1 * math.sin(yaw_rad)
        self.current_position.x_val += dx
        self.current_position.y_val += dy
        self._update_camera()
    
    def _move_backward(self):
        """Move camera backward"""
        yaw_rad = math.radians(self.current_yaw)
        dx = self.move_speed * 0.1 * math.cos(yaw_rad)
        dy = self.move_speed * 0.1 * math.sin(yaw_rad)
        self.current_position.x_val -= dx
        self.current_position.y_val -= dy
        self._update_camera()
    
    def _move_left(self):
        """Move camera left"""
        yaw_rad = math.radians(self.current_yaw - 90)
        dx = self.move_speed * 0.1 * math.cos(yaw_rad)
        dy = self.move_speed * 0.1 * math.sin(yaw_rad)
        self.current_position.x_val += dx
        self.current_position.y_val += dy
        self._update_camera()
    
    def _move_right(self):
        """Move camera right"""
        yaw_rad = math.radians(self.current_yaw + 90)
        dx = self.move_speed * 0.1 * math.cos(yaw_rad)
        dy = self.move_speed * 0.1 * math.sin(yaw_rad)
        self.current_position.x_val += dx
        self.current_position.y_val += dy
        self._update_camera()
    
    def _move_up(self):
        """Move camera up"""
        self.current_position.z_val -= self.move_speed * 0.1  # Negative Z is up
        self._update_camera()
    
    def _move_down(self):
        """Move camera down"""
        self.current_position.z_val += self.move_speed * 0.1  # Positive Z is down
        self._update_camera()
    
    def _rotate_pitch_up(self):
        """Rotate camera pitch up"""
        self.current_pitch = max(self.current_pitch - 2, -90)
        self._update_camera()
    
    def _rotate_pitch_down(self):
        """Rotate camera pitch down"""
        self.current_pitch = min(self.current_pitch + 2, 90)
        self._update_camera()
    
    def _rotate_yaw_left(self):
        """Rotate camera yaw left"""
        self.current_yaw = (self.current_yaw - 2) % 360
        self._update_camera()
    
    def _rotate_yaw_right(self):
        """Rotate camera yaw right"""
        self.current_yaw = (self.current_yaw + 2) % 360
        self._update_camera()
    
    def _reset_camera(self):
        """Reset camera to default position"""
        self.current_position = airsim.Vector3r(
            self.default_position.x_val,
            self.default_position.y_val, 
            self.default_position.z_val
        )
        self.current_yaw = 0
        self.current_pitch = 0
        self._update_camera()
        print("🎥 Camera reset to default position")
    
    def _update_camera(self):
        """Update camera position and orientation"""
        try:
            # Convert angles to quaternion
            yaw_rad = math.radians(self.current_yaw)
            pitch_rad = math.radians(self.current_pitch)
            roll_rad = 0  # Keep roll at 0
            
            # Create quaternion from Euler angles
            orientation = airsim.to_quaternion(pitch_rad, roll_rad, yaw_rad)
            
            # Create pose
            pose = airsim.Pose(self.current_position, orientation)
            
            # Set camera pose
            self.client.simSetCameraPose("0", pose)
            
        except Exception as e:
            pass  # Silently handle camera update errors
    
    def _print_position(self):
        """Print current camera position"""
        print(f"🎥 Camera Position: X={self.current_position.x_val:.1f}, "
              f"Y={self.current_position.y_val:.1f}, Z={self.current_position.z_val:.1f}")
        print(f"🎥 Camera Rotation: Yaw={self.current_yaw:.1f}°, Pitch={self.current_pitch:.1f}°")
    
    def position_for_formation(self, points, altitude=-15):
        """Position camera to view formation optimally"""
        if not points:
            return
        
        try:
            # Calculate formation center and size
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            # Calculate formation size
            max_x, min_x = max(x_coords), min(x_coords)
            max_y, min_y = max(y_coords), min(y_coords)
            formation_size = max(max_x - min_x, max_y - min_y)
            
            # Position camera for optimal viewing
            # Place camera at an angle to see the formation well
            camera_distance = max(30, formation_size * 2)
            camera_height = max(25, abs(altitude) + 10)
            
            # Position camera at 45-degree angle from formation
            angle = math.radians(45)
            camera_x = center_x + camera_distance * math.cos(angle)
            camera_y = center_y + camera_distance * math.sin(angle)
            camera_z = -camera_height  # Negative Z for elevation
            
            # Update camera position
            self.current_position = airsim.Vector3r(camera_x, camera_y, camera_z)
            
            # Calculate angle to look at formation center
            dx = center_x - camera_x
            dy = center_y - camera_y
            self.current_yaw = math.degrees(math.atan2(dy, dx))
            
            # Look down at formation
            distance_to_formation = math.sqrt(dx*dx + dy*dy)
            dz = abs(altitude) + camera_height
            self.current_pitch = math.degrees(math.atan2(dz, distance_to_formation))
            
            # Update camera
            self._update_camera()
            
            print(f"🎥 Camera positioned for formation viewing")
            print(f"🎥 Distance: {camera_distance:.1f}m, Height: {camera_height:.1f}m")
            
        except Exception as e:
            print(f"❌ Failed to position camera for formation: {e}")

class DroneFormationController:
    def __init__(self):
        self.drawing_capture = PreciseCanvasCapture()
        self.drone_manager = DroneManager()
        self.coordinate_scaler = CoordinateScaler()
        self.camera_controller = CameraController()
        self.is_running = False
        self.last_shape = None
        self.last_points = None
        
    def start_system(self):
        """Initialize the entire system"""
        print("=== AI Drone Formation System with Camera Control ===")
        print("1. Make sure AirSim is running")
        print("2. Open MS Paint")
        print("3. Start drawing shapes!")
        print("4. Use camera controls to view formations:")
        print("   - WASD: Move horizontally")
        print("   - Q/E: Move up/down")
        print("   - Arrow Keys: Rotate camera")
        print("   - R: Reset camera")
        
        print("🚁 Starting AI Drone Formation System...")
        
        # Connect to drones
        print("🔌 Connecting to drones...")
        num_connected = self.drone_manager.connect_drones(5)
        
        if num_connected == 0:
            print("❌ No drones connected! Make sure AirSim is running.")
            return False
            
        print(f"✅ Connected {num_connected} drones")
        
        # Takeoff all drones
        self.drone_manager.takeoff_all()
        
        # Start camera control
        self.camera_controller.start()
        
        return True
    
    def capture_and_process_drawing(self):
        """Capture drawing and process it into drone coordinates"""
        print("📸 Capturing drawing...")
        
        try:
            # The PreciseCanvasCapture class uses main_capture_and_analyze() method
            result = self.drawing_capture.main_capture_and_analyze()
            
            if result is None or len(result) != 4:
                print("❌ No drawing detected or capture failed")
                return None, None
                
            contour, points, waypoints, shape_name = result
            
            if contour is None or not points:
                print("❌ No drawing detected or capture failed")
                return None, None
                
            print(f"🎯 Detected: {shape_name} with {len(points)} points")
            
            # Scale coordinates for drone formation
            if len(points) > 0:
                scaled_points = self.coordinate_scaler.scale_to_drone_coordinates(
                    points, target_size=20, center_at_origin=True
                )
                print(f"📐 Scaled coordinates: {scaled_points}")
                return shape_name, scaled_points
            else:
                print("❌ No valid points found in drawing")
                return None, None
                
        except Exception as e:
            print(f"❌ Error in capture and process: {e}")
            return None, None
    
    def execute_formation(self, shape_type, points):
        """Execute the drone formation based on detected shape"""
        if not points:
            print("❌ No points to execute formation")
            return False
            
        print(f"🎯 Executing {shape_type} formation with {len(points)} points")
        
        try:
            # Position camera for optimal viewing
            self.camera_controller.position_for_formation(points, altitude=-15)
            
            # Move drones to formation
            success = self.drone_manager.move_to_formation(points, altitude=-15)
            
            if success:
                print(f"✅ {shape_type.upper()} formation completed!")
                return True
            else:
                print(f"❌ Formation failed")
                return False
                
        except Exception as e:
            print(f"❌ Error executing formation: {e}")
            return False
    
    def run_single_mode(self):
        """Run single capture and formation mode"""
        print("\n🎯 === SINGLE MODE ===")
        print("Instructions:")
        print("1. Draw a shape in MS Paint (triangle, square, circle, etc.)")
        print("2. Use camera controls (WASD, Q/E, Arrow keys) to position view")
        print("3. Press ENTER when ready to capture")
        print("4. Watch drones form your shape!")
        
        input("\n📸 Press ENTER when your drawing is ready...")
        
        # Capture and process
        shape_type, points = self.capture_and_process_drawing()
        
        if shape_type and points:
            # Execute formation
            success = self.execute_formation(shape_type, points)
            
            if success:
                # Hold formation
                print("⏳ Holding formation for 15 seconds...")
                print("🎥 Use camera controls to view from different angles!")
                
                # Wait while allowing camera control
                for i in range(15):
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"⏳ {15-i} seconds remaining...")
                
                print("✅ Single mode completed!")
            else:
                print("❌ Formation execution failed")
        else:
            print("❌ Could not detect valid shape")
    
    def run_continuous_mode(self):
        """Run continuous monitoring mode"""
        print("\n🔄 === CONTINUOUS MODE ===")
        print("Instructions:")
        print("1. Draw shapes in MS Paint")
        print("2. System will detect changes automatically")
        print("3. Use camera controls to view formations")
        print("4. Press 'Ctrl+C' to quit continuous mode")
        
        self.is_running = True
        print("🚀 Starting continuous monitoring...")
        print("📝 Draw shapes in Paint - system will detect automatically!")
        
        while self.is_running:
            try:
                # Capture and process drawing
                shape_type, points = self.capture_and_process_drawing()
                
                if shape_type and points:
                    # Check if this is a new/different shape
                    if (self.last_shape != shape_type or 
                        self.last_points != points):
                        
                        print(f"🆕 New shape detected: {shape_type}")
                        
                        # Execute new formation
                        success = self.execute_formation(shape_type, points)
                        
                        if success:
                            self.last_shape = shape_type
                            self.last_points = points
                            print(f"✅ Updated to {shape_type} formation")
                        
                        # Hold formation briefly
                        print("⏳ Holding formation for 8 seconds...")
                        time.sleep(8)
                    else:
                        print("⏳ Same shape detected, maintaining formation...")
                else:
                    print("⏳ No valid shape detected, waiting...")
                
                # Wait before next capture
                time.sleep(3)
                
            except KeyboardInterrupt:
                print("🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error in continuous mode: {e}")
                time.sleep(2)
        
        self.is_running = False
        print("✅ Continuous mode stopped")
    
    def shutdown_system(self):
        """Safely shutdown the system"""
        print("🛬 Shutting down system...")
        
        try:
            # Stop camera control
            self.camera_controller.stop()
            
            # Land all drones
            self.drone_manager.land_all()
            
            # Disconnect
            self.drone_manager.disconnect()
            
            print("✅ System shutdown complete")
            
        except Exception as e:
            print(f"❌ Shutdown error: {e}")

def main():
    # Create controller
    controller = DroneFormationController()
    
    try:
        # Start system
        if not controller.start_system():
            print("❌ System startup failed")
            return
        
        # Choose mode
        print("\n🎮 Choose operating mode:")
        print("1. Single Mode - Capture once and form shape")
        print("2. Continuous Mode - Monitor and update formations")
        
        while True:
            mode = input("\nEnter choice (1 or 2): ").strip()
            if mode in ['1', '2']:
                break
            print("❌ Invalid choice! Please enter 1 or 2")
        
        # Run selected mode
        if mode == "1":
            controller.run_single_mode()
        elif mode == "2":
            controller.run_continuous_mode()
        
    except KeyboardInterrupt:
        print("\n🛑 Program interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Always shutdown properly
        controller.shutdown_system()

if __name__ == "__main__":
    main()