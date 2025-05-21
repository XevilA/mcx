"""Manages UI themes (dark/light mode) and brightness adjustments for the application.

This module provides the ThemeManager class, which is responsible for loading,
applying, and saving theme settings. It can detect system theme changes (if
darkdetect is available) and allows manual theme toggling and brightness control.
"""
import os
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor

# App constants - Define these or pass them to ThemeManager
ORGANIZATION_NAME = "DotminiTech"
APP_NAME = "Dotmini MCX"

# For detecting OS theme
try:
    from darkdetect import isDark, theme, listener
    DARKDETECT_AVAILABLE = True
except ImportError:
    DARKDETECT_AVAILABLE = False

class ThemeManager:
    """Manages the application's visual theme, including dark/light modes and brightness.
    
    It handles loading and saving theme preferences, applying stylesheets,
    and responding to system theme changes.
    """
    def __init__(self, app, main_window=None):
        """Initializes the ThemeManager."""
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
            if listener: # Ensure listener is callable
                listener(self.on_system_theme_change)
        
        # Apply initial theme
        self.apply_theme()
    
    def load_settings(self):
        """Loads theme mode and brightness from application settings."""
        # Load theme mode, default to "auto" if using darkdetect and available
        default_theme_mode = "auto" if DARKDETECT_AVAILABLE else "dark"
        theme_mode_setting = self.settings.value("theme/mode", default_theme_mode)

        if theme_mode_setting == "auto" and DARKDETECT_AVAILABLE:
            self.detect_system_theme() # Sets self.current_theme
        else:
            # Fallback to specific theme or default if auto is not possible/set
            self.current_theme = theme_mode_setting if theme_mode_setting in ["light", "dark"] else "dark"

        saved_brightness = self.settings.value("theme/brightness", None)
        if saved_brightness is not None:
            try:
                self.brightness = int(saved_brightness)
            except (ValueError, TypeError):
                self.brightness = 100
        else:
             self.brightness = 100 # Default if nothing is saved
    
    def save_settings(self):
        """Saves the current theme mode and brightness to application settings."""
        # Save the mode chosen by the user (auto, light, or dark)
        # If DARKDETECT_AVAILABLE and user chose auto, save "auto"
        # Otherwise, save the explicit theme (light/dark)
        chosen_mode = self.settings.value("theme/chosen_mode", self.current_theme) # Persist explicit choice if not auto
        if DARKDETECT_AVAILABLE and chosen_mode == "auto":
             self.settings.setValue("theme/mode", "auto")
        else:
            self.settings.setValue("theme/mode", self.current_theme) # Save the actual current theme
        self.settings.setValue("theme/brightness", self.brightness)
    
    def detect_system_theme(self):
        """Detects the current system theme and updates the application theme if in auto mode."""
        if DARKDETECT_AVAILABLE:
            system_is_dark = isDark()
            detected_theme = "dark" if system_is_dark else "light"
            if self.current_theme != detected_theme:
                self.current_theme = detected_theme
                # Do not save here if mode is "auto", apply_theme will be called by on_system_theme_change
                # or by initial setup if auto is selected.
                # self.save_settings() # This might overwrite "auto" preference
                self.apply_theme()


    def on_system_theme_change(self, new_mode_is_dark): # Listener provides the new mode
        """Responds to system theme changes when in automatic mode."""
        # This callback receives the new system theme state from darkdetect.
        # Ensure settings reflect 'auto' mode before changing theme based on system.
        if DARKDETECT_AVAILABLE and self.settings.value("theme/mode", "auto") == "auto":
            new_theme = "dark" if new_mode_is_dark else "light"
            if new_theme != self.current_theme:
                self.current_theme = new_theme
                # No need to call self.save_settings() here as the mode is "auto"
                self.apply_theme()

    def set_theme_mode(self, mode):
        """Sets the theme mode (auto, light, dark) and applies it."""
        if mode == "auto" and DARKDETECT_AVAILABLE:
            self.settings.setValue("theme/chosen_mode", "auto") # User explicitly chose auto
            self.settings.setValue("theme/mode", "auto")
            self.detect_system_theme() # This will set current_theme and apply
        elif mode in ["light", "dark"]:
            self.settings.setValue("theme/chosen_mode", mode) # User explicitly chose light/dark
            self.settings.setValue("theme/mode", mode)
            if self.current_theme != mode:
                self.current_theme = mode
                self.apply_theme()
            elif self.current_theme == mode: # If already current, re-apply (e.g. brightness changed)
                 self.apply_theme()
        self.save_settings() # Save the new mode preference

    def is_system_dark(self):
        """Checks if the system theme is currently dark."""
        if DARKDETECT_AVAILABLE:
            return isDark()
        return False # Default if darkdetect is not available

    def set_brightness(self, value):
        """Sets the UI brightness level and applies the theme."""
        self.brightness = value
        self.save_settings() # Save brightness setting
        self.apply_theme()
    
    def toggle_theme(self):
        """Toggles between light and dark themes manually."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme_mode(new_theme) # Use set_theme_mode to handle saving preference

    def apply_theme(self):
        """Applies the current theme and brightness to the application using stylesheets."""
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
