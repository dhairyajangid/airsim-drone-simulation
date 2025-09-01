import numpy as np

class CoordinateScaler:
    def __init__(self):
        self.default_origin = (0, 0)  # Default formation center
        
    def scale_to_drone_coordinates(self, points, target_size=20, center_at_origin=True):
        """
        Scale drawing coordinates to drone world coordinates
        
        Args:
            points: List of (x, y) coordinates from drawing
            target_size: Desired size of formation in meters
            center_at_origin: Whether to center formation at (0, 0)
        
        Returns:
            List of scaled (x, y) coordinates for drone positions
        """
        if not points or len(points) == 0:
            return []
        
        # Convert to numpy array for easier manipulation
        points_array = np.array(points)
        
        # Find bounding box of the shape
        min_x, min_y = np.min(points_array, axis=0)
        max_x, max_y = np.max(points_array, axis=0)
        
        # Calculate current dimensions
        width = max_x - min_x
        height = max_y - min_y
        
        # Handle edge case where width or height is 0
        if width == 0:
            width = 1
        if height == 0:
            height = 1
        
        # Calculate scale factor to fit target size
        max_dimension = max(width, height)
        scale_factor = target_size / max_dimension
        
        # Scale the points
        scaled_points = points_array * scale_factor
        
        if center_at_origin:
            # Center the formation at origin
            scaled_min_x, scaled_min_y = np.min(scaled_points, axis=0)
            scaled_max_x, scaled_max_y = np.max(scaled_points, axis=0)
            
            # Calculate center offset
            center_x = (scaled_min_x + scaled_max_x) / 2
            center_y = (scaled_min_y + scaled_max_y) / 2
            
            # Translate to center at origin
            scaled_points[:, 0] -= center_x
            scaled_points[:, 1] -= center_y
        
        # Convert back to list of tuples
        result = [(float(x), float(y)) for x, y in scaled_points]
        
        print(f"📐 Coordinate scaling:")
        print(f"   Original bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
        print(f"   Original size: {width:.1f} x {height:.1f}")
        print(f"   Scale factor: {scale_factor:.3f}")
        print(f"   Target size: {target_size}m")
        print(f"   Scaled points: {len(result)} positions")
        
        return result
    
    def generate_formation_points(self, shape_type, num_points, size=20):
        """
        Generate standard formation points for common shapes
        
        Args:
            shape_type: Type of shape ('triangle', 'square', 'circle', etc.)
            num_points: Number of points to generate
            size: Size of formation in meters
        
        Returns:
            List of (x, y) coordinates
        """
        points = []
        
        if shape_type == 'triangle':
            # Equilateral triangle
            for i in range(min(3, num_points)):
                angle = i * 2 * np.pi / 3 - np.pi/2  # Start from top
                x = size/2 * np.cos(angle)
                y = size/2 * np.sin(angle)
                points.append((x, y))
                
        elif shape_type == 'square':
            # Square formation
            positions = [
                (-size/2, -size/2),  # Bottom left
                (size/2, -size/2),   # Bottom right
                (size/2, size/2),    # Top right
                (-size/2, size/2)    # Top left
            ]
            points = positions[:min(4, num_points)]
            
        elif shape_type == 'circle':
            # Circular formation
            for i in range(num_points):
                angle = i * 2 * np.pi / num_points
                x = size/2 * np.cos(angle)
                y = size/2 * np.sin(angle)
                points.append((x, y))
                
        elif shape_type == 'pentagon':
            # Pentagon formation
            for i in range(min(5, num_points)):
                angle = i * 2 * np.pi / 5 - np.pi/2  # Start from top
                x = size/2 * np.cos(angle)
                y = size/2 * np.sin(angle)
                points.append((x, y))
                
        elif shape_type == 'hexagon':
            # Hexagon formation
            for i in range(min(6, num_points)):
                angle = i * 2 * np.pi / 6
                x = size/2 * np.cos(angle)
                y = size/2 * np.sin(angle)
                points.append((x, y))
                
        elif shape_type == 'line':
            # Line formation
            spacing = size / max(1, num_points - 1)
            for i in range(num_points):
                x = -size/2 + i * spacing
                y = 0
                points.append((x, y))
                
        else:
            # Default to circular formation
            for i in range(num_points):
                angle = i * 2 * np.pi / num_points
                x = size/2 * np.cos(angle)
                y = size/2 * np.sin(angle)
                points.append((x, y))
        
        return points
    
    def optimize_drone_assignment(self, current_positions, target_positions):
        """
        Optimize assignment of drones to target positions to minimize total travel distance
        
        Args:
            current_positions: List of current drone (x, y) positions
            target_positions: List of target (x, y) positions
        
        Returns:
            List of target positions reordered to minimize total travel
        """
        if not current_positions or not target_positions:
            return target_positions
        
        # Simple greedy assignment (for more complex scenarios, use Hungarian algorithm)
        assigned_targets = []
        remaining_targets = target_positions.copy()
        
        for current_pos in current_positions:
            if not remaining_targets:
                break
                
            # Find closest target
            min_distance = float('inf')
            closest_target = None
            
            for target in remaining_targets:
                distance = np.sqrt((current_pos[0] - target[0])**2 + 
                                 (current_pos[1] - target[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_target = target
            
            if closest_target:
                assigned_targets.append(closest_target)
                remaining_targets.remove(closest_target)
        
        return assigned_targets

# Test the coordinate scaler
if __name__ == "__main__":
    print("🧪 Testing Coordinate Scaler...")
    
    scaler = CoordinateScaler()
    
    # Test with sample drawing points (representing a square)
    drawing_points = [
        (100, 100),  # Top-left
        (200, 100),  # Top-right
        (200, 200),  # Bottom-right
        (100, 200)   # Bottom-left
    ]
    
    print("📝 Original drawing points:", drawing_points)
    
    # Scale to drone coordinates
    scaled = scaler.scale_to_drone_coordinates(drawing_points, target_size=15)
    print("🚁 Scaled drone coordinates:", scaled)
    
    # Test generation of standard formations
    print("\n🎯 Testing standard formations:")
    shapes = ['triangle', 'square', 'circle', 'pentagon', 'hexagon']
    
    for shape in shapes:
        points = scaler.generate_formation_points(shape, 4, size=10)
        print(f"   {shape}: {points}")