import pyautogui
import time
import math
import threading
from pynput import keyboard, mouse

# ---------------------- Configuration Parameters ----------------------

# Time (in seconds) the mouse must be idle before starting circular movement
IDLE_TIME = 1

# Radius of the circular mouse movement
RADIUS = 100  # Initial radius

# Angle increment (degrees) per iteration for circular movement
STEP_ANGLE = 40  # Initial step angle

# Sleep time between iterations (seconds) for circular movement
SLEEP_TIME = 0.000001  # Smaller values = faster iterations

# Interrupt key to terminate the script
INTERRUPT_KEY = keyboard.Key.esc  # You can change this to another key if desired

# Keys to adjust step_angle and radius
ADJUST_UP_KEY = keyboard.Key.page_up
ADJUST_DOWN_KEY = keyboard.Key.page_down

# ---------------------- Global Variables ----------------------

# Track the last time the mouse was moved
last_move_time = time.time()

# Flag to control circular movement
circle_movement_active = False

# Lock for thread-safe operations
lock = threading.Lock()

# Event to signal program termination
terminate_event = threading.Event()

# ---------------------- Function Definitions ----------------------

def on_move(x, y):
    """
    Callback function for mouse movement.
    Updates the last_move_time whenever the mouse is moved.
    If circular movement is active, stops it.
    """
    global last_move_time, circle_movement_active
    with lock:
        last_move_time = time.time()
        if circle_movement_active:
            circle_movement_active = False
            print("Mouse moved manually. Stopping circular movement.")

def on_click(x, y, button, pressed):
    """
    Callback function for mouse clicks.
    Updates the last_move_time whenever the mouse is clicked.
    If circular movement is active, stops it.
    """
    global last_move_time, circle_movement_active
    if pressed:
        with lock:
            last_move_time = time.time()
            if circle_movement_active:
                circle_movement_active = False
                print("Mouse clicked manually. Stopping circular movement.")

def on_scroll(x, y, dx, dy):
    """
    Callback function for mouse scrolls.
    Updates the last_move_time whenever the mouse is scrolled.
    If circular movement is active, stops it.
    """
    global last_move_time, circle_movement_active
    with lock:
        last_move_time = time.time()
        if circle_movement_active:
            circle_movement_active = False
            print("Mouse scrolled manually. Stopping circular movement.")

def move_mouse_in_circle():
    """
    Moves the mouse in a circular path around the center of the screen.
    Continues until circle_movement_active is set to False.
    """
    global circle_movement_active, STEP_ANGLE, RADIUS

    # Get screen dimensions and calculate center
    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2

    angle = 0  # Starting angle

    print("Starting circular mouse movement...")

    while True:
        with lock:
            if not circle_movement_active or terminate_event.is_set():
                break

        # Calculate new position using trigonometry
        x = center_x + RADIUS * math.cos(math.radians(angle))
        y = center_y + RADIUS * math.sin(math.radians(angle))

        # Move the mouse to the new position instantly
        pyautogui.moveTo(x, y, duration=0)

        # Print the new position for debugging
        print(f"Mouse moved to position: ({x:.2f}, {y:.2f})")

        # Increment the angle
        angle = (angle + STEP_ANGLE) % 360

        # Control the speed of movement
        time.sleep(SLEEP_TIME)

def monitor_idle():
    """
    Monitors mouse idle time.
    If idle for IDLE_TIME seconds, starts circular movement.
    """
    global circle_movement_active

    while not terminate_event.is_set():
        with lock:
            current_time = time.time()
            time_since_last_move = current_time - last_move_time

            if time_since_last_move >= IDLE_TIME and not circle_movement_active:
                circle_movement_active = True
                # Start circular movement in a separate thread
                movement_thread = threading.Thread(target=move_mouse_in_circle)
                movement_thread.start()

        # Check every 0.5 seconds
        time.sleep(0.5)

def on_press(key):
    """
    Callback function for keyboard key presses.
    Handles interrupt key and adjustment keys.
    """
    global RADIUS, STEP_ANGLE

    if key == INTERRUPT_KEY:
        print("Interrupt key pressed. Exiting program...")
        terminate_event.set()
        # Stop circular movement if active
        with lock:
            circle_movement_active = False
        # Stop the listener
        return False

    elif key == ADJUST_UP_KEY:
        with lock:
            # Increase step_angle and radius with upper limits
            if STEP_ANGLE < 90:
                STEP_ANGLE += 5
                print(f"Step Angle increased to {STEP_ANGLE} degrees.")
            else:
                print("Step Angle is already at maximum (90 degrees).")

            if RADIUS < 500:
                RADIUS += 10
                print(f"Radius increased to {RADIUS} pixels.")
            else:
                print("Radius is already at maximum (500 pixels).")

    elif key == ADJUST_DOWN_KEY:
        with lock:
            # Decrease step_angle and radius with lower limits
            if STEP_ANGLE > 5:
                STEP_ANGLE -= 5
                print(f"Step Angle decreased to {STEP_ANGLE} degrees.")
            else:
                print("Step Angle is already at minimum (5 degrees).")

            if RADIUS > 50:
                RADIUS -= 10
                print(f"Radius decreased to {RADIUS} pixels.")
            else:
                print("Radius is already at minimum (50 pixels).")

def start_keyboard_listener():
    """
    Starts the keyboard listener to listen for the interrupt key and adjustment keys.
    """
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# ---------------------- Main Execution ----------------------

def main():
    # Start mouse listener
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    mouse_listener.start()

    # Start idle monitor in a separate thread
    idle_thread = threading.Thread(target=monitor_idle, daemon=True)
    idle_thread.start()

    # Start keyboard listener in the main thread
    start_keyboard_listener()

    # Wait for termination signal
    terminate_event.wait()

    # Cleanup
    mouse_listener.stop()
    print("Program terminated gracefully.")

if __name__ == "__main__":
    main()
