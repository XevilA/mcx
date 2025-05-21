"""Main application module for Dotmini MCX.

This module initializes and runs the Dotmini MCX application,
setting up the main window, theme management, license verification,
and coordinating various UI components and functionalities.
"""
import os
import sys
import hashlib
import threading
import time
import json
import platform
from pathlib import Path
from functools import partial
import concurrent.futures

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, QListWidget, 
                            QProgressBar, QMessageBox, QDialog, QSplashScreen, QComboBox,
                            QScrollArea, QGridLayout, QFrame, QSizePolicy, QSpacerItem,
                            QSlider, QCheckBox, QMenu, QMenuBar, QToolBar, QStatusBar, 
                            QListWidgetItem, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt6.QtCore import (Qt, QSize, QThread, pyqtSignal, QTimer, QRect, QPropertyAnimation,
                         QSettings, QStandardPaths, QDir, QPoint, QEasingCurve, QMimeData, QUrl)
from PyQt6.QtGui import (QIcon, QPixmap, QFont, QPalette, QColor, QCursor, QFontDatabase, 
                        QGuiApplication, QAction, QKeySequence, QDrag, QDragEnterEvent,
                        QDropEvent)

# For image classification
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image # Retained as it's a common Keras import
from PIL import Image
import glob

# Performance optimization - enable TF GPU memory growth
try:
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
except Exception as e:
    print(f"GPU memory growth setting failed: {e}")

# App constants
APP_NAME = "Dotmini MCX"
APP_VERSION = "1.2.0"
ORGANIZATION_NAME = "DotminiTech"
CONFIG_PATH = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), 
                          ORGANIZATION_NAME, APP_NAME)

# Ensure config directory exists
os.makedirs(CONFIG_PATH, exist_ok=True)

# Import ThemeManager
from theme_manager import ThemeManager

# Import LicenseManager and LicenseDialog
from license_manager import LicenseManager, LicenseDialog

# Import classification components
from classification import load_model_safely, ClassificationThread

# Import file selection widgets
from file_widgets import FolderSelectionWidget, FileSelectionWidget

# Import brightness control
from brightness_control import BrightnessControl

# Import SettingsDialog
from settings_dialog import SettingsDialog

# Need DARKDETECT_AVAILABLE for SettingsDialog, ensure it's accessible or pass it if it's defined in theme_manager
# For now, assuming SettingsDialog correctly imports it or handles its absence.
# from theme_manager import DARKDETECT_AVAILABLE # This is already imported by settings_dialog.py

