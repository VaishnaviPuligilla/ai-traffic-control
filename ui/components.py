import pygame
from config import COLORS, UI_CONFIG, VEHICLE_TYPES, SIGNAL_CONFIG

class Button:
    """Interactive button component"""
    
    def __init__(self, x, y, width, height, text, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color or COLORS['dark_blue']
        self.hover_color = hover_color or COLORS['blue']
        self.current_color = self.color
        self.font = pygame.font.Font(None, UI_CONFIG['font_size'])
        self.enabled = True
        self.clicked = False
        
    def handle_event(self, event):
        """Handle mouse events"""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
            else:
                self.current_color = self.color
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
            
        return False
    
    def draw(self, screen):
        """Draw the button"""
        # Draw button background
        color = self.current_color if self.enabled else COLORS['gray']
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['white'], self.rect, 2, border_radius=8)
        
        # Draw text
        text_color = COLORS['white'] if self.enabled else COLORS['light_gray']
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class Slider:
    """Slider for numeric input"""
    
    def __init__(self, x, y, width, height, min_val, max_val, initial, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False
        self.font = pygame.font.Font(None, UI_CONFIG['font_size'])
        
    def handle_event(self, event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value(event.pos[0])
                
    def _update_value(self, x):
        """Update slider value based on mouse position"""
        ratio = (x - self.rect.x) / self.rect.width
        ratio = max(0, min(1, ratio))
        self.value = int(self.min_val + ratio * (self.max_val - self.min_val))
        
    def draw(self, screen):
        """Draw the slider"""
        # Label
        label_text = self.font.render(f"{self.label}: {self.value}", True, COLORS['white'])
        screen.blit(label_text, (self.rect.x, self.rect.y - 25))
        
        # Track
        track_rect = pygame.Rect(self.rect.x, self.rect.y + 5, self.rect.width, 10)
        pygame.draw.rect(screen, COLORS['gray'], track_rect, border_radius=5)
        
        # Fill
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = int(self.rect.width * ratio)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y + 5, fill_width, 10)
        pygame.draw.rect(screen, COLORS['blue'], fill_rect, border_radius=5)
        
        # Handle
        handle_x = self.rect.x + fill_width
        pygame.draw.circle(screen, COLORS['white'], (handle_x, self.rect.y + 10), 12)
        pygame.draw.circle(screen, COLORS['blue'], (handle_x, self.rect.y + 10), 10)


class Dropdown:
    """Dropdown selection component"""
    
    def __init__(self, x, y, width, height, options, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = 0
        self.label = label
        self.expanded = False
        self.font = pygame.font.Font(None, UI_CONFIG['font_size'])
        
    def handle_event(self, event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
            elif self.expanded:
                # Check if clicked on an option
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.bottom + i * self.rect.height,
                        self.rect.width,
                        self.rect.height
                    )
                    if option_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.expanded = False
                        return True
                self.expanded = False
        return False
    
    @property
    def value(self):
        return self.options[self.selected_index]
    
    def draw(self, screen):
        """Draw the dropdown"""
        # Label
        label_text = self.font.render(self.label, True, COLORS['white'])
        screen.blit(label_text, (self.rect.x, self.rect.y - 25))
        
        # Main box
        pygame.draw.rect(screen, COLORS['dark_gray'], self.rect, border_radius=5)
        pygame.draw.rect(screen, COLORS['white'], self.rect, 2, border_radius=5)
        
        # Selected value
        text = self.font.render(str(self.value), True, COLORS['white'])
        screen.blit(text, (self.rect.x + 10, self.rect.y + 8))
        
        # Arrow
        arrow_x = self.rect.right - 20
        arrow_y = self.rect.centery
        if self.expanded:
            points = [(arrow_x - 5, arrow_y + 3), (arrow_x + 5, arrow_y + 3), (arrow_x, arrow_y - 5)]
        else:
            points = [(arrow_x - 5, arrow_y - 3), (arrow_x + 5, arrow_y - 3), (arrow_x, arrow_y + 5)]
        pygame.draw.polygon(screen, COLORS['white'], points)
        
        # Options dropdown
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.bottom + i * self.rect.height,
                    self.rect.width,
                    self.rect.height
                )
                color = COLORS['blue'] if i == self.selected_index else COLORS['dark_gray']
                pygame.draw.rect(screen, color, option_rect)
                pygame.draw.rect(screen, COLORS['white'], option_rect, 1)
                
                text = self.font.render(str(option), True, COLORS['white'])
                screen.blit(text, (option_rect.x + 10, option_rect.y + 8))


class VehicleCounter:
    """Component for counting vehicles per type per lane"""
    
    def __init__(self, x, y, width, lane_id):
        self.x = x
        self.y = y
        self.width = width
        self.lane_id = lane_id
        self.font = pygame.font.Font(None, UI_CONFIG['font_size'])
        self.small_font = pygame.font.Font(None, 14)
        
        # Vehicle counts
        self.counts = {
            'truck': 0,
            'car': 0,
            'bike': 0,
            'pedestrian': 0
        }
        
        # +/- buttons for each type
        self.buttons = {}
        self._create_buttons()
        
    def _create_buttons(self):
        """Create increment/decrement buttons for each vehicle type"""
        y_offset = 0
        btn_size = 20
        
        for v_type in ['truck', 'car', 'bike', 'pedestrian']:
            self.buttons[v_type] = {
                'minus': pygame.Rect(self.x + self.width - 60, self.y + 30 + y_offset, btn_size, btn_size),
                'plus': pygame.Rect(self.x + self.width - 30, self.y + 30 + y_offset, btn_size, btn_size)
            }
            y_offset += 25
            
    def handle_event(self, event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for v_type, btns in self.buttons.items():
                if btns['minus'].collidepoint(event.pos):
                    self.counts[v_type] = max(0, self.counts[v_type] - 1)
                    return True
                elif btns['plus'].collidepoint(event.pos):
                    self.counts[v_type] = min(20, self.counts[v_type] + 1)
                    return True
        return False
    
    def draw(self, screen):
        """Draw the vehicle counter"""
        # Background
        bg_rect = pygame.Rect(self.x, self.y, self.width, 140)
        pygame.draw.rect(screen, COLORS['panel_bg'], bg_rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['panel_border'], bg_rect, 2, border_radius=8)
        
        # Title
        title = self.font.render(f"Lane {self.lane_id + 1}", True, COLORS['white'])
        screen.blit(title, (self.x + 10, self.y + 5))
        
        # Vehicle types and counts
        y_offset = 0
        for v_type in ['truck', 'car', 'bike', 'pedestrian']:
            y_pos = self.y + 30 + y_offset
            
            # Type name
            config = VEHICLE_TYPES.get(v_type, {})
            name = config.get('name', v_type.capitalize())
            color = config.get('color', COLORS['white'])
            
            # Color indicator
            pygame.draw.rect(screen, color, (self.x + 10, y_pos + 2, 15, 15), border_radius=3)
            
            # Name
            name_text = self.small_font.render(name, True, COLORS['white'])
            screen.blit(name_text, (self.x + 30, y_pos + 3))
            
            # Minus button
            pygame.draw.rect(screen, COLORS['red'], self.buttons[v_type]['minus'], border_radius=3)
            minus_text = self.small_font.render("-", True, COLORS['white'])
            screen.blit(minus_text, (self.buttons[v_type]['minus'].x + 7, self.buttons[v_type]['minus'].y + 3))
            
            # Count
            count_text = self.font.render(str(self.counts[v_type]), True, COLORS['white'])
            screen.blit(count_text, (self.x + self.width - 52, y_pos))
            
            # Plus button
            pygame.draw.rect(screen, COLORS['green'], self.buttons[v_type]['plus'], border_radius=3)
            plus_text = self.small_font.render("+", True, COLORS['white'])
            screen.blit(plus_text, (self.buttons[v_type]['plus'].x + 6, self.buttons[v_type]['plus'].y + 3))
            
            y_offset += 25
            
    def get_counts(self):
        """Get vehicle counts"""
        return {k: v for k, v in self.counts.items() if v > 0}


class AnalyticsPanel:
    """Side panel showing real-time analytics"""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, UI_CONFIG['font_size'])
        self.title_font = pygame.font.Font(None, UI_CONFIG['title_font_size'])
        self.small_font = pygame.font.Font(None, 16)
        
        # Data to display
        self.data = {
            'current_green_lane': 0,
            'next_predicted_lane': 0,
            'time_remaining': 0,
            'total_vehicles': 0,
            'total_waiting': 0,
            'avg_wait_time': 0,
            'throughput': 0,
            'emergency_active': False,
            'accident_active': False,
            'lane_stats': {}
        }
        
    def update(self, data):
        """Update panel data"""
        self.data.update(data)
        
    def draw(self, screen):
        """Draw the analytics panel"""
        # Background
        pygame.draw.rect(screen, COLORS['panel_bg'], self.rect, border_radius=10)
        pygame.draw.rect(screen, COLORS['panel_border'], self.rect, 2, border_radius=10)
        
        y = self.rect.y + 15
        x = self.rect.x + 15
        
        # Title
        title = self.title_font.render("📊 Live Analytics", True, COLORS['white'])
        screen.blit(title, (x, y))
        y += 35
        
        # Divider
        pygame.draw.line(screen, COLORS['panel_border'], (x, y), (self.rect.right - 15, y), 2)
        y += 15
        
        # Current Signal Info
        self._draw_section(screen, "🚦 Signal Status", x, y)
        y += 25
        
        current_lane = self.data.get('current_green_lane', 0)
        time_remaining = self.data.get('time_remaining', 0)
        
        self._draw_stat(screen, f"Green Lane: Lane {current_lane + 1}", x, y, COLORS['green'])
        y += 22
        
        # Time remaining with color coding
        if time_remaining <= 5:
            time_color = COLORS['red']
        elif time_remaining <= 10:
            time_color = COLORS['yellow']
        else:
            time_color = COLORS['white']
        self._draw_stat(screen, f"Time Left: {int(time_remaining)}s", x, y, time_color)
        y += 22
        
        next_lane = self.data.get('next_predicted_lane', 0)
        self._draw_stat(screen, f"Next: Lane {next_lane + 1} (predicted)", x, y, COLORS['light_blue'])
        y += 30
        
        # Divider
        pygame.draw.line(screen, COLORS['panel_border'], (x, y), (self.rect.right - 15, y), 1)
        y += 15
        
        # Traffic Stats
        self._draw_section(screen, "🚗 Traffic Stats", x, y)
        y += 25
        
        self._draw_stat(screen, f"Total Vehicles: {self.data.get('total_vehicles', 0)}", x, y)
        y += 22
        self._draw_stat(screen, f"Waiting: {self.data.get('total_waiting', 0)}", x, y)
        y += 22
        self._draw_stat(screen, f"Passed: {self.data.get('throughput', 0)}", x, y)
        y += 22
        
        avg_wait = self.data.get('avg_wait_time', 0)
        wait_color = COLORS['red'] if avg_wait > 30 else COLORS['yellow'] if avg_wait > 15 else COLORS['green']
        self._draw_stat(screen, f"Avg Wait: {avg_wait:.1f}s", x, y, wait_color)
        y += 30
        
        # Divider
        pygame.draw.line(screen, COLORS['panel_border'], (x, y), (self.rect.right - 15, y), 1)
        y += 15
        
        # Emergency Status
        self._draw_section(screen, "🚨 Events", x, y)
        y += 25
        
        if self.data.get('emergency_active'):
            self._draw_stat(screen, "⚠️ AMBULANCE ACTIVE!", x, y, COLORS['ambulance_red'])
        else:
            self._draw_stat(screen, "No Emergency", x, y, COLORS['gray'])
        y += 22
        
        if self.data.get('accident_active'):
            self._draw_stat(screen, "⚠️ ACCIDENT REPORTED!", x, y, COLORS['orange'])
        else:
            self._draw_stat(screen, "No Accidents", x, y, COLORS['gray'])
        y += 30
        
        # Divider
        pygame.draw.line(screen, COLORS['panel_border'], (x, y), (self.rect.right - 15, y), 1)
        y += 15
        
        # Lane-wise breakdown
        self._draw_section(screen, "📋 Lane Details", x, y)
        y += 25
        
        lane_stats = self.data.get('lane_stats', {})
        for lane_id in range(4):
            stats = lane_stats.get(lane_id, {})
            count = stats.get('count', 0)
            weight = stats.get('weight', 0)
            
            # Lane indicator
            is_green = (lane_id == current_lane)
            indicator_color = COLORS['green'] if is_green else COLORS['red']
            pygame.draw.circle(screen, indicator_color, (x + 5, y + 8), 5)
            
            text = f"L{lane_id + 1}: {count} vehicles (W:{weight:.0f})"
            self._draw_stat(screen, text, x + 15, y, COLORS['white'])
            y += 20
            
    def _draw_section(self, screen, title, x, y):
        """Draw a section title"""
        text = self.font.render(title, True, COLORS['light_blue'])
        screen.blit(text, (x, y))
        
    def _draw_stat(self, screen, text, x, y, color=None):
        """Draw a statistic line"""
        color = color or COLORS['white']
        text_surface = self.small_font.render(text, True, color)
        screen.blit(text_surface, (x, y))


class AlertPopup:
    """Popup for emergency/accident alerts"""
    
    def __init__(self):
        self.active = False
        self.message = ""
        self.alert_type = "info"  # 'emergency', 'accident', 'info'
        self.timer = 0
        self.duration = 3  # seconds
        self.font = pygame.font.Font(None, 28)
        
    def show(self, message, alert_type="info", duration=3):
        """Show alert popup"""
        self.active = True
        self.message = message
        self.alert_type = alert_type
        self.duration = duration
        self.timer = 0
        
    def update(self, dt):
        """Update popup timer"""
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False
                
    def draw(self, screen, center_x, center_y):
        """Draw the popup"""
        if not self.active:
            return
            
        # Colors based on type
        if self.alert_type == "emergency":
            bg_color = (200, 0, 0, 200)
            border_color = COLORS['white']
        elif self.alert_type == "accident":
            bg_color = (200, 100, 0, 200)
            border_color = COLORS['white']
        else:
            bg_color = (0, 100, 200, 200)
            border_color = COLORS['white']
            
        # Calculate size
        text_surface = self.font.render(self.message, True, COLORS['white'])
        width = text_surface.get_width() + 40
        height = 60
        
        # Create semi-transparent surface
        popup_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        popup_surface.fill(bg_color)
        
        # Draw on main screen
        x = center_x - width // 2
        y = center_y - height // 2
        
        screen.blit(popup_surface, (x, y))
        pygame.draw.rect(screen, border_color, (x, y, width, height), 3, border_radius=10)
        
        # Draw text
        text_rect = text_surface.get_rect(center=(center_x, center_y))
        screen.blit(text_surface, text_rect)
