import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def read_prompt_file(folder_path):
    """Read prompt.md file from the given folder"""
    prompt_file = folder_path / "prompt.md"
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def call_openrouter_api(prompt, model_name):
    """Call OpenRouter API with the given prompt and model"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo",  # Optional
        "X-Title": "OneShot Code Generation"  # Optional
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def save_result(folder_path, model_name, content):
    """Save the generated content to a file"""
    # Clean model name for filename
    clean_model_name = model_name.replace("/", "-").replace(":", "-")
    output_file = folder_path / f"{clean_model_name}-generated.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Saved result to: {output_file}")

def main():
    # Models to test
    models = [
        "anthropic/claude-sonnet-4",
        "z-ai/glm-4.5"
    ]
    
    # Find all one-shot folders
    one_shot_dir = Path("../one-shot")
    if not one_shot_dir.exists():
        print("one-shot directory not found!")
        return
    
    folders = [f for f in one_shot_dir.iterdir() if f.is_dir()]
    
    for folder in folders:
        print(f"\nProcessing folder: {folder.name}")
        
        # Read prompt
        prompt = read_prompt_file(folder)
        if not prompt:
            print(f"No prompt.md found in {folder.name}")
            continue
        
        print(f"Found prompt: {prompt[:100]}...")
        
        # Generate results for each model
        for model in models:
            print(f"Generating with model: {model}")
            
            result = call_openrouter_api(prompt, model)
            if result:
                save_result(folder, model, result)
            else:
                print(f"Failed to generate result for {model}")

if __name__ == "__main__":
    main()
