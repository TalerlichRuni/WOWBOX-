import os

# The URL of your deployed cloud server
SERVER_URL = os.environ.get('WOWBOX_SERVER', 'https://your-app.onrender.com')

# Must match the AGENT_KEY on the server
AGENT_KEY = os.environ.get('AGENT_KEY', 'agent-secret-key-change-me')

# Your Canon Ivy 2 printer MAC address
PRINTER_MAC = os.environ.get('PRINTER_MAC', '10:23:81:A4:6A:D4')

# How often (seconds) to check the server for new print jobs
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))
