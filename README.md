# Internet Carbon Tracker

## Overview
The **Internet Carbon Tracker** is a Python-based application that monitors your internet data usage and estimates the associated carbon emissions. This tool encourages users to make more conscious decisions about internet usage and helps track carbon reduction efforts over time.

This project is part of **Planet Help** (https://planet.help/), an initiative focused on reducing CO2 emissions.

---

## Key Features
- **Data-Driven Tracking**: Monitors your **actual internet data usage** (upload/download) and estimates CO2 emissions in real time, using a **data-driven approach**.
- **Daily and Total CO2 Emissions**: Separately tracks daily emissions and accumulates total CO2 emissions over time.
- **Projected Yearly Emissions**: Provides a projected yearly estimate of CO2 emissions based on current usage patterns.
- **Custom CO2 Reduction Targets**: Allows users to set personal reduction goals and track their progress.
- **Visual Graphs**: Displays live graphs showing CO2 emissions per hour and rolling averages.
- **Reset Functionality**: Daily CO2 usage resets at midnight, with an option for users to manually reset the tracking data if needed.

---

## CO2 Calculation: Data-Driven Approach

### How It Works:
The **Internet Carbon Tracker** uses a **data-driven approach** to calculate CO2 emissions. Instead of relying on average usage estimates, the app measures the exact **data sent** and **data received** on your device and calculates emissions based on actual usage.

- **CO2 Emissions per GB**: The app calculates that each **gigabyte (GB) of data transferred** emits approximately **0.16 grams of CO2**. This estimate accounts for the energy consumption of data centers, networks, and user devices.
  
- **Real-Time Feedback**: The app tracks data usage in real time, dynamically calculating CO2 emissions as data is sent and received. The more data-intensive the activity (such as streaming or downloading large files), the higher the CO2 emissions will be.

- **Dynamic Calculations**: Since the app is based on actual usage, users get a precise and personalized view of their carbon footprint rather than relying on average estimates.

### Example of CO2 Calculation:
If you transfer **5 GB** of data in a day, the app calculates your emissions as follows:

\[
\text{CO2 Emissions} = 5 \, \text{GB} \times 0.16 \, \text{grams per GB} = 0.8 \, \text{grams of CO2}
\]

This approach ensures that your emissions reflect the actual data you've used, providing more accurate insights into your internet-related CO2 footprint.

---

## Installation

### Prerequisites
- **Python 3.12 or higher** must be installed on your system.
- Install the required Python libraries by running:
    ```bash
    pip install -r requirements.txt
    ```

### Setup
1. **Clone the Repository**:
    ```bash
    git clone https://github.com/vwcamper77/Internet-Carbon-Tracker.git
    cd Internet-Carbon-Tracker
    ```

2. **Run the Application**:
    To start the application, run:
    ```bash
    python SRC/co2_tracker.py
    ```

### Optional: Creating an Executable (Windows)
You can use `PyInstaller` to create an executable for the application:
```bash
pyinstaller --onefile --windowed --add-data "app_icon.ico;." --add-data "planet-help-logo2.png;." SRC/co2_tracker.py
