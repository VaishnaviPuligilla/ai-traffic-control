import pygame
from config import COLORS, UI_CONFIG, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.components import Button, Dropdown, VehicleCounter


class ConfigScreen:
    """Initial configuration screen for simulation setup"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 52)
        self.small_font = pygame.font.Font(None, 24)
        
        # Configuration state
        self.step = 1  # 1: Lane selection, 2: Vehicle config, 3: Ready
        self.num_lanes = 4
        self.view_mode = 'top_down'
        self.vehicle_counts = {}
        
        self._create_components()
        
    def _create_components(self):
        """Create UI components"""
        center_x = WINDOW_WIDTH // 2
        
        # Step 1: Lane selection
        self.lane_buttons = {
            4: Button(center_x - 150, 300, 120, 60, "4 Lanes", COLORS['dark_blue']),
            6: Button(center_x + 30, 300, 120, 60, "6 Lanes", COLORS['dark_blue'])
        }
        
        # View mode selection
        self.view_dropdown = Dropdown(
            center_x - 80, 420, 160, 35,
            ['top_down', 'isometric'],
            "View Mode"
        )
        
        # Next button for step 1
        self.next_btn_1 = Button(center_x - 60, 520, 120, 45, "Next →", COLORS['green'])
        
        # Step 2: Vehicle counters (created dynamically based on lane count)
        self.vehicle_counters = []
        
        # Start simulation button
        self.start_btn = Button(center_x - 100, WINDOW_HEIGHT - 100, 200, 50, 
                               "🚀 Start Simulation", COLORS['green'])
        
        # Back button
        self.back_btn = Button(50, WINDOW_HEIGHT - 60, 100, 40, "← Back", COLORS['gray'])
        
    def _create_vehicle_counters(self):
        """Create vehicle counters based on selected lanes"""
        self.vehicle_counters = []
        
        # Calculate positions for counters
        counter_width = 180
        total_width = self.num_lanes * (counter_width + 20)
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        for i in range(self.num_lanes):
            counter = VehicleCounter(
                start_x + i * (counter_width + 20),
                300,
                counter_width,
                i
            )
            self.vehicle_counters.append(counter)
            
    def handle_event(self, event):
        """Handle input events"""
        if self.step == 1:
            # Lane selection
            for lanes, btn in self.lane_buttons.items():
                if btn.handle_event(event):
                    self.num_lanes = lanes
                    # Highlight selected button
                    for l, b in self.lane_buttons.items():
                        b.color = COLORS['green'] if l == lanes else COLORS['dark_blue']
                        
            self.view_dropdown.handle_event(event)
            
            if self.next_btn_1.handle_event(event):
                self.view_mode = self.view_dropdown.value
                self._create_vehicle_counters()
                self.step = 2
                
        elif self.step == 2:
            # Vehicle configuration
            for counter in self.vehicle_counters:
                counter.handle_event(event)
                
            if self.back_btn.handle_event(event):
                self.step = 1
                
            if self.start_btn.handle_event(event):
                # Collect configuration
                self.vehicle_counts = {
                    counter.lane_id: counter.get_counts()
                    for counter in self.vehicle_counters
                }
                return True  # Signal to start simulation
                
        return False
    
    def draw(self):
        """Draw the configuration screen"""
        # Background
        self.screen.fill(COLORS['dark_gray'])
        
        # Draw animated background pattern
        self._draw_background_pattern()
        
        if self.step == 1:
            self._draw_step_1()
        elif self.step == 2:
            self._draw_step_2()
            
    def _draw_background_pattern(self):
        """Draw decorative background"""
        # Draw road-like pattern
        for i in range(0, WINDOW_WIDTH, 100):
            pygame.draw.line(self.screen, (45, 45, 55), (i, 0), (i, WINDOW_HEIGHT), 1)
        for i in range(0, WINDOW_HEIGHT, 100):
            pygame.draw.line(self.screen, (45, 45, 55), (0, i), (WINDOW_WIDTH, i), 1)
            
    def _draw_step_1(self):
        """Draw step 1: Lane and view selection"""
        center_x = WINDOW_WIDTH // 2
        
        # Title
        title = self.title_font.render("🚦 AI Traffic Simulation", True, COLORS['white'])
        title_rect = title.get_rect(center=(center_x, 80))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Reinforcement Learning Traffic Signal Control", True, COLORS['light_gray'])
        subtitle_rect = subtitle.get_rect(center=(center_x, 120))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Step indicator
        step_text = self.font.render("Step 1: Choose Configuration", True, COLORS['light_blue'])
        step_rect = step_text.get_rect(center=(center_x, 200))
        self.screen.blit(step_text, step_rect)
        
        # Lane selection label
        lanes_label = self.small_font.render("Select Number of Lanes:", True, COLORS['white'])
        self.screen.blit(lanes_label, (center_x - 90, 260))
        
        # Lane buttons
        for btn in self.lane_buttons.values():
            btn.draw(self.screen)
            
        # View mode dropdown
        self.view_dropdown.draw(self.screen)
        
        # Next button
        self.next_btn_1.draw(self.screen)
        
        # Instructions
        instructions = [
            "ℹ️ Choose 4 or 6 lanes for your intersection",
            "🎮 Select view mode: Top-down or Isometric (2.5D)",
            "🤖 AI will learn optimal signal timing"
        ]
        
        y = 600
        for inst in instructions:
            text = self.small_font.render(inst, True, COLORS['light_gray'])
            self.screen.blit(text, (center_x - text.get_width() // 2, y))
            y += 30
            
    def _draw_step_2(self):
        """Draw step 2: Vehicle configuration"""
        center_x = WINDOW_WIDTH // 2
        
        # Title
        title = self.title_font.render("🚗 Configure Traffic", True, COLORS['white'])
        title_rect = title.get_rect(center=(center_x, 60))
        self.screen.blit(title, title_rect)
        
        # Step indicator
        step_text = self.font.render("Step 2: Set Initial Vehicles per Lane", True, COLORS['light_blue'])
        step_rect = step_text.get_rect(center=(center_x, 120))
        self.screen.blit(step_text, step_rect)
        
        # Instructions
        inst = self.small_font.render(
            "Click + or - to add/remove vehicles. AI will spawn more dynamically during simulation.",
            True, COLORS['light_gray']
        )
        self.screen.blit(inst, (center_x - inst.get_width() // 2, 170))
        
        # Info panel
        info_rect = pygame.Rect(center_x - 200, 210, 400, 60)
        pygame.draw.rect(self.screen, (40, 40, 60), info_rect, border_radius=8)
        
        info_lines = [
            "🚛 Truck (Weight: 4) | 🚗 Car (Weight: 2)",
            "🏍️ Bike (Weight: 1) | 🚶 Pedestrian (Weight: 1)"
        ]
        
        for i, line in enumerate(info_lines):
            text = self.small_font.render(line, True, COLORS['white'])
            self.screen.blit(text, (center_x - text.get_width() // 2, 220 + i * 25))
        
        # Vehicle counters
        for counter in self.vehicle_counters:
            counter.draw(self.screen)
            
        # Lane direction indicators
        y_indicator = 460
        directions = ["↓ North (Down)", "↑ South (Up)", "→ West (Right)", "← East (Left)"]
        for i, counter in enumerate(self.vehicle_counters):
            if i < len(directions):
                dir_text = self.small_font.render(directions[i], True, COLORS['yellow'])
                self.screen.blit(dir_text, (counter.x + 20, y_indicator))
        
        # Buttons
        self.back_btn.draw(self.screen)
        self.start_btn.draw(self.screen)
        
        # Tips
        tips = [
            "💡 Tip: Add an ambulance during simulation to test emergency response!",
            "💡 Tip: Watch the AI learn to reduce waiting time over multiple cycles."
        ]
        
        y = WINDOW_HEIGHT - 170
        for tip in tips:
            text = self.small_font.render(tip, True, COLORS['light_gray'])
            self.screen.blit(text, (center_x - text.get_width() // 2, y))
            y += 25
            
    def get_config(self):
        """Get final configuration"""
        return {
            'num_lanes': self.num_lanes,
            'view_mode': self.view_mode,
            'vehicle_counts': self.vehicle_counts
        }
