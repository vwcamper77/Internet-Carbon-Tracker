import os 
import sys
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog
import tkinter.messagebox
import psutil
import time
import threading
import datetime
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import webbrowser
from tkinter import PhotoImage

# Constants
CO2_PER_GB = 10  # Grams of CO2 per GB of data transferred
AVERAGE_CO2_PER_YEAR = 300_000  # 300 kg in grams
personal_reduction_target = 10  # Default personal target reduction percentage

# Function to get the resource path (for icons, etc.)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function to format CO2 units
def format_co2(co2_grams):
    if co2_grams >= 1_000_000:
        return f"{co2_grams / 1_000_000:.2f} tonnes"
    elif co2_grams >= 1_000:
        return f"{co2_grams / 1_000:.2f} kg"
    else:
        return f"{co2_grams:.2f} grams"

# Function to format data units
def format_data_units(data_mb):
    if data_mb >= 1_048_576:
        return f"{data_mb / 1_048_576:.2f} TB"
    elif data_mb >= 1024:
        return f"{data_mb / 1024:.2f} GB"
    else:
        return f"{data_mb:.2f} MB"

# Function to log errors
def log_error(message):
    documents_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'logs')
    if not os.path.exists(documents_folder):
        os.makedirs(documents_folder)
    log_path = os.path.join(documents_folder, 'error_log.txt')
    with open(log_path, 'a') as error_file:
        error_file.write(f"{datetime.datetime.now()}: {message}\n")

