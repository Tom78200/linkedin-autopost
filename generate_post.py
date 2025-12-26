import os
import random
import sys
from groq import Groq

# Constants
IDEAS_FILE = "ideas/web3.txt"
PROMPT_FILE = "prompt.txt"
OUTPUT_FILE = "post.txt"
MODEL_NAME = "llama-3.3-70b-versatile"

def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not found.")
        sys.exit(1)

    # 1. Load Ideas
    try:
        with open(IDEAS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            print(f"Error: {IDEAS_FILE} is empty.")
            sys.exit(1)
            
        topic = random.choice(lines)
        print(f"Selected Topic: {topic}")

    except FileNotFoundError:
        print(f"Error: Could not find {IDEAS_FILE}")
        sys.exit(1)

    # 2. Load Prompt
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Could not find {PROMPT_FILE}")
        sys.exit(1)

    # 3. Call API
    client = Groq(api_key=api_key)
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Sujet : {topic}"}
            ],
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            stop=None,
            stream=False
        )

        content = completion.choices[0].message.content.strip()
        
        # Simple cleanup if the model outputs quotes
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
            
        print("--- Generated Post ---")
        print(content)
        print("----------------------")

        # 4. Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Success: Post saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
