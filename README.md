# 🛡️ Linux Network Security Auditor

Automated tool to scan local network (Nmap) and maintain a persistent, versioned inventory of all connected devices (MAC, IP, Vendor) in a SQLite database.

This project implements a lightweight and automated solution to scan a local network, identify connected devices (IP, MAC, and vendor), and maintain a persistent inventory in a SQLite database. The entire process is managed by a Systemd user service to ensure autonomous and non-interactive execution upon system startup.

## 🚀 Key Features

* **Network Scanning (Nmap):** Uses `nmap -sn` for fast host discovery on the local IP range.
* **MAC Address Acquisition:** Requires `root` privileges (via `sudo`) to ensure successful ARP scanning and accurate MAC address retrieval, essential for device identification.
* **Persistent Data Storage:** Stores information (IP, MAC, Manufacturer, Timestamp) in an embedded **SQLite** database (`nmap_devices.db`).
* **UPSERT Logic:** The script uses an **UPSERT** (Update or Insert) mechanism to refresh information for existing devices and record new ones, tracking the `last_seen` timestamp.
* **Robust Automation:** A Systemd User Service launches the scan automatically shortly after the user session starts.

## ⚙️ Technologies Used

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Scanning** | Nmap | Network sweeping for host discovery. |
| **Logic/Parsing** | Python 3 | Orchestration, parsing Nmap output (Regex), and database management. |
| **Storage** | SQLite3 | Embedded database for persistent inventory tracking. |
| **Automation** | Systemd User Service | Ensures execution of the task upon user session start (common on modern Linux distributions). |
| **Permissions** | Sudoers (`NOPASSWD`) | Allows non-interactive execution of `Nmap` (which requires `root` privileges). |

## 💡 Technical Challenges Addressed

This project successfully overcame several common system integration challenges:

1.  **Privilege Management:** Resolving `sudo` password prompts in a non-interactive (Systemd) environment required precise configuration of the `NOPASSWD` rule in `/etc/sudoers.d/`.
2.  **Robust Parsing:** The Python script utilizes regular expressions to reliably analyze Nmap's variable output format and extract MAC/IP addresses.
3.  **Environment Issues:** Solving common path and execution errors encountered within the minimal environment context of a Systemd service (e.g., ensuring correct file permissions and absolute paths).

---

## 📥 Installation and Configuration Guide

### Prerequisites

* Nmap (`sudo dnf install nmap` or equivalent)
* Python 3.x
* A Linux distribution utilizing Systemd.

### 1. Clone the Repository

```bash
git clone [https://github.com/Virginie-9/Linux-Network-Security-Auditor.git](https://github.com/Virginie-9/Linux-Network-Security-Auditor.git)
cd Linux-Network-Security-Auditor
# The path used here is your project's absolute path.
```
### 2. Configure Scripts

The scripts use generic IP ranges. You must configure them to match your local network.

* **Modify Nmap Target:** Edit `nmap-startup.sh` and update the `NMAP_TARGET` variable with your local network IP range (e.g., `192.168.1.0/24`).

### 3. Configure Execution Permissions (Crucial Step)

To allow Nmap to retrieve MAC addresses without blocking the system for a password, you must configure a `NOPASSWD` rule for the shell script that executes it.

**CRITICAL ACTION:**

* Create a `sudoers` rule file (e.g., `/etc/sudoers.d/nmap-scan`) based on the provided `sudoers.d.example` file.

    ```bash
    # Use 'sudo visudo' to safely edit the sudoers file or a new file in /etc/sudoers.d/

    # Rule to be added (replace <YOUR_USERNAME> and the absolute path):
    # <YOUR_USERNAME> ALL=(root) NOPASSWD: /path/to/your/project/nmap-startup.sh
    ```

### 4. Configure and Enable the Systemd Service

1.  **Copy the service file:** Copy the example service file to your user's Systemd directory:

    ```bash
    mkdir -p ~/.config/systemd/user
    cp nmap-scan-startup.example.service ~/.config/systemd/user/nmap-scan-startup.service
    ```
2.  **Edit the Path:** Open the new service file (`nmap-scan-startup.service`) and replace all placeholder paths (`/home/utilisateur/mon-projet/...`) with the actual absolute path to your project folder (e.g., `/home/vmairesse/Linux-Network-Security-Auditor/`).
3.  **Enable the Service:**

    ```bash
    systemctl --user daemon-reload
    systemctl --user enable nmap-scan-startup.service
    ```

The service will run automatically after your next session login or can be manually started using `systemctl --user start nmap-scan-startup.service`.