# Function to initialize the database
def init_database():
    documents_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker')
    if not os.path.exists(documents_folder):
        os.makedirs(documents_folder)
    db_path = os.path.join(documents_folder, 'co2_usage.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create necessary tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_usage (
            timestamp TEXT,
            data_sent REAL,
            data_received REAL,
            total_usage REAL,
            daily_usage REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS start_date (
            start_date TEXT
        )
    ''')

    # Set and fetch the tracking start date
    cursor.execute('SELECT * FROM start_date')
    result = cursor.fetchone()
    if result is None:
        start_date = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute('INSERT INTO start_date (start_date) VALUES (?)', (start_date,))
        conn.commit()
    else:
        start_date = result[0]
    
    start_date_var.set(f"📅 Tracking Start Date: {start_date}")
    conn.close()
    return start_date

# Function to reset daily CO2 usage with confirmation
def reset_daily_usage():
    confirmation_code = tk.simpledialog.askstring(
        "Reset Confirmation", 
        "Are you sure you want to reset?\nPlease enter '12345678' to confirm.",
    )

    if confirmation_code == "12345678":
        db_path = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'co2_usage.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Ensure only the daily CO2 is reset, and not the total
        cursor.execute('DELETE FROM network_usage WHERE timestamp >= ?', (datetime.datetime.now().strftime('%Y-%m-%d'),))
        conn.commit()
        conn.close()
        
        # Clear log file
        documents_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'logs')
        log_path = os.path.join(documents_folder, 'error_log.txt')
        with open(log_path, 'w') as log_file:
            log_file.write('')  # Clear the log file

        # Update GUI after reset
        init_database()
        update_gui()
        tk.messagebox.showinfo("Reset", "Reset successful!")
    else:
        tk.messagebox.showwarning("Reset", "Incorrect code. Reset canceled.")

# Function to get total network usage
def get_total_network_usage():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent, net_io.bytes_recv

# Function to track network usage
def track_network_usage():
    global current_grams_per_hour
    db_path = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'co2_usage.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    initial_sent, initial_recv = get_total_network_usage()

    while True:
        try:
            time.sleep(60)
            final_sent, final_recv = get_total_network_usage()

            data_sent_mb = (final_sent - initial_sent) / (1024 * 1024)
            data_received_mb = (final_recv - initial_sent) / (1024 * 1024)
            total_usage_mb = data_sent_mb + data_received_mb
            total_data_gb = total_usage_mb / 1024

            # Calculate CO2 emissions
            grams_per_hour = total_data_gb * CO2_PER_GB * 60
            current_grams_per_hour = grams_per_hour

            # Log data for debugging
            log_error(f"Data Sent: {data_sent_mb}, Data Received: {data_received_mb}, Grams Per Hour: {grams_per_hour}")

            # Store network usage in the database
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO network_usage (timestamp, data_sent, data_received, total_usage, daily_usage)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, data_sent_mb, data_received_mb, total_usage_mb, grams_per_hour))
            conn.commit()

            initial_sent, initial_recv = final_sent, final_recv

            # Update GUI
            update_gui()
        except Exception as e:
            log_error(f"Error in track_network_usage: {str(e)}")

    conn.close()

# Function to reset daily CO2 usage at midnight
def reset_daily_usage_at_midnight():
    global last_reset_date
    while True:
        current_date = datetime.datetime.now().date()
        if current_date != last_reset_date:
            last_reset_date = current_date
            # Reset only today's CO2 usage
            db_path = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'co2_usage.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM network_usage')  # Clear the network usage table for the new day
            conn.commit()
            conn.close()
            
            update_gui()  # Update the GUI after resetting
        time.sleep(60)  # Check every minute

# Function to update the live graph
def update_graph(frame):
    global current_grams_per_hour

    # Append data for the graph
    graph_data.append(current_grams_per_hour)
    time_data.append(len(graph_data))  # Store in seconds

    # Limit the graph to the last 10 minutes (600 seconds)
    graph_data_to_plot = graph_data[-600:]  # Last 600 seconds (10 minutes)
    time_data_to_plot = range(len(graph_data_to_plot))  # Generate range based on data length

    # Calculate the rolling average
    rolling_average = sum(graph_data_to_plot) / len(graph_data_to_plot) if graph_data_to_plot else 0

    # Clear the graph and plot the new data
    ax.clear()
    ax.plot(time_data_to_plot, graph_data_to_plot, color='blue', label='CO2 Emitted')

    # Add horizontal line for the rolling average
    ax.axhline(rolling_average, color='green', linestyle='--', label=f'Rolling Average: {rolling_average:.2f} g/hour')

    # Set graph labels and title
    ax.set_title('Live CO2 Emissions per Hour')
    ax.set_xlabel('Time (minutes)')
    ax.set_ylabel('CO2 grams')

    # Set x-axis limits and ticks
    ax.set_xlim(0, 600)  # Limits for x-axis (in seconds)
    ax.set_xticks([0, 300, 600])  # Show ticks at 0, 5 minutes, and 10 minutes (0, 300, 600 seconds)
    ax.set_xticklabels(['0', '5', '10'])  # Set labels for x-ticks
    ax.set_ylim(bottom=0)  # Ensure y-axis starts at 0

    # Add a legend to display the average
    ax.legend()

    plt.tight_layout()  # Adjust layout to make room for titles

# Function to update GUI labels
def update_gui():
    global current_grams_per_hour, projected_yearly_co2
    db_path = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'co2_usage.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT SUM(data_sent), SUM(data_received), SUM(total_usage), SUM(daily_usage) FROM network_usage')
        result = cursor.fetchone()
        total_sent_mb = result[0] or 0
        total_received_mb = result[1] or 0
        total_usage_mb = result[2] or 0
        daily_usage = result[3] or 0

        total_data_gb = total_usage_mb / 1024
        total_co2_emissions_data = total_data_gb * CO2_PER_GB * 60
        total_co2_var.set(f"🌿 Total CO2: {format_co2(total_co2_emissions_data)}")

        # Calculate the rolling average CO2 usage across the last 10 minutes
        rolling_average = sum(graph_data[-600:]) / min(len(graph_data), 600)
        grams_per_minute_var.set(f"💨 Overall Average CO2 g/hour: {rolling_average:.2f}")

        data_sent_var.set(f"⬆ Data Sent: {format_data_units(total_sent_mb)}")
        data_received_var.set(f"⬇ Data Received: {format_data_units(total_received_mb)}")
        total_data_used_var.set(f"🗂 Total Data Used: {format_data_units(total_usage_mb)}")
        todays_grams_var.set(f"🕛 Today's CO2 Emitted: {format_co2(daily_usage)}")

        # Project yearly CO2 using the average daily usage
        cursor.execute('SELECT start_date FROM start_date')
        start_date = cursor.fetchone()[0]
        start_date_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        days_since_start = max((datetime.datetime.now() - start_date_dt).days, 1)

        if days_since_start < 7:
            average_daily_co2 = max(current_grams_per_hour * 60 * 6, total_co2_emissions_data / days_since_start)
            projected_yearly_co2 = average_daily_co2 * 365
        else:
            early_estimate = current_grams_per_hour * 60 * 6
            actual_daily_average = total_co2_emissions_data / days_since_start

            weight_early = max(0.4 - (0.05 * (days_since_start - 7)), 0)
            weight_actual = 1 - weight_early

            blended_daily_co2 = (weight_early * early_estimate) + (weight_actual * actual_daily_average)
            projected_yearly_co2 = blended_daily_co2 * 365

        projected_yearly_var.set(f"📅 Projected Yearly CO2: {format_co2(projected_yearly_co2)}")
        update_status()
    except Exception as e:
        log_error(f"Error in update_gui: {str(e)}")

    conn.close()

# Function to update status based on target
def update_status():
    global projected_yearly_co2
    target_co2 = AVERAGE_CO2_PER_YEAR * (1 - personal_reduction_target / 100)
    if projected_yearly_co2 <= target_co2:
        status_var.set("Status: On Target")
        status_label.config(fg='green')
    else:
        status_var.set("Status: Above Target")
        status_label.config(fg='red')

# Initialize the Tkinter root window
root = tk.Tk()
root.title("CO2 Internet Tracker")
root.geometry("470x800")
root.option_add("*Font", "Segoe 12")

# Load the icon for the window and the system tray
try:
    root.iconbitmap(resource_path('app_icon.ico'))
except Exception as e:
    print(f"Icon loading error: {e}")

# Add a frame and canvas to allow for scrolling
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)
canvas = tk.Canvas(main_frame)
scroll_y = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scroll_x = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)

scroll_frame = tk.Frame(canvas)
scroll_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
canvas.pack(fill="both", expand=True)

# GUI Variables
start_date_var = tk.StringVar(value="📅 Tracking Start Date: ")
data_sent_var = tk.StringVar(value="⬆ Data Sent: ")
data_received_var = tk.StringVar(value="⬇ Data Received: ")
total_data_used_var = tk.StringVar(value="🗂 Total Data Used: ")
total_co2_var = tk.StringVar(value="🌿 Total CO2: ")
grams_per_minute_var = tk.StringVar(value="💨 Overall Average CO2 g/hour: ")
todays_grams_var = tk.StringVar(value="🕛 Today's CO2 Emitted: ")
projected_yearly_var = tk.StringVar(value="📅 Projected Yearly CO2: ")
average_user_var = tk.StringVar(value=f"👥 Assumed Average PC User CO2: {AVERAGE_CO2_PER_YEAR / 1000:.2f} kg")
personal_target_var = tk.StringVar(value=f"🎯 Personal Target: {AVERAGE_CO2_PER_YEAR * (1 - personal_reduction_target / 100) / 1000:.2f} kg")
status_var = tk.StringVar(value="📊 Status: ")

# Variables for live graph
graph_data = []
time_data = []
current_grams_per_hour = 0
projected_yearly_co2 = 0

# Track the last reset date for today's CO2 usage
last_reset_date = datetime.datetime.now().date()

# Add elements to the scrollable frame
tk.Label(scroll_frame, textvariable=data_sent_var, font=("Segoe", 12)).pack(pady=2)
tk.Label(scroll_frame, textvariable=data_received_var, font=("Segoe", 12)).pack(pady=5)
tk.Label(scroll_frame, textvariable=total_data_used_var, font=("Segoe", 12)).pack(pady=5)
tk.Label(scroll_frame, textvariable=total_co2_var, font=("Segoe", 12)).pack(pady=5)
tk.Label(scroll_frame, textvariable=grams_per_minute_var, font=("Segoe", 12), fg='blue').pack(pady=5)
tk.Label(scroll_frame, textvariable=todays_grams_var, font=("Segoe", 12)).pack(pady=5)
tk.Label(scroll_frame, textvariable=projected_yearly_var, font=("Segoe", 12)).pack(pady=5)
tk.Label(scroll_frame, textvariable=average_user_var, font=("Segoe", 10)).pack(pady=5)
tk.Label(scroll_frame, textvariable=personal_target_var, font=("Segoe", 12)).pack(pady=5)
status_label = tk.Label(scroll_frame, textvariable=status_var, font=("Segoe", 12))
status_label.pack(pady=5)

# Place the tracking start date label
tk.Label(scroll_frame, textvariable=start_date_var, font=("Segoe", 12)).pack(pady=5)

# Input for personal target percentage
tk.Label(scroll_frame, text="Set Personal Reduction Target (%):", font=("Segoe", 12)).pack(pady=5)
personal_target_entry = tk.Entry(scroll_frame, font=("Segoe", 12))
personal_target_entry.insert(0, "10")
personal_target_entry.pack(pady=5)

# Function to update the personal CO2 reduction target
def update_personal_target():
    global personal_reduction_target
    try:
        new_target = int(personal_target_entry.get())
        if 0 <= new_target <= 100:
            personal_reduction_target = new_target
            personal_target_var.set(f"🎯 Personal Target: {AVERAGE_CO2_PER_YEAR * (1 - personal_reduction_target / 100) / 1000:.2f} kg")
            update_status()
        else:
            tk.messagebox.showwarning("Invalid Input", "Please enter a value between 0 and 100.")
    except ValueError:
        tk.messagebox.showwarning("Invalid Input", "Please enter a valid integer.")

update_button = tk.Button(scroll_frame, text="Update Target", command=update_personal_target, font=("Segoe", 12))
update_button.pack(pady=5)

# Add Reset button
reset_button = tk.Button(scroll_frame, text="Reset", command=reset_daily_usage, font=("Segoe", 12))
reset_button.pack(pady=5)

# Live graph
fig, ax = plt.subplots(figsize=(4.5, 3))
canvas_graph = FigureCanvasTkAgg(fig, master=scroll_frame)
canvas_graph.draw()
canvas_graph.get_tk_widget().pack(pady=5, fill=tk.BOTH, expand=True)

# Adding watermark logo
try:
    watermark_img = Image.open(resource_path('planet-help-logo2.png')).resize((150, 28), Image.Resampling.LANCZOS)
    watermark_img_tk = ImageTk.PhotoImage(watermark_img)
    watermark_label = tk.Label(scroll_frame, image=watermark_img_tk, bg='white', cursor="hand2")
    watermark_label.image = watermark_img_tk
    watermark_label.pack(pady=5)
    watermark_label.bind("<Button-1>", lambda e: open_website())
except Exception as e:
    print(f"Watermark logo not found: {e}")

# Adding link to website
def open_website():
    webbrowser.open_new("https://planet.help/resources")

link_label = tk.Label(scroll_frame, text="More resources here: planet.help/resources", font=("Segoe", 10), fg="blue", cursor="hand2")
link_label.pack(pady=5)
link_label.bind("<Button-1>", lambda e: open_website())

# Animation for live graph
ani = FuncAnimation(fig, update_graph, interval=1000, cache_frame_data=False)

# Start initialization
init_database()

# Start network tracking in a separate thread
threading.Thread(target=track_network_usage, daemon=True).start()
# Start the thread to reset daily usage at midnight
threading.Thread(target=reset_daily_usage_at_midnight, daemon=True).start()

import os
import shutil

# Add this function to create a startup shortcut
def create_startup_shortcut():
    startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(startup_folder, "CO2 Internet Tracker.lnk")

    # Ensure to change 'co2_tracker.exe' to your actual executable name if it is different
    target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'co2_tracker.exe')

    # Create a shortcut using a simple batch command
    with open(os.path.join(os.getcwd(), 'create_shortcut.bat'), 'w') as bat_file:
        bat_file.write(f'@echo off\n')
        bat_file.write(f'set shortcut="{shortcut_path}"\n')
        bat_file.write(f'set target="{target_path}"\n')
        bat_file.write(f'set wshshell=CreateObject("WScript.Shell")\n')
        bat_file.write(f'set shortcutObj=wshshell.CreateShortcut(shortcut)\n')
        bat_file.write(f'shortcutObj.TargetPath=target\n')
        bat_file.write(f'shortcutObj.Save\n')

    # Run the batch file to create the shortcut
    os.system('create_shortcut.bat')
    os.remove('create_shortcut.bat')

# Call the function to create a startup shortcut
create_startup_shortcut()

# Run the GUI
root.mainloop()
