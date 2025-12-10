#!/bin/bash

# Detects the script directory for portability (resolves symlinks)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" 

# --- CONFIGURATION (TO BE MODIFIED BY THE USER) ---
# This target must match the local network for ARP/MAC scanning.
NMAP_TARGET="192.168.1.0/24" 
# ----------------------------------------------------

NMAP_FILE="$SCRIPT_DIR/scan_network.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/import_nmap.py" 

# 1. Launch Nmap (requires sudo) and overwrite the scan file
# IMPORTANT: The Nmap command must be launched with SUDO to get MAC addresses.
/usr/bin/sudo /usr/bin/nmap -sn "$NMAP_TARGET" > "$NMAP_FILE"

# 2. Execute the Python script
# Note: We export NMAP_TARGET via an environment variable for the Python script
export NMAP_TARGET="$NMAP_TARGET"
/usr/bin/python3 "$PYTHON_SCRIPT"

exit 0