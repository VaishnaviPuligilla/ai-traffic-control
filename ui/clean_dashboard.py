import pygame
from config import COLORS, UI_CONFIG, VEHICLE_TYPES


class CleanDashboard:
    """Simple, clean dashboard for the simulation"""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 36)
        
        # Data
        self.data = {}
        
    def update(self, data):
        """Update dashboard data"""
        self.data = data
        
    def draw(self, screen):
        """Draw the dashboard"""
        # Background
        pygame.draw.rect(screen, (25, 30, 40), self.rect, border_radius=10)
        pygame.draw.rect(screen, (60, 70, 90), self.rect, 2, border_radius=10)
        
        x = self.rect.x + 15
        y = self.rect.y + 15
        
        # Title
        title = self.title_font.render("🚦 AI Traffic Control", True, (255, 255, 255))
        screen.blit(title, (x, y))
        y += 35
        
        # Current Signal Box
        pygame.draw.rect(screen, (35, 40, 55), (x, y, self.rect.width - 30, 80), border_radius=8)
        
        current_lane = self.data.get('current_green', 0)
        time_left = self.data.get('time_remaining', 0)
        
        # Green indicator
        lane_text = self.big_font.render(f"Lane {current_lane + 1}", True, (100, 255, 100))
        screen.blit(lane_text, (x + 15, y + 10))
        
        # Timer
        timer_color = (255, 100, 100) if time_left < 5 else (255, 255, 100) if time_left < 10 else (100, 255, 100)
        timer_text = self.big_font.render(f"{int(time_left)}s", True, timer_color)
        screen.blit(timer_text, (x + 120, y + 10))
        
        # Next lane prediction
        next_lane = self.data.get('next_lane', 0)
        next_text = self.font.render(f"Next → Lane {next_lane + 1}", True, (150, 200, 255))
        screen.blit(next_text, (x + 15, y + 50))
        
        y += 95
        
        # Divider
        pygame.draw.line(screen, (60, 70, 90), (x, y), (x + self.rect.width - 30, y), 1)
        y += 15
        
        # Lane Stats Header
        header = self.font.render("Lane Status", True, (200, 200, 200))
        screen.blit(header, (x, y))
        y += 25
        
        # Lane stats (dynamic)
        lane_stats = self.data.get('lane_stats', {})
        for lane_id in range(4):
            stats = lane_stats.get(lane_id, {})
            
            # Lane row background
            is_green = (lane_id == current_lane)
            row_color = (40, 60, 40) if is_green else (35, 40, 55)
            pygame.draw.rect(screen, row_color, (x, y, self.rect.width - 30, 45), border_radius=5)
            
            # Signal indicator
            signal_color = (100, 255, 100) if is_green else (255, 80, 80)
            pygame.draw.circle(screen, signal_color, (x + 15, y + 22), 8)
            
            # Lane number
            lane_label = self.font.render(f"L{lane_id + 1}", True, (255, 255, 255))
            screen.blit(lane_label, (x + 30, y + 12))
            
            # Vehicle counts (dynamic)
            counts = stats.get('by_type', {})
            count_x = x + 70
            
            # Show count for each vehicle type with icon
            for v_type, icon in [('truck', '🚛'), ('car', '🚗'), ('bike', '🏍')]:
                count = counts.get(v_type, 0)
                if count > 0:
                    count_text = self.font.render(f"{icon}{count}", True, (200, 200, 200))
                    screen.blit(count_text, (count_x, y + 12))
                    count_x += 45
            
            # Weight
            weight = stats.get('weight', 0)
            weight_text = self.font.render(f"W:{weight}", True, (150, 180, 255))
            screen.blit(weight_text, (x + self.rect.width - 80, y + 12))
            
            y += 50
            
        y += 10
        
        # Emergency/Accident Status
        pygame.draw.line(screen, (60, 70, 90), (x, y), (x + self.rect.width - 30, y), 1)
        y += 15
        
        if self.data.get('emergency_active'):
            em_lane = self.data.get('emergency_lane', 0)
            pygame.draw.rect(screen, (100, 30, 30), (x, y, self.rect.width - 30, 35), border_radius=5)
            em_text = self.font.render(f"🚑 AMBULANCE in Lane {em_lane + 1}!", True, (255, 255, 255))
            screen.blit(em_text, (x + 10, y + 8))
            y += 40
        
        if self.data.get('accident_active'):
            acc_lane = self.data.get('accident_lane', 0)
            pygame.draw.rect(screen, (100, 70, 30), (x, y, self.rect.width - 30, 35), border_radius=5)
            acc_text = self.font.render(f"⚠️ ACCIDENT in Lane {acc_lane + 1}!", True, (255, 255, 255))
            screen.blit(acc_text, (x + 10, y + 8))
            y += 40
            
        # Pedestrians
        ped_waiting = self.data.get('pedestrians_waiting', 0)
        if ped_waiting > 0:
            ped_text = self.font.render(f"🚶 {ped_waiting} pedestrians waiting", True, (200, 200, 150))
            screen.blit(ped_text, (x, y + 10))
            y += 30
            
        # Stats summary
        y = self.rect.bottom - 80
        pygame.draw.line(screen, (60, 70, 90), (x, y), (x + self.rect.width - 30, y), 1)
        y += 10
        
        total_stats = self.data.get('total_stats', {})
        
        stats_text = [
            f"Total: {total_stats.get('total_vehicles', 0)} vehicles",
            f"Passed: {total_stats.get('total_passed', 0)}",
            f"Waiting: {total_stats.get('total_waiting', 0)}",
        ]
        
        for text in stats_text:
            stat = self.font.render(text, True, (180, 180, 180))
            screen.blit(stat, (x, y))
            y += 20


