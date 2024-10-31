import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable
from pynput import mouse
from lifai.utils.ollama_client import OllamaClient
from lifai.utils.clipboard_utils import ClipboardManager

class QuickImprover:
    def __init__(self, parent: tk.Tk, settings: Dict, ollama_client: OllamaClient):
        self.parent = parent
        self.settings = settings
        self.ollama_client = ollama_client
        self.clipboard = ClipboardManager()
        
        # Initialize toolbar
        self.toolbar = FloatingToolbar(parent, self.process_text)
        self.setup_mouse_listener()
        
    def setup_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if button == mouse.Button.right and pressed:
                self.check_selection(x, y)
        
        self.listener = mouse.Listener(on_click=on_click)
        self.listener.start()
        
    def check_selection(self, x: int, y: int):
        selected_text = self.clipboard.get_selected_text()
        if selected_text:
            self.toolbar.show_at_position(x, y)
            
    def process_text(self, mode: str = "improve"):
        selected_text = self.clipboard.get_selected_text()
        if not selected_text:
            return
            
        try:
            # Select prompt based on mode
            if mode == "improve":
                prompt = f"""Please improve the following text while maintaining its original meaning.
                            Make it more clear and professional, but keep the same tone:
                            
                            {selected_text}"""
            else:  # grammar mode
                prompt = f"""Please fix any grammar and spelling errors in the following text,
                            while keeping the original meaning and tone intact:
                            
                            {selected_text}"""
            
            # Generate improved text
            improved_text = self.ollama_client.generate_response(
                prompt=prompt,
                model=self.settings['model'].get()
            )
            
            if improved_text:
                self.clipboard.replace_selected_text(improved_text.strip())
            else:
                messagebox.showerror("Error", "Failed to generate improved text")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error processing text: {e}")
            
    def show(self):
        # Enable the mouse listener
        if not self.listener.is_alive():
            self.setup_mouse_listener()
            
    def hide(self):
        # Disable the mouse listener and hide toolbar
        if self.listener.is_alive():
            self.listener.stop()
        self.toolbar.hide()


class FloatingToolbar(tk.Toplevel):
    def __init__(self, parent: tk.Tk, callback: Callable):
        super().__init__()
        self.parent = parent
        self.callback = callback
        
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.config(bg='#e0e0e0')
        self.attributes('-alpha', 0.95)
        
    def setup_ui(self):
        # Create frames
        self.inner_frame = ttk.Frame(self)
        self.inner_frame.pack(padx=1, pady=1)
        
        self.frame = ttk.Frame(self.inner_frame)
        self.frame.pack(padx=2, pady=2)
        
        # Create buttons
        self.improve_btn = ttk.Button(
            self.frame,
            text="✨ Improve Writing",
            command=lambda: self.process_and_hide("improve")
        )
        self.improve_btn.pack(padx=3, pady=3)
        
        self.grammar_btn = ttk.Button(
            self.frame,
            text="📝 Fix Grammar",
            command=lambda: self.process_and_hide("grammar")
        )
        self.grammar_btn.pack(padx=3, pady=3)
        
        # Bind events
        self.bind('<Leave>', self.hide)
        
        # Update size
        self.update_idletasks()
        self.height = self.winfo_height()
        
        # Initially hidden
        self.withdraw()
        
    def process_and_hide(self, mode: str):
        self.hide()
        self.callback(mode)
        
    def hide(self, event=None):
        self.withdraw()
        
    def show_at_position(self, x: int, y: int):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        toolbar_width = self.winfo_width()
        toolbar_height = self.height
        
        # Adjust position to keep toolbar on screen
        new_x = max(0, min(x - 30, screen_width - toolbar_width))
        new_y = max(0, min(y - self.height - 20, screen_height - toolbar_height))
        
        self.geometry(f"+{new_x}+{new_y}")
        self.deiconify()
        self.lift() 