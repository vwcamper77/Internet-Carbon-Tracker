from setuptools import setup

APP = ['co2_tracker.py']
DATA_FILES = [
    ('', ['app_icon.ico', 'planet-help-logo2.png']),
]
OPTIONS = {
    'argv_exe': 'co2_tracker.py',
    'packages': ['matplotlib', 'PIL', 'psutil', 'tkinter', 'sqlite3', 'webbrowser'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'build_exe': OPTIONS},
    setup_requires=['py2app'],
    name='Internet Carbon Tracker',
    version='0.1',
    description='Track your internet usage and carbon emissions.',
)