class DotminiMCX(QMainWindow):
    """The main window class for the Dotmini MCX application.
    
    This class sets up the user interface, manages application state,
    and handles interactions for image classification tasks.
    """
    def __init__(self):
        """Initializes the main application window and its components."""
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        
        # Create theme manager
        # self.theme_manager will be set by the main() function after QApplication is created.
        self.theme_manager = None 
        
        # Initialize UI
        self.init_ui()
        
        # Member variables
        self.classification_thread = None
        self.batch_size = 16 # Default batch size, loaded from settings in load_settings()
        self.recent_paths = [] # For storing recent file/folder paths
    
    def init_ui(self):
        """Sets up the main window's user interface layout and widgets."""
        self.setWindowTitle("Dotmini MCX - Image Classification Tool")
        self.setMinimumSize(900, 700)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create a container for scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with logo and title
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setText("🔍")
        logo_label.setStyleSheet("font-size: 32px;")
        
        title_label = QLabel("Dotmini MCX")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: #888888;")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(version_label)
        header_layout.addStretch()
        
        # Create cards for different sections
        
        # Input Selection Card
        input_card = QFrame()
        input_card.setObjectName("card")
        self.add_shadow(input_card)
        input_layout = QVBoxLayout(input_card)
        
        input_title = QLabel("Input Selection")
        input_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.input_folders_widget = FolderSelectionWidget("Input Image Folders", multiple=True, 
                                                        placeholder_text="Add folders containing images to classify...")
        
        input_layout.addWidget(input_title)
        input_layout.addWidget(self.input_folders_widget)
        
        # Model Selection Card
        model_card = QFrame()
        model_card.setObjectName("card")
        self.add_shadow(model_card)
        model_layout = QVBoxLayout(model_card)
        
        model_title = QLabel("Model Configuration")
        model_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.model_file_widget = FileSelectionWidget("Model File (.h5, .tflite)", 
                                                  "Model Files (*.h5 *.tflite *.pb);;All Files (*)",
                                                  "Select your ML model file...")
        
        self.label_file_widget = FileSelectionWidget("Labels File (.txt)", 
                                                  "Text Files (*.txt);;All Files (*)",
                                                  "Select your labels file...")
        
        model_layout.addWidget(model_title)
        model_layout.addWidget(self.model_file_widget)
        model_layout.addWidget(self.label_file_widget)
        
        # Output Selection Card
        output_card = QFrame()
        output_card.setObjectName("card")
        self.add_shadow(output_card)
        output_layout = QVBoxLayout(output_card)
        
        output_title = QLabel("Output Configuration")
        output_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.output_folder_widget = FolderSelectionWidget("Output Folder", multiple=False,
                                                       placeholder_text="Select folder to save classified images...")
        
        output_layout.addWidget(output_title)
        output_layout.addWidget(self.output_folder_widget)
        
        # Action Buttons
        actions_card = QFrame()
        actions_card.setObjectName("card")
        self.add_shadow(actions_card)
        actions_layout = QVBoxLayout(actions_card)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m (%p%)")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        button_layout = QHBoxLayout()
        
        self.classify_button = QPushButton("Start Classification")
        self.classify_button.setMinimumHeight(40)
        self.classify_button.clicked.connect(self.start_classification)
        self.classify_button.setToolTip("Begin classifying images using the selected model")
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.cancel_classification)
        self.cancel_button.setToolTip("Cancel the current classification process")
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.classify_button)
        
        actions_layout.addWidget(QLabel("Progress:"))
        actions_layout.addWidget(self.progress_bar)
        actions_layout.addLayout(button_layout)
        
        # Results area
        results_card = QFrame()
        results_card.setObjectName("card")
        self.add_shadow(results_card)
        results_layout = QVBoxLayout(results_card)
        
        results_title = QLabel("Classification Results")
        results_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Switch from QListWidget to a more sophisticated result view
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(200)
        self.results_list.setIconSize(QSize(40, 40))
        
        # Add results stats tracking
        self.results_stats_label = QLabel("No results yet")
        
        results_buttons_layout = QHBoxLayout()
        
        clear_results_button = QPushButton("Clear Results")
        clear_results_button.setObjectName("secondaryButton")
        clear_results_button.clicked.connect(self.clear_results)
        clear_results_button.setToolTip("Clear all classification results")
        
        export_results_button = QPushButton("Export Results")
        export_results_button.setObjectName("secondaryButton")
        export_results_button.clicked.connect(self.export_results)
        export_results_button.setToolTip("Save classification results to a CSV file")
        
        results_buttons_layout.addWidget(clear_results_button)
        results_buttons_layout.addWidget(export_results_button)
        
        results_layout.addWidget(results_title)
        results_layout.addWidget(self.results_stats_label)
        results_layout.addWidget(self.results_list)
        results_layout.addLayout(results_buttons_layout)
        
        # Add all sections to the scroll layout
        scroll_layout.addLayout(header_layout)
        scroll_layout.addWidget(input_card)
        scroll_layout.addWidget(model_card)
        scroll_layout.addWidget(output_card)
        scroll_layout.addWidget(actions_card)
        scroll_layout.addWidget(results_card)
        
        # Set the scroll widget and layout
        scroll_area.setWidget(scroll_widget)
        
        # Main layout just contains the scroll area
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # Load saved settings
        self.load_settings()
        
        # Center the window on screen
        self.center_on_screen()
    
    def create_toolbar(self):
        """Creates the main application toolbar with theme and settings actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add theme toggle button to toolbar
        # The icon will be updated by update_theme_ui
        theme_action = QAction("Toggle Theme", self) 
        theme_action.triggered.connect(self.toggle_theme)
        theme_action.setToolTip("Switch between light and dark mode")
        toolbar.addAction(theme_action)
        
        # Add spacer
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer_widget)
        
        # Add settings button
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        settings_action.setToolTip("Open application settings")
        toolbar.addAction(settings_action)
        
        self.addToolBar(toolbar)
    
    def create_menu_bar(self):
        """Creates the main application menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        # Recent files section
        self.recent_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Results", self)
        export_action.triggered.connect(self.export_results)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+T"))
        view_menu.addAction(toggle_theme_action)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
    
    def toggle_theme(self):
        """Toggles the application theme between light and dark modes."""
        if self.theme_manager:
            self.theme_manager.toggle_theme()
            # Update toolbar button (update_theme_ui is called by ThemeManager.apply_theme)
    
    def update_theme_ui(self):
        """Updates specific UI elements when the theme changes (e.g., toolbar icons)."""
        # Update toolbar button
        toolbar = self.findChild(QToolBar)
        if toolbar:
            for action in toolbar.actions():
                if "Toggle Theme" in action.text() or "🌙" in action.text() or "☀️" in action.text(): # Check for text or icons
                    theme_icon = "🌙" if self.theme_manager and self.theme_manager.current_theme == "light" else "☀️"
                    action.setText(f"{theme_icon} Toggle Theme")
                    break
    
    def add_shadow(self, widget):
        """Adds a pre-configured drop shadow effect to the given widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)
    
    def update_recent_menu(self):
        """Populates the 'Recent Files' menu with recently used paths."""
        self.recent_menu.clear()
        
        recent_paths = self.settings.value("recent/paths", [])
        if not isinstance(recent_paths, list): recent_paths = [] # Ensure it's a list

        if not recent_paths:
            no_recent = QAction("No recent files", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
            return
        
        for path in recent_paths:
            if not path: continue # Skip empty paths
            action = QAction(os.path.basename(path) or path, self) # Use full path if basename is empty
            action.setData(path)
            action.setToolTip(path)
            action.triggered.connect(self.load_recent_path)
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.recent_menu.addAction(clear_action)
    
    def load_recent_path(self):
        """Loads a path selected from the 'Recent Files' menu into the appropriate widget."""
        action = self.sender()
        if action:
            path = action.data()
            if os.path.isfile(path):
                # Determine whether it's a model or labels file based on extension
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.h5', '.tflite', '.pb']:
                    self.model_file_widget.set_path(path)
                elif ext in ['.txt']:
                    self.label_file_widget.set_path(path)
            elif os.path.isdir(path):
                # For directories, assume it's for input or output
                # A more sophisticated approach might be needed if context is ambiguous
                if not self.input_folders_widget.get_paths(): # If input is empty, populate it
                    self.input_folders_widget.set_paths([path])
                else: # Otherwise, assume it's for output
                    self.output_folder_widget.set_paths(path)
    
    def add_to_recent_files(self, path):
        """Adds a given path to the list of recent files in settings."""
        if not path:
            return
            
        recent_paths = self.settings.value("recent/paths", [])
        if not isinstance(recent_paths, list): # Ensure it's a list
            recent_paths = []
            
        # Remove duplicates
        if path in recent_paths:
            recent_paths.remove(path)
            
        # Add to the beginning of the list
        recent_paths.insert(0, path)
        
        # Limit to 10 recent paths
        recent_paths = recent_paths[:10]
        
        self.settings.setValue("recent/paths", recent_paths)
        self.update_recent_menu() # Refresh the menu
    
    def clear_recent_files(self):
        """Clears all entries from the 'Recent Files' list and menu."""
        self.settings.setValue("recent/paths", [])
        self.update_recent_menu()
    
    def show_settings(self):
        """Displays the application settings dialog."""
        if not self.theme_manager: return # Guard against missing theme_manager
        settings_dialog = SettingsDialog(self.theme_manager, self)
        if settings_dialog.exec():
            settings_dialog.save_settings() # Dialog now handles saving its own relevant settings
            # Batch size is saved by dialog, now main window needs to update its own batch_size
            self.batch_size = settings_dialog.get_batch_size() 
            self.settings.setValue("classification/batch_size", self.batch_size) # Also save to QSettings

            if self.theme_manager:
                 self.theme_manager.apply_theme() # Re-apply theme if settings changed it
    
    def show_about(self):
        """Displays the 'About' dialog with application information."""
        about_text = f"""<h2>Dotmini MCX v{APP_VERSION}</h2>
