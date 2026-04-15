# 🖨️ WOWBOX - Remote Printing Platform

WOWBOX is a modern, fully-automated cloud platform designed to send photos from a smartphone directly to a Canon Ivy 2 Bluetooth printer from anywhere in the world. 

The system bridges the gap between web applications and low-level hardware communication using a persistent Raspberry Pi agent and a cloud-hosted Flask API.

![WOWBOX Architecture](https://img.shields.io/badge/Architecture-Cloud%20to%20Hardware-blue)
![Python](https://img.shields.io/badge/Python-3.13-yellow)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green)

---

## 🌟 Key Features

* **Global Access:** Upload photos from any device, anywhere in the world, over the internet.
* **Responsive UI:** A premium, dark-mode web interface tailored perfectly for mobile devices (RTL support, drag-and-drop, and live previews).
* **Live Status:** Real-time printing queue and status tracking (Pending -> Printing -> Completed).
* **Automated Hardware Agent:** A custom-built agent running as a highly-privileged `systemd` service on a Raspberry Pi, meaning it is 100% self-healing, automatic, and handles hardware Bluetooth sockets (`/dev/rfcomm0`) gracefully.
* **Security:** Password-protected web interface & authenticated server-agent API keys.

---

## 🏗️ Architecture

The platform acts as a non-destructive outer layer on top of the original `ivy2.py` API. It is divided into two parts:

### 1. Cloud Server (`/server`)
A Python Flask application (designed to be deployed on platforms like Render or Railway).
* Exposes a Web UI for users to upload and queue prints.
* Exposes an API for the Agent to fetch pending jobs.
* Uses SQLite to manage print queuing and persistence.

### 2. Raspberry Pi Agent (`/agent`)
A Python Daemon tracking the cloud server.
* Connects via API to pull the next available print job.
* Silently orchestrates the low-level `rfcomm` socket connection to the physical MAC address of the Canon Ivy 2 printer.
* Sends the binary photo data over Bluetooth and reports the status back to the cloud.

---

## 🛠️ Tech Stack & Requirements

* **Cloud Server:** Flask, Gunicorn, Vanilla HTML/CSS/JS (Lightweight, No modern frameworks needed to keep it lightning-fast).
* **Pi Agent:** Python `requests`, `subprocess`, `loguru`.
* **Hardware:** Raspberry Pi (running Raspberry Pi OS/Linux) and Canon Ivy 2 Printer.

---

## 🚀 Setup & Deployment

### ☁️ Cloud Server Setup
1. Clone the project.
2. Enter the `server/` directory and install dependencies: `pip install -r requirements.txt`.
3. Set your environment variables:
   * `WOWBOX_PASSWORD`: The password for the Web UI.
   * `AGENT_KEY`: A shared secret between the Server and the Pi.
   * `SECRET_KEY`: Flask Session key.
4. Deploy using the provided `Procfile` (e.g., `gunicorn app:app --bind 0.0.0.0:$PORT`).

### 🍓 Raspberry Pi Setup
1. Transfer the `agent/` folder to your Raspberry Pi.
2. Update `config.py` with your server's URL, the shared `AGENT_KEY`, and the printer's MAC address.
3. Install the provided Systemd Service (`wowbox-agent.service`). The service manages running as `root` (to create sockets) and restarts on its own in case of failure.

---

## 🧙‍♂️ How It Works (The Workflow)

1. Turn on the physical printer.
2. Go to the web app (`https://wowbox.onrender.com` or local equivalent) and enter your password.
3. Select an image and hit **"שלח להדפסה"** (Send to Print).
4. The Raspberry Pi automatically detects the new file, hooks into the Bluetooth stack, connects to the Canon Ivy, and prints it immediately.

---

*Built with ❤️ for remote, seamless memories.*
