"""
WOWBOX Agent - Runs on the Raspberry Pi.
Polls the cloud server for new print jobs and sends them to the Canon Ivy 2 printer.

Usage:
    python agent.py

Environment variables (or edit config.py):
    WOWBOX_SERVER  - URL of the cloud server
    AGENT_KEY      - Secret key to authenticate with the server
    PRINTER_MAC    - Bluetooth MAC address of the printer
    POLL_INTERVAL  - Seconds between polls (default: 5)
"""

import os
import sys
import time
import tempfile
import requests
import subprocess
from loguru import logger

# Add the project root to the path so we can import ivy2
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from config import SERVER_URL, AGENT_KEY, PRINTER_MAC, POLL_INTERVAL


def create_printer():
    """Create a fresh Ivy2Printer instance.

    We need to create a new ClientThread each time because threading.Thread
    cannot be restarted after it finishes. We do this by re-assigning the
    class-level `client` attribute before instantiation.
    """
    from client import ClientThread
    from ivy2 import Ivy2Printer

    # Replace the class-level client with a fresh thread
    Ivy2Printer.client = ClientThread()
    return Ivy2Printer()


def manage_bluetooth(connect=True):
    """Manage the rfcomm bluetooth connection."""
    try:
        if connect:
            logger.info("Initializing Bluetooth connection...")
            subprocess.run(["hciconfig", "hci0", "sspmode", "0"], check=False)
            subprocess.run(["rfcomm", "release", "all"], check=False)
            subprocess.Popen(["rfcomm", "connect", "hci0", PRINTER_MAC, "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            subprocess.run(["chmod", "666", "/dev/rfcomm0"], check=False)
        else:
            logger.info("Releasing Bluetooth connection...")
            subprocess.run(["rfcomm", "release", "all"], check=False)
    except Exception as e:
        logger.error(f"Bluetooth management error: {e}")


def report_status(job_id, status, error=None):
    """Report the result of a print job back to the server."""
    try:
        requests.post(
            f"{SERVER_URL}/api/agent/status",
            headers={'X-Agent-Key': AGENT_KEY},
            json={'id': job_id, 'status': status, 'error': error},
            timeout=10
        )
        logger.info(f"Reported status '{status}' for job {job_id[:8]}...")
    except Exception as e:
        logger.error(f"Failed to report status: {e}")


def handle_print_job(job_id, filename):
    """Download an image from the server and print it."""
    temp_path = None
    printer = None

    try:
        # Download the image
        logger.info(f"Downloading image: {filename}")
        img_response = requests.get(
            f"{SERVER_URL}/api/agent/download/{filename}",
            headers={'X-Agent-Key': AGENT_KEY},
            timeout=60
        )

        if img_response.status_code != 200:
            report_status(job_id, 'failed', f'Failed to download image (HTTP {img_response.status_code})')
            return

        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        with open(temp_path, 'wb') as f:
            f.write(img_response.content)

        logger.info(f"Image saved ({len(img_response.content)} bytes), connecting to printer...")

        # Loop to retry connection if the printer is offline
        while True:
            try:
                # Establish bluetooth connection automatically
                manage_bluetooth(connect=True)

                # Create a fresh printer instance and print
                printer = create_printer()
                printer.connect(PRINTER_MAC)

                logger.info("Connected! Sending to printer...")
                printer.print(temp_path)

                logger.success(f"Print complete for job {job_id[:8]}!")
                printer.disconnect()

                report_status(job_id, 'completed')
                break  # Success, exit the retry loop

            except Exception as e:
                error_msg = str(e)
                if printer:
                    try:
                        printer.disconnect()
                    except Exception:
                        pass
                
                # Check if it's a temporary error (e.g., printer is off)
                if any(err in error_msg for err in ["Failed to open", "Connection", "Battery", "Host is down", "Errno 112", "Errno 2", "No such file"]):
                    logger.warning(f"Printer offline or low battery ({error_msg}). Retrying in 20 seconds...")
                    manage_bluetooth(connect=False)
                    time.sleep(20)
                else:
                    # Fatal error (e.g. bad format)
                    logger.error(f"Fatal Print error: {error_msg}")
                    report_status(job_id, 'failed', error_msg)
                    break

    finally:
        manage_bluetooth(connect=False)
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def main():
    logger.info("=" * 50)
    logger.info("  WOWBOX Agent Starting")
    logger.info(f"  Server:  {SERVER_URL}")
    logger.info(f"  Printer: {PRINTER_MAC}")
    logger.info(f"  Poll:    every {POLL_INTERVAL}s")
    logger.info("=" * 50)

    while True:
        try:
            # Poll the server for new jobs
            response = requests.get(
                f"{SERVER_URL}/api/agent/next",
                headers={'X-Agent-Key': AGENT_KEY},
                timeout=15
            )

            if response.status_code != 200:
                logger.warning(f"Server returned HTTP {response.status_code}")
                time.sleep(POLL_INTERVAL)
                continue

            data = response.json()

            if not data.get('has_job'):
                # No pending jobs, wait and try again
                time.sleep(POLL_INTERVAL)
                continue

            job_id = data['id']
            filename = data['filename']
            original_name = data.get('original_name', filename)

            logger.info(f"New print job: {original_name} (ID: {job_id[:8]}...)")

            handle_print_job(job_id, filename)

            # Small delay between jobs
            time.sleep(2)

        except requests.ConnectionError:
            logger.warning("Cannot reach server. Retrying in 10 seconds...")
            time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Agent stopped by user.")
            break

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