class VehicleSelector:
    """UI for selecting which vehicles to spawn"""
    
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 28)
        
        self.vehicle_options = {
            'truck': {'name': 'Truck 🚛', 'color': (139, 90, 43), 'selected': True},
            'car': {'name': 'Car 🚗', 'color': (65, 105, 225), 'selected': True},
            'bike': {'name': 'Bike 🏍', 'color': (255, 140, 0), 'selected': True},
        }
        
        self.checkboxes = {}
        self._create_checkboxes()
        
    def _create_checkboxes(self):
        """Create checkbox rectangles"""
        y_offset = 0
        for v_type in self.vehicle_options:
            self.checkboxes[v_type] = pygame.Rect(
                self.x + 10, self.y + 40 + y_offset, 20, 20
            )
            y_offset += 35
            
    def handle_event(self, event):
        """Handle click events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for v_type, rect in self.checkboxes.items():
                if rect.collidepoint(event.pos):
                    self.vehicle_options[v_type]['selected'] = not self.vehicle_options[v_type]['selected']
                    return True
        return False
        
    def get_selected(self):
        """Get list of selected vehicle types"""
        return [v for v, data in self.vehicle_options.items() if data['selected']]
        
    def draw(self, screen):
        """Draw the vehicle selector"""
        # Background
        height = 160
        pygame.draw.rect(screen, (30, 35, 50), (self.x, self.y, self.width, height), border_radius=8)
        pygame.draw.rect(screen, (60, 70, 90), (self.x, self.y, self.width, height), 2, border_radius=8)
        
        # Title
        title = self.title_font.render("Select Vehicles", True, (255, 255, 255))
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Checkboxes
        for v_type, rect in self.checkboxes.items():
            data = self.vehicle_options[v_type]
            
            # Checkbox
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=3)
            if data['selected']:
                inner = rect.inflate(-6, -6)
                pygame.draw.rect(screen, (100, 200, 100), inner, border_radius=2)
                
            # Label
            label = self.font.render(data['name'], True, (200, 200, 200))
            screen.blit(label, (rect.right + 10, rect.y + 2))


class ControlPanel:
    """Control buttons panel"""
    
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.font = pygame.font.Font(None, 22)
        
        self.buttons = {}
        self._create_buttons()
        
    def _create_buttons(self):
        """Create control buttons"""
        btn_w = (self.width - 20) // 2
        btn_h = 40
        
        self.buttons = {
            'ambulance': {
                'rect': pygame.Rect(self.x + 5, self.y, btn_w, btn_h),
                'text': '🚑 Add Ambulance',
                'color': (180, 50, 50),
                'hover': (220, 70, 70)
            },
            'accident': {
                'rect': pygame.Rect(self.x + btn_w + 15, self.y, btn_w, btn_h),
                'text': '⚠️ Accident',
                'color': (180, 120, 50),
                'hover': (220, 150, 70)
            },
            'pedestrian': {
                'rect': pygame.Rect(self.x + 5, self.y + 50, btn_w, btn_h),
                'text': '🚶 Add Pedestrians',
                'color': (50, 120, 180),
                'hover': (70, 150, 220)
            },
            'pause': {
                'rect': pygame.Rect(self.x + btn_w + 15, self.y + 50, btn_w, btn_h),
                'text': '⏸️ Pause',
                'color': (100, 100, 120),
                'hover': (130, 130, 150)
            },
        }
        
        self.hovered = None
        
    def handle_event(self, event):
        """Handle events, return clicked button name or None"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = None
            for name, btn in self.buttons.items():
                if btn['rect'].collidepoint(event.pos):
                    self.hovered = name
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, btn in self.buttons.items():
                if btn['rect'].collidepoint(event.pos):
                    return name
        return None
        
    def set_pause_text(self, paused):
        """Update pause button text"""
        self.buttons['pause']['text'] = '▶️ Resume' if paused else '⏸️ Pause'
        
    def draw(self, screen):
        """Draw control panel"""
        for name, btn in self.buttons.items():
            color = btn['hover'] if name == self.hovered else btn['color']
            pygame.draw.rect(screen, color, btn['rect'], border_radius=6)
            pygame.draw.rect(screen, (255, 255, 255), btn['rect'], 2, border_radius=6)
            
            text = self.font.render(btn['text'], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn['rect'].center)
            screen.blit(text, text_rect)
