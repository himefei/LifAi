import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict
from lifai.utils.ollama_client import OllamaClient
from lifai.config.prompts import improvement_options, llm_prompts
from lifai.utils.logger_utils import get_module_logger

logger = get_module_logger(__name__)

class TextImproverWindow:
    def __init__(self, settings: Dict, ollama_client: OllamaClient):
        logger.info("Initializing Text Improver Window")
        self.settings = settings
        self.ollama_client = ollama_client
        self.window = None
        self.selected_improvement = None

    def create_window(self):
        self.window = tk.Toplevel()
        self.window.title("Text Improver")
        self.window.geometry("600x600")
        
        # Prevent closing with X button (hide instead)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        self.selected_improvement = tk.StringVar(self.window)
        self.setup_ui()
        logger.info("Text Improver window created successfully")

    def process_text(self):
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            logger.warning("No text provided for processing")
            return

        logger.info("Processing text with Text Improver")
        self.status_label.config(text="Processing...")
        self.window.update()

        try:
            current_model = self.settings.get('model')
            if not current_model or not hasattr(current_model, 'get'):
                logger.error("Model settings not properly initialized")
                messagebox.showerror("Error", "Model not properly selected")
                return

            model_name = current_model.get()
            if not model_name:
                logger.error("No model selected")
                messagebox.showerror("Error", "Please select a model first")
                return

            improvement = self.selected_improvement.get()
            logger.debug(f"Selected improvement type: {improvement}")
            
            # Simple, clear prompt
            prompt = f"Please {improvement}:\n\n{text}"
            
            logger.debug("Sending request to Ollama")
            improved_text = self.ollama_client.generate_response(
                prompt=prompt,
                model=model_name
            )
            
            if improved_text:
                logger.info("Successfully improved text")
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, improved_text)
            else:
                logger.error("Failed to generate improved text")
                messagebox.showerror("Error", "Failed to generate improved text")
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.status_label.config(text="")

    def setup_ui(self):
        # Input area
        self.input_label = ttk.Label(self.window, text="Original Text:")
        self.input_label.pack(pady=5)
        self.input_text = tk.Text(self.window, height=10)
        self.input_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Output area
        self.output_label = ttk.Label(self.window, text="Improved Text:")
        self.output_label.pack(pady=5)
        self.output_text = tk.Text(self.window, height=10)
        self.output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Improvement selection
        self.improvement_label = ttk.Label(self.window, text="Select Improvement:")
        self.improvement_label.pack(pady=5)
        self.improvement_dropdown = ttk.Combobox(
            self.window,
            textvariable=self.selected_improvement,
            values=improvement_options,
            width=30
        )
        self.improvement_dropdown.pack(pady=5)
        self.improvement_dropdown.current(0)

        # Enhance button
        self.enhance_button = ttk.Button(
            self.window,
            text="Enhance",
            command=self.process_text
        )
        self.enhance_button.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self.window, text="")
        self.status_label.pack(pady=5)

    def process_text(self):
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            return

        self.status_label.config(text="Processing...")
        self.window.update()

        try:
            improvement = self.selected_improvement.get()
            prompt = llm_prompts.get(improvement, "Please improve this text:")
            prompt = prompt.format(text=text)
            
            improved_text = self.ollama_client.generate_response(
                prompt=prompt,
                model=self.settings['model'].get()
            )
            
            if improved_text:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, improved_text)
            else:
                messagebox.showerror("Error", "Failed to generate improved text")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.status_label.config(text="")

    def show(self):
        if not self.window:
            self.create_window()
        self.window.deiconify()

    def hide(self):
        if self.window:
            self.window.withdraw()