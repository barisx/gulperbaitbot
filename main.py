import pyautogui
import time
import math
import threading
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import messagebox

# ---------------------- Configuration Parameters ----------------------

# Time (in seconds) the mouse must be idle before starting circular movement
IDLE_TIME = 1

# Radius of the circular mouse movement
RADIUS = 100  # Initial radius

# Angle increment (degrees) per iteration for circular movement
STEP_ANGLE = 40  # Initial step angle

# Sleep time between iterations (seconds) for circular movement
SLEEP_TIME = 0.000001  # Smaller values = faster iterations

# ---------------------- Global Variables ----------------------

# Track the last time the mouse was moved
last_move_time = time.time()

# Flag to control circular movement
circle_movement_active = False

# Lock for thread-safe operations
lock = threading.Lock()

# Event to signal program termination
terminate_event = threading.Event()

# Offset values for adjusting the center of the circle
x_offset = 0
y_offset = 0

# ---------------------- Function Definitions ----------------------

def on_move(x, y):
    global last_move_time, circle_movement_active
    with lock:
        last_move_time = time.time()
        if circle_movement_active:
            circle_movement_active = False
            status_label.config(text="Mouse moved manually. Circular movement stopped.")
        # Update debug information
        update_debug_info()

def on_click(x, y, button, pressed):
    global last_move_time, circle_movement_active
    if pressed:
        with lock:
            last_move_time = time.time()
            if circle_movement_active:
                circle_movement_active = False
                status_label.config(text="Mouse clicked manually. Circular movement stopped.")

def on_scroll(x, y, dx, dy):
    global last_move_time, circle_movement_active
    with lock:
        last_move_time = time.time()
        if circle_movement_active:
            circle_movement_active = False
            status_label.config(text="Mouse scrolled manually. Circular movement stopped.")

def move_mouse_in_circle():
    global circle_movement_active, STEP_ANGLE, RADIUS, x_offset, y_offset

    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2
    aspect_ratio = screen_width / screen_height

    angle = 0

    while True:
        with lock:
            if not circle_movement_active or terminate_event.is_set():
                break

        # Calculate new position using trigonometry and offsets
        x = center_x + x_offset + (RADIUS * aspect_ratio) * math.cos(math.radians(angle))
        y = center_y + y_offset + RADIUS * math.sin(math.radians(angle))
        
        print(f"Moving mouse to ({x}, {y})")

        pyautogui.moveTo(x, y, duration=0)

        angle = (angle + STEP_ANGLE) % 360

        time.sleep(SLEEP_TIME)

def start_circular_movement():
    global circle_movement_active
    with lock:
        circle_movement_active = True
        status_label.config(text="Circular movement started.")
        movement_thread = threading.Thread(target=move_mouse_in_circle, daemon=False)
        movement_thread.start()

def stop_circular_movement():
    global circle_movement_active
    global x_offset, y_offset
    x_offset = 0
    y_offset = 0
    with lock:
        circle_movement_active = False
    status_label.config(text="Circular movement stopped.")

def adjust_radius_and_angle(increase=True):
    global RADIUS, STEP_ANGLE
    with lock:
        if increase:
            if STEP_ANGLE < 90:
                STEP_ANGLE += 5
                print(f"Step Angle increased to {STEP_ANGLE} degrees.")
            if RADIUS < 500:
                RADIUS += 10
                print(f"Radius increased to {RADIUS} pixels.")
        else:
            if STEP_ANGLE > 5:
                STEP_ANGLE -= 5
                print(f"Step Angle decreased to {STEP_ANGLE} degrees.")
            if RADIUS > 50:
                RADIUS -= 10
                print(f"Radius decreased to {RADIUS} pixels.")

        status_label.config(text=f"Radius: {RADIUS}, Step Angle: {STEP_ANGLE}")
        update_debug_info()

def adjust_offset(dx, dy):
    global x_offset, y_offset
    with lock:
        x_offset += dx
        y_offset += dy
        # After dot 1 number must be
        x_offset = round(x_offset, 1)
        y_offset = round(y_offset, 1)
        status_label.config(text=f"Offset - X: {x_offset}, Y: {y_offset}")
        print(f"Offset adjusted - X: {x_offset}, Y: {y_offset}")
        update_debug_info()

def on_press(key):
    if key == keyboard.Key.page_up:
        adjust_radius_and_angle(increase=True)
    elif key == keyboard.Key.page_down:
        adjust_radius_and_angle(increase=False)
    elif key == keyboard.Key.insert:  # Use INS key for starting
        start_circular_movement()
    elif key == keyboard.Key.delete:  # Use DEL key for stopping
        stop_circular_movement()
    elif key == keyboard.Key.left:
        adjust_offset(-0.2, 0)  # Move left
    elif key == keyboard.Key.right:
        adjust_offset(0.2, 0)   # Move right
    elif key == keyboard.Key.up:
        adjust_offset(0, -0.2)  # Move up
    elif key == keyboard.Key.down:
        adjust_offset(0, 0.2)   # Move down
    elif key == keyboard.Key.esc:
        terminate_event.set()
        window.quit()

def update_debug_info():
    # Update the debug info label with the current offsets, radius, and step angle
    debug_label.config(text=f"(Press 'DEL' to Reset) | X Offset: {x_offset}, Y Offset: {y_offset}, Radius: {RADIUS}, Step Angle: {STEP_ANGLE} | (Move Mouse to Stop)")

# ---------------------- GUI Setup ----------------------

window = tk.Tk()
window.title("Circular Mouse Movement")

# Debug Overlay
debug_window = tk.Toplevel(window)
debug_window.overrideredirect(True)
debug_window.geometry(f"{window.winfo_screenwidth()}x30+0+0")
debug_window.attributes("-topmost", True)
debug_window.attributes("-transparentcolor", debug_window["bg"])
debug_label = tk.Label(debug_window, text="", font=("Helvetica", 12), bg="green", fg="white")
debug_label.pack()

# Main GUI setup
start_button = tk.Button(window, text="Start (INS)", command=start_circular_movement)
start_button.pack(pady=10)

stop_button = tk.Button(window, text="Stop (DEL)", command=stop_circular_movement)
stop_button.pack(pady=10)

status_label = tk.Label(window, text="Press 'INS' to start, 'DEL' to stop. Adjust with PgUp and PgDn. Move with Arrow Keys.")
status_label.pack(pady=10)

exit_button = tk.Button(window, text="Exit", command=lambda: terminate_event.set())
exit_button.pack(pady=10)

# ---------------------- Main Execution ----------------------

def main():
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    mouse_listener.start()

    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

    update_debug_info()  # Initialize debug info display
    window.mainloop()

    terminate_event.set()
    mouse_listener.stop()
    keyboard_listener.stop()
    print("Program terminated gracefully.")

if __name__ == "__main__":
    main()
