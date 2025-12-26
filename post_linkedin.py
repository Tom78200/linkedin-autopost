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
    state_json_str = os.environ.get("LINKEDIN_STATE_JSON")
    
    state = None
    if state_json_str:
        print("Using state from environment variable.")
        try:
            state = json.loads(state_json_str)
        except json.JSONDecodeError:
            print("Error: LINKEDIN_STATE_JSON is not valid JSON.")
            sys.exit(1)
    elif os.path.exists(STATE_FILE):
        print("Using local state.json file.")
        # Playwright accepts path string for local file, or dict for memory object
        state = STATE_FILE
    else:
        print("Error: No authentication state found. Set LINKEDIN_STATE_JSON.")
        sys.exit(1)

    # 3. Launch Browser
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        
        try:
            # storage_state accepts path (str) or full state object (dict)
            context = browser.new_context(storage_state=state)
        except Exception as e:
            print(f"Error loading storage_state: {e}")
            sys.exit(1)
            
        page = context.new_page()

        print(f"Navigating to {LINKEDIN_URL}...")
        page.goto(LINKEDIN_URL, timeout=60000)
        
        print(f"Current URL after navigation: {page.url}")
        
        if "login" in page.url or "checkpoint" in page.url or "auth" in page.url:
            print("\n" + "="*50)
            print("❌ ERROR: SESSION INVALID")
            print("LinkedIn redirected you to a login or security checkpoint page.")
            print("This means your LINKEDIN_STATE_JSON cookies are expired or rejected by LinkedIn.")
            print("👉 ACTION: You must regenerate your cookies using 'get_linkedin_cookies.py' locally and update the GitHub Secret.")
            print("="*50 + "\n")
            page.screenshot(path="debug_redirect.png")
            sys.exit(1)
        
        print("Waiting for feed/post button...")
        try:
            # Robust selector: Text-based (English + French)
            page.wait_for_selector(
                "button:has-text('Start a post'), button:has-text('Commencer un post')", 
                timeout=60000
            )
        except Exception:
            print("timeout waiting for button, dumping debug screenshot")
            page.screenshot(path="debug_home.png")
            raise

        random_sleep(3, 6)
            
        print("Clicking 'Start a post'...")
        page.click("button:has-text('Start a post'), button:has-text('Commencer un post')")
        
        random_sleep(2, 4)
        
        print("Typing content...")
        # Check for editor validity
        page.wait_for_selector("div.ql-editor[role='textbox']", state="visible")
        type_like_human(page, "div.ql-editor[role='textbox']", content)
        
        random_sleep(2, 5)
        
        print("Clicking 'Post'...")
        page.click("button:has-text('Post'), button:has-text('Publier')")
        
        # Wait for modal to disappear or success toast
        random_sleep(5, 8)
        
        print("Post submitted (assumed success).")
        # Optional: check for recent post in feed?
        # For now, we assume success if no error.
        
        browser.close()

if __name__ == "__main__":
    main()
