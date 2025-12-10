import os
import sqlite3
import re
from datetime import datetime
import subprocess

# --- CONFIGURATION (TO BE MODIFIED BY THE USER) ---
# Uses an environment variable (set in nmap-startup.sh) for the network range.
# Otherwise, uses a generic range (e.g., 192.168.1.0/24).
NMAP_RANGE = os.environ.get("NMAP_TARGET", "192.168.1.0/24")

DB_NAME = "nmap_devices.db"
SCAN_FILE = "scan_network.txt"
NMAP_CMD = "/usr/bin/nmap"
# ----------------------------------------------------

# Regular expressions for Nmap parsing 
RE_FULL = re.compile(r"Nmap scan report for (.+?) \(([\d\.]+)\)")
RE_IP_ONLY = re.compile(r"Nmap scan report for ([\d\.]+)")
RE_MAC = re.compile(r"MAC Address: ([0-9A-F:]+) \((.+?)\)") 

def setup_database():
    """Initializes the connection and creates the 'devices' table if it does not exist."""
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                mac_address TEXT PRIMARY KEY,
                ip_address TEXT,
                hostname TEXT,
                vendor TEXT,
                first_seen TEXT,
                last_seen TEXT
            );
        """)
        db.commit()
        return db, cursor
    except sqlite3.Error as e:
        print(f"[ERROR] Failed to connect/create DB: {e}")
        return None, None

def upsert_device(cursor, ip, host, mac, vendor):
    """Inserts or updates a device using the MAC as the primary key."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Attempt to insert (setting both first_seen and last_seen)
    try:
        cursor.execute("""
            INSERT INTO devices (mac_address, ip_address, hostname, vendor, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mac, ip, host, vendor, now, now))
    
    # 2. If a conflict occurs (MAC already exists), update ip, hostname, and last_seen
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE devices
            SET ip_address = ?, hostname = ?, last_seen = ?
            WHERE mac_address = ?
        """, (ip, host, now, mac))
    
def run_nmap_scan():
    """Executes the Nmap command and writes the output to SCAN_FILE."""
    command = f"{NMAP_CMD} -sn {NMAP_RANGE}"
    print(f"[INFO] Launching scan: {command}")
    
    try:
        # Executes the command and pipes output to the file
        # Note: The calling shell (Systemd) must execute this script with sudo for Nmap to get the MAC
        with open(SCAN_FILE, "w") as f:
            subprocess.run(command, shell=True, check=True, stdout=f, stderr=subprocess.PIPE)
        print("[INFO] Nmap scan completed successfully.")
    except subprocess.CalledProcessError as e:
        # Displays the Nmap error if check=True failed
        print(f"[ERROR] Nmap failed. Error output: {e.stderr.decode().strip()}")
        return False
    except Exception as e:
        print(f"[ERROR] Subprocess execution error: {e}")
        return False
    return True

def process_scan_file(db, cursor):
    """Analyzes the Nmap scan file and performs the UPSERT into the DB."""
    print(f"[INFO] Importing file: {SCAN_FILE}")
    
    try:
        with open(SCAN_FILE, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Scan file '{SCAN_FILE}' not found. Did Nmap succeed?")
        return

    current_ip = None
    current_host = None

    for line in content.splitlines():
        
        # 1. Look for IP and Hostname
        match_full = RE_FULL.search(line)
        match_ip_only = RE_IP_ONLY.search(line)

        if match_full:
            current_host = match_full.group(1).strip()
            current_ip = match_full.group(2)
        elif match_ip_only:
            current_host = None # No hostname found
            current_ip = match_ip_only.group(1)
        
        # 2. Look for MAC (triggers the UPSERT if the IP is known)
        match_mac = RE_MAC.search(line)
        
        if match_mac and current_ip:
            current_mac = match_mac.group(1).upper()
            current_vendor = match_mac.group(2).strip()

            # Insert/Update into DB
            upsert_device(cursor, current_ip, current_host, current_mac, current_vendor)
            
            # Reset for the next host
            current_ip = None
            current_host = None

    db.commit()
    print("[OK] Database updated.")

# --- Main entry point ---
if __name__ == "__main__":
    
    # 1. Attempt to execute Nmap
    if run_nmap_scan():
        # 2. If the scan succeeded, process the data
        db, cursor = setup_database()
        if db:
            process_scan_file(db, cursor)
            db.close()