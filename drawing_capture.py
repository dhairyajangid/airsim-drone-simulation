import cv2
import numpy as np
from PIL import ImageGrab
import pygetwindow as gw
import time
import os
import math

class PreciseCanvasCapture:
    def __init__(self):
        self.previous_screenshot = None
        self.background_captured = False
        self.min_contour_area = 300  # Reduced for better detection
        self.debug = True
        self.canvas_bounds = None  # Store exact canvas coordinates
        
        # DRONE COORDINATE SETTINGS
        self.drone_flight_area = {
            'center_lat': 0.0,
            'center_lon': 0.0,
            'width_meters': 20.0,
            'height_meters': 20.0,
            'altitude': 10.0
        }
        
    def find_paint_window_precise(self):
        """🔧 FIXED: Find MS Paint window with precise detection"""
        paint_titles = [
            "Untitled - Paint",
            "Paint", 
            "untitled - Paint",
            "Drawing - Paint",
            "Sketch - Paint",
            "Без названия - Paint"  # For different language versions
        ]
        
        windows = gw.getAllWindows()
        paint_windows = []
        
        # Find all potential Paint windows
        for window in windows:
            if any(title.lower() in window.title.lower() for title in paint_titles):
                if "paint" in window.title.lower() and window.width > 300 and window.height > 300:
                    paint_windows.append(window)
                    if self.debug:
                        print(f"🎨 Found Paint window: '{window.title}' - {window.width}x{window.height}")
        
        if not paint_windows:
            print("❌ No Paint windows found!")
            print("Available windows:")
            for w in windows[:10]:  # Show first 10 windows
                print(f"   - '{w.title}' ({w.width}x{w.height})")
            return None
        
        # Get the largest Paint window (most likely the main one)
        paint_window = max(paint_windows, key=lambda w: w.width * w.height)
        
        if self.debug:
            print(f"✅ Selected Paint window: '{paint_window.title}'")
            print(f"   Position: ({paint_window.left}, {paint_window.top})")
            print(f"   Size: {paint_window.width} x {paint_window.height}")
        
        return paint_window

    def calculate_precise_canvas_bounds(self, paint_window):
        """🔧 FIXED: Calculate exact canvas area excluding ALL toolbars and UI"""
        # Get window coordinates
        win_left = paint_window.left
        win_top = paint_window.top
        win_width = paint_window.width
        win_height = paint_window.height
        
        # More precise canvas calculation based on Paint's UI layout
        # These values account for different versions of Paint
        
        # Horizontal margins (left and right borders)
        left_margin = 8   # Window border
        right_margin = 8  # Window border
        
        # Vertical margins (title bar, ribbon, status bar)
        top_margin = 31    # Title bar
        ribbon_height = 95 # Ribbon toolbar (varies by Paint version)
        status_bar = 25    # Bottom status bar
        
        # Calculate exact canvas boundaries
        canvas_left = win_left + left_margin
        canvas_top = win_top + top_margin + ribbon_height
        canvas_right = win_left + win_width - right_margin
        canvas_bottom = win_top + win_height - status_bar
        
        # Ensure minimum canvas size
        canvas_width = canvas_right - canvas_left
        canvas_height = canvas_bottom - canvas_top
        
        if canvas_width < 200 or canvas_height < 200:
            print("⚠️ Canvas area seems too small. Adjusting margins...")
            # Fallback with smaller margins
            top_margin = 60
            ribbon_height = 60
            canvas_top = win_top + top_margin + ribbon_height
            canvas_bottom = win_top + win_height - 30
        
        self.canvas_bounds = (canvas_left, canvas_top, canvas_right, canvas_bottom)
        
        if self.debug:
            print(f"🎯 Calculated canvas bounds:")
            print(f"   Left: {canvas_left}, Top: {canvas_top}")
            print(f"   Right: {canvas_right}, Bottom: {canvas_bottom}")
            print(f"   Canvas size: {canvas_right-canvas_left} x {canvas_bottom-canvas_top}")
        
        return self.canvas_bounds

    def capture_canvas_only(self):
        """🔧 FIXED: Capture ONLY the canvas area, no toolbars or other windows"""
        paint_window = self.find_paint_window_precise()
        if not paint_window:
            return None
        
        # Calculate precise canvas bounds
        canvas_bounds = self.calculate_precise_canvas_bounds(paint_window)
        canvas_left, canvas_top, canvas_right, canvas_bottom = canvas_bounds
        
        try:
            # Bring Paint window to front to avoid capturing other windows
            paint_window.activate()
            time.sleep(0.2)  # Small delay to ensure window is active
            
            # Capture ONLY the canvas area
            print(f"📸 Capturing canvas area: ({canvas_left}, {canvas_top}) to ({canvas_right}, {canvas_bottom})")
            screenshot = ImageGrab.grab(bbox=(canvas_left, canvas_top, canvas_right, canvas_bottom))
            canvas_array = np.array(screenshot)
            
            if self.debug:
                print(f"✅ Canvas captured: {canvas_array.shape[1]} x {canvas_array.shape[0]} pixels")
                
                # Check if we captured mostly white (good canvas capture)
                gray = cv2.cvtColor(canvas_array, cv2.COLOR_RGB2GRAY)
                white_percentage = np.sum(gray > 240) / gray.size * 100
                print(f"📊 White area: {white_percentage:.1f}% (should be >80% for clean canvas)")
            
            return canvas_array
            
        except Exception as e:
            print(f"❌ Error capturing canvas: {e}")
            return None

    def show_capture_preview(self, image, title="Captured Image", duration=3000):
        """Show what was captured for debugging"""
        if image is None:
            return
        
        # Convert RGB to BGR for OpenCV display
        if len(image.shape) == 3 and image.shape[2] == 3:
            display_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            display_image = image.copy()
        
        # Resize if too large
        height, width = display_image.shape[:2]
        if width > 800 or height > 600:
            scale = min(800/width, 600/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_image = cv2.resize(display_image, (new_width, new_height))
        
        # Show the image
        cv2.imshow(title, display_image)
        cv2.waitKey(duration)
        cv2.destroyWindow(title)

    def capture_clean_background(self):
        """🔧 FIXED: Capture clean canvas background with better validation"""
        print("\n📋 CLEAN CANVAS SETUP")
        print("=" * 50)
        print("🧹 CRITICAL: Ensure canvas is completely clean!")
        print("   1. Close any overlapping windows (including this terminal!)")
        print("   2. Maximize Paint window or ensure it's fully visible")
        print("   3. Clear canvas: Ctrl+A then Delete")
        print("   4. Ensure canvas is pure white with no drawings")
        print("   5. No other windows should overlap Paint")
        print("\n⚠️  IMPORTANT: Minimize this terminal or move it away from Paint!")
        print("Press Enter when ready...")
        input()
        
        # Give user time to minimize terminal
        print("⏳ Capturing in 3 seconds... (minimize this window now!)")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        background = self.capture_canvas_only()
        if background is not None:
            print("✅ Background captured!")
            
            # Validate background quality
            gray = cv2.cvtColor(background, cv2.COLOR_RGB2GRAY)
            white_percentage = np.sum(gray > 240) / gray.size * 100
            
            if white_percentage < 70:
                print(f"⚠️ Warning: Only {white_percentage:.1f}% white pixels detected")
                print("   This might indicate overlapping windows or UI elements")
                print("   Consider recapturing with cleaner setup")
            
            # Show background preview
            print("👀 Showing captured background...")
            self.show_capture_preview(background, "Clean Background", 2000)
            
            self.previous_screenshot = background.copy()
            self.background_captured = True
            return True
        else:
            print("❌ Failed to capture background")
            return False

    def detect_drawing_changes(self, current_image):
        """🔧 IMPROVED: Better change detection with noise filtering"""
        if not self.background_captured or self.previous_screenshot is None:
            print("⚠️ No background reference. Using direct thresholding...")
            gray = cv2.cvtColor(current_image, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)
            return binary
        
        # Ensure images are same size
        if current_image.shape != self.previous_screenshot.shape:
            print("⚠️ Image size mismatch. Resizing background...")
            self.previous_screenshot = cv2.resize(self.previous_screenshot, 
                                                (current_image.shape[1], current_image.shape[0]))
        
        # Convert to grayscale
        current_gray = cv2.cvtColor(current_image, cv2.COLOR_RGB2GRAY)
        background_gray = cv2.cvtColor(self.previous_screenshot, cv2.COLOR_RGB2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(background_gray, current_gray)
        
        # Adaptive thresholding for better detection
        _, binary = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        
        # Noise reduction - remove small artifacts
        kernel = np.ones((3,3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # Remove noise
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel) # Fill gaps
        
        # Remove very small contours (likely noise)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_binary = np.zeros_like(binary)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:  # Keep only contours larger than 50 pixels
                cv2.fillPoly(filtered_binary, [contour], 255)
        
        if self.debug:
            print("👀 Showing detected changes (filtered)...")
            self.show_capture_preview(filtered_binary, "Detected Drawing", 2000)
        
        return filtered_binary

    def advanced_shape_detection(self, binary_image):
        """🔧 IMPROVED: Better shape detection with contour filtering"""
        # Find all contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, [], "no_contours_found"
        
        # Filter and sort contours by area
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                # Additional filtering: check aspect ratio to avoid UI elements
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = max(w, h) / min(w, h)
                
                # Reject extremely thin contours (likely UI elements or lines)
                if aspect_ratio < 10:  # Reasonable shape should not be extremely thin
                    valid_contours.append((area, contour))
        
        if not valid_contours:
            if contours:
                max_area = max(cv2.contourArea(c) for c in contours)
                print(f"⚠️ Largest contour: {max_area}, minimum: {self.min_contour_area}")
            return None, [], f"too_small_max_{int(max_area) if contours else 0}"
        
        # Get the largest valid contour
        valid_contours.sort(reverse=True)  # Sort by area, largest first
        largest_area, largest_contour = valid_contours[0]
        
        if self.debug:
            print(f"📏 Selected contour area: {largest_area}")
            print(f"🔍 Found {len(valid_contours)} valid contours")
        
        # Polygon approximation with multiple epsilon values
        perimeter = cv2.arcLength(largest_contour, True)
        best_approx = None
        best_vertices = 0
        
        # Try different approximation strengths
        epsilon_values = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04]
        approximations = []
        
        for epsilon_factor in epsilon_values:
            epsilon = epsilon_factor * perimeter
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            vertices = len(approx)
            approximations.append((vertices, approx, epsilon_factor))
        
        # Find most stable vertex count
        from collections import Counter
        vertex_counts = [a[0] for a in approximations]
        vertex_counter = Counter(vertex_counts)
        most_common_vertices = vertex_counter.most_common(1)[0][0]
        
        # Select best approximation
        for vertices, approx, epsilon_factor in approximations:
            if vertices == most_common_vertices:
                best_approx = approx
                best_vertices = vertices
                break
        
        if best_approx is None:
            return None, [], "approximation_failed"
        
        if self.debug:
            print(f"🎯 Detected vertices: {best_vertices}")
            
            # Show contour and approximation
            debug_image = np.zeros_like(binary_image)
            cv2.drawContours(debug_image, [largest_contour], -1, 128, 2)  # Original contour
            cv2.drawContours(debug_image, [best_approx], -1, 255, 3)     # Approximation
            
            # Mark vertices
            for point in best_approx:
                cv2.circle(debug_image, tuple(point[0]), 8, 200, -1)
            
            self.show_capture_preview(debug_image, f"Shape: {best_vertices} vertices", 3000)
        
        # Convert to coordinate list
        points = [(int(point[0][0]), int(point[0][1])) for point in best_approx]
        
        # Classify shape
        shape_name = self.classify_shape(best_vertices, largest_contour, largest_area)
        
        return largest_contour, points, shape_name

    def classify_shape(self, vertices, contour, area):
        """Classify shape based on vertices and geometry"""
        if vertices < 3:
            return "line"
        elif vertices == 3:
            return "triangle"
        elif vertices == 4:
            # Distinguish square from rectangle
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = max(w, h) / min(w, h)
            if aspect_ratio < 1.2:
                return "square"
            else:
                return "rectangle"
        elif vertices == 5:
            return "pentagon"
        elif vertices == 6:
            return "hexagon"
        elif vertices >= 7:
            # Check if it's more circular
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.75:
                return "circle"
            elif vertices == 7:
                return "heptagon"
            elif vertices == 8:
                return "octagon"
            else:
                return f"polygon_{vertices}_vertices"
        else:
            return "unknown"

    def convert_to_drone_coordinates(self, screen_points, canvas_shape):
        """Convert screen coordinates to drone GPS waypoints"""
        if not screen_points:
            return []
        
        print("\n🚁 CONVERTING TO DRONE COORDINATES")
        print("=" * 45)
        
        canvas_height, canvas_width = canvas_shape[:2]
        
        # Find bounding box of the shape
        min_x = min(point[0] for point in screen_points)
        max_x = max(point[0] for point in screen_points)
        min_y = min(point[1] for point in screen_points)
        max_y = max(point[1] for point in screen_points)
        
        shape_width = max_x - min_x
        shape_height = max_y - min_y
        shape_center_x = (min_x + max_x) / 2
        shape_center_y = (min_y + max_y) / 2
        
        print(f"📐 Canvas: {canvas_width}x{canvas_height}px")
        print(f"📏 Shape: {shape_width}x{shape_height}px at center ({shape_center_x:.0f}, {shape_center_y:.0f})")
        
        # Convert each point to drone coordinates
        drone_waypoints = []
        
        for i, (x, y) in enumerate(screen_points):
            # Normalize relative to shape center (-1 to 1)
            if shape_width > 0:
                norm_x = (x - shape_center_x) / (shape_width / 2)
            else:
                norm_x = 0
            
            if shape_height > 0:
                norm_y = (y - shape_center_y) / (shape_height / 2)
            else:
                norm_y = 0
            
            # Scale to flight area
            flight_x = norm_x * (self.drone_flight_area['width_meters'] / 2)
            flight_y = -norm_y * (self.drone_flight_area['height_meters'] / 2)  # Flip Y for correct orientation
            
            # Convert to GPS (simplified approximation)
            lat_offset = flight_y / 111320
            lon_offset = flight_x / (111320 * math.cos(math.radians(self.drone_flight_area['center_lat'])))
            
            drone_lat = self.drone_flight_area['center_lat'] + lat_offset
            drone_lon = self.drone_flight_area['center_lon'] + lon_offset
            drone_alt = self.drone_flight_area['altitude']
            
            waypoint = {
                'id': i + 1,
                'screen_coords': (x, y),
                'flight_coords': (flight_x, flight_y),
                'gps_coords': (drone_lat, drone_lon, drone_alt)
            }
            
            drone_waypoints.append(waypoint)
            print(f"📍 Point {i+1}: Screen({x}, {y}) → Flight({flight_x:.1f}, {flight_y:.1f})m → GPS({drone_lat:.8f}, {drone_lon:.8f})")
        
        return drone_waypoints

    def set_flight_area(self, center_lat, center_lon, width_m, height_m, altitude_m):
        """Configure drone flight area"""
        self.drone_flight_area = {
            'center_lat': center_lat,
            'center_lon': center_lon,
            'width_meters': width_m,
            'height_meters': height_m,
            'altitude': altitude_m
        }
        print(f"✅ Flight area: {width_m}x{height_m}m at ({center_lat:.6f}, {center_lon:.6f}), {altitude_m}m altitude")

    def main_capture_and_analyze(self):
        """🔧 FIXED: Main analysis with precise canvas capture"""
        print("\n🎨 PRECISE CANVAS-ONLY CAPTURE")
        print("🔧 Fixes: Canvas-only capture + Better shape detection")
        print("=" * 60)
        
        # Always capture fresh background
        if not self.capture_clean_background():
            return None, [], [], "background_failed"
        
        print("\n🖊️ DRAW YOUR SHAPE")
        print("=" * 25)
        print("1. Draw ONE clear shape in Paint")
        print("2. Use thick, dark lines (black is best)")
        print("3. Make it reasonably large")
        print("4. Ensure no windows overlap Paint")
        print("5. Press Enter when done...")
        input()
        
        # Capture current canvas
        print("📸 Capturing current canvas...")
        current_canvas = self.capture_canvas_only()
        
        if current_canvas is None:
            return None, [], [], "capture_failed"
        
        print("👀 Showing current canvas...")
        self.show_capture_preview(current_canvas, "Current Canvas", 2000)
        
        # Detect changes
        print("🔍 Detecting your drawing...")
        changes = self.detect_drawing_changes(current_canvas)
        
        # Analyze shape
        print("🎯 Analyzing shape...")
        contour, points, shape_name = self.advanced_shape_detection(changes)
        
        # Convert to drone coordinates
        drone_waypoints = []
        if contour is not None and points:
            drone_waypoints = self.convert_to_drone_coordinates(points, current_canvas.shape)
        
        # Report results
        if contour is not None and points:
            print(f"\n🎉 SUCCESS!")
            print(f"✨ Shape detected: {shape_name}")
            print(f"📍 Vertices: {len(points)}")
            print(f"🚁 Drone waypoints: {len(drone_waypoints)}")
            return contour, points, drone_waypoints, shape_name
        else:
            print(f"\n❌ Detection failed: {shape_name}")
            return None, [], [], shape_name

def main():
    """Test the precise canvas capture system"""
    print("🚀 PRECISE CANVAS-ONLY CAPTURE SYSTEM")
    print("🔧 Solves: Toolbar capture + Window overlap + Wrong coordinates")
    print("=" * 70)
    
    capture = PreciseCanvasCapture()
    
    # Set flight area
    capture.set_flight_area(
        center_lat=37.7749,    # San Francisco example
        center_lon=-122.4194,
        width_m=15.0,
        height_m=15.0,
        altitude_m=8.0
    )
    
    try:
        while True:
            contour, points, waypoints, shape = capture.main_capture_and_analyze()
            
            if shape in ["no_contours_found", "capture_failed", "background_failed"]:
                print(f"\n⚠️ Issue: {shape}")
                print("💡 Tips:")
                print("   - Ensure Paint window is visible and active")
                print("   - Draw with thick, dark lines")
                print("   - Close overlapping windows")
                print("   - Make sure canvas is clean before background capture")
            elif "too_small" in str(shape):
                print(f"\n⚠️ Drawing too small. Try drawing larger!")
            elif contour is not None:
                print(f"\n🎊 Perfect! Detected: {shape}")
                if waypoints:
                    print("🚁 Drone mission ready!")
            
            print("\n" + "="*70)
            choice = input("🔄 Try another shape? (y/n): ").lower()
            if choice != 'y':
                break
                
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cv2.destroyAllWindows()
    
    print("👋 Testing complete!")

if __name__ == "__main__":
    main()