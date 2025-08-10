import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import argparse

# Load environment variables
load_dotenv()

# Provider selection (env overrideable via CLI)
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# API endpoints
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openai_api(prompt, model_name, folder_name=None):
    """Call OpenAI official API with the given prompt and model (HTTP)."""
    thread_id = threading.current_thread().ident
    if folder_name:
        print(f"[Thread {thread_id}] Generating {folder_name} with model: {model_name} (openai)")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "OPENAI_API_KEY not found in environment variables"
        if folder_name:
            print(f"[Thread {thread_id}] Error for {folder_name} with {model_name}: {msg}")
        else:
            print(f"[Thread {thread_id}] {msg}")
        return None

    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = base.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        end_time = time.time()

        result = response.json()['choices'][0]['message']['content']
        if folder_name:
            print(f"[Thread {thread_id}] Completed {folder_name} with {model_name} in {end_time - start_time:.2f}s")
        return result
    except Exception as e:
        if folder_name:
            print(f"[Thread {thread_id}] Error for {folder_name} with {model_name}: {e}")
        else:
            print(f"[Thread {thread_id}] Error calling OpenAI API: {e}")
        return None

def read_prompt_file(folder_path, file_path=None):
    """Read a prompt file from the given folder.

    If file_path is provided, read that file; otherwise read 'prompt.md'.
    """
    if file_path is not None:
        prompt_file = Path(file_path)
    else:
        prompt_file = folder_path / "prompt.md"

    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def call_openrouter_api(prompt, model_name, folder_name=None):
    """Call OpenRouter API with the given prompt and model"""
    thread_id = threading.current_thread().ident
    if folder_name:
        print(f"[Thread {thread_id}] Generating {folder_name} with model: {model_name}")

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        msg = "OPENROUTER_API_KEY not found in environment variables"
        if folder_name:
            print(f"[Thread {thread_id}] Error for {folder_name} with {model_name}: {msg}")
        else:
            print(f"[Thread {thread_id}] {msg}")
        return None

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
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
        start_time = time.time()
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        end_time = time.time()

        result = response.json()['choices'][0]['message']['content']
        if folder_name:
            print(f"[Thread {thread_id}] Completed {folder_name} with {model_name} in {end_time - start_time:.2f}s")
        return result
    except Exception as e:
        if folder_name:
            print(f"[Thread {thread_id}] Error for {folder_name} with {model_name}: {e}")
        else:
            print(f"[Thread {thread_id}] Error calling API: {e}")
        return None

def save_result(folder_path, model_name, content):
    """Save the generated content to a file"""
    thread_id = threading.current_thread().ident

    # Clean model name for filename
    clean_model_name = model_name.replace("/", "-").replace(":", "-")

    # Check if folder name starts with "python" to determine file extension
    folder_name = folder_path.name.lower()
    if folder_name.startswith("python"):
        file_extension = ".py"
    else:
        file_extension = ".html"

    output_file = folder_path / f"{clean_model_name}{file_extension}"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[Thread {thread_id}] Saved result to: {output_file}")

def process_folder_model_combination(folder, model, prompt, provider):
    """Process a single folder-model combination"""
    folder_name = folder.name

    if provider == "openai":
        result = call_openai_api(prompt, model, folder_name)
    elif provider == "openrouter":
        result = call_openrouter_api(prompt, model, folder_name)
    else:
        print(f"[Thread {threading.current_thread().ident}] Unknown provider: {provider}")
        result = None
    if result:
        save_result(folder, model, result)
        return f"Success: {folder_name} + {model}"
    else:
        return f"Failed: {folder_name} + {model}"

def main():
    parser = argparse.ArgumentParser(description="Generate one-shot results using LLM providers")
    parser.add_argument("--provider", choices=["openrouter", "openai"], default=DEFAULT_PROVIDER, help="LLM provider to use")
    parser.add_argument("--folder", type=str, help="Only process this folder under one-shot")
    parser.add_argument("-f", "--file", type=str, help="Only process this file inside the folder (relative to the folder or absolute path)")
    args = parser.parse_args()

    provider = args.provider
    print(f"Using provider: {provider}")

    # Models to test
    models = [
        # "anthropic/claude-sonnet-4",
        # "z-ai/glm-4.5-air:free",
        # "moonshotai/kimi-k2:free",
        # "qwen/qwen3-coder:free",
        # "openrouter/horizon-alpha"
        # "openrouter/horizon-beta"
        "gpt-5"
    ]

    # Find all one-shot folders
    one_shot_dir = Path("../one-shot")
    if not one_shot_dir.exists():
        print("one-shot directory not found!")
        return

    # If a specific folder is provided, only process that folder
    if args.folder:
        target_folder = one_shot_dir / args.folder
        if not target_folder.exists() or not target_folder.is_dir():
            print(f"Specified folder not found: {target_folder}")
            return
        folders = [target_folder]
    else:
        folders = [f for f in one_shot_dir.iterdir() if f.is_dir()]

    # Prepare all tasks (folder-model combinations)
    tasks = []
    for folder in folders:
        print(f"Preparing folder: {folder.name}")

        # Resolve prompt file (default to 'prompt.md', or a specific file if provided)
        prompt_file_path = None
        if args.file:
            # Absolute path or path relative to the folder
            prompt_file_path = Path(args.file) if os.path.isabs(args.file) else (folder / args.file)

        # Read prompt
        prompt = read_prompt_file(folder, prompt_file_path)
        if not prompt:
            missing = str(prompt_file_path) if prompt_file_path else "prompt.md"
            print(f"No prompt file found in {folder.name}: {missing}")
            continue

        print(f"Found prompt: {prompt[:100]}...")

        # Add all model combinations for this folder
        for model in models:
            tasks.append((folder, model, prompt))

    num_workers = min(8, len(tasks))
    print(f"\nTotal tasks to process: {len(tasks)}")
    print(f"Using {num_workers} threads for parallel processing...")

    if num_workers == 0:
        print("No tasks to process. Exiting.")
        return

    # Process all tasks in parallel
    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(process_folder_model_combination, folder, model, prompt, provider): (folder.name, model)
            for folder, model, prompt in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            folder_name, model = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                error_msg = f"Failed: {folder_name} + {model} generated an exception: {exc}"
                print(f"[ERROR] {error_msg}")
                results.append(error_msg)

    end_time = time.time()

    # Print summary
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Total tasks: {len(tasks)}")
    print(f"Success rate: {len([r for r in results if r.startswith('Success')])}/{len(results)}")
    print(f"\nResults summary:")
    for result in results:
        print(f"  {result}")

if __name__ == "__main__":
    main()
