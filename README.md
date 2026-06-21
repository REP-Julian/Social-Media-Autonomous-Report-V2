# Social-Media-Autonomous-Report-V2
SMAR is an autonomous desktop/web-automation application designed to report abusive, malicious, or impersonator profiles across multiple social media platforms. It features a Python/Playwright automation backend and a modern React (Vite + TypeScript) frontend, allowing users to configure, launch, and monitor automated reporting tasks in real-time.

# SMAR (Social Media Autonomous Report)

SMAR is a modern desktop automation suite designed to streamline and automate the process of reporting malicious, abusive, or impersonator profiles across multiple social media platforms. Built with a Python/Playwright backend and a React/TypeScript frontend, SMAR handles authentication, session persistence, and multi-platform automation workflows in real-time.

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

## 🚀 Potential & Extensibility Paths

* **🛡️ Brand Protection & Anti-Scam:** Deployable as an enterprise utility to defend against corporate copyright infringement, trademark violations, and brand phishing scams.
* **⚡ Proxy & Multi-Account Rotation:** Extensible to support session pools and proxies, allowing users to rotate accounts dynamically and submit multiple reports simultaneously to amplify rate limits.
* **🧠 AI-Driven Auditing:** Integrate visual or textual LLMs (e.g., Gemini) to scan a target profile's posts first, programmatically audit whether the content violates guidelines, and dynamically select the correct reporting policy.
* **📈 Analytics & Takedown Tracking:** Connect a persistent database (SQLite or PostgreSQL) to track success rates, logs, and account statuses, producing actionable moderation metrics.
