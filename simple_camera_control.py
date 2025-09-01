import airsim
import numpy as np
import cv2
import time
import threading
import keyboard
from pynput import keyboard as pynput_keyboard

class AirSimCameraController:
    def __init__(self):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        
        # Camera settings
        self.camera_name = "0"  # Default camera
        self.move_speed = 5.0
        self.rotation_speed = 30.0
        self.zoom_speed = 2.0
        
        # Current camera state
        self.camera_pose = airsim.Pose()
        self.is_following = False
        self.follow_target = None
        self.running = True
        
        # View modes
        self.view_modes = {
            'free': 'Free Camera',
            'follow': 'Follow Drone',
            'overhead': 'Overhead View',
            'formation': 'Formation View',
            'cinematic': 'Cinematic'
        }
        self.current_mode = 'free'
        
        print("🎬 AirSim Camera Controller Initialized")
        print("📋 Available view modes:", list(self.view_modes.keys()))

    def get_drone_positions(self):
        """Get positions of all connected drones"""
        drone_positions = {}
        try:
            # Try to get positions for multiple drones
            for i in range(10):  # Check up to 10 drones
                vehicle_name = f"Drone{i}" if i > 0 else "Drone0"
                try:
                    state = self.client.getMultirotorState(vehicle_name=vehicle_name)
                    pos = state.kinematics_estimated.position
                    drone_positions[vehicle_name] = pos
                except:
                    if i == 0:  # Try default name for first drone
                        try:
                            state = self.client.getMultirotorState()
                            pos = state.kinematics_estimated.position
                            drone_positions["Drone0"] = pos
                        except:
                            pass
                    break
        except Exception as e:
            print(f"⚠️ Error getting drone positions: {e}")
        
        return drone_positions

    def calculate_formation_center(self, drone_positions):
        """Calculate the center point of drone formation"""
        if not drone_positions:
            return airsim.Vector3r(0, 0, 0)
        
        positions = list(drone_positions.values())
        center_x = sum(pos.x_val for pos in positions) / len(positions)
        center_y = sum(pos.y_val for pos in positions) / len(positions)
        center_z = sum(pos.z_val for pos in positions) / len(positions)
        
        return airsim.Vector3r(center_x, center_y, center_z)

    def set_camera_pose(self, position, orientation=None):
        """Set camera to specific position and orientation"""
        if orientation is None:
            orientation = airsim.to_quaternion(0, 0, 0)
        
        pose = airsim.Pose(position, orientation)
        self.client.simSetCameraPose(self.camera_name, pose)
        self.camera_pose = pose

    def move_camera_relative(self, dx=0, dy=0, dz=0):
        """Move camera relative to current position"""
        current_pos = self.camera_pose.position
        new_position = airsim.Vector3r(
            current_pos.x_val + dx,
            current_pos.y_val + dy,
            current_pos.z_val + dz
        )
        self.set_camera_pose(new_position, self.camera_pose.orientation)

    def rotate_camera(self, pitch=0, yaw=0, roll=0):
        """Rotate camera by given angles (in degrees)"""
        # Convert to radians
        pitch_rad = np.radians(pitch)
        yaw_rad = np.radians(yaw)
        roll_rad = np.radians(roll)
        
        # Get current orientation
        current_orientation = self.camera_pose.orientation
        
        # Apply rotation
        new_orientation = airsim.to_quaternion(pitch_rad, roll_rad, yaw_rad)
        
        # Combine with current orientation
        self.set_camera_pose(self.camera_pose.position, new_orientation)

    def set_overhead_view(self):
        """Set camera to overhead view of formation"""
        drone_positions = self.get_drone_positions()
        if not drone_positions:
            print("⚠️ No drones found for overhead view")
            return
        
        center = self.calculate_formation_center(drone_positions)
        
        # Position camera high above the formation
        camera_position = airsim.Vector3r(
            center.x_val,
            center.y_val,
            center.z_val - 50  # 50 meters above
        )
        
        # Point camera downward
        camera_orientation = airsim.to_quaternion(np.radians(-90), 0, 0)
        
        self.set_camera_pose(camera_position, camera_orientation)
        print("📸 Overhead view activated")

    def set_formation_view(self):
        """Set camera to view entire formation from an angle"""
        drone_positions = self.get_drone_positions()
        if not drone_positions:
            print("⚠️ No drones found for formation view")
            return
        
        center = self.calculate_formation_center(drone_positions)
        
        # Calculate formation size
        positions = list(drone_positions.values())
        max_distance = 0
        for pos in positions:
            distance = np.sqrt(
                (pos.x_val - center.x_val)**2 + 
                (pos.y_val - center.y_val)**2
            )
            max_distance = max(max_distance, distance)
        
        # Position camera at an angle to view the formation
        distance_factor = max(max_distance * 2, 30)  # Minimum 30m distance
        
        camera_position = airsim.Vector3r(
            center.x_val - distance_factor,
            center.y_val - distance_factor,
            center.z_val - 20  # 20 meters above
        )
        
        # Point camera toward formation center
        camera_orientation = airsim.to_quaternion(
            np.radians(-15),  # Slight downward angle
            0,
            np.radians(45)    # 45-degree angle
        )
        
        self.set_camera_pose(camera_position, camera_orientation)
        print("🎯 Formation view activated")

    def follow_drone(self, drone_name="Drone0", distance=20, height=10):
        """Follow a specific drone"""
        try:
            state = self.client.getMultirotorState(vehicle_name=drone_name)
            drone_pos = state.kinematics_estimated.position
            
            # Position camera behind and above the drone
            camera_position = airsim.Vector3r(
                drone_pos.x_val - distance,
                drone_pos.y_val,
                drone_pos.z_val - height
            )
            
            # Point camera toward the drone
            dx = drone_pos.x_val - camera_position.x_val
            dy = drone_pos.y_val - camera_position.y_val
            yaw = np.arctan2(dy, dx)
            
            camera_orientation = airsim.to_quaternion(0, 0, yaw)
            
            self.set_camera_pose(camera_position, camera_orientation)
            
        except Exception as e:
            print(f"⚠️ Error following drone {drone_name}: {e}")

    def cinematic_orbit(self, center_pos, radius=30, height=-20, speed=0.5):
        """Create cinematic orbiting camera movement"""
        angle = 0
        while self.current_mode == 'cinematic' and self.running:
            # Calculate position on orbit
            x = center_pos.x_val + radius * np.cos(angle)
            y = center_pos.y_val + radius * np.sin(angle)
            z = center_pos.z_val + height
            
            camera_position = airsim.Vector3r(x, y, z)
            
            # Always look at center
            dx = center_pos.x_val - x
            dy = center_pos.y_val - y
            yaw = np.arctan2(dy, dx)
            pitch = np.arctan2(height, radius)
            
            camera_orientation = airsim.to_quaternion(pitch, 0, yaw)
            
            self.set_camera_pose(camera_position, camera_orientation)
            
            angle += speed * 0.1
            if angle > 2 * np.pi:
                angle = 0
            
            time.sleep(0.1)

    def start_cinematic_mode(self):
        """Start cinematic orbiting around formation"""
        drone_positions = self.get_drone_positions()
        if not drone_positions:
            print("⚠️ No drones found for cinematic mode")
            return
        
        center = self.calculate_formation_center(drone_positions)
        self.current_mode = 'cinematic'
        
        # Start orbiting in separate thread
        cinematic_thread = threading.Thread(
            target=self.cinematic_orbit,
            args=(center,)
        )
        cinematic_thread.daemon = True
        cinematic_thread.start()
        
        print("🎬 Cinematic mode activated (orbiting formation)")

    def handle_keyboard_input(self):
        """Handle keyboard input for camera control"""
        print("\n🎮 CAMERA CONTROLS:")
        print("=" * 40)
        print("MOVEMENT:")
        print("  W/S - Forward/Backward")
        print("  A/D - Left/Right") 
        print("  Q/E - Up/Down")
        print("ROTATION:")
        print("  Arrow Keys - Look around")
        print("  Z/X - Roll left/right")
        print("VIEW MODES:")
        print("  1 - Free camera")
        print("  2 - Follow drone")
        print("  3 - Overhead view")
        print("  4 - Formation view")
        print("  5 - Cinematic orbit")
        print("OTHER:")
        print("  R - Reset to default position")
        print("  ESC - Exit")
        print("=" * 40)
        
        while self.running:
            try:
                if keyboard.is_pressed('w'):
                    self.move_camera_relative(dx=self.move_speed)
                elif keyboard.is_pressed('s'):
                    self.move_camera_relative(dx=-self.move_speed)
                elif keyboard.is_pressed('a'):
                    self.move_camera_relative(dy=-self.move_speed)
                elif keyboard.is_pressed('d'):
                    self.move_camera_relative(dy=self.move_speed)
                elif keyboard.is_pressed('q'):
                    self.move_camera_relative(dz=-self.move_speed)
                elif keyboard.is_pressed('e'):
                    self.move_camera_relative(dz=self.move_speed)
                
                # Rotation
                elif keyboard.is_pressed('up'):
                    self.rotate_camera(pitch=-self.rotation_speed)
                elif keyboard.is_pressed('down'):
                    self.rotate_camera(pitch=self.rotation_speed)
                elif keyboard.is_pressed('left'):
                    self.rotate_camera(yaw=-self.rotation_speed)
                elif keyboard.is_pressed('right'):
                    self.rotate_camera(yaw=self.rotation_speed)
                elif keyboard.is_pressed('z'):
                    self.rotate_camera(roll=-self.rotation_speed)
                elif keyboard.is_pressed('x'):
                    self.rotate_camera(roll=self.rotation_speed)
                
                # View modes
                elif keyboard.is_pressed('1'):
                    self.current_mode = 'free'
                    print("📹 Free camera mode")
                elif keyboard.is_pressed('2'):
                    self.current_mode = 'follow'
                    self.follow_drone()
                    print("🎯 Following drone")
                elif keyboard.is_pressed('3'):
                    self.current_mode = 'overhead'
                    self.set_overhead_view()
                elif keyboard.is_pressed('4'):
                    self.current_mode = 'formation'
                    self.set_formation_view()
                elif keyboard.is_pressed('5'):
                    self.start_cinematic_mode()
                
                # Reset
                elif keyboard.is_pressed('r'):
                    self.reset_camera()
                    print("🔄 Camera reset")
                
                # Exit
                elif keyboard.is_pressed('esc'):
                    self.running = False
                    break
                
                time.sleep(0.1)  # Prevent excessive CPU usage
                
            except Exception as e:
                print(f"⚠️ Keyboard input error: {e}")
                time.sleep(0.1)

    def reset_camera(self):
        """Reset camera to default position"""
        default_position = airsim.Vector3r(0, 0, -20)
        default_orientation = airsim.to_quaternion(0, 0, 0)
        self.set_camera_pose(default_position, default_orientation)
        self.current_mode = 'free'

    def start_camera_control(self):
        """Start the camera control system"""
        print("🎬 Starting AirSim Camera Controller")
        print("🔌 Connecting to AirSim...")
        
        try:
            # Reset camera to default position
            self.reset_camera()
            
            # Check for drones
            drone_positions = self.get_drone_positions()
            print(f"🚁 Found {len(drone_positions)} drones")
            
            if drone_positions:
                for name, pos in drone_positions.items():
                    print(f"   {name}: ({pos.x_val:.1f}, {pos.y_val:.1f}, {pos.z_val:.1f})")
            
            # Start keyboard input handling
            self.handle_keyboard_input()
            
        except Exception as e:
            print(f"❌ Error starting camera controller: {e}")
        finally:
            print("👋 Camera controller stopped")

def main():
    """Main function to run the camera controller"""
    try:
        controller = AirSimCameraController()
        controller.start_camera_control()
    except KeyboardInterrupt:
        print("\n👋 Camera controller interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()