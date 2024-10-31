import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import pyperclip
import requests
import json
import threading
import logging
import time
from pynput import mouse
from improvement_options import improvement_options
from llm_prompts import llm_prompts
from floating_toolbar import FloatingToolbar
import win32clipboard
import win32api

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class TextCheckerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Checker")
        self.root.geometry("600x600")

        # Ollama API endpoint
        self.base_url = "http://localhost:11434/api"
        self.generate_url = f"{self.base_url}/generate"
        self.tags_url = f"{self.base_url}/tags"

        # Model selection
        self.selected_model = tk.StringVar(self.root)
        self.selected_improvement = tk.StringVar(self.root)

        # UI elements
        self.setup_ui()

        # Floating toolbar
        self.toolbar = FloatingToolbar(self.root, self.process_selected_text)
        self.setup_mouse_listener()

    def setup_ui(self):
        # Input/Output
        self.input_label = ttk.Label(self.root, text="Original Text:")
        self.input_label.pack(pady=5)
        self.input_text = tk.Text(self.root, height=10)
        self.input_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.output_label = ttk.Label(self.root, text="Improved Text:")
        self.output_label.pack(pady=5)
        self.output_text = tk.Text(self.root, height=10)
        self.output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Model selection
        self.fetch_models()
        self.model_label = ttk.Label(self.root, text="Select Model:")
        self.model_label.pack(pady=5)
        self.model_dropdown = ttk.Combobox(self.root, textvariable=self.selected_model, values=self.model_options)
        self.model_dropdown.pack(pady=5)
        if self.model_options:
            self.model_dropdown.current(0)

        # Improvement selection
        self.improvement_label = ttk.Label(self.root, text="Select Improvement:")
        self.improvement_label.pack(pady=5)
        self.improvement_dropdown = ttk.Combobox(self.root, textvariable=self.selected_improvement, values=improvement_options)
        self.improvement_dropdown.pack(pady=5)
        self.improvement_dropdown.current(0)

        # Check button
        self.check_button = ttk.Button(self.root, text="Check Text", command=self.check_text)
        self.check_button.pack(pady=10)
        self.status_label = ttk.Label(self.root, text="")
        self.status_label.pack(pady=5)

        self.root.update_idletasks()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Toolbar.TButton', padding=6, relief='flat', background='#ffffff')

    def setup_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if button == mouse.Button.right and pressed:
                self.check_selection(x, y)
        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def check_selection(self, x, y):
        prev_clipboard = pyperclip.paste()
        keyboard.send('ctrl+c')
        time.sleep(0.1)
        selected_text = pyperclip.paste()
        pyperclip.copy(prev_clipboard)
        if selected_text.strip():
            self.toolbar.geometry(f"+{x+10}+{y+10}")
            self.toolbar.deiconify()
            self.toolbar.lift()

    def check_text(self):
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            return
        self.process_text(text)

    def process_text(self, text):
        try:
            improvement = self.selected_improvement.get()
            prompt = llm_prompts.get(improvement, "Please improve this text:")
            prompt = prompt.format(text=text)
            payload = {
                "model": self.selected_model.get(),
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.generate_url, json=payload)
            if response.status_code == 200:
                improved_text = response.json()["response"]
                self.update_output(improved_text)
            else:
                self.show_error(f"Ollama API error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.show_error(f"Could not connect to Ollama: {e}")
        except Exception as e:
            self.show_error(f"An unexpected error occurred: {e}")

    def update_output(self, text):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)

    def show_error(self, message):
        self.status_label.config(text=message)
        messagebox.showerror("Error", message)

    def process_selected_text(self, mode="improve"):
        try:
            prev_clipboard = pyperclip.paste()
            keyboard.send('ctrl+c')
            time.sleep(0.1)
            selected_text = pyperclip.paste()
            pyperclip.copy(prev_clipboard)
            if not selected_text.strip():
                return
            if mode == "improve":
                prompt = f"""Please improve the following text while maintaining its original meaning.
                            Make it more clear and professional, but keep the same tone:
                            
                            {selected_text}"""
            else:
                prompt = f"""Please fix any grammar and spelling errors in the following text,
                            while keeping the original meaning and tone intact:
                            
                            {selected_text}"""
            payload = {
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.generate_url, json=payload)
            if response.status_code == 200:
                improved_text = response.json()["response"].strip()
                pyperclip.copy(improved_text)
                keyboard.send('ctrl+v')
                time.sleep(0.1)
                pyperclip.copy(prev_clipboard)
            else:
                messagebox.showerror("Error", f"Ollama API error: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Error processing text: {e}")

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

app = TextCheckerApp()
app.run()
