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
        
        # Make window floating and remove decorations
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Create semi-transparent background
        self.config(bg='#f0f0f0')
        self.attributes('-alpha', 0.95)
        
        # Create frame for buttons
        self.frame = ttk.Frame(self)
        self.frame.pack(padx=2, pady=2)
        
        # Create improve button with icon
        self.improve_btn = ttk.Button(
            self.frame, 
            text="✨ Improve Writing",
            command=self.improve_text,
            style='Toolbar.TButton'
        )
        self.improve_btn.pack(padx=3, pady=3)
        
        # Create grammar check button
        self.grammar_btn = ttk.Button(
            self.frame,
            text="📝 Fix Grammar",
            command=self.check_grammar,
            style='Toolbar.TButton'
        )
        self.grammar_btn.pack(padx=3, pady=3)
        
        # Bind mouse leave event to hide toolbar
        self.bind('<Leave>', self.check_mouse_leave)
        
        # Hide window initially
        self.withdraw()
        
    def improve_text(self):
        self.withdraw()
        self.callback("improve")
        
    def check_grammar(self):
        self.withdraw()
        self.callback("grammar")
    
    def check_mouse_leave(self, event):
        # Get mouse position
        point = POINT()
        windll.user32.GetCursorPos(byref(point))
        
        # Get toolbar position and size
        x = self.winfo_x()
        y = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Check if mouse is outside toolbar
        if not (x <= point.x <= x + width and y <= point.y <= y + height):
            self.withdraw()
