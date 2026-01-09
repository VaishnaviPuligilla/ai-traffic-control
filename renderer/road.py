import pygame
import math
from config import COLORS, LANE_CONFIG, WINDOW_WIDTH, WINDOW_HEIGHT

class Road:
    """Represents a road segment"""
    
    def __init__(self, start_x, start_y, end_x, end_y, num_lanes=2, direction='horizontal'):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.num_lanes = num_lanes
        self.direction = direction
        self.lane_width = LANE_CONFIG['width']
        
        # Calculate road dimensions
        if direction == 'horizontal':
            self.width = abs(end_x - start_x)
            self.height = self.lane_width * num_lanes
        else:
            self.width = self.lane_width * num_lanes
            self.height = abs(end_y - start_y)
            
    def draw(self, screen, view_mode='top_down'):
        """Draw the road segment"""
        if view_mode == 'top_down':
            self._draw_top_down(screen)
        elif view_mode == 'isometric':
            self._draw_isometric(screen)
        else:
            self._draw_top_down(screen)
            
    def _draw_top_down(self, screen):
        """Draw road from top-down view"""
        # Main road surface
        if self.direction == 'horizontal':
            road_rect = pygame.Rect(
                min(self.start_x, self.end_x),
                self.start_y - self.height // 2,
                self.width,
                self.height
            )
        else:
            road_rect = pygame.Rect(
                self.start_x - self.width // 2,
                min(self.start_y, self.end_y),
                self.width,
                self.height
            )
            
        # Draw road surface
        pygame.draw.rect(screen, COLORS['road'], road_rect)
        
        # Draw road border
        pygame.draw.rect(screen, COLORS['white'], road_rect, 3)
        
        # Draw lane markings
        self._draw_lane_markings(screen, road_rect)
        
    def _draw_lane_markings(self, screen, road_rect):
        """Draw dashed lane markings"""
        dash_length = 30
        gap_length = 20
        
        if self.direction == 'horizontal':
            # Draw horizontal lane dividers
            for i in range(1, self.num_lanes):
                y = road_rect.top + i * self.lane_width
                x = road_rect.left
                while x < road_rect.right:
                    end_x = min(x + dash_length, road_rect.right)
                    pygame.draw.line(screen, COLORS['road_marking'],
                                   (x, y), (end_x, y), 2)
                    x += dash_length + gap_length
        else:
            # Draw vertical lane dividers
            for i in range(1, self.num_lanes):
                x = road_rect.left + i * self.lane_width
                y = road_rect.top
                while y < road_rect.bottom:
                    end_y = min(y + dash_length, road_rect.bottom)
                    pygame.draw.line(screen, COLORS['road_marking'],
                                   (x, y), (x, end_y), 2)
                    y += dash_length + gap_length
                    
    def _draw_isometric(self, screen):
        """Draw road in isometric view"""
        # Convert to isometric coordinates
        points = self._get_isometric_road_points()
        
        # Draw road surface
        pygame.draw.polygon(screen, COLORS['road'], points)
        pygame.draw.polygon(screen, COLORS['white'], points, 2)
        
    def _get_isometric_road_points(self):
        """Get isometric transformed road polygon points"""
        if self.direction == 'horizontal':
            points = [
                self._to_iso(self.start_x, self.start_y - self.height//2),
                self._to_iso(self.end_x, self.start_y - self.height//2),
                self._to_iso(self.end_x, self.start_y + self.height//2),
                self._to_iso(self.start_x, self.start_y + self.height//2)
            ]
        else:
            points = [
                self._to_iso(self.start_x - self.width//2, self.start_y),
                self._to_iso(self.start_x + self.width//2, self.start_y),
                self._to_iso(self.start_x + self.width//2, self.end_y),
                self._to_iso(self.start_x - self.width//2, self.end_y)
            ]
        return points
    
    def _to_iso(self, x, y):
        """Convert 2D coordinates to isometric"""
        iso_x = x - y
        iso_y = (x + y) / 2
        return (iso_x + WINDOW_WIDTH // 2, iso_y)


class Junction:
    """Represents a traffic junction/intersection"""
    
    def __init__(self, center_x, center_y, num_lanes=4, lanes_per_road=2):
        self.center_x = center_x
        self.center_y = center_y
        self.num_lanes = num_lanes
        self.lanes_per_road = lanes_per_road
        self.road_width = LANE_CONFIG['width'] * lanes_per_road
        
        # Junction dimensions
        self.junction_size = self.road_width * 2
        
        # Create roads leading to junction
        self.roads = self._create_roads()
        
        # Stop lines and crosswalks
        self.stop_line_distance = LANE_CONFIG['stop_line_distance']
        
        # Pedestrian crossings
        self.pedestrian_crossings = self._create_crossings()
        
        # Lane spawn/exit positions
        self.lane_positions = self._calculate_lane_positions()
        
    def _create_roads(self):
        """Create roads connecting to the junction"""
        roads = []
        half_junction = self.junction_size // 2
        
        # North road (traffic going down)
        roads.append(Road(
            self.center_x, 0,
            self.center_x, self.center_y - half_junction,
            self.lanes_per_road, 'vertical'
        ))
        
        # South road (traffic going up)
        roads.append(Road(
            self.center_x, self.center_y + half_junction,
            self.center_x, WINDOW_HEIGHT,
            self.lanes_per_road, 'vertical'
        ))
        
        # West road (traffic going right)
        roads.append(Road(
            0, self.center_y,
            self.center_x - half_junction, self.center_y,
            self.lanes_per_road, 'horizontal'
        ))
        
        # East road (traffic going left)
        roads.append(Road(
            self.center_x + half_junction, self.center_y,
            WINDOW_WIDTH, self.center_y,
            self.lanes_per_road, 'horizontal'
        ))
        
        return roads
    
    def _create_crossings(self):
        """Create pedestrian crossing zones"""
        crossings = []
        half_junction = self.junction_size // 2
        crossing_width = 30
        
        # North crossing
        crossings.append({
            'rect': pygame.Rect(
                self.center_x - self.road_width // 2,
                self.center_y - half_junction - crossing_width,
                self.road_width,
                crossing_width
            ),
            'direction': 'horizontal'
        })
        
        # South crossing
        crossings.append({
            'rect': pygame.Rect(
                self.center_x - self.road_width // 2,
                self.center_y + half_junction,
                self.road_width,
                crossing_width
            ),
            'direction': 'horizontal'
        })
        
        # West crossing
        crossings.append({
            'rect': pygame.Rect(
                self.center_x - half_junction - crossing_width,
                self.center_y - self.road_width // 2,
                crossing_width,
                self.road_width
            ),
            'direction': 'vertical'
        })
        
        # East crossing
        crossings.append({
            'rect': pygame.Rect(
                self.center_x + half_junction,
                self.center_y - self.road_width // 2,
                crossing_width,
                self.road_width
            ),
            'direction': 'vertical'
        })
        
        return crossings
    
    def _calculate_lane_positions(self):
        """Calculate spawn and exit positions for each lane"""
        positions = {}
        half_junction = self.junction_size // 2
        lane_offset = LANE_CONFIG['width'] // 2
        
        # Lane 0: North (vehicles coming from top, going down)
        positions[0] = {
            'spawn': (self.center_x + lane_offset, 0),
            'exit': (self.center_x - lane_offset, 0),
            'direction': 'down',
            'signal_pos': (self.center_x + self.road_width // 2 + 40,
                          self.center_y - half_junction - 30)
        }
        
        # Lane 1: South (vehicles coming from bottom, going up)
        positions[1] = {
            'spawn': (self.center_x - lane_offset, WINDOW_HEIGHT),
            'exit': (self.center_x + lane_offset, WINDOW_HEIGHT),
            'direction': 'up',
            'signal_pos': (self.center_x - self.road_width // 2 - 40,
                          self.center_y + half_junction + 30)
        }
        
        # Lane 2: West (vehicles coming from left, going right)
        positions[2] = {
            'spawn': (0, self.center_y + lane_offset),
            'exit': (0, self.center_y - lane_offset),
            'direction': 'right',
            'signal_pos': (self.center_x - half_junction - 30,
                          self.center_y + self.road_width // 2 + 40)
        }
        
        # Lane 3: East (vehicles coming from right, going left)
        positions[3] = {
            'spawn': (WINDOW_WIDTH, self.center_y - lane_offset),
            'exit': (WINDOW_WIDTH, self.center_y + lane_offset),
            'direction': 'left',
            'signal_pos': (self.center_x + half_junction + 30,
                          self.center_y - self.road_width // 2 - 40)
        }
        
        # Additional lanes for 6-lane configuration
        if self.num_lanes >= 6:
            # Lane 4: North-East diagonal
            positions[4] = {
                'spawn': (self.center_x + lane_offset * 3, 0),
                'exit': (WINDOW_WIDTH, self.center_y - lane_offset * 3),
                'direction': 'down',
                'signal_pos': (self.center_x + self.road_width + 40,
                              self.center_y - half_junction - 30)
            }
            
            # Lane 5: South-West diagonal
            positions[5] = {
                'spawn': (self.center_x - lane_offset * 3, WINDOW_HEIGHT),
                'exit': (0, self.center_y + lane_offset * 3),
                'direction': 'up',
                'signal_pos': (self.center_x - self.road_width - 40,
                              self.center_y + half_junction + 30)
            }
            
        return positions
    
    def get_junction_bounds(self):
        """Get the bounding box of the junction"""
        half = self.junction_size // 2
        return (
            self.center_x - half,
            self.center_y - half,
            self.junction_size,
            self.junction_size
        )
    
    def get_signal_positions(self):
        """Get positions for traffic signals"""
        signal_positions = {}
        for lane_id, pos in self.lane_positions.items():
            signal_positions[lane_id] = (
                pos['signal_pos'][0],
                pos['signal_pos'][1],
                pos['direction']
            )
        return signal_positions
    
    def draw(self, screen, view_mode='top_down'):
        """Draw the junction"""
        if view_mode == 'top_down':
            self._draw_top_down(screen)
        elif view_mode == 'isometric':
            self._draw_isometric(screen)
        else:
            self._draw_top_down(screen)
            
    def _draw_top_down(self, screen):
        """Draw junction from top-down view"""
        # Draw grass background
        screen.fill(COLORS['grass'])
        
        # Draw roads
        for road in self.roads:
            road.draw(screen, 'top_down')
        
        # Draw junction center
        junction_rect = pygame.Rect(
            self.center_x - self.junction_size // 2,
            self.center_y - self.junction_size // 2,
            self.junction_size,
            self.junction_size
        )
        pygame.draw.rect(screen, COLORS['road'], junction_rect)
        
        # Draw pedestrian crossings
        self._draw_crossings(screen)
        
        # Draw stop lines
        self._draw_stop_lines(screen)
        
        # Draw junction markings
        self._draw_junction_markings(screen)
        
    def _draw_crossings(self, screen):
        """Draw zebra crossing patterns"""
        stripe_width = 8
        
        for crossing in self.pedestrian_crossings:
            rect = crossing['rect']
            
            if crossing['direction'] == 'horizontal':
                # Horizontal stripes
                x = rect.left
                while x < rect.right:
                    stripe_rect = pygame.Rect(x, rect.top, stripe_width, rect.height)
                    pygame.draw.rect(screen, COLORS['white'], stripe_rect)
                    x += stripe_width * 2
            else:
                # Vertical stripes
                y = rect.top
                while y < rect.bottom:
                    stripe_rect = pygame.Rect(rect.left, y, rect.width, stripe_width)
                    pygame.draw.rect(screen, COLORS['white'], stripe_rect)
                    y += stripe_width * 2
                    
    def _draw_stop_lines(self, screen):
        """Draw stop lines at each approach"""
        half_junction = self.junction_size // 2
        line_thickness = 5
        
        # North approach
        pygame.draw.line(screen, COLORS['white'],
                        (self.center_x - self.road_width // 2, self.center_y - half_junction),
                        (self.center_x + self.road_width // 2, self.center_y - half_junction),
                        line_thickness)
        
        # South approach
        pygame.draw.line(screen, COLORS['white'],
                        (self.center_x - self.road_width // 2, self.center_y + half_junction),
                        (self.center_x + self.road_width // 2, self.center_y + half_junction),
                        line_thickness)
        
        # West approach
        pygame.draw.line(screen, COLORS['white'],
                        (self.center_x - half_junction, self.center_y - self.road_width // 2),
                        (self.center_x - half_junction, self.center_y + self.road_width // 2),
                        line_thickness)
        
        # East approach
        pygame.draw.line(screen, COLORS['white'],
                        (self.center_x + half_junction, self.center_y - self.road_width // 2),
                        (self.center_x + half_junction, self.center_y + self.road_width // 2),
                        line_thickness)
        
    def _draw_junction_markings(self, screen):
        """Draw center markings and turn guides"""
        # Center circle (optional decorative element)
        pygame.draw.circle(screen, COLORS['road_marking'],
                          (self.center_x, self.center_y), 15, 2)
        
    def _draw_isometric(self, screen):
        """Draw junction in isometric view"""
        screen.fill(COLORS['grass'])
        
        # Draw roads in isometric
        for road in self.roads:
            road.draw(screen, 'isometric')
            
        # Draw junction center
        half = self.junction_size // 2
        points = [
            self._to_iso(self.center_x - half, self.center_y - half),
            self._to_iso(self.center_x + half, self.center_y - half),
            self._to_iso(self.center_x + half, self.center_y + half),
            self._to_iso(self.center_x - half, self.center_y + half)
        ]
        pygame.draw.polygon(screen, COLORS['road'], points)
        
    def _to_iso(self, x, y):
        """Convert to isometric coordinates"""
        iso_x = x - y
        iso_y = (x + y) / 2
        return (iso_x + WINDOW_WIDTH // 2, iso_y)
