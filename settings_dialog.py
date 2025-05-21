"""Provides the settings dialog for the Dotmini MCX application.

This module contains the SettingsDialog class, which allows users to configure
various application settings such as theme, brightness, and classification parameters.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCheckBox, QComboBox, QFrame)
from PyQt6.QtCore import pyqtSignal

# Import BrightnessControl from its own module
from brightness_control import BrightnessControl

# Import DARKDETECT_AVAILABLE from theme_manager
# This is used to conditionally enable system theme detection features.
try:
    from theme_manager import DARKDETECT_AVAILABLE
except ImportError:
    # Fallback if theme_manager or DARKDETECT_AVAILABLE is not found,
    # though in the integrated application this should always be available.
    DARKDETECT_AVAILABLE = False


class SettingsDialog(QDialog):
    """A dialog window for configuring application settings.
    
    Allows users to adjust theme (light/dark/auto), UI brightness,
    and classification batch size.
    """
    settingsChanged = pyqtSignal()
    
    def __init__(self, theme_manager, parent=None):
        """Initializes the SettingsDialog UI and connects signals."""
        super().__init__(parent)
        self.theme_manager = theme_manager # Instance of ThemeManager passed from main.py
        
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
        # Disable 'Auto' if darkdetect is not available
        if not DARKDETECT_AVAILABLE:
            self.theme_auto.setChecked(False)
            self.theme_auto.setEnabled(False)
            self.theme_auto.setToolTip("System theme detection is not available.")
        else:
            self.theme_auto.setChecked(self.theme_manager.settings.value("theme/mode", "auto") == "auto")


        theme_button_layout = QHBoxLayout()
        
        self.light_theme_button = QPushButton("Light")
        self.light_theme_button.setCheckable(True)
        
        self.dark_theme_button = QPushButton("Dark")
        self.dark_theme_button.setCheckable(True)
        
        # Set initial state based on theme_manager's current_theme
        # and whether auto mode was previously selected
        current_mode = self.theme_manager.settings.value("theme/mode", "auto")
        if current_mode == "auto" and DARKDETECT_AVAILABLE:
            self.theme_auto.setChecked(True)
            # Buttons get checked/unchecked in on_theme_auto_changed or by system theme
        elif self.theme_manager.current_theme == "light":
            self.theme_auto.setChecked(False)
            self.light_theme_button.setChecked(True)
            self.dark_theme_button.setChecked(False)
        elif self.theme_manager.current_theme == "dark":
            self.theme_auto.setChecked(False)
            self.light_theme_button.setChecked(False)
            self.dark_theme_button.setChecked(True)
        
        self.update_manual_theme_buttons_state(self.theme_auto.isChecked())

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
        
        # Load saved batch size from main app settings (passed via theme_manager for convenience)
        # Or ideally, pass main_app.settings directly if SettingsDialog needs more settings.
        # For now, assuming batch_size is part of what theme_manager might know or have access to.
        # This part might need adjustment based on where batch_size is actually stored/managed.
        # A better approach: pass settings object to SettingsDialog.
        saved_batch_size = self.theme_manager.settings.value("classification/batch_size", "16")
        self.batch_size_combo.setCurrentText(str(saved_batch_size))

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
        save_button.clicked.connect(self.accept) # accept calls save_settings via main_window
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        # Add all to main layout
        layout.addWidget(theme_frame)
        layout.addWidget(brightness_frame)
        layout.addWidget(classification_frame)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def update_manual_theme_buttons_state(self, auto_is_checked):
        """Updates the enabled state of manual theme buttons based on auto mode."""
        self.light_theme_button.setEnabled(not auto_is_checked)
        self.dark_theme_button.setEnabled(not auto_is_checked)
        if auto_is_checked:
            # Reflect current system theme if auto is on
            if DARKDETECT_AVAILABLE:
                is_dark = self.theme_manager.is_system_dark() # Assuming ThemeManager has such a method
                self.light_theme_button.setChecked(not is_dark)
                self.dark_theme_button.setChecked(is_dark)
        else: # Manual mode, reflect current app theme
            self.light_theme_button.setChecked(self.theme_manager.current_theme == "light")
            self.dark_theme_button.setChecked(self.theme_manager.current_theme == "dark")


    def on_theme_auto_changed(self, checked):
        """Handles changes to the 'Auto (use system theme)' checkbox."""
        self.update_manual_theme_buttons_state(checked)
        if checked and DARKDETECT_AVAILABLE:
            self.theme_manager.set_theme_mode("auto") # Tell ThemeManager to use auto mode
            # ThemeManager should then detect and apply system theme.
        elif not checked:
            # Switched to manual: keep current theme or default to one if needed
            # The specific light/dark button click will handle setting manual theme.
             self.theme_manager.set_theme_mode(self.theme_manager.current_theme) # Stay with current theme
    
    def on_light_theme_clicked(self):
        """Handles clicks on the 'Light' theme button."""
        if not self.theme_auto.isChecked(): # Only if not in auto mode
            self.light_theme_button.setChecked(True)
            self.dark_theme_button.setChecked(False)
            self.theme_manager.set_theme_mode("light")
            self.theme_manager.apply_theme() # Apply immediately
    
    def on_dark_theme_clicked(self):
        """Handles clicks on the 'Dark' theme button."""
        if not self.theme_auto.isChecked(): # Only if not in auto mode
            self.light_theme_button.setChecked(False)
            self.dark_theme_button.setChecked(True)
            self.theme_manager.set_theme_mode("dark")
            self.theme_manager.apply_theme() # Apply immediately
    
    def on_brightness_changed(self, value):
        """Handles changes from the BrightnessControl widget."""
        self.theme_manager.set_brightness(value) 
        # ThemeManager.set_brightness should call apply_theme
    
    def get_batch_size(self):
        """Returns the selected classification batch size."""
        return int(self.batch_size_combo.currentText())

    def save_settings(self):
        """Saves the configured settings to the application's persistent storage."""
        # This method is called by DotminiMCX.show_settings after dialog.exec()
        # Theme and brightness settings are applied reactively.
        # Save theme mode (auto, light, dark)
        if self.theme_auto.isChecked() and DARKDETECT_AVAILABLE:
            self.theme_manager.settings.setValue("theme/mode", "auto")
        else:
            self.theme_manager.settings.setValue("theme/mode", self.theme_manager.current_theme)
        
        # Brightness is saved by ThemeManager when changed.
        # self.theme_manager.save_settings() # ThemeManager already saves its own settings
        
        # Save batch size (example of another setting)
        self.theme_manager.settings.setValue("classification/batch_size", self.get_batch_size())
        
        # Emit signal to notify main window if other non-reactive changes were made
        self.settingsChanged.emit()
