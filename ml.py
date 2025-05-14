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
from tensorflow.keras.preprocessing import image
from PIL import Image
import glob

# For detecting OS theme
try:
    from darkdetect import isDark, theme, listener
    DARKDETECT_AVAILABLE = True
except ImportError:
    DARKDETECT_AVAILABLE = False

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

class ThemeManager:
    def __init__(self, app, main_window=None):
        self.app = app
        self.main_window = main_window
        self.current_theme = "dark"  # Default theme
        self.brightness = 100  # Default brightness (percentage)
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        
        # Load saved preferences
        self.load_settings()
        
        # Set up theme detection
        if DARKDETECT_AVAILABLE:
            self.detect_system_theme()
            listener(self.on_system_theme_change)
        
        # Apply initial theme
        self.apply_theme()
    
    def load_settings(self):
        theme_mode = self.settings.value("theme/mode", None)
        if theme_mode:
            self.current_theme = theme_mode
        
        saved_brightness = self.settings.value("theme/brightness", None)
        if saved_brightness is not None:
            try:
                self.brightness = int(saved_brightness)
            except (ValueError, TypeError):
                self.brightness = 100
    
    def save_settings(self):
        self.settings.setValue("theme/mode", self.current_theme)
        self.settings.setValue("theme/brightness", self.brightness)
    
    def detect_system_theme(self):
        if DARKDETECT_AVAILABLE:
            self.current_theme = "dark" if isDark() else "light"
            self.save_settings()
    
    def on_system_theme_change(self):
        if DARKDETECT_AVAILABLE:
            new_theme = "dark" if isDark() else "light"
            if new_theme != self.current_theme:
                self.current_theme = new_theme
                self.save_settings()
                self.apply_theme()
    
    def set_brightness(self, value):
        self.brightness = value
        self.save_settings()
        self.apply_theme()
    
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.save_settings()
        self.apply_theme()
    
    def apply_theme(self):
        # Generate CSS based on theme and brightness
        if self.current_theme == "dark":
            # Calculate adjusted colors based on brightness
            brightness_factor = self.brightness / 100.0
            
            # Background colors
            bg_color = self._adjust_color("#1e1e1e", brightness_factor)
            card_bg_color = self._adjust_color("#2d2d2d", brightness_factor)
            input_bg_color = self._adjust_color("#333333", brightness_factor)
            
            # Text colors
            text_color = self._adjust_color("#ffffff", brightness_factor)
            secondary_text = self._adjust_color("#bbbbbb", brightness_factor)
            
            # Accent colors
            accent_color = self._adjust_color("#0071e3", brightness_factor)
            accent_hover = self._adjust_color("#0077ED", brightness_factor)
            accent_pressed = self._adjust_color("#005BBB", brightness_factor)
            border_color = self._adjust_color("#3d3d3d", brightness_factor)
            
            # Generate stylesheet
            stylesheet = f"""
                QMainWindow, QDialog, QWidget#splashContent {{
                    background-color: {bg_color};
                }}
                QLabel {{
                    color: {text_color};
                    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                }}
                QLineEdit, QComboBox, QListWidget {{
                    padding: 8px;
                    border-radius: 6px;
                    background-color: {input_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    font-size: 13px;
                }}
                QPushButton {{
                    padding: 10px 15px;
                    border-radius: 6px;
                    background-color: {accent_color};
                    color: {text_color};
                    border: none;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {accent_pressed};
                }}
                QPushButton:disabled {{
                    background-color: #555555;
                    color: #888888;
                }}
                QPushButton#secondaryButton {{
                    background-color: {input_bg_color};
                }}
                QPushButton#secondaryButton:hover {{
                    background-color: #444444;
                }}
                QToolBar {{
                    background-color: {card_bg_color};
                    border: none;
                    spacing: 10px;
                    padding: 5px;
                }}
                QStatusBar {{
                    background-color: {card_bg_color};
                    color: {secondary_text};
                    border-top: 1px solid {border_color};
                }}
                QProgressBar {{
                    border: none;
                    border-radius: 6px;
                    background-color: {input_bg_color};
                    text-align: center;
                    color: {text_color};
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: {accent_color};
                    border-radius: 6px;
                }}
                QListWidget {{
                    background-color: {input_bg_color};
                    border-radius: 6px;
                    color: {text_color};
                    padding: 5px;
                }}
                QListWidget::item {{
                    border-radius: 4px;
                    padding: 8px;
                    margin: 2px 0px;
                }}
                QListWidget::item:selected {{
                    background-color: {accent_color};
                }}
                QScrollArea {{
                    border: none;
                    background-color: {bg_color};
                }}
                QFrame#card {{
                    background-color: {card_bg_color};
                    border-radius: 10px;
                    border: 1px solid {border_color};
                }}
                QFrame#resultItem {{
                    background-color: {card_bg_color};
                    border-radius: 6px;
                    border: 1px solid {border_color};
                    padding: 10px;
                    margin: 5px;
                }}
                QSlider::groove:horizontal {{
                    height: 8px;
                    background: #555555;
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {accent_color};
                    border: none;
                    width: 18px;
                    margin: -5px 0;
                    border-radius: 9px;
                }}
                QSlider::add-page:horizontal {{
                    background: #555555;
                    border-radius: 4px;
                }}
                QSlider::sub-page:horizontal {{
                    background: {accent_color};
                    border-radius: 4px;
                }}
                QCheckBox {{
                    color: {text_color};
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid {accent_color};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {accent_color};
                }}
                QMessageBox {{
                    background-color: {bg_color};
                }}
                QMessageBox QLabel {{
                    color: {text_color};
                }}
                QMenu {{
                    background-color: {card_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 6px 25px 6px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {accent_color};
                }}
                QMenuBar {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QMenuBar::item {{
                    padding: 5px 10px;
                    border-radius: 4px;
                }}
                QMenuBar::item:selected {{
                    background-color: {accent_color};
                }}
                QToolTip {{
                    background-color: {card_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 5px;
                }}
            """
        else:  # Light theme
            brightness_factor = self.brightness / 100.0
            
            # Calculate adjusted colors
            bg_color = self._adjust_color("#f5f5f7", brightness_factor)
            card_bg_color = self._adjust_color("#ffffff", brightness_factor)
            input_bg_color = self._adjust_color("#e7e7e7", brightness_factor)
            text_color = self._adjust_color("#121212", brightness_factor)
            secondary_text = self._adjust_color("#555555", brightness_factor)
            accent_color = self._adjust_color("#0071e3", brightness_factor)
            accent_hover = self._adjust_color("#0077ED", brightness_factor)
            accent_pressed = self._adjust_color("#005BBB", brightness_factor)
            border_color = self._adjust_color("#d1d1d1", brightness_factor)
            
            # Generate stylesheet
            stylesheet = f"""
                QMainWindow, QDialog, QWidget#splashContent {{
                    background-color: {bg_color};
                }}
                QLabel {{
                    color: {text_color};
                    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                }}
                QLineEdit, QComboBox, QListWidget {{
                    padding: 8px;
                    border-radius: 6px;
                    background-color: {input_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    font-size: 13px;
                }}
                QPushButton {{
                    padding: 10px 15px;
                    border-radius: 6px;
                    background-color: {accent_color};
                    color: white;
                    border: none;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {accent_pressed};
                }}
                QPushButton:disabled {{
                    background-color: #c0c0c0;
                    color: #888888;
                }}
                QPushButton#secondaryButton {{
                    background-color: {input_bg_color};
                    color: {text_color};
                }}
                QPushButton#secondaryButton:hover {{
                    background-color: #d5d5d5;
                }}
                QToolBar {{
                    background-color: {card_bg_color};
                    border: none;
                    spacing: 10px;
                    padding: 5px;
                }}
                QStatusBar {{
                    background-color: {card_bg_color};
                    color: {secondary_text};
                    border-top: 1px solid {border_color};
                }}
                QProgressBar {{
                    border: none;
                    border-radius: 6px;
                    background-color: {input_bg_color};
                    text-align: center;
                    color: {text_color};
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: {accent_color};
                    border-radius: 6px;
                }}
                QListWidget {{
                    background-color: {input_bg_color};
                    border-radius: 6px;
                    color: {text_color};
                    padding: 5px;
                }}
                QListWidget::item {{
                    border-radius: 4px;
                    padding: 8px;
                    margin: 2px 0px;
                }}
                QListWidget::item:selected {{
                    background-color: {accent_color};
                    color: white;
                }}
                QScrollArea {{
                    border: none;
                    background-color: {bg_color};
                }}
                QFrame#card {{
                    background-color: {card_bg_color};
                    border-radius: 10px;
                    border: 1px solid {border_color};
                }}
                QFrame#resultItem {{
                    background-color: {card_bg_color};
                    border-radius: 6px;
                    border: 1px solid {border_color};
                    padding: 10px;
                    margin: 5px;
                }}
                QSlider::groove:horizontal {{
                    height: 8px;
                    background: #c0c0c0;
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {accent_color};
                    border: none;
                    width: 18px;
                    margin: -5px 0;
                    border-radius: 9px;
                }}
                QSlider::add-page:horizontal {{
                    background: #c0c0c0;
                    border-radius: 4px;
                }}
                QSlider::sub-page:horizontal {{
                    background: {accent_color};
                    border-radius: 4px;
                }}
                QCheckBox {{
                    color: {text_color};
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid {accent_color};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {accent_color};
                }}
                QMessageBox {{
                    background-color: {bg_color};
                }}
                QMessageBox QLabel {{
                    color: {text_color};
                }}
                QMenu {{
                    background-color: {card_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 6px 25px 6px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {accent_color};
                    color: white;
                }}
                QMenuBar {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QMenuBar::item {{
                    padding: 5px 10px;
                    border-radius: 4px;
                }}
                QMenuBar::item:selected {{
                    background-color: {accent_color};
                    color: white;
                }}
                QToolTip {{
                    background-color: {card_bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 5px;
                }}
            """
        
        self.app.setStyleSheet(stylesheet)
        
        # Update main window UI elements if needed
        if self.main_window:
            self.main_window.update_theme_ui()
    
    def _adjust_color(self, hex_color, brightness_factor):
        """Adjust color brightness based on the brightness factor"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        if brightness_factor < 1.0:  # Darkening
            r = int(r * brightness_factor)
            g = int(g * brightness_factor)
            b = int(b * brightness_factor)
        elif brightness_factor > 1.0:  # Lightening
            # Calculate how much room we have to brighten
            r = int(min(r + (255 - r) * (brightness_factor - 1), 255))
            g = int(min(g + (255 - g) * (brightness_factor - 1), 255))
            b = int(min(b + (255 - b) * (brightness_factor - 1), 255))
        
        # Return as hex
        return f"#{r:02x}{g:02x}{b:02x}"


class LicenseManager:
    def __init__(self):
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.correct_key = "D1QE80fxUUVcNs4VAAOvNNkJvHHy0dWM"
    
    def is_valid_license(self):
        """Check if a valid license key is already stored"""
        saved_key = self.settings.value("license/key", None)
        saved_hash = self.settings.value("license/hash", None)
        
        if saved_key and saved_hash:
            # Verify hash to prevent tampering
            computed_hash = self._hash_key(saved_key)
            if computed_hash == saved_hash and saved_key == self.correct_key:
                return True
        
        return False
    
    def save_license(self, key):
        """Save a valid license key"""
        if key == self.correct_key:
            key_hash = self._hash_key(key)
            self.settings.setValue("license/key", key)
            self.settings.setValue("license/hash", key_hash)
            return True
        return False
    
    def _hash_key(self, key):
        """Generate a hash of the license key with a salt"""
        salt = b"DotminiMCX_salt"  # Use a consistent salt
        key_bytes = key.encode('utf-8')
        return hashlib.sha256(key_bytes + salt).hexdigest()


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dotmini MCX License Verification")
        self.setFixedSize(450, 280)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        # Create license manager
        self.license_manager = LicenseManager()
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Content widget for styling
        content_widget = QWidget()
        content_widget.setObjectName("splashContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)
        
        # Logo and title
        title_label = QLabel(f"Dotmini MCX v{APP_VERSION}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        
        logo_label = QLabel("🔍")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px;")
        
        self.msg_label = QLabel("Please enter your license key to continue:")
        
        # Add a card for the license input
        license_frame = QFrame()
        license_frame.setObjectName("card")
        license_layout = QVBoxLayout(license_frame)
        license_layout.setContentsMargins(15, 15, 15, 15)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your license key...")
        
        # Create keyboard shortcuts for paste
        paste_shortcut = QAction("Paste", self)
        paste_shortcut.setShortcut(QKeySequence.StandardKey.Paste)
        paste_shortcut.triggered.connect(self.paste_from_clipboard)
        self.key_input.addAction(paste_shortcut)
        
        # Remember license checkbox
        self.remember_checkbox = QCheckBox("Remember license key")
        self.remember_checkbox.setChecked(True)
        
        license_layout.addWidget(self.key_input)
        license_layout.addWidget(self.remember_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.verify_button = QPushButton("Verify License")
        self.verify_button.clicked.connect(self.verify_license)
        
        quit_button = QPushButton("Quit")
        quit_button.setObjectName("secondaryButton")
        quit_button.clicked.connect(self.reject)
        
        button_layout.addWidget(quit_button)
        button_layout.addWidget(self.verify_button)
        
        # Add widgets to layout
        content_layout.addWidget(logo_label)
        content_layout.addWidget(title_label)
        content_layout.addWidget(self.msg_label)
        content_layout.addWidget(license_frame)
        content_layout.addLayout(button_layout)
        
        # Add shadow effect to content widget
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        content_widget.setGraphicsEffect(shadow)
        
        # Add content widget to main layout
        layout.addWidget(content_widget)
        self.setLayout(layout)
        
        # Center on screen
        self.center_on_screen()
        
        # Set default button and key event
        self.key_input.returnPressed.connect(self.verify_license)
        self.verify_button.setDefault(True)
        
        # Add tip for demo key
        tip_label = QLabel("Tip: For demo purposes, use key: D1QE80fxUUVcNs4VAAOvNNkJvHHy0dWM")
        tip_label.setStyleSheet("color: #888888; font-size: 10px;")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tip_label)

    def center_on_screen(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def paste_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        self.key_input.setText(clipboard.text())

    def verify_license(self):
        entered_key = self.key_input.text().strip()
        
        if self.license_manager.correct_key == entered_key:
            if self.remember_checkbox.isChecked():
                self.license_manager.save_license(entered_key)
            self.accept()
        else:
            self.msg_label.setText("Invalid license key. Please try again.")
            self.msg_label.setStyleSheet("color: #FF5555;")
            # Shake animation to indicate error
            self.shake_animation()
    
    def shake_animation(self):
        """Create a shake animation to indicate invalid input"""
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(100)
        
        current_pos = self.pos()
        x, y = current_pos.x(), current_pos.y()
        
        self.animation.setKeyValueAt(0, QPoint(x, y))
        self.animation.setKeyValueAt(0.1, QPoint(x + 10, y))
        self.animation.setKeyValueAt(0.2, QPoint(x - 10, y))
        self.animation.setKeyValueAt(0.3, QPoint(x + 10, y))
        self.animation.setKeyValueAt(0.4, QPoint(x - 10, y))
        self.animation.setKeyValueAt(0.5, QPoint(x + 10, y))
        self.animation.setKeyValueAt(0.6, QPoint(x - 10, y))
        self.animation.setKeyValueAt(0.7, QPoint(x + 10, y))
        self.animation.setKeyValueAt(0.8, QPoint(x - 10, y))
        self.animation.setKeyValueAt(0.9, QPoint(x + 5, y))
        self.animation.setKeyValueAt(1, QPoint(x, y))
        
        self.animation.start()


# Custom model loader to fix DepthwiseConv2D issue
def load_model_safely(model_path):
    """Load model with custom objects to handle the DepthwiseConv2D issue"""
    try:
        # First try to load the model with standard TF method
        model = tf.keras.models.load_model(model_path, compile=False)
        return model
    except Exception as e:
        error_str = str(e)
        
        # Check if it's the specific DepthwiseConv2D error we're trying to fix
        if "DepthwiseConv2D" in error_str and "groups" in error_str:
            print("Detected DepthwiseConv2D issue, trying custom loader...")
            
            # Define a custom DepthwiseConv2D layer to handle the 'groups' parameter
            class CustomDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
                def __init__(self, **kwargs):
                    # Remove 'groups' parameter if present
                    if 'groups' in kwargs:
                        del kwargs['groups']
                    super().__init__(**kwargs)
            
            # Load the model with the custom object
            model = tf.keras.models.load_model(
                model_path,
                custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D},
                compile=False
            )
            return model
        else:
            # If it's a different error, re-raise
            raise


class ClassificationThread(QThread):
    progress_update = pyqtSignal(int, int)
    result_update = pyqtSignal(str, str, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model_path, label_path, input_folders, output_folder, batch_size=16):
        super().__init__()
        self.model_path = model_path
        self.label_path = label_path
        self.input_folders = input_folders
        self.output_folder = output_folder
        self.batch_size = batch_size
        self.is_running = True
        
        # Performance optimization
        self.max_workers = min(os.cpu_count() or 4, 8)  # Limit thread count

    def run(self):
        try:
            # Load the model using our safe loader
            model = load_model_safely(self.model_path)
            
            # Load labels
            with open(self.label_path, 'r') as f:
                labels = [line.strip() for line in f.readlines()]
            
            # Get all image files from input folders
            image_files = []
            for folder in self.input_folders:
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                    image_files.extend(glob.glob(os.path.join(folder, ext)))
                    image_files.extend(glob.glob(os.path.join(folder, '**', ext), recursive=True))
            
            # Remove duplicates
            image_files = list(set(image_files))
            total_files = len(image_files)
            processed = 0
            
            # Create output folders for all classes in advance
            for class_name in labels:
                class_folder = os.path.join(self.output_folder, class_name)
                os.makedirs(class_folder, exist_ok=True)
            
            # Process images in batches for better performance
            for i in range(0, total_files, self.batch_size):
                if not self.is_running:
                    break
                
                batch_files = image_files[i:i+self.batch_size]
                batch_results = []
                
                # Process batch in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    for img_path in batch_files:
                        futures.append(executor.submit(self.process_image, img_path, model, labels))
                    
                    for future in concurrent.futures.as_completed(futures):
                        if not self.is_running:
                            break
                        
                        result = future.result()
                        if result:
                            batch_results.append(result)
                            processed += 1
                            self.progress_update.emit(processed, total_files)
                
                # Update UI with batch results
                for result in batch_results:
                    if not self.is_running:
                        break
                    
                    img_path, predicted_class, confidence, output_path = result
                    self.result_update.emit(img_path, predicted_class, f"{confidence:.2f}")
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Error in classification process: {str(e)}")
            self.finished.emit()
    
    def process_image(self, img_path, model, labels):
        """Process a single image and return the results"""
        try:
            # Preprocess image
            img = Image.open(img_path).convert('RGB')
            img = img.resize((224, 224))  # Adjust size according to your model
            img_array = np.array(img) / 255.0  # Normalize
            img_array = np.expand_dims(img_array, axis=0)
            
            # Make prediction
            predictions = model.predict(img_array, verbose=0)  # Disable verbose output
            predicted_class_idx = np.argmax(predictions[0])
            predicted_class = labels[predicted_class_idx]
            confidence = float(predictions[0][predicted_class_idx])
            
            # Prepare output path
            class_folder = os.path.join(self.output_folder, predicted_class)
            filename = os.path.basename(img_path)
            output_path = os.path.join(class_folder, filename)
            
            # Save the image to the output folder
            img.save(output_path)
            
            return (img_path, predicted_class, confidence, output_path)
        
        except Exception as e:
            self.error.emit(f"Error processing {img_path}: {str(e)}")
            return None
    
    def stop(self):
        self.is_running = False


class FolderSelectionWidget(QWidget):
    def __init__(self, title, multiple=False, placeholder_text="Select folder..."):
        super().__init__()
        self.multiple = multiple
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(placeholder_text)
        self.path_input.setReadOnly(True)
        
        browse_button = QPushButton("Browse")
        browse_button.setFixedWidth(100)
        browse_button.clicked.connect(self.browse_folder)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.path_input)
        input_layout.addWidget(browse_button)
        
        if multiple:
            self.folder_list = QListWidget()
            self.folder_list.setMaximumHeight(120)
            self.folder_list.setDragDropMode(QListWidget.DragDropMode.DragDrop)
            self.folder_list.setAcceptDrops(True)
            self.folder_list.viewport().setAcceptDrops(True)
            self.folder_list.setDropIndicatorShown(True)
            self.folder_list.dragEnterEvent = self.dragEnterEvent
            self.folder_list.dragMoveEvent = self.dragMoveEvent
            self.folder_list.dropEvent = self.dropEvent

            # Add a drop zone label
            self.drop_label = QLabel("Drop folders here or use Browse button")
            self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drop_label.setStyleSheet("color: #888888; font-style: italic; padding: 10px;")
            
            layout.addWidget(title_label)
            layout.addLayout(input_layout)
            layout.addWidget(self.drop_label)
            layout.addWidget(self.folder_list)
            
            buttons_layout = QHBoxLayout()
            
            remove_button = QPushButton("Remove Selected")
            remove_button.setObjectName("secondaryButton")
            remove_button.clicked.connect(self.remove_selected)
            
            clear_button = QPushButton("Clear All")
            clear_button.setObjectName("secondaryButton")
            clear_button.clicked.connect(self.clear_all)
            
            buttons_layout.addWidget(remove_button)
            buttons_layout.addWidget(clear_button)
            
            layout.addLayout(buttons_layout)
        else:
            # Setup drop area for single folder selection too
            self.setAcceptDrops(True)
            
            # Add a visual drop zone
            drop_zone = QFrame()
            drop_zone.setObjectName("card")
            drop_zone.setMinimumHeight(80)
            drop_layout = QVBoxLayout(drop_zone)
            
            self.drop_label = QLabel("Drop folder here or use Browse button")
            self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drop_label.setStyleSheet("color: #888888; font-style: italic;")
            
            drop_layout.addWidget(self.drop_label)
            
            layout.addWidget(title_label)
            layout.addLayout(input_layout)
            layout.addWidget(drop_zone)
        
        self.setLayout(layout)
        
    def browse_folder(self):
        if self.multiple:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                if self.folder_list.findItems(folder, Qt.MatchFlag.MatchExactly) == []:
                    self.folder_list.addItem(folder)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.path_input.setText(folder)
    
    def remove_selected(self):
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))
    
    def clear_all(self):
        self.folder_list.clear()
    
    def get_paths(self):
        if self.multiple:
            return [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        else:
            return self.path_input.text()
    
    def set_paths(self, paths):
        if self.multiple and isinstance(paths, list):
            self.folder_list.clear()
            for path in paths:
                self.folder_list.addItem(path)
        elif not self.multiple and isinstance(paths, str):
            self.path_input.setText(paths)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    if self.multiple:
                        # Check if the path already exists in the list
                        if self.folder_list.findItems(path, Qt.MatchFlag.MatchExactly) == []:
                            self.folder_list.addItem(path)
                    else:
                        self.path_input.setText(path)
                        break  # Only use the first folder for single selection
            
            event.acceptProposedAction()


class FileSelectionWidget(QWidget):
    def __init__(self, title, file_filter="All Files (*)", placeholder_text="Select file..."):
        super().__init__()
        self.file_filter = file_filter
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(placeholder_text)
        self.path_input.setReadOnly(True)
        
        browse_button = QPushButton("Browse")
        browse_button.setFixedWidth(100)
        browse_button.clicked.connect(self.browse_file)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.path_input)
        input_layout.addWidget(browse_button)
        
        # Add a visual drop zone
        drop_zone = QFrame()
        drop_zone.setObjectName("card")
        drop_zone.setMinimumHeight(80)
        drop_layout = QVBoxLayout(drop_zone)
        
        self.drop_label = QLabel("Drop file here or use Browse button")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("color: #888888; font-style: italic;")
        
        drop_layout.addWidget(self.drop_label)
        
        layout.addWidget(title_label)
        layout.addLayout(input_layout)
        layout.addWidget(drop_zone)
        
        self.setLayout(layout)
    
    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.file_filter)
        if file:
            self.path_input.setText(file)
    
    def get_path(self):
        return self.path_input.text()
    
    def set_path(self, path):
        self.path_input.setText(path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    # Check if file matches the filter
                    file_ext = os.path.splitext(path)[1].lower()
                    
                    # Extract extensions from filter
                    filter_exts = []
                    for filter_part in self.file_filter.split(';;'):
                        if '(*)' in filter_part:  # All files
                            self.path_input.setText(path)
                            event.acceptProposedAction()
                            return
                        
                        ext_part = filter_part.split('(')[1].split(')')[0] if '(' in filter_part else ""
                        exts = [e.strip().lower() for e in ext_part.split() if e.startswith('*.')]
                        filter_exts.extend([e[1:] for e in exts])  # Remove the '*'
                    
                    # If no specific extensions or file matches the filter
                    if not filter_exts or file_ext in filter_exts:
                        self.path_input.setText(path)
                        break
            
            event.acceptProposedAction()


class BrightnessControl(QWidget):
    brightnessChanged = pyqtSignal(int)
    
    def __init__(self, initial_value=100):
        super().__init__()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        
        brightness_label = QLabel("Brightness")
        brightness_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.value_label = QLabel(f"{initial_value}%")
        
        header_layout.addWidget(brightness_label)
        header_layout.addStretch()
        header_layout.addWidget(self.value_label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(50)  # Minimum 50% brightness
        self.slider.setMaximum(150)  # Maximum 150% brightness
        self.slider.setValue(initial_value)
        self.slider.setTracking(True)
        
        self.slider.valueChanged.connect(self.on_value_changed)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        dim_button = QPushButton("Dim")
        dim_button.setObjectName("secondaryButton")
        dim_button.setFixedWidth(80)
        dim_button.clicked.connect(self.on_dim_clicked)
        
        reset_button = QPushButton("Reset")
        reset_button.setObjectName("secondaryButton")
        reset_button.setFixedWidth(80)
        reset_button.clicked.connect(self.on_reset_clicked)
        
        bright_button = QPushButton("Bright")
        bright_button.setObjectName("secondaryButton")
        bright_button.setFixedWidth(80)
        bright_button.clicked.connect(self.on_bright_clicked)
        
        controls_layout.addWidget(dim_button)
        controls_layout.addStretch()
        controls_layout.addWidget(reset_button)
        controls_layout.addStretch()
        controls_layout.addWidget(bright_button)
        
        # Add all to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.slider)
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def on_value_changed(self, value):
        self.value_label.setText(f"{value}%")
        self.brightnessChanged.emit(value)
    
    def on_dim_clicked(self):
        current_value = self.slider.value()
        new_value = max(current_value - 10, self.slider.minimum())
        self.slider.setValue(new_value)
    
    def on_reset_clicked(self):
        self.slider.setValue(100)
    
    def on_bright_clicked(self):
        current_value = self.slider.value()
        new_value = min(current_value + 10, self.slider.maximum())
        self.slider.setValue(new_value)
    
    def get_brightness(self):
        return self.slider.value()
    
    def set_brightness(self, value):
        self.slider.setValue(value)


class SettingsDialog(QDialog):
    settingsChanged = pyqtSignal()
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        
        self.setWindowTitle("Dotmini MCX Settings")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Theme selection
        theme_frame = QFrame()
        theme_frame.setObjectName("card")
        theme_layout = QVBoxLayout(theme_frame)
        
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.theme_auto = QCheckBox("Auto (use system theme)")
        self.theme_auto.setChecked(True)
        
        theme_button_layout = QHBoxLayout()
        
        self.light_theme_button = QPushButton("Light")
        self.light_theme_button.setCheckable(True)
        
        self.dark_theme_button = QPushButton("Dark")
        self.dark_theme_button.setCheckable(True)
        
        # Set initial state
        if self.theme_manager.current_theme == "light":
            self.theme_auto.setChecked(False)
            self.light_theme_button.setChecked(True)
            self.dark_theme_button.setChecked(False)
        elif self.theme_manager.current_theme == "dark":
            self.theme_auto.setChecked(False)
            self.light_theme_button.setChecked(False)
            self.dark_theme_button.setChecked(True)
        
        # Connect theme change signals
        self.theme_auto.toggled.connect(self.on_theme_auto_changed)
        self.light_theme_button.clicked.connect(self.on_light_theme_clicked)
        self.dark_theme_button.clicked.connect(self.on_dark_theme_clicked)
        
        theme_button_layout.addWidget(self.light_theme_button)
        theme_button_layout.addWidget(self.dark_theme_button)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_auto)
        theme_layout.addLayout(theme_button_layout)
        
        # Brightness control
        brightness_frame = QFrame()
        brightness_frame.setObjectName("card")
        brightness_layout = QVBoxLayout(brightness_frame)
        
        brightness_label = QLabel("Appearance")
        brightness_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.brightness_control = BrightnessControl(self.theme_manager.brightness)
        self.brightness_control.brightnessChanged.connect(self.on_brightness_changed)
        
        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(self.brightness_control)
        
        # Classification settings
        classification_frame = QFrame()
        classification_frame.setObjectName("card")
        classification_layout = QVBoxLayout(classification_frame)
        
        classification_label = QLabel("Classification Settings")
        classification_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.batch_size_label = QLabel("Batch Size:")
        self.batch_size_combo = QComboBox()
        for size in [1, 4, 8, 16, 32, 64]:
            self.batch_size_combo.addItem(str(size))
        self.batch_size_combo.setCurrentText("16")  # Default batch size
        
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(self.batch_size_label)
        batch_layout.addWidget(self.batch_size_combo)
        
        classification_layout.addWidget(classification_label)
        classification_layout.addLayout(batch_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        # Add all to main layout
        layout.addWidget(theme_frame)
        layout.addWidget(brightness_frame)
        layout.addWidget(classification_frame)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_theme_auto_changed(self, checked):
        if checked:
            # Enable system theme detection
            if DARKDETECT_AVAILABLE:
                self.theme_manager.detect_system_theme()
                self.theme_manager.apply_theme()
            
            # Update buttons
            self.light_theme_button.setChecked(False)
            self.dark_theme_button.setChecked(False)
    
    def on_light_theme_clicked(self):
        self.theme_auto.setChecked(False)
        self.light_theme_button.setChecked(True)
        self.dark_theme_button.setChecked(False)
        self.theme_manager.current_theme = "light"
        self.theme_manager.apply_theme()
    
    def on_dark_theme_clicked(self):
        self.theme_auto.setChecked(False)
        self.light_theme_button.setChecked(False)
        self.dark_theme_button.setChecked(True)
        self.theme_manager.current_theme = "dark"
        self.theme_manager.apply_theme()
    
    def on_brightness_changed(self, value):
        self.theme_manager.set_brightness(value)
    
    def save_settings(self):
        # Save settings
        self.theme_manager.save_settings()
        
        # Emit signal to notify main window
        self.settingsChanged.emit()


class DotminiMCX(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        
        # Create theme manager
        self.theme_manager = None  # Will be set after QApplication is created
        
        # Initialize UI
        self.init_ui()
        
        # Member variables
        self.classification_thread = None
        self.batch_size = 16
        self.recent_paths = []
    
    def init_ui(self):
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
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add theme toggle button to toolbar
        theme_icon = "🌙" if self.theme_manager and self.theme_manager.current_theme == "light" else "☀️"
        theme_action = QAction(f"{theme_icon} Toggle Theme", self)
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
        if self.theme_manager:
            self.theme_manager.toggle_theme()
            # Update toolbar button
            for action in self.findChild(QToolBar).actions():
                if "Toggle Theme" in action.text():
                    theme_icon = "🌙" if self.theme_manager.current_theme == "light" else "☀️"
                    action.setText(f"{theme_icon} Toggle Theme")
                    break
    
    def update_theme_ui(self):
        """Called when theme is changed to update UI elements that need specific handling"""
        # Update toolbar button
        for action in self.findChild(QToolBar).actions():
            if "Toggle Theme" in action.text():
                theme_icon = "🌙" if self.theme_manager.current_theme == "light" else "☀️"
                action.setText(f"{theme_icon} Toggle Theme")
                break
    
    def add_shadow(self, widget):
        """Add shadow effect to a widget"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)
    
    def update_recent_menu(self):
        """Update the recent files menu with saved recent paths"""
        self.recent_menu.clear()
        
        recent_paths = self.settings.value("recent/paths", [])
        if not recent_paths:
            no_recent = QAction("No recent files", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
            return
        
        for path in recent_paths:
            action = QAction(os.path.basename(path), self)
            action.setData(path)
            action.setToolTip(path)
            action.triggered.connect(self.load_recent_path)
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.recent_menu.addAction(clear_action)
    
    def load_recent_path(self):
        """Load a selected recent path"""
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
                # For directories, try to determine the context
                if self.input_folders_widget.get_paths():
                    self.output_folder_widget.set_paths(path)
                else:
                    self.input_folders_widget.set_paths([path])
    
    def add_to_recent_files(self, path):
        """Add a path to recent files"""
        if not path:
            return
            
        recent_paths = self.settings.value("recent/paths", [])
        if not isinstance(recent_paths, list):
            recent_paths = []
            
        # Remove duplicates
        if path in recent_paths:
            recent_paths.remove(path)
            
        # Add to the beginning of the list
        recent_paths.insert(0, path)
        
        # Limit to 10 recent paths
        recent_paths = recent_paths[:10]
        
        self.settings.setValue("recent/paths", recent_paths)
        self.update_recent_menu()
    
    def clear_recent_files(self):
        """Clear all recent files"""
        self.settings.setValue("recent/paths", [])
        self.update_recent_menu()
    
    def show_settings(self):
        settings_dialog = SettingsDialog(self.theme_manager, self)
        if settings_dialog.exec():
            settings_dialog.save_settings()
            self.load_settings()
    
    def show_about(self):
        about_text = f"""<h2>Dotmini MCX v{APP_VERSION}</h2>
<p>A machine learning image classification tool with modern UI.</p>
<p>© 2023 DotminiTech</p>"""
        
        QMessageBox.about(self, "About Dotmini MCX", about_text)
    
    def show_documentation(self):
        """Show documentation or help about the app"""
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
        """Load application settings"""
        # Load batch size
        batch_size = self.settings.value("classification/batch_size", 16, type=int)
        self.batch_size = batch_size
        
        # Load last used paths
        last_model_path = self.settings.value("paths/model", "")
        if last_model_path:
            self.model_file_widget.set_path(last_model_path)
        
        last_label_path = self.settings.value("paths/labels", "")
        if last_label_path:
            self.label_file_widget.set_path(last_label_path)
        
        last_output_path = self.settings.value("paths/output", "")
        if last_output_path:
            self.output_folder_widget.set_paths(last_output_path)
        
        # Load input folders
        input_folders = self.settings.value("paths/input_folders", [])
        if input_folders:
            self.input_folders_widget.set_paths(input_folders)
        
        # Update recent files menu
        self.update_recent_menu()
    
    def save_settings(self):
        """Save application settings"""
        # Save batch size
        self.settings.setValue("classification/batch_size", self.batch_size)
        
        # Save paths
        model_path = self.model_file_widget.get_path()
        label_path = self.label_file_widget.get_path()
        output_path = self.output_folder_widget.get_paths()
        input_folders = self.input_folders_widget.get_paths()
        
        self.settings.setValue("paths/model", model_path)
        self.settings.setValue("paths/labels", label_path)
        self.settings.setValue("paths/output", output_path)
        self.settings.setValue("paths/input_folders", input_folders)
        
        # Add to recent files
        if model_path:
            self.add_to_recent_files(model_path)
        if label_path:
            self.add_to_recent_files(label_path)
        if output_path:
            self.add_to_recent_files(output_path)
        for folder in input_folders:
            self.add_to_recent_files(folder)
    
    def center_on_screen(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def start_classification(self):
        # Validate inputs
        input_folders = self.input_folders_widget.get_paths()
        model_path = self.model_file_widget.get_path()
        label_path = self.label_file_widget.get_path()
        output_folder = self.output_folder_widget.get_paths()
        
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
        if self.classification_thread is not None and self.classification_thread.isRunning():
            self.classification_thread.stop()
            self.classification_thread.wait()
            self.classification_finished()
            self.add_result("", "Classification canceled by user", "")
            self.statusBar().showMessage("Classification canceled.")
    
    def update_progress(self, value, maximum):
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"Processing images: {value}/{maximum} ({int(value/maximum*100)}%)")
    
    def add_result(self, file_path, class_name, confidence):
        if file_path:
            # Create a custom widget item for better display
            item = QListWidgetItem()
            
            # Try to create a thumbnail for the image
            try:
                pixmap = QPixmap(file_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
                item.setIcon(QIcon(pixmap))
            except:
                # If thumbnail creation fails, use a generic icon
                item.setIcon(QIcon())
            
            item_text = f"{os.path.basename(file_path)} → {class_name} (confidence: {confidence})"
            item.setText(item_text)
            item.setToolTip(f"File: {file_path}\nClass: {class_name}\nConfidence: {confidence}")
            
            self.results_list.addItem(item)
            
            # Update statistics
            if class_name in self.class_counts:
                self.class_counts[class_name] += 1
            else:
                self.class_counts[class_name] = 1
            
            self.total_processed += 1
            self.update_result_stats()
        else:
            # For messages like "canceled"
            item = QListWidgetItem()
            item.setText(class_name)
            item.setForeground(QColor("#FF5555"))  # Red color for error/status messages
            self.results_list.addItem(item)
        
        self.results_list.scrollToBottom()
    
    def update_result_stats(self):
        """Update the results statistics label"""
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
        self.classify_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.classification_thread = None
        
        if self.total_processed > 0:
            self.statusBar().showMessage(f"Classification complete. Processed {self.total_processed} images.")
        else:
            self.statusBar().showMessage("Ready")
    
    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.statusBar().showMessage(f"Error: {error_message}")
    
    def clear_results(self):
        self.results_list.clear()
        self.class_counts = {}
        self.total_processed = 0
        self.update_result_stats()
    
    def export_results(self):
        """Export classification results to a CSV file"""
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
                        
                    filename = parts[0].strip()
                    
                    # Extract class and confidence
                    class_conf = parts[1].strip()
                    class_name = class_conf.split("(confidence:")[0].strip()
                    
                    # Try to extract confidence value
                    confidence = ""
                    if "confidence:" in class_conf:
                        confidence = class_conf.split("confidence:")[1].strip()
                        confidence = confidence.rstrip(")")
                    
                    # Write to CSV
                    f.write(f'"{filename}","{class_name}",{confidence}\n')
                
            self.statusBar().showMessage(f"Results exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting results: {str(e)}")
    
    def closeEvent(self, event):
        # Save settings before closing
        self.save_settings()
        event.accept()


def main():
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
    def update_progress():
        nonlocal progress_value
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
        splash_content.render(splash_pixmap)
        splash.setPixmap(splash_pixmap)
        
        if progress_value >= 100:
            progress_timer.stop()
    
    # Start progress animation
    progress_value = 0
    progress_timer = QTimer()
    progress_timer.timeout.connect(update_progress)
    progress_timer.start(30)  # Update every 30ms for smooth animation
    
    # Check license first
    license_manager = LicenseManager()
    if not license_manager.is_valid_license():
        # Show license dialog if no valid license is stored
        license_dialog = LicenseDialog()
        if not license_dialog.exec():
            # Exit if license is not verified or user cancels
            return
    
    # Create theme manager
    theme_manager = ThemeManager(app)
    
    # Create main window
    main_window = DotminiMCX()
    main_window.theme_manager = theme_manager
    theme_manager.main_window = main_window
    
    # Apply theme based on settings
    theme_manager.apply_theme()
    
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
    
    QTimer.singleShot(3000, show_main_window)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
