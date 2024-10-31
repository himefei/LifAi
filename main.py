import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import requests
import json
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class TextCheckerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Checker")
        self.root.geometry("600x600") # Set initial window size

        # Hotkey combination
        self.hotkey = "ctrl+shift+space"

        # Ollama API endpoints
        self.ollama_url = "http://localhost:11434/api/generate"
        self.tags_url = "http://localhost:11434/api/tags"

        # Model selection
        self.selected_model = tk.StringVar(self.root)

        # Configure main window
        self.setup_ui()
        
        # Register hotkey
        keyboard.add_hotkey(self.hotkey, self.check_clipboard)
        
    def setup_ui(self):
        # Input text area
        self.input_label = ttk.Label(self.root, text="Original Text:")
        self.input_label.pack(pady=5)
        
        self.input_text = tk.Text(self.root, height=6)
        self.input_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Output text area
        self.output_label = ttk.Label(self.root, text="Improved Text:")
        self.output_label.pack(pady=5)
        
        self.output_text = tk.Text(self.root, height=6)
        self.output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Model selection dropdown
        self.fetch_models() #Fetch models on startup

        self.model_label = ttk.Label(self.root, text="Select Model:")
        self.model_label.pack(pady=5)

        # Determine optimal width for combobox
        max_width = 0
        for model in self.model_options:
            max_width = max(max_width, len(model))
        optimal_width = max_width * 8  # Adjust multiplier as needed

        self.model_dropdown = ttk.Combobox(self.root, textvariable=self.selected_model, values=self.model_options, width=optimal_width)
        self.model_dropdown.pack(pady=5)
        if self.model_options:
            self.model_dropdown.current(0) #Set default model

        # Check button
        self.check_button = ttk.Button(self.root, text="Check Text", command=self.check_text)
        self.check_button.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(self.root, text=f"Press {self.hotkey} anywhere to check clipboard text")
        self.status_label.pack(pady=5)

        # Resize window to fit content
        self.root.update_idletasks()
        #self.root.geometry("") # Reset geometry to let Tkinter manage it automatically

    def check_clipboard(self):
        # Get text from clipboard
        text = pyperclip.paste()
        if text:
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(tk.END, text)
            self.check_text()

    def check_text(self):
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            return
            
        self.status_label.config(text="Checking text...")
        
        # Run the check in a separate thread to avoid freezing UI
        threading.Thread(target=self.process_text, args=(text,), daemon=True).start()

    def process_text(self, text):
        try:
            prompt = f"""Please check the following text for spelling and grammar errors, 
                        and suggest improvements while maintaining the original meaning:
                        
                        {text}"""
            
            payload = {
                "model": self.selected_model.get(),
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            if response.status_code == 200:
                improved_text = response.json()["response"]
                
                # Update UI in the main thread
                self.root.after(0, self.update_output, improved_text)
                self.root.after(0, self.status_label.config, {"text": f"Press {self.hotkey} anywhere to check clipboard text"})
            else:
                self.root.after(0, self.status_label.config, {"text": f"Error: Ollama API request failed with status code {response.status_code}"})
                logging.error(f"Ollama API request failed with status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.root.after(0, self.status_label.config, {"text": f"Error: Could not connect to Ollama: {e}"})
            logging.error(f"Could not connect to Ollama: {e}")
        except Exception as e:
            self.root.after(0, self.status_label.config, {"text": f"Error: {str(e)}"})
            logging.exception(f"An unexpected error occurred: {e}")

    def update_output(self, text):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)

    def fetch_models(self):
        try:
            response = requests.get(self.tags_url)
            response.raise_for_status()
            data = response.json()
            if "models" in data:
                self.model_options = [model["model"] for model in data["models"]]
            else:
                logging.error(f"Unexpected response from Ollama API: {data}")
                self.model_options = ["llama2"]  # Fallback
        except requests.exceptions.RequestException as e:
            self.model_options = ["llama2"]  # Fallback
            logging.error(f"Error fetching models: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TextCheckerApp()
    app.run()
