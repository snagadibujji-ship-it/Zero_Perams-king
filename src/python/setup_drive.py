#!/usr/bin/env python3
"""
Google Drive Setup via Rclone — No Google Cloud project, no credit card.

Rclone has built-in Google API credentials, so you skip:
  - Google Cloud Console
  - Billing profile / credit card
  - OAuth client ID creation
  - Service account JSON files

This script:
  1. Checks if rclone is installed (installs if not)
  2. Checks if 'gdrive' remote is configured
  3. Guides headless authentication (paste URL in your browser)
  4. Tests the connection
  5. Lists available folders for training

Run this ONCE before using the vision training pipeline:
    python3 src/python/setup_drive.py
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# ═══ Paths ═══
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REMOTE_NAME = "gdrive"


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     Google Drive Setup via Rclone (No Credit Card!)          ║
║                                                              ║
║  Rclone uses its own built-in Google API keys.               ║
║  No Google Cloud project. No billing. No OAuth setup.        ║
║  Just authenticate with your Google account and go.          ║
╚══════════════════════════════════════════════════════════════╝
""")


def is_rclone_installed() -> bool:
    """Check if rclone is available on PATH."""
    return shutil.which("rclone") is not None


def install_rclone() -> bool:
    """Install rclone via the official installer script."""
    print("  [..] Installing rclone...")
    try:
        result = subprocess.run(
            ["bash", "-c", "curl -s https://rclone.org/install.sh | bash"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 or is_rclone_installed():
            print("  [OK] Rclone installed successfully")
            return True
        else:
            # Try alternative: direct binary download
            print("  [..] Trying alternative install method...")
            cmds = [
                "curl -O https://downloads.rclone.org/current/rclone-current-linux-amd64.zip",
                "unzip -o rclone-current-linux-amd64.zip",
                "cp rclone-*-linux-amd64/rclone /usr/local/bin/ 2>/dev/null || "
                "cp rclone-*-linux-amd64/rclone ~/.local/bin/",
                "chmod +x /usr/local/bin/rclone 2>/dev/null || "
                "chmod +x ~/.local/bin/rclone",
                "rm -rf rclone-*-linux-amd64*",
            ]
            for cmd in cmds:
                subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=60)
            
            if is_rclone_installed():
                print("  [OK] Rclone installed successfully")
                return True
            
            print("  [!] Failed to install rclone automatically.")
            print("      Install manually: https://rclone.org/install/")
            return False
    except Exception as e:
        print(f"  [!] Install failed: {e}")
        return False


def is_remote_configured() -> bool:
    """Check if the 'gdrive' remote is already configured."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            capture_output=True, text=True, timeout=10
        )
        return f"{REMOTE_NAME}:" in result.stdout
    except Exception:
        return False


def get_remote_info() -> dict:
    """Get info about the configured remote."""
    try:
        result = subprocess.run(
            ["rclone", "about", f"{REMOTE_NAME}:"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            info = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    info[key.strip()] = val.strip()
            return info
    except Exception:
        pass
    return {}



def configure_remote_interactive():
    """Guide user through rclone config for Google Drive (headless mode)."""
    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │  HEADLESS AUTHENTICATION GUIDE                                  │
  └─────────────────────────────────────────────────────────────────┘

  Since this environment doesn't have a desktop browser, we'll use
  rclone's headless mode. Here's what will happen:

  1. rclone config will start interactively
  2. Follow these prompts:
     • "n" for New remote
     • Name: "gdrive"
     • Storage type: type "drive" (for Google Drive)
     • Client ID: leave BLANK (press Enter — uses rclone's built-in keys)
     • Client Secret: leave BLANK (press Enter)
     • Scope: type "1" (full access)
     • Root folder ID: leave BLANK (press Enter)
     • Service account: leave BLANK (press Enter)
     • Advanced config: "n"
     • Auto config: "n" (IMPORTANT — headless mode)

  3. Rclone will print a long URL. Copy it and open in YOUR browser
     (on your computer/phone where your Google account is logged in)

  4. Allow access, then copy the verification code back here

  5. Team Drive: "n"
  6. Confirm: "y", then "q" to quit

  Starting rclone config now...
  ─────────────────────────────────────────────────────────────────
""")
    
    # Run rclone config interactively
    os.system("rclone config")
    
    # Check if it worked
    if is_remote_configured():
        print("\n  [OK] Remote 'gdrive' configured successfully!")
        return True
    else:
        print("\n  [!] Remote 'gdrive' not found after config.")
        print("      Try running: rclone config")
        return False