<p>A machine learning image classification tool with modern UI.</p>
<p>© 2023 DotminiTech</p>"""
        
        QMessageBox.about(self, "About Dotmini MCX", about_text)
    
    def show_documentation(self):
        """Displays a simple documentation/help message box."""
        help_text = """
<h2>Dotmini MCX - Quick Guide</h2>

<h3>Getting Started</h3>
<ol>
  <li>Add input folders containing images to classify</li>
  <li>Select your ML model file (*.h5, *.tflite, *.pb)</li>
  <li>Select your labels file (*.txt)</li>
  <li>Choose an output folder for classified images</li>
  <li>Click "Start Classification"</li>
</ol>

<h3>Features</h3>
<ul>
  <li>Drag and drop support for files and folders</li>
  <li>Light and dark theme</li>
  <li>Export classification results</li>
  <li>Automatic organization of classified images</li>
</ul>

<h3>Keyboard Shortcuts</h3>
<ul>
  <li>Ctrl+T: Toggle theme</li>
  <li>Ctrl+E: Export results</li>
  <li>Ctrl+,: Open settings</li>
  <li>Ctrl+Q: Exit application</li>
</ul>
"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Dotmini MCX Documentation")
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def load_settings(self):
        """Loads application settings from persistent storage (e.g., QSettings)."""
        # Load batch size
        self.batch_size = self.settings.value("classification/batch_size", 16, type=int)
        
        # Load last used paths
        last_model_path = self.settings.value("paths/model", "")
        if last_model_path: self.model_file_widget.set_path(last_model_path)
        
        last_label_path = self.settings.value("paths/labels", "")
        if last_label_path: self.label_file_widget.set_path(last_label_path)
        
        last_output_path = self.settings.value("paths/output", "")
        if last_output_path: self.output_folder_widget.set_paths(last_output_path)
        
        # Load input folders
        input_folders = self.settings.value("paths/input_folders", [])
        if isinstance(input_folders, list) and input_folders: # Ensure it's a non-empty list
            self.input_folders_widget.set_paths(input_folders)
        
        # Update recent files menu
        self.update_recent_menu()
    
    def save_settings(self):
        """Saves current application settings to persistent storage."""
        # Save batch size
        self.settings.setValue("classification/batch_size", self.batch_size)
        
        # Save paths
        model_path = self.model_file_widget.get_path()
        label_path = self.label_file_widget.get_path()
        output_path = self.output_folder_widget.get_paths() # This is a string
        input_folders = self.input_folders_widget.get_paths() # This is a list of strings
        
        if model_path: self.settings.setValue("paths/model", model_path)
        if label_path: self.settings.setValue("paths/labels", label_path)
        if output_path: self.settings.setValue("paths/output", output_path) # Save single path string
        if input_folders: self.settings.setValue("paths/input_folders", input_folders) # Save list
        
        # Add to recent files (these methods also update the menu)
        if model_path: self.add_to_recent_files(model_path)
        if label_path: self.add_to_recent_files(label_path)
        if output_path: self.add_to_recent_files(output_path)
        for folder in input_folders:
            if folder: self.add_to_recent_files(folder)
    
    def center_on_screen(self):
        """Centers the main window on the primary screen."""
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def start_classification(self):
        """Starts the image classification process in a separate thread."""
        # Validate inputs
        input_folders = self.input_folders_widget.get_paths()
        model_path = self.model_file_widget.get_path()
        label_path = self.label_file_widget.get_path()
        output_folder = self.output_folder_widget.get_paths() # Single string
        
        if not input_folders:
            QMessageBox.warning(self, "Input Error", "Please select at least one input folder.")
            return
        if not model_path:
            QMessageBox.warning(self, "Input Error", "Please select a model file.")
            return
        if not label_path:
            QMessageBox.warning(self, "Input Error", "Please select a labels file.")
            return
        if not output_folder:
            QMessageBox.warning(self, "Input Error", "Please select an output folder.")
            return
        
        # Save settings for next time
        self.save_settings()
        
        # Clear previous results
        self.clear_results()
        
        # Show status message
        self.statusBar().showMessage("Starting classification...")
        
        # Start classification thread
        self.classification_thread = ClassificationThread(
            model_path, label_path, input_folders, output_folder, self.batch_size
        )
        
        # Connect signals
        self.classification_thread.progress_update.connect(self.update_progress)
        self.classification_thread.result_update.connect(self.add_result)
        self.classification_thread.finished.connect(self.classification_finished)
        self.classification_thread.error.connect(self.show_error)
        
        # Update UI state
        self.classify_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Initialize result stats
        self.class_counts = {}
        self.total_processed = 0
        self.update_result_stats()
        
        # Start processing
        self.classification_thread.start()
    
    def cancel_classification(self):
        """Cancels the ongoing classification process."""
        if self.classification_thread is not None and self.classification_thread.isRunning():
            self.classification_thread.stop()
            self.classification_thread.wait() # Wait for thread to finish cleanly
            # classification_finished() will be called by the thread's finished signal
            self.statusBar().showMessage("Classification canceled by user.")
            self.add_result("", "Classification canceled by user.", "") # Add a message to results
    
    def update_progress(self, value, maximum):
        """Updates the progress bar and status message during classification."""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"Processing images: {value}/{maximum} ({int(value/maximum*100)}%)")
    
    def add_result(self, file_path, class_name, confidence):
        """Adds a classification result to the results list and updates statistics."""
        if file_path: # Actual result item
            item = QListWidgetItem()
            try:
                pixmap = QPixmap(file_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            except Exception as e: # Catch potential errors with QPixmap
                print(f"Error creating thumbnail for {file_path}: {e}")
                item.setIcon(QIcon()) # Use a generic icon
            
            item_text = f"{os.path.basename(file_path)} → {class_name} (confidence: {confidence})"
            item.setText(item_text)
            item.setToolTip(f"File: {file_path}\nClass: {class_name}\nConfidence: {confidence}")
            
            self.results_list.addItem(item)
            
            # Update statistics
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
            self.total_processed += 1
            self.update_result_stats()
        else: # For status messages like "canceled"
            item = QListWidgetItem()
            item.setText(class_name) # class_name here is the message string
            item.setForeground(QColor("#FF5555"))  # Red color for error/status messages
            self.results_list.addItem(item)
        
        self.results_list.scrollToBottom()
    
    def update_result_stats(self):
        """Updates the label displaying statistics about classification results."""
        if self.total_processed == 0:
            self.results_stats_label.setText("No results yet")
            return
        
        # Create statistics text
        stats_text = f"Total processed: {self.total_processed} images | Classes: "
        
        # Add class distribution
        class_stats = []
        for class_name, count in sorted(self.class_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.total_processed) * 100
            class_stats.append(f"{class_name}: {count} ({percentage:.1f}%)")
        
        stats_text += ", ".join(class_stats)
        self.results_stats_label.setText(stats_text)
    
    def classification_finished(self):
        """Handles tasks to perform after classification is complete or canceled."""
        self.classify_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.classification_thread = None # Clear the thread reference
        
        if self.total_processed > 0 and self.statusBar().currentMessage() != "Classification canceled by user.":
             self.statusBar().showMessage(f"Classification complete. Processed {self.total_processed} images.")
        elif self.statusBar().currentMessage() != "Classification canceled by user.": # If not canceled and no images processed
            self.statusBar().showMessage("Ready")
    
    def show_error(self, error_message):
        """Displays an error message in a message box and the status bar."""
        QMessageBox.critical(self, "Error", error_message)
        self.statusBar().showMessage(f"Error: {error_message}")
    
    def clear_results(self):
        """Clears all classification results from the list and resets statistics."""
        self.results_list.clear()
        self.class_counts = {}
        self.total_processed = 0
        self.update_result_stats()
        self.statusBar().showMessage("Results cleared.")
    
    def export_results(self):
        """Exports the current classification results to a CSV file."""
        if self.results_list.count() == 0:
            QMessageBox.information(self, "Export Results", "No results to export.")
            return
        
        # Ask for save location
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'w') as f:
                # Write header
                f.write("Filename,Class,Confidence\n")
                
                # Write each result
                for i in range(self.results_list.count()):
                    item = self.results_list.item(i)
                    text = item.text()
                    
                    # Skip status messages (no file path)
                    if "→" not in text:
                        continue
                    
                    # Parse the result text
                    parts = text.split("→")
                    if len(parts) != 2:
                        continue
                        
                    file_name_part = parts[0].strip() # Using file_name_part to avoid conflict
                    
                    # Extract class and confidence
                    class_conf = parts[1].strip()
                    class_name = class_conf.split("(confidence:")[0].strip()
                    
                    # Try to extract confidence value
                    confidence_val = "" # Using confidence_val to avoid conflict
                    if "confidence:" in class_conf:
                        confidence_val = class_conf.split("confidence:")[1].strip()
                        confidence_val = confidence_val.rstrip(")")
                    
                    # Write to CSV
                    f.write(f'"{file_name_part}","{class_name}",{confidence_val}\n')
                
            self.statusBar().showMessage(f"Results exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting results: {str(e)}")
    
    def closeEvent(self, event):
        """Handles the close event of the main window to save settings."""
        self.save_settings()
        event.accept()


