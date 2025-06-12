import pygame
import sys

# Init
pygame.init()
pygame.joystick.init()

# Setup window
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎮 Controller Visualizer")

# Colors
BG = (30, 30, 30)  # Dark background
GRAY = (100, 100, 100)  # Default button background
WHITE = (230, 230, 230)  # Text and borders
BLUE = (80, 150, 255)  # Stick movement
GREEN = (0, 255, 100)  # Active button color
RED = (255, 80, 80)  # Inactive button color
YELLOW = (255, 255, 0)  # D-pad color
PURPLE = (255, 50, 255)  # Extra vibrant color for highlighting
BLACK = (0, 0, 0)  # Button text
CARD = (45, 45, 45)  # Card background

# Fonts
font = pygame.font.SysFont("comicsansms", 22)
small_font = pygame.font.SysFont("comicsansms", 18)

# Check for joystick
if pygame.joystick.get_count() == 0:
    print("No joystick detected.")
    pygame.quit()
    sys.exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Controller: {joystick.get_name()}")

# Button mapping
button_names = {
    0: "Y", 1: "B", 2: "A", 3: "X",
    4: "L1", 5: "R1", 6: "L2", 7: "R2",
    8: "Select", 9: "Start",
    10: "LS", 11: "RS"
}

# Drawing helpers
def draw_card(x, y, w, h, title):
    pygame.draw.rect(screen, CARD, (x, y, w, h), border_radius=20)
    text = font.render(title, True, WHITE)
    screen.blit(text, (x + 10, y + 10))

def draw_stick(val_x, val_y, cx, cy, label, is_right=False):
    pygame.draw.circle(screen, GRAY, (cx, cy), 50, 3)
    dx = int(val_x * 35)
    dy = int(val_y * 35)
    pygame.draw.circle(screen, BLUE, (cx + dx, cy + dy), 15)
    screen.blit(small_font.render(label, True, WHITE), (cx - 20, cy + 60))

def draw_buttons(buttons):
    # Draw button grid in classic controller layout
    for idx, pressed in enumerate(buttons):
        label = button_names.get(idx, f"B{idx}")
        x = 350 + (idx % 2) * 80  # Align buttons in two columns
        y = 120 + (idx // 2) * 80
        color = GREEN if pressed else GRAY
        pygame.draw.rect(screen, color, (x, y, 70, 70), border_radius=20)
        text = small_font.render(label, True, BLACK if pressed else WHITE)
        screen.blit(text, (x + 18, y + 20))

def draw_dpad(hx, hy):
    # D-Pad - positioned in the top-left corner
    cx, cy = 100, 100
    s = 30
    pygame.draw.polygon(screen, WHITE if hy == 1 else GRAY, [(cx, cy - 50), (cx - s, cy - 20), (cx + s, cy - 20)])
    pygame.draw.polygon(screen, WHITE if hy == -1 else GRAY, [(cx, cy + 50), (cx - s, cy + 20), (cx + s, cy + 20)])
    pygame.draw.polygon(screen, WHITE if hx == -1 else GRAY, [(cx - 50, cy), (cx - 20, cy - s), (cx - 20, cy + s)])
    pygame.draw.polygon(screen, WHITE if hx == 1 else GRAY, [(cx + 50, cy), (cx + 20, cy - s), (cx + 20, cy + s)])
    pygame.draw.circle(screen, GRAY, (cx, cy), 10)
    screen.blit(small_font.render("D-Pad", True, WHITE), (cx - 30, cy + 60))

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    screen.fill(BG)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.event.pump()

    # Draw cards for the sections
    draw_card(30, 30, 220, 180, "D-Pad")
    draw_card(30, 250, 220, 180, "Left Stick")
    draw_card(350, 30, 200, 350, "Buttons")
    draw_card(580, 250, 220, 180, "Right Stick")

    # D-Pad (Hat)
    if joystick.get_numhats() > 0:
        hat_x, hat_y = joystick.get_hat(0)
        draw_dpad(hat_x, hat_y)

    # Left Stick: Axis 0 & 1
    lx = joystick.get_axis(0)
    ly = joystick.get_axis(1)
    draw_stick(lx, ly, 140, 340, "Left", is_right=False)

    # Right Stick: Axis 2 & 3
    rx = joystick.get_axis(2)
    ry = joystick.get_axis(3)
    draw_stick(rx, ry, 690, 340, "Right", is_right=True)

    # Buttons
    num_buttons = joystick.get_numbuttons()
    buttons = [joystick.get_button(i) for i in range(min(12, num_buttons))]
    draw_buttons(buttons)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
