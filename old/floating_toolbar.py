import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import pyperclip
import requests
import json
import threading
import win32gui
import win32con
import win32api
from ctypes import windll, Structure, c_long, byref
import time
from pynput import mouse

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class FloatingToolbar(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__()
        self.parent = parent
        self.callback = callback
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        self.config(bg='#e0e0e0')
        self.attributes('-alpha', 0.95)
        
        self.inner_frame = ttk.Frame(self)
        self.inner_frame.pack(padx=1, pady=1)
        
        self.frame = ttk.Frame(self.inner_frame, style='Inner.TFrame')
        self.frame.pack(padx=2, pady=2)
        
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
        
        self.bind('<Leave>', self.hide)
        
        self.update_idletasks()
        self.height = self.winfo_height()
        
        self.withdraw()
        
    def process_and_hide(self, mode):
        self.hide()
        self.callback(mode)
        
    def hide(self, event=None):
        self.withdraw()
    
    def show_at_position(self, x, y):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        toolbar_width = self.winfo_width()
        toolbar_height = self.height

        # Adjust position to be 20 pixels above the cursor, ensuring it stays on screen
        new_x = max(0, min(x - 30, screen_width - toolbar_width))  # Keep within screen bounds
        new_y = max(0, min(y - self.height - 20, screen_height - toolbar_height))  # Keep within screen bounds

        self.geometry(f"+{new_x}+{new_y}")
        self.deiconify()
        self.lift()
