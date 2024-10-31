import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import os
import sys
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from lifai.utils.ollama_client import OllamaClient
from lifai.modules.text_improver.improver import TextImproverWindow
from lifai.modules.floating_toolbar.toolbar import FloatingToolbarModule
from lifai.core.toggle_switch import ToggleSwitch

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class LogHandler(logging.Handler):
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        super().__init__()
        self.text_widget = text_widget
        
        # Create a formatter
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

    def emit(self, record):
        msg = self.formatter.format(record)
        self.text_widget.configure(state='normal')
        
        # Add color tags based on log level
        if record.levelno >= logging.ERROR:
            tag = 'error'
            color = '#FF5252'  # Red
        elif record.levelno >= logging.WARNING:
            tag = 'warning'
            color = '#FFA726'  # Orange
        elif record.levelno >= logging.INFO:
            tag = 'info'
            color = '#4CAF50'  # Green
        else:
            tag = 'debug'
            color = '#9E9E9E'  # Gray
            
        # Configure tag if it doesn't exist
        if tag not in self.text_widget.tag_names():
            self.text_widget.tag_configure(tag, foreground=color)
        
        # Insert the message with appropriate tag
        self.text_widget.insert(tk.END, msg + '\n', tag)
        self.text_widget.see(tk.END)  # Auto-scroll to bottom
        self.text_widget.configure(state='disabled')

class LifAiHub:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LifAi Control Hub")
        self.root.geometry("600x500")  # Made window larger to accommodate logs
        
        # Configure background color
        self.root.configure(bg='#ffffff')
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#ffffff')
        self.style.configure('TLabelframe', background='#ffffff')
        self.style.configure('TLabelframe.Label', background='#ffffff')
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient()
        
        # Shared settings
        self.settings = {
            'model': tk.StringVar(value=''),  # Initialize with empty string
            'models_list': []
        }
        
        self.setup_ui()
        self.modules = {}
        self.initialize_modules()
        
        # Log initialization
        logging.info("LifAi Control Hub initialized")

    def setup_ui(self):
        # Settings panel with padding
        self.settings_frame = ttk.LabelFrame(
            self.root, 
            text="Global Settings",
            padding=10
        )
        self.settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Model selection container
        model_container = ttk.Frame(self.settings_frame)
        model_container.pack(fill=tk.X, expand=True)
        
        # Model label
        model_label = ttk.Label(model_container, text="Model:")
        model_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Model selection with longer width
        self.models_list = self.ollama_client.fetch_models()
        self.model_dropdown = ttk.Combobox(
            model_container, 
            textvariable=self.settings['model'],
            values=self.models_list,
            state='readonly'
        )
        self.model_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        if self.models_list:
            self.model_dropdown.current(0)
        
        # Module controls
        self.modules_frame = ttk.LabelFrame(
            self.root, 
            text="Module Controls",
            padding=10
        )
        self.modules_frame.pack(fill=tk.X, padx=10, pady=5)

        # Text Improver toggle
        self.text_improver_toggle = ToggleSwitch(
            self.modules_frame,
            "Text Improver Window",
            self.toggle_text_improver
        )
        self.text_improver_toggle.pack(fill=tk.X, pady=5)

        # Floating Toolbar toggle
        self.toolbar_toggle = ToggleSwitch(
            self.modules_frame,
            "Floating Toolbar",
            self.toggle_floating_toolbar
        )
        self.toolbar_toggle.pack(fill=tk.X, pady=5)

        # Initialize logging setup
        self.setup_logging()

    def setup_logging(self):
        # Create debug frame
        self.debug_frame = ttk.LabelFrame(
            self.root,
            text="Debug Logs",
            padding=10
        )
        self.debug_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create log text widget with scrollbar
        self.log_widget = scrolledtext.ScrolledText(
            self.debug_frame,
            height=10,
            width=50,
            font=('Consolas', 9),
            bg='#f8f9fa',
            wrap=tk.WORD,
            state='disabled'
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure logging
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our custom handler
        log_handler = LogHandler(self.log_widget)
        root_logger.addHandler(log_handler)
        
        # Create log controls at the bottom
        self.create_log_controls()
        
        # Add initial test logs
        logging.debug("Debug message test")
        logging.info("Info message test")
        logging.warning("Warning message test")
        logging.error("Error message test")

    def create_log_controls(self):
        control_frame = ttk.Frame(self.debug_frame)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Log level selector
        ttk.Label(control_frame, text="Log Level:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_level = tk.StringVar(value="INFO")
        level_combo = ttk.Combobox(
            control_frame,
            textvariable=self.log_level,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state='readonly',
            width=10
        )
        level_combo.pack(side=tk.LEFT, padx=5)
        
        # Bind log level change
        level_combo.bind('<<ComboboxSelected>>', self.change_log_level)
        
        # Clear logs button
        ttk.Button(
            control_frame,
            text="Clear Logs",
            command=self.clear_logs
        ).pack(side=tk.RIGHT, padx=5)
        
        # Save logs button
        ttk.Button(
            control_frame,
            text="Save Logs",
            command=self.save_logs
        ).pack(side=tk.RIGHT, padx=5)

    def change_log_level(self, event=None):
        level = getattr(logging, self.log_level.get())
        logging.getLogger().setLevel(level)
        logging.info(f"Log level changed to {self.log_level.get()}")

    def clear_logs(self):
        self.log_widget.configure(state='normal')
        self.log_widget.delete(1.0, tk.END)
        self.log_widget.configure(state='disabled')
        logging.info("Logs cleared")

    def save_logs(self):
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/lifai_log_{timestamp}.txt'
            
            # Save logs
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_widget.get(1.0, tk.END))
            
            logging.info(f"Logs saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save logs: {e}")

    def initialize_modules(self):
        # Initialize modules (but don't show them)
        self.modules['text_improver'] = TextImproverWindow(
            settings=self.settings,
            ollama_client=self.ollama_client
        )
        
        self.modules['floating_toolbar'] = FloatingToolbarModule(
            settings=self.settings,
            ollama_client=self.ollama_client
        )

    def toggle_text_improver(self):
        if self.text_improver_toggle.get():
            self.modules['text_improver'].show()
        else:
            self.modules['text_improver'].hide()

    def toggle_floating_toolbar(self):
        if self.toolbar_toggle.get():
            self.modules['floating_toolbar'].enable()
        else:
            self.modules['floating_toolbar'].disable()

    def run(self):
        # Make sure the hub window stays on top
        self.root.attributes('-topmost', True)
        self.root.mainloop()

if __name__ == "__main__":
    app = LifAiHub()
    app.run() 