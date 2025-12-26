import os
import sys
import time
import random
import json
from playwright.sync_api import sync_playwright

# Constants
POST_FILE = "post.txt"
STATE_FILE = "state.json"
LINKEDIN_URL = "https://www.linkedin.com/feed/"

def random_sleep(min_seconds, max_seconds):
    sleep_time = random.uniform(min_seconds, max_seconds)
    print(f"Sleeping for {sleep_time:.2f}s...")
    time.sleep(sleep_time)

def type_like_human(page, selector, text):
    """Types text into a selector with variable delays between keystrokes."""
    page.focus(selector)
    for char in text:
        page.keyboard.type(char)
        # Random typing speed: 30ms to 100ms per key
        time.sleep(random.uniform(0.03, 0.1))

def main():
    # 1. Check for content
    if not os.path.exists(POST_FILE):
        print(f"Error: {POST_FILE} not found. Generate it first.")
        sys.exit(1)
    
    with open(POST_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    if not content:
        print("Error: Post content is empty.")
        sys.exit(1)

    # 2. Setup Authentication State
    # We expect the JSON state string in the env var LINKEDIN_STATE_JSON
    state_json_str = os.environ.get("LINKEDIN_STATE_JSON")
    
    # If not in env, check if file exists locally (for local testing)
    if not state_json_str and os.path.exists(STATE_FILE):
        print("Using local state.json file.")
    elif state_json_str:
        print("Using state from environment variable.")
        # Write to temporary file for Playwright
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(state_json_str)
    else:
        print("Error: No authentication state found. Set LINKEDIN_STATE_JSON or provide state.json.")
        sys.exit(1)

    # 3. Launch Browser
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True) # Set headless=False to debug visually
        
        try:
            context = browser.new_context(storage_state=STATE_FILE)
        except Exception as e:
            print(f"Error loading storage_state: {e}")
            print("Your cookie/state might be invalid or expired.")
            sys.exit(1)
            
        page = context.new_page()

        print(f"Navigating to {LINKEDIN_URL}...")
        page.goto(LINKEDIN_URL, timeout=60000)
        
        # LinkedIn never settles to networkidle due to background polling.
        # We wait for the "Start a post" button (or feed) to be visible instead.
        print("Waiting for feed to load...")
        try:
            # Wait for the "Start a post" button triggers
            page.wait_for_selector("button.share-box-feed-entry__trigger", timeout=60000)
        except Exception:
            print("Warning: explicit selector wait timed out, checking visibility anyway.")

        random_sleep(3, 6)
        
        random_sleep(2, 5)

        # Check login success by looking for the 'Start a post' button trigger or profile
        # "Start a post" button usually has text "Start a post" or similar class
        # We rely on text selector for robustness across class updates, though language specific.
        # Fallback to more generic selectors if possible.
        
        # Attempt to find the "Start a post" button. 
        # Selector strategy: Look for the button that opens the modal.
        start_post_btn = page.locator("button.share-box-feed-entry__trigger")
        
        if not start_post_btn.is_visible():
            print("Error: 'Start a post' button not found. You might not be logged in.")
            # Capture screenshot for debug
            page.screenshot(path="debug_login_fail.png")
            sys.exit(1)
            
        print("Logged in successfully. Clicking 'Start a post'...")
        start_post_btn.click()
        
        random_sleep(2, 4)
        
        # The input box in the modal. 
        # It's usually a div with role='textbox' inside the modal.
        editor = page.locator("div.ql-editor[role='textbox']")
        
        if not editor.is_visible():
            print("Error: Post editor not visible.")
            page.screenshot(path="debug_editor_fail.png")
            sys.exit(1)
            
        print("Typing content...")
        # We use fill or manual typing. Text is short so simple fill is okay, 
        # but typing is safer for anti-bot.
        type_like_human(page, "div.ql-editor[role='textbox']", content)
        
        random_sleep(2, 5)
        
        # Click Post
        # Button usually says "Post"
        post_button = page.locator("button.share-actions__primary-action")
        
        if not post_button.is_enabled():
            print("Error: Post button is disabled.")
            sys.exit(1)
            
        print("Clicking 'Post'...")
        post_button.click()
        
        # Wait for modal to disappear or success toast
        random_sleep(5, 8)
        
        print("Post submitted (assumed success).")
        # Optional: check for recent post in feed?
        # For now, we assume success if no error.
        
        browser.close()

if __name__ == "__main__":
    main()
