import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from typing import Dict, Callable
from datetime import datetime
from lifai.utils.logger_utils import get_module_logger
from lifai.config.prompts import improvement_options, llm_prompts

logger = get_module_logger(__name__)

class PromptEditorWindow:
    def __init__(self, settings: Dict):
        self.settings = settings
        self.window = None
        self.prompts_data = {
            'options': improvement_options.copy(),
            'templates': llm_prompts.copy()
        }
        self.update_callbacks = []
        self.is_visible = False
        self.has_unsaved_changes = False
        
    def add_update_callback(self, callback: Callable):
        """Add a callback to be notified when prompts are updated"""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
        
    def notify_prompt_updates(self):
        improvement_options.clear()
        improvement_options.extend(self.prompts_data['options'])
        
        llm_prompts.clear()
        llm_prompts.update(self.prompts_data['templates'])
        
        for callback in self.update_callbacks:
            try:
                callback(self.prompts_data['options'])
            except Exception as e:
                logger.error(f"Error notifying prompt update: {e}")
        
    def show(self):
        """Show the editor window"""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        self.window.deiconify()
        self.is_visible = True
        
    def hide(self):
        """Hide the editor window"""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
        self.is_visible = False
            
    def create_window(self):
        """Create the editor window"""
        if self.window:
            self.window.destroy()
            
        self.window = tk.Toplevel()
        self.window.title("Prompt Editor")
        self.window.geometry("600x500")
        
        # Prevent window from being closed with X button
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Main container
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Prompts list frame (left side)
        list_frame = ttk.LabelFrame(main_frame, text="Prompts", padding=5)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Prompts listbox
        self.prompts_list = tk.Listbox(list_frame, width=30, exportselection=False)
        self.prompts_list.pack(fill=tk.Y, expand=True)
        self.prompts_list.bind('<<ListboxSelect>>', self.on_prompt_select)
        
        # Populate list
        for option in self.prompts_data['options']:
            self.prompts_list.insert(tk.END, option)
            
        # Editor frame (right side)
        editor_frame = ttk.Frame(main_frame)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Name field
        name_frame = ttk.Frame(editor_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Template editor
        ttk.Label(editor_frame, text="Prompt Template:").pack(anchor=tk.W)
        self.template_text = tk.Text(editor_frame, height=10, wrap=tk.WORD)
        self.template_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Help text
        help_text = "Use {text} as placeholder for the selected text in your prompt template"
        ttk.Label(editor_frame, text=help_text, foreground='gray').pack(anchor=tk.W)
        
        # Buttons frame
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="New", command=self.new_prompt).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Save", command=self.save_prompt).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_prompt).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Export", command=self.export_prompts).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Import", command=self.import_prompts).pack(side=tk.RIGHT, padx=2)
        
        # Add status label and apply button at the bottom
        status_frame = ttk.Frame(editor_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="No unsaved changes",
            foreground='gray'
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.apply_btn = ttk.Button(
            status_frame,
            text="Apply Changes",
            command=self.apply_changes,
            state='disabled'
        )
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
    def on_prompt_select(self, event):
        selection = self.prompts_list.curselection()
        if not selection:
            return
            
        name = self.prompts_list.get(selection[0])
        template = self.prompts_data['templates'].get(name, "")
        
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)
        
        self.template_text.delete('1.0', tk.END)
        self.template_text.insert('1.0', template)
        
    def new_prompt(self):
        self.name_entry.delete(0, tk.END)
        self.template_text.delete('1.0', tk.END)
        self.prompts_list.selection_clear(0, tk.END)
        
    def save_prompt(self):
        name = self.name_entry.get().strip()
        template = self.template_text.get('1.0', 'end-1c').strip()
        
        if not name or not template:
            messagebox.showerror("Error", "Name and template are required")
            return
            
        if "{text}" not in template:
            messagebox.showerror("Error", "Template must contain {text} placeholder")
            return
            
        # Update data
        if name not in self.prompts_data['options']:
            self.prompts_data['options'].append(name)
            self.prompts_list.insert(tk.END, name)
            
        self.prompts_data['templates'][name] = template
        self.save_to_file()
        
        # Mark as having unsaved changes
        self.mark_unsaved_changes()
        messagebox.showinfo("Success", "Prompt saved successfully")
        
    def delete_prompt(self):
        selection = self.prompts_list.curselection()
        if not selection:
            return
            
        name = self.prompts_list.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Delete prompt '{name}'?"):
            self.prompts_data['options'].remove(name)
            self.prompts_data['templates'].pop(name, None)
            self.prompts_list.delete(selection[0])
            self.save_to_file()
            self.new_prompt()
            
            # Mark as having unsaved changes
            self.mark_unsaved_changes()
            
    def mark_unsaved_changes(self):
        """Mark that there are changes that need to be applied"""
        self.has_unsaved_changes = True
        self.status_label.config(
            text="Changes need to be applied",
            foreground='#1976D2'  # Blue color
        )
        self.apply_btn.config(state='normal')
        
    def apply_changes(self):
        """Apply changes to all modules"""
        try:
            # Update the global prompt variables
            improvement_options.clear()
            improvement_options.extend(self.prompts_data['options'])
            
            llm_prompts.clear()
            llm_prompts.update(self.prompts_data['templates'])
            
            # Notify all registered callbacks
            for callback in self.update_callbacks:
                try:
                    callback(self.prompts_data['options'])
                except Exception as e:
                    logger.error(f"Error notifying prompt update: {e}")
            
            # Reset status
            self.has_unsaved_changes = False
            self.status_label.config(
                text="Changes applied successfully",
                foreground='#4CAF50'  # Green color
            )
            self.apply_btn.config(state='disabled')
            
            logger.info("Prompt changes applied to all modules")
            
        except Exception as e:
            logger.error(f"Error applying changes: {e}")
            messagebox.showerror("Error", f"Failed to apply changes: {e}")
    
    def save_to_file(self):
        try:
            # Save to config file
            config_path = os.path.join('lifai', 'config', 'custom_prompts.json')
            with open(config_path, 'w') as f:
                json.dump(self.prompts_data, f, indent=4)
            logger.info("Prompts saved to file")
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            messagebox.showerror("Error", f"Failed to save prompts: {e}")
            
    def export_prompts(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'prompts_export_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.prompts_data, f, indent=4)
            messagebox.showinfo("Success", f"Prompts exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
            
    def import_prompts(self):
        try:
            filename = filedialog.askopenfilename(
                title="Import Prompts",
                filetypes=[("JSON files", "*.json")]
            )
            if filename:
                with open(filename) as f:
                    data = json.load(f)
                    if 'options' in data and 'templates' in data:
                        self.prompts_data = data
                        self.refresh_list()
                        self.save_to_file()
                        messagebox.showinfo("Success", "Prompts imported successfully")
                    else:
                        raise ValueError("Invalid prompts file format")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")
            
    def refresh_list(self):
        self.prompts_list.delete(0, tk.END)
        for option in self.prompts_data['options']:
            self.prompts_list.insert(tk.END, option) 