def configure_remote_scripted():
    """
    Create rclone config non-interactively (if token is already available).
    Useful for re-setup when token JSON is provided directly.
    """
    print("  [..] To configure non-interactively, provide your OAuth token JSON.")
    print("       (Get this by running 'rclone authorize drive' on a machine with a browser)\n")
    
    token = input("  Paste OAuth token JSON (or press Enter to use interactive mode): ").strip()
    
    if not token:
        return configure_remote_interactive()
    
    # Write rclone config directly
    rclone_config_dir = os.path.expanduser("~/.config/rclone")
    os.makedirs(rclone_config_dir, exist_ok=True)
    config_path = os.path.join(rclone_config_dir, "rclone.conf")
    
    config_content = f"""[{REMOTE_NAME}]
type = drive
scope = drive
token = {token}
"""
    
    # Append or create config
    with open(config_path, 'a') as f:
        f.write(config_content)
    
    if is_remote_configured():
        print("  [OK] Remote configured from token!")
        return True
    else:
        print("  [!] Configuration failed. Try interactive mode: rclone config")
        return False



def test_connection():
    """Test the Drive connection and show account info."""
    print("\n  [..] Testing connection to Google Drive...")
    
    # Get storage info
    info = get_remote_info()
    if info:
        print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  CONNECTION SUCCESSFUL                                          │
  └─────────────────────────────────────────────────────────────────┘

  Storage Info:""")
        for key, val in info.items():
            print(f"    {key:<12}: {val}")
    else:
        # Fallback: try listing root
        try:
            result = subprocess.run(
                ["rclone", "lsd", f"{REMOTE_NAME}:"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print("\n  [OK] Connection successful!")
            else:
                print(f"\n  [!] Connection failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"\n  [!] Connection test failed: {e}")
            return False
    
    # List top-level folders
    print("\n  Top-level Drive folders:")
    try:
        result = subprocess.run(
            ["rclone", "lsd", f"{REMOTE_NAME}:"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            folders = result.stdout.strip().split('\n')
            for folder in folders[:20]:
                if folder.strip():
                    # rclone lsd format: "    -1 2024-01-01 12:00:00  -1 FolderName"
                    parts = folder.strip().split()
                    if len(parts) >= 5:
                        name = ' '.join(parts[4:])
                        print(f"    📁 {name}")
                    else:
                        print(f"    📁 {folder.strip()}")
            if len(folders) > 20:
                print(f"    ... and {len(folders) - 20} more")
        else:
            print(f"    (Could not list: {result.stderr.strip()})")
    except Exception as e:
        print(f"    (Error: {e})")
    
    # Count images
    print("\n  [..] Scanning for images (checking first level)...")
    try:
        result = subprocess.run(
            ["rclone", "ls", f"{REMOTE_NAME}:", "--max-depth", "2",
             "--include", "*.jpg", "--include", "*.png", "--include", "*.webp",
             "--max-count", "1000"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            count = len(lines)
            print(f"  Found: {count}+ images (top 2 levels)")
        else:
            print("  (Could not count images)")
    except subprocess.TimeoutExpired:
        print("  (Scan timed out — you have a LOT of files! That's good.)")
    except Exception:
        print("  (Could not count images)")
    
    return True


def print_quickstart():
    """Print quickstart guide after successful setup."""
    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  QUICKSTART GUIDE                                               │
  └─────────────────────────────────────────────────────────────────┘

  Your 5TB Drive is connected! Here's how to use it:

  ─── Rclone CLI Commands ───

    # List folders
    rclone lsd {REMOTE_NAME}:

    # List images in a folder
    rclone ls {REMOTE_NAME}:MyPhotos/ --include "*.jpg"

    # Stream a URL directly to Drive (0 local disk usage)
    rclone copyurl "https://example.com/file.zip" {REMOTE_NAME}:Downloads/file.zip --progress

    # Download folder to local cache for training
    rclone copy {REMOTE_NAME}:TrainingImages/ ./user_data/image_cache/ --progress

    # Sync (mirror) a local folder to Drive
    rclone sync ./user_data/models/ {REMOTE_NAME}:AI_Models/ --progress

  ─── Python Training Pipeline ───

    from cloud_storage import RcloneDriveConnector
    from vision_trainer import quick_train

    connector = RcloneDriveConnector()

    # List folders
    folders = connector.list_folders()

    # Train on a folder (subfolders = categories)
    result = quick_train(connector, folder_path="TrainingImages",
                         model_name="my_classifier")

  ─── Full Pipeline ───

    from cloud_storage import RcloneDriveConnector
    from dataset_manager import DatasetManager
    from vision_trainer import VisionTrainer, TrainingConfig

    connector = RcloneDriveConnector()
    dm = DatasetManager()
    dm.create_dataset("animals")
    dm.auto_categorize_from_drive(connector, "animals", 
                                   folder_path="Animals")
    dm.generate_splits("animals")

    trainer = VisionTrainer()
    config = TrainingConfig(dataset_name="animals",
                            model_name="animal_v1", model_size="small")
    result = trainer.train(dm, connector, config)

  ─────────────────────────────────────────────────────────────────

  Folder structure for training (on your Drive):

    📁 TrainingImages/
    ├── 📁 cats/         ← category 1
    │   ├── img001.jpg
    │   └── ...
    ├── 📁 dogs/         ← category 2
    │   └── ...
    └── 📁 birds/        ← category 3
        └── ...
""")