def main():
    """Main function to launch the Dotmini MCX application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # Create a more visually appealing splash screen
    splash_size = QSize(500, 300)
    splash_pixmap = QPixmap(splash_size)
    splash_pixmap.fill(Qt.GlobalColor.transparent)  # Make transparent to start
    
    # Create a widget for the splash content
    splash_content = QWidget()
    splash_content.setObjectName("splashContent")
    splash_content.setFixedSize(splash_size)
    
    splash_layout = QVBoxLayout(splash_content)
    splash_layout.setContentsMargins(30, 30, 30, 30)
    splash_layout.setSpacing(15)
    
    # Logo and app name
    logo_label = QLabel("🔍")
    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo_label.setStyleSheet("font-size: 72px;")
    
    app_label = QLabel(APP_NAME)
    app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    app_label.setStyleSheet("font-size: 28px; font-weight: bold;")
    
    version_label = QLabel(f"Version {APP_VERSION}")
    version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    version_label.setStyleSheet("color: #888888; font-size: 14px;")
    
    # Progress indicator
    splash_progress = QProgressBar()
    splash_progress.setRange(0, 100)
    splash_progress.setValue(0)
    splash_progress.setTextVisible(False)
    splash_progress.setFixedHeight(6)
    
    # Add fade-in animation
    splash_opacity = QGraphicsOpacityEffect()
    splash_opacity.setOpacity(0)
    splash_content.setGraphicsEffect(splash_opacity)
    
    # Status label
    status_label = QLabel("Loading application...")
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Add widgets to layout
    splash_layout.addStretch()
    splash_layout.addWidget(logo_label)
    splash_layout.addWidget(app_label)
    splash_layout.addWidget(version_label)
    splash_layout.addStretch()
    splash_layout.addWidget(status_label)
    splash_layout.addWidget(splash_progress)
    
    # Render widget to pixmap
    splash_content.render(splash_pixmap)
    
    # Create and show splash screen
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    
    # Fade-in animation
    fade_anim = QPropertyAnimation(splash_opacity, b"opacity")
    fade_anim.setDuration(500)
    fade_anim.setStartValue(0)
    fade_anim.setEndValue(1)
    fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade_anim.start()
    
    # Progress animation
    progress_value = 0 # Ensure progress_value is defined in main's scope
    def update_splash_progress():
        nonlocal progress_value # Refer to progress_value in main's scope
        progress_value += 1
        splash_progress.setValue(progress_value)
        
        # Update status messages
        if progress_value == 20:
            status_label.setText("Initializing theme...")
        elif progress_value == 40:
            status_label.setText("Loading settings...")
        elif progress_value == 60:
            status_label.setText("Preparing interface...")
        elif progress_value == 80:
            status_label.setText("Almost ready...")
        
        # Re-render widget to pixmap
        splash_content.render(splash_pixmap) # Re-render with updated progress bar
        splash.setPixmap(splash_pixmap)
        
        if progress_value >= 100:
            progress_timer.stop() # Stop the timer when progress reaches 100
    
    # Start progress animation
    progress_timer = QTimer() # progress_timer should also be in main's scope
    progress_timer.timeout.connect(update_splash_progress)
    progress_timer.start(30)  # Update every 30ms for smooth animation
    
    # Check license first
    license_manager = LicenseManager()
    if not license_manager.is_valid_license():
        # Show license dialog if no valid license is stored
        license_dialog = LicenseDialog()
        if not license_dialog.exec():
            # Exit if license is not verified or user cancels
            return # Exit main()
    
    # Create theme manager
    theme_manager_instance = ThemeManager(app) # Renamed to avoid conflict
    
    # Create main window
    main_window = DotminiMCX()
    main_window.theme_manager = theme_manager_instance # Assign to main_window
    theme_manager_instance.main_window = main_window # Link back
    
    # Apply theme based on settings (ThemeManager constructor already does this)
    # theme_manager_instance.apply_theme() # Already called in ThemeManager.__init__
    main_window.update_theme_ui() # Ensure UI elements like toolbar icon are set
    
    # Finish splash screen after a slight delay and fade it out
    def show_main_window():
        # Start fade-out animation
        fade_out = QPropertyAnimation(splash_opacity, b"opacity")
        fade_out.setDuration(400)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_out.finished.connect(lambda: splash.finish(main_window))
        fade_out.start()
        
        # Show main window
        main_window.show()
    
    # Ensure splash screen completes its animation before showing main window
    # Use a timer that considers the progress animation duration
    QTimer.singleShot(3000, show_main_window) # 30ms * 100 updates = 3000ms
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
