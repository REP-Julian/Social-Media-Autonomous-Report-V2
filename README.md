# SMAR (Social-Media-Autonomous-Report) 🛡️

SMAR is a modern desktop automation suite designed to streamline and automate the process of reporting malicious, abusive, or impersonator profiles across multiple social media platforms. Built with a robust Python/Playwright backend and a sleek, real-time React/TypeScript frontend, SMAR handles authentication, session persistence, and multi-platform automation workflows.

---

## ⚠️ Important Disclaimer & Best Practices

> [!WARNING]
> **Use Alternate Accounts (Burners):** Always run this automation using dedicated dump/alternate accounts. Running repeated automated reporting sequences from your main account can lead to your account being suspended or restricted by social media platforms for spamming.

---

## 🔑 Key Features & Session Persistence

* **💾 Local Profile Storage:** To avoid logging in manually every time you launch an automation sequence, the backend creates local Chrome profile directories (such as `./facebook_chrome_profile`, `./chrome_profile`, etc.).
* **🔐 Persistent Login:** Once you log in successfully during your first run on any platform, your session data and cookies are stored securely inside these profiles. Subsequent runs will bypass the login page and navigate straight to the target profiles.

---

## 🏗️ Core Technical Architecture

### 🎨 Frontend UI (`src/App.tsx`)
* **Modern Aesthetic:** Built with a dark glassmorphism layout, featuring rich gradient glows, custom SVGs for platform brand icons, and dynamic status indicator micro-animations.
* **Event Streaming (SSE):** Subscribes to the backend event stream `/api/events` to dynamically refresh execution logs, progress tracking, and sequence state without browser-polling.
* **Interactive Authentication:** Intercepts automation status updates to alert the user when a manual login is required, prompting resumption once the user clicks "Confirm Logged In".

### 🌐 Flask Web Server (`backend.py`)
* **Control Endpoints:** Exposes REST API routes including `/api/start` to run automation tasks, `/api/stop` to abort runs, `/api/confirm-login` to resume after login verification, and `/api/events` for the SSE stream.
* **Multi-Threaded Execution:** Coordinates execution safely across background execution threads using Python's `threading.Thread` and thread-safe queues.

### 🤖 Playwright Automation Engine (`backend.py`)
* **Session Persistence:** Launches local Chrome instances via Playwright's `launch_persistent_context` to retain cookies and login sessions under specific platform profile folders (e.g., `./facebook_chrome_profile`).
* **Anti-Detection Configurations:** Sets anti-detection arguments such as `--disable-blink-features=AutomationControlled` to minimize platform bot-detection triggers.
* **Platform Workflows:**
  * **Facebook:** Navigates, expands action menus, and files reports under "Bullying or harassment".
  * **Instagram:** Automates report menus to flag accounts violating community guidelines.
  * **Threads:** Executes target selector logic to file reports under platform violation categories.
  * **TikTok:** Triggers reports for policy violations using anti-detection browser flags.
  * **Twitter / X:** Simulates menu navigation to file reports under "Hate, Abuse, or Harassment".

---

## 🚀 How to Run the Application

Follow the steps below to set up and run both the backend server and frontend dashboard.

### 1. Prerequisites
Before setting up the project, make sure your machine has:
* [Node.js](https://nodejs.org/) (for the React frontend)
* [Python 3](https://www.python.org/) (for the Flask backend)
* **Google Chrome browser** installed locally (the backend uses the host Chrome channel `channel='chrome'` to run Playwright).

### 2. Backend Setup & Run
Open a terminal in the project root directory:

```bash
# Install Python dependencies
pip install flask flask-cors colorama playwright

# Install browser binaries required by Playwright
playwright install chromium

# Start the Flask API server
python backend.py --server
```
The backend server will spin up on **`http://localhost:5000`**.

### 3. Frontend Setup & Run
Open a second terminal window in the project root directory:

```bash
# Install Node dependencies
npm install

# Start the React/Vite development server
npm run dev
```
The frontend interface will spin up (usually on **`http://localhost:5173`**). Click the terminal link to launch the dashboard!

---

## 📈 Future Potential & Extensibility

* **🛡️ Brand Protection & Anti-Scam:** Deployable as an enterprise utility to defend against corporate copyright infringement, trademark violations, and brand phishing scams.
* **⚡ Proxy & Multi-Account Rotation:** Extensible to support session pools and proxies, allowing users to rotate accounts dynamically and submit multiple reports simultaneously to amplify rate limits.
* **🧠 AI-Driven Auditing:** Integrate visual or textual LLMs (e.g., Gemini) to scan a target profile's posts first, programmatically audit whether the content violates guidelines, and dynamically select the correct reporting policy.
* **📊 Analytics & Takedown Tracking:** Connect a database (SQLite or PostgreSQL) to track success rates, logs, and account statuses, producing actionable moderation metrics.
