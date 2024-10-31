import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable
from pynput import mouse
from lifai.utils.ollama_client import OllamaClient
from lifai.utils.clipboard_utils import ClipboardManager
from lifai.utils.logger_utils import get_module_logger
from lifai.config.prompts import improvement_options, llm_prompts
import time
import threading
import keyboard

logger = get_module_logger(__name__)

class FloatingToolbar(tk.Toplevel):
    def __init__(self, callback: Callable, clipboard: ClipboardManager):
        super().__init__()
        self.callback = callback
        self.clipboard = clipboard
        self.setup_window()
        self.setup_ui()
        
        # Variables for dragging
        self.drag_data = {"x": 0, "y": 0}
        self.waiting_for_selection = False
        self.mouse_listener = None
    
    def setup_window(self):
        self.title("✨ Text Enhancer")
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        # Make window draggable
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)
        
    def setup_ui(self):
        # Main frame with border and padding
        self.main_frame = ttk.Frame(self, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create dropdown using existing improvement_options
        self.selected_prompt = tk.StringVar()
        self.prompt_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.selected_prompt,
            values=improvement_options,
            state='readonly',
            width=25
        )
        self.prompt_combo.pack(padx=3, pady=3)
        self.prompt_combo.set(improvement_options[0])
        
        # Create enhance button
        self.enhance_btn = ttk.Button(
            self.main_frame,
            text="✨ Select & Enhance",
            width=20,
            command=self.start_enhancement
        )
        self.enhance_btn.pack(padx=3, pady=3)
        
        # Add minimize button
        self.min_btn = ttk.Button(
            self.main_frame,
            text="−",
            width=3,
            command=self.minimize_toolbar
        )
        self.min_btn.pack(side=tk.RIGHT, padx=(3,0))
        
    def start_drag(self, event):
        """Begin drag of the window"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        """Handle window drag"""
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")
        
    def minimize_toolbar(self):
        """Minimize to a small floating button"""
        self.withdraw()
        if not hasattr(self, 'mini_window'):
            self.mini_window = tk.Toplevel()
            self.mini_window.overrideredirect(True)
            self.mini_window.attributes('-topmost', True)
            
            # Create small button
            btn = ttk.Button(self.mini_window, text="✨", width=3,
                           command=self.restore_toolbar)
            btn.pack()
            
            # Make mini window draggable
            btn.bind("<Button-1>", self.start_mini_drag)
            btn.bind("<B1-Motion>", self.on_mini_drag)
            
        self.mini_window.geometry(f"+{self.winfo_x()}+{self.winfo_y()}")
        self.mini_window.deiconify()
        
    def restore_toolbar(self):
        """Restore the full toolbar"""
        if hasattr(self, 'mini_window'):
            x = self.mini_window.winfo_x()
            y = self.mini_window.winfo_y()
            self.mini_window.withdraw()
            self.geometry(f"+{x}+{y}")
        self.deiconify()
        
    def start_mini_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
    def on_mini_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.mini_window.geometry(f"+{self.mini_window.winfo_x() + dx}+{self.mini_window.winfo_y() + dy}")
    
    def start_enhancement(self):
        """Start the enhancement process"""
        if self.waiting_for_selection:
            return
            
        selected_prompt = self.selected_prompt.get()
        prompt_template = llm_prompts[selected_prompt]
        self.enhance_btn.configure(text="Select text now...", state='disabled')
        self.waiting_for_selection = True
        
        # Start waiting for selection in a separate thread
        threading.Thread(target=self.wait_for_selection, 
                       args=(prompt_template,), 
                       daemon=True).start()
    
    def wait_for_selection(self, prompt_template):
        """Wait for text selection and then process it"""
        try:
            self.mouse_down = False
            self.mouse_down_time = None
            
            def on_click(x, y, button, pressed):
                if button == mouse.Button.left:
                    if pressed:
                        self.mouse_down = True
                        self.mouse_down_time = time.time()
                    else:  # Mouse released
                        if self.mouse_down:
                            # Calculate how long the mouse was held down
                            hold_duration = time.time() - (self.mouse_down_time or 0)
                            
                            # If held for more than 0.2 seconds, consider it a drag-select
                            if hold_duration > 0.2:
                                # Small delay after release
                                time.sleep(0.2)
                                selected_text = self.clipboard.get_selected_text()
                                if selected_text:
                                    logger.debug(f"Selection complete after {hold_duration:.2f}s: {selected_text[:100]}...")
                                    self.waiting_for_selection = False
                                    self.callback(prompt_template, selected_text)
                                    return False  # Stop listener
                            else:
                                logger.debug(f"Ignored quick click ({hold_duration:.2f}s)")
                                
                        self.mouse_down = False
                        self.mouse_down_time = None
            
            # Start mouse listener
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
                
        except Exception as e:
            logger.error(f"Error waiting for selection: {e}")
        finally:
            # Reset button state
            self.waiting_for_selection = False
            self.after(0, lambda: self.enhance_btn.configure(
                text="✨ Select & Enhance", 
                state='normal'
            ))

class FloatingToolbarModule:
    def __init__(self, settings: Dict, ollama_client: OllamaClient):
        logger.info("Initializing Floating Toolbar Module")
        self.settings = settings
        self.ollama_client = ollama_client
        self.clipboard = ClipboardManager()
        self.toolbar = None

    def enable(self):
        logger.info("Enabling Floating Toolbar")
        if not self.toolbar:
            # Pass clipboard manager to toolbar
            self.toolbar = FloatingToolbar(
                callback=self.process_text,
                clipboard=self.clipboard
            )
            # Position in top-right corner initially
            screen_width = self.toolbar.winfo_screenwidth()
            self.toolbar.geometry(f"+{screen_width-300}+50")

    def disable(self):
        logger.info("Disabling Floating Toolbar")
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

    def process_text(self, prompt_template: str, selected_text: str):
        """Process the text after user selects it"""
        try:
            logger.info("Processing text with prompt template")
            logger.debug(f"Selected text length: {len(selected_text)}")

            prompt = prompt_template.format(text=selected_text)

            logger.debug("Sending request to Ollama")
            improved_text = self.ollama_client.generate_response(
                prompt=prompt,
                model=self.settings['model'].get()
            )

            if improved_text:
                logger.info("Successfully processed text")
                self.clipboard.replace_selected_text(improved_text.strip())
            else:
                logger.error("Failed to process text")
                messagebox.showerror("Error", "Failed to generate improved text")

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            messagebox.showerror("Error", f"Error processing text: {e}")