def main():
    """Main setup flow."""
    print_banner()
    
    # Step 1: Check/install rclone
    print("  Step 1: Checking for rclone...")
    if is_rclone_installed():
        # Get version
        try:
            ver = subprocess.run(["rclone", "version"], capture_output=True, text=True, timeout=5)
            first_line = ver.stdout.strip().split('\n')[0] if ver.stdout else "unknown"
            print(f"  [OK] Rclone found: {first_line}")
        except Exception:
            print("  [OK] Rclone found")
    else:
        print("  [!] Rclone not installed.")
        response = input("  Install it now? (y/n) > ").strip().lower()
        if response in ('y', 'yes', ''):
            if not install_rclone():
                sys.exit(1)
        else:
            print("\n  Install rclone manually: https://rclone.org/install/")
            print("  Or run: curl https://rclone.org/install.sh | bash\n")
            sys.exit(1)
    
    # Step 2: Check if remote is configured
    print("\n  Step 2: Checking for 'gdrive' remote...")
    if is_remote_configured():
        print(f"  [OK] Remote '{REMOTE_NAME}' already configured!")
    else:
        print(f"  [!] Remote '{REMOTE_NAME}' not found.")
        print("\n  Choose setup method:")
        print("    1. Interactive (rclone config wizard)")
        print("    2. Paste token (if you have one from another machine)")
        
        choice = input("\n  Choice (1/2) > ").strip()
        if choice == "2":
            if not configure_remote_scripted():
                sys.exit(1)
        else:
            if not configure_remote_interactive():
                sys.exit(1)
    
    # Step 3: Test connection
    print("\n  Step 3: Testing connection...")
    if test_connection():
        print_quickstart()
        print("  [DONE] Setup complete! Your 5TB Drive is ready for training.\n")
    else:
        print("\n  Connection test failed. Try running: rclone config")
        sys.exit(1)


if __name__ == "__main__":
    main()
