@echo off
REM Launch Chrome with CDP debugging for quiz automation (separate profile, runs alongside normal Chrome)
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=D:\Du_an_mini\auto_tich\chrome_debug_profile --no-first-run --no-default-browser-check https://anthropic.skilljar.com/
