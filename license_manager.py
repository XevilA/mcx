"""Handles license key validation and the display of the license dialog.

This module provides the LicenseManager class for verifying license keys
and the LicenseDialog class for prompting the user to enter a license key.
"""
import hashlib
from PyQt6.QtCore import (Qt, QSettings, QPropertyAnimation, QPoint)
from PyQt6.QtGui import (QColor, QGuiApplication, QAction, QKeySequence)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QDialog, QFrame, QCheckBox, 
                             QGraphicsDropShadowEffect)

# App constants - Define these as they are used by the classes below
ORGANIZATION_NAME = "DotminiTech"
APP_NAME = "Dotmini MCX"
APP_VERSION = "1.2.0"

class LicenseManager:
    """Manages the storage and validation of the application's license key."""
    def __init__(self):
        """Initializes the LicenseManager and loads settings."""
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        # The following key is for demonstration/testing purposes only.
        # For a production application, this should be replaced with a proper
        # license key generation and validation mechanism.
        self.correct_key = "D1QE80fxUUVcNs4VAAOvNNkJvHHy0dWM"
    
    def is_valid_license(self):
        """Checks if a valid and verified license key is stored in settings."""
        saved_key = self.settings.value("license/key", None)
        saved_hash = self.settings.value("license/hash", None)
        
        if saved_key and saved_hash:
            # Verify hash to prevent tampering
            computed_hash = self._hash_key(saved_key)
            if computed_hash == saved_hash and saved_key == self.correct_key:
                return True
        
        return False
    
    def save_license(self, key):
        """Saves the provided license key to settings if it's valid."""
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
    """A dialog window for users to enter and verify their license key."""
    def __init__(self, parent=None):
        """Initializes the LicenseDialog UI elements and layout."""
        super().__init__(parent)
        self.setWindowTitle("Dotmini MCX License Verification")
        self.setFixedSize(450, 280) # Adjusted size slightly as tip is removed
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        # Create license manager
        self.license_manager = LicenseManager()
        
        # Main layout
        main_dialog_layout = QVBoxLayout() # Renamed to avoid conflict
        main_dialog_layout.setSpacing(15)
        main_dialog_layout.setContentsMargins(20, 20, 20, 20) # Adjusted margins a bit
        
        # Content widget for styling
        content_widget = QWidget()
        content_widget.setObjectName("splashContent") # This ID might be used by stylesheet
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
        
        logo_label = QLabel("🔑") # Changed icon for variety
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px;")
        
        self.msg_label = QLabel("Please enter your license key to continue:")
        
        # Add a card for the license input
        license_frame = QFrame()
        license_frame.setObjectName("card") # This ID might be used by stylesheet
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
        quit_button.setObjectName("secondaryButton") # This ID might be used by stylesheet
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
        main_dialog_layout.addWidget(content_widget)
        self.setLayout(main_dialog_layout)
        
        # Center on screen
        self.center_on_screen()
        
        # Set default button and key event
        self.key_input.returnPressed.connect(self.verify_license)
        self.verify_button.setDefault(True)
        
        # Removed the tip_label for the demo key

    def center_on_screen(self):
        """Centers the dialog on the primary screen."""
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def paste_from_clipboard(self):
        """Pastes text from the clipboard into the license key input field."""
        clipboard = QGuiApplication.clipboard()
        self.key_input.setText(clipboard.text())

    def verify_license(self):
        """Verifies the entered license key."""
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
        """Creates a shake animation to indicate invalid input in the dialog."""
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
