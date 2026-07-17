import ollama

try:
    print("[*] Contacting local Ollama engine...")
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[
            {'role': 'system', 'content': 'You are a precise test utility. Respond with exactly one word: Pass.'},
            {'role': 'user', 'content': 'Run check.'}
        ]
    )
    print(f"[+] Local LLM Response: {response['message']['content']}")
except Exception as e:
    print(f"[-] Connection failed. Make sure the Ollama app is running in your system tray.\nError: {e}") 
