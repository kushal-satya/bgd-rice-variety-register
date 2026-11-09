"""Run scripts/rebuild_all.sh with Git Bash; used to start a full rebuild as an independent process:
    powershell -ExecutionPolicy Bypass -File scripts\run_detached.ps1 -Name rebuild scripts\run_rebuild.py"""
import os, pathlib, shutil, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
bash = shutil.which("bash") or os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe")
sys.exit(subprocess.run([bash, "scripts/rebuild_all.sh"], cwd=root).returncode)
