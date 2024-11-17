import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import json
from datetime import datetime
from session_manager import SessionManager
from profile_manager import ProfileManager, UserProfile
import threading
import time
from typing import Dict
import os
from profile_summarizer import ProfileSummarizer

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Profile Builder Chatbot")
        
        # Set color scheme
        self.bg_color = "#000000"  # Black background
        self.fg_color = "#FFD700"  # Gold text
        self.accent_color = "#B8860B"  # Dark golden rod accent
        self.text_font = ("Consolas", 10)
        self.header_font = ("Consolas", 11, "bold")
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        self.root.geometry("1200x800")  # Larger default size
        
        # Initialize managers
        self.session_manager = SessionManager()
        self.current_session_id = None
        self.summarizer = ProfileSummarizer()
        
        # Configure style
        self._configure_styles()
        
        # Create main container
        self.main_container = ttk.PanedWindow(root, orient=tk.HORIZONTAL, style="Custom.TPanedwindow")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create panels
        self._create_panels()
        
        # Create UI elements
        self._create_chat_interface()
        self._create_profile_visualization()
        self._create_toolbar()
        
        # Initialize session
        self._initialize_session()
        
    def _configure_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background=self.bg_color)
        self.style.configure("Custom.TLabel", 
                           background=self.bg_color, 
                           foreground=self.fg_color,
                           font=self.text_font)
        self.style.configure("Header.TLabel",
                           background=self.bg_color,
                           foreground=self.accent_color,
                           font=self.header_font)
        self.style.configure("Custom.TButton",
                           font=self.text_font,
                           padding=5)
        self.style.configure("Custom.TPanedwindow", 
                           background=self.bg_color)
                           
    def _create_panels(self):
        """Create main panels."""
        # Create left panel (chat interface)
        self.left_panel = ttk.Frame(self.main_container, style="Custom.TFrame")
        self.main_container.add(self.left_panel, weight=2)
        
        # Create right panel (profile visualization)
        self.right_panel = ttk.Frame(self.main_container, style="Custom.TFrame")
        self.main_container.add(self.right_panel, weight=1)
        
    def _initialize_session(self):
        """Initialize the first session."""
        try:
            # Create new session
            self.current_session_id = self.session_manager.create_session()
            session = self.session_manager.get_session(self.current_session_id)
            
            if not session:
                print("Failed to create session")
                return
                
            # Initialize chat display
            if hasattr(self, 'chat_display'):
                self.chat_display.config(state=tk.NORMAL)
                welcome_msg = "Bot: Hello! I'm here to help build your professional profile. Let's start with your name. What should I call you?\n\n"
                self.chat_display.insert(tk.END, welcome_msg)
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)
            
            # Initialize displays
            self.update_session_info()
            self.update_profile_display()
            
        except Exception as e:
            print(f"Error initializing session: {str(e)}")

    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar = ttk.Frame(self.root, style="Custom.TFrame")
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        

    def _create_profile_visualization(self):
        """Create profile visualization section."""
        # Create vertical paned window for right panel
        self.profile_paned = ttk.PanedWindow(self.right_panel, orient=tk.VERTICAL, style="Custom.TPanedwindow")
        self.profile_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Upper section - Profile Details
        self.upper_frame = ttk.Frame(self.profile_paned, style="Custom.TFrame")
        self.profile_paned.add(self.upper_frame, weight=1)
        
        # Profile sections
        sections = [
            ("Basic Info", ["name", "age", "location"]),
            ("Education", ["degree", "institution", "graduation_year"]),
            ("Experience", ["current_role", "company"]),
            ("Skills", ["programming", "tools", "soft_skills"]),
            ("Additional", ["languages", "certifications"])
        ]
        
        # Create notebook for tabbed sections
        self.profile_notebook = ttk.Notebook(self.upper_frame)
        self.profile_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for each section
        self.section_frames = {}
        for section_name, fields in sections:
            frame = ttk.Frame(self.profile_notebook, style="Custom.TFrame")
            self.profile_notebook.add(frame, text=section_name)
            self.section_frames[section_name] = frame
            
            # Add fields to section
            for field in fields:
                field_frame = ttk.Frame(frame, style="Custom.TFrame")
                field_frame.pack(fill=tk.X, padx=5, pady=2)
                
                label = ttk.Label(
                    field_frame,
                    text=field.replace("_", " ").title() + ":",
                    style="Custom.TLabel",
                    width=15
                )
                label.pack(side=tk.LEFT)
                
                value_label = ttk.Label(
                    field_frame,
                    text="Not set",
                    style="Custom.TLabel"
                )
                value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                setattr(self, f"{field}_label", value_label)
        
        # Lower section - Controls and Completion
        self.lower_frame = ttk.Frame(self.profile_paned, style="Custom.TFrame")
        self.profile_paned.add(self.lower_frame, weight=1)
        
        # Completeness meter
        self.completeness_frame = ttk.Frame(self.lower_frame, style="Custom.TFrame")
        self.completeness_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.completeness_label = ttk.Label(
            self.completeness_frame,
            text="Profile Completeness: 0%",
            style="Header.TLabel"
        )
        self.completeness_label.pack(side=tk.TOP)
        
        self.completeness_bar = ttk.Progressbar(
            self.completeness_frame,
            mode='determinate',
            length=200
        )
        self.completeness_bar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Control buttons
        self.controls_frame = ttk.Frame(self.lower_frame, style="Custom.TFrame")
        self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Clear button
        clear_btn = ttk.Button(
            self.controls_frame,
            text="Clear Profile",
            command=self.clear_profile,
            style="Custom.TButton"
        )
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Summarize button
        summarize_btn = ttk.Button(
            self.controls_frame,
            text="Generate Summary",
            command=self.generate_summary,
            style="Custom.TButton"
        )
        summarize_btn.pack(side=tk.LEFT, padx=2)
        
        # Theme toggle
        theme_btn = ttk.Button(
            self.controls_frame,
            text="Toggle Theme",
            command=self.toggle_theme,
            style="Custom.TButton"
        )
        theme_btn.pack(side=tk.LEFT, padx=2)

    def export_profile(self):
        """Export profile to JSON file."""
        if not self.current_session_id:
            messagebox.showwarning("No Profile", "No profile data to export.")
            return
            
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            messagebox.showwarning("No Profile", "No profile data to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                profile_data = session['profile_manager'].profile.to_dict()
                with open(file_path, 'w') as f:
                    json.dump(profile_data, f, indent=4)
                messagebox.showinfo("Success", "Profile exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export profile: {str(e)}")

    def import_profile(self):
        """Import profile from JSON file."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "Please start a new session first.")
            return
            
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            messagebox.showwarning("No Session", "Please start a new session first.")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    profile_data = json.load(f)
                session['profile_manager'].profile.from_dict(profile_data)
                self.update_profile_display()
                messagebox.showinfo("Success", "Profile imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import profile: {str(e)}")

    def clear_profile(self):
        """Clear current profile data."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the current profile?"):
            self.session_manager.current_session.profile_manager.profile = UserProfile()
            self.update_profile_display()
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "Profile cleared. Let's start fresh!\n")

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.bg_color == "#000000":  # Currently dark
            self.bg_color = "#FFFFFF"  # Light background
            self.fg_color = "#000000"  # Black text
            self.accent_color = "#007AFF"  # Blue accent
        else:  # Currently light
            self.bg_color = "#000000"  # Dark background
            self.fg_color = "#FFD700"  # Gold text
            self.accent_color = "#B8860B"  # Dark golden rod accent
            
        # Update styles
        self._update_styles()
        
    def _update_styles(self):
        """Update all widget styles."""
        self.root.configure(bg=self.bg_color)
        self.style.configure("Custom.TFrame", background=self.bg_color)
        self.style.configure("Custom.TLabel", 
                           background=self.bg_color, 
                           foreground=self.fg_color)
        self.style.configure("Header.TLabel",
                           background=self.bg_color,
                           foreground=self.accent_color)
        
        # Update text widgets
        self.chat_display.configure(
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color
        )
        self.input_field.configure(
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color
        )

    def update_profile_display(self):
        """Update profile visualization with current data."""
        try:
            # Get current session
            if not self.current_session_id:
                return
                
            session = self.session_manager.get_session(self.current_session_id)
            if not session or 'profile_manager' not in session:
                return
                
            profile = session['profile_manager'].profile
            if not profile:
                return
                
            # Update basic info
            for field in ["name", "age", "location"]:
                value = getattr(profile, field, "Not set")
                label = getattr(self, f"{field}_label", None)
                if label:
                    label.configure(text=str(value))
            
            # Update education
            edu = profile.education
            if edu and hasattr(self, 'degree_label'):
                self.degree_label.configure(text=edu.degree or "Not set")
            if edu and hasattr(self, 'institution_label'):
                self.institution_label.configure(text=edu.institution or "Not set")
            if edu and hasattr(self, 'graduation_year_label'):
                self.graduation_year_label.configure(text=str(edu.graduation_year) if edu.graduation_year else "Not set")
            
            # Update experience
            exp = profile.professional_experience[0] if profile.professional_experience else None
            if hasattr(self, 'current_role_label'):
                self.current_role_label.configure(text=exp.job_title if exp else "Not set")
            if hasattr(self, 'company_label'):
                self.company_label.configure(text=exp.company_name if exp else "Not set")
            
            # Update skills
            if hasattr(self, 'programming_label'):
                self.programming_label.configure(text=", ".join(profile.programming_languages) if profile.programming_languages else "Not set")
            if hasattr(self, 'tools_label'):
                self.tools_label.configure(text=", ".join(profile.tools_technologies) if profile.tools_technologies else "Not set")
            if hasattr(self, 'soft_skills_label'):
                self.soft_skills_label.configure(text=", ".join(profile.soft_skills) if profile.soft_skills else "Not set")
            
            # Update completeness
            if hasattr(self, 'completeness_label') and hasattr(self, 'completeness_bar'):
                completeness = session['profile_manager'].calculate_completeness()
                self.completeness_label.configure(text=f"Profile Completeness: {completeness:.1f}%")
                self.completeness_bar['value'] = completeness
                
        except Exception as e:
            print(f"Error updating profile display: {str(e)}")

    def _create_chat_interface(self):
        """Create the chat interface elements."""
        # Session info label
        self.session_info = ttk.Label(
            self.left_panel,
            text="Session Info",
            style="Custom.TLabel"
        )
        self.session_info.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Chat display with custom colors
        self.chat_display = scrolledtext.ScrolledText(
            self.left_panel,
            wrap=tk.WORD,
            height=20,
            bg=self.bg_color,
            fg=self.fg_color,
            font=self.text_font,
            insertbackground=self.fg_color
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input container frame
        input_container = ttk.Frame(self.left_panel, style="Custom.TFrame")
        input_container.pack(fill=tk.X, padx=5, pady=5)
        input_container.grid_columnconfigure(0, weight=1)  # Make input field expand
        
        # Input field with custom colors
        self.input_field = tk.Entry(
            input_container,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=self.text_font,
            relief=tk.SOLID,
            highlightbackground=self.fg_color,
            highlightcolor=self.fg_color,
            highlightthickness=1
        )
        self.input_field.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.input_field.bind("<Return>", self.process_input)
        
        # Send button
        self.send_button = ttk.Button(
            input_container,
            text="Send",
            command=self.process_input,
            style="Custom.TButton"
        )
        self.send_button.grid(row=0, column=1)

    def start_new_session(self):
        """Start a new chat session."""
        if self.current_session_id:
            self.session_manager.end_session(self.current_session_id)
        
        self.current_session_id = self.session_manager.create_session()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Reset completeness bar
        self.completeness_bar['value'] = 0
        self.completeness_label.configure(text="Profile Completeness: 0%")
        
        # Get the session
        session = self.session_manager.get_session(self.current_session_id)
        if session:
            self.chat_display.config(state=tk.NORMAL)
            welcome_msg = "Bot: Hello! I'm here to help build your professional profile. Let's start with your name. What should I call you?\n\n"
            self.chat_display.insert(tk.END, welcome_msg)
            self.chat_display.config(state=tk.DISABLED)
            self.update_session_info()
            self.chat_display.see(tk.END)
            
        # Reset profile display
        self.update_profile_display()

    def update_session_info(self):
        """Update the session information display."""
        try:
            if not self.current_session_id:
                self.session_info.config(text="No active session")
                return
                
            session = self.session_manager.get_session(self.current_session_id)
            if not session:
                self.session_info.config(text="No active session")
                return
                
            created_at = datetime.fromisoformat(session['created_at'])
            active_time = datetime.now() - created_at
            minutes = int(active_time.total_seconds() / 60)
            seconds = int(active_time.total_seconds() % 60)
            info_text = f"Session ID: {self.current_session_id[:8]}... | Active for: {minutes}m {seconds}s"
            self.session_info.config(text=info_text)
            
        except Exception as e:
            print(f"Error updating session info: {str(e)}")
            self.session_info.config(text="Error updating session info")

    def process_input(self, event=None):
        """Process user input and update the chat."""
        user_input = self.input_field.get().strip()
        if not user_input:
            return
            
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Get current session
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            self.start_new_session()
            session = self.session_manager.get_session(self.current_session_id)
            
        if not session:
            return
            
        try:
            # Display user input
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"You: {user_input}\n")
            
            # Process input and get response
            profile_manager = session['profile_manager']
            if not profile_manager:
                raise Exception("No profile manager found")
                
            response, updated = profile_manager.process_input(user_input)
            
            # Display bot response
            self.chat_display.insert(tk.END, f"Bot: {response}\n\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            
            # Update displays
            self.update_profile_display()
            self.update_session_info()
            
        except Exception as e:
            print(f"Error processing input: {str(e)}")
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "Bot: I encountered an error processing your input. Please try again.\n\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

    def generate_summary(self):
        """Generate and display a summary of the profile."""
        try:
            session = self.session_manager.get_session(self.current_session_id)
            if not session or 'profile_manager' not in session:
                messagebox.showwarning("Warning", "No active profile to summarize.")
                return

            profile = session['profile_manager'].profile
            
            # Show loading message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "\nBot: Generating profile summary...\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            
            # Generate summary in a separate thread
            def summarize():
                summary = self.summarizer.generate_summary(profile)
                
                if summary:
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, f"\nProfile Summary:\n{summary}\n\n")
                    self.chat_display.config(state=tk.DISABLED)
                    self.chat_display.see(tk.END)
                else:
                    messagebox.showerror("Error", "Failed to generate summary. Please try again.")
            
            threading.Thread(target=summarize, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating summary: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()
