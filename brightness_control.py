"""Provides a custom PyQt6 widget for adjusting UI brightness.

This module contains the BrightnessControl class, which includes a slider
and buttons to control and display a brightness percentage value.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal

class BrightnessControl(QWidget):
    """A widget for controlling and displaying a brightness level.

    Emits a `brightnessChanged` signal when the brightness value changes.
    Includes a slider and buttons for fine-grained control.
    """
    brightnessChanged = pyqtSignal(int)
    
    def __init__(self, initial_value=100):
        """Initializes the BrightnessControl widget."""
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
        """Handles the slider value change and emits the brightnessChanged signal."""
        self.value_label.setText(f"{value}%")
        self.brightnessChanged.emit(value)
    
    def on_dim_clicked(self):
        """Decreases the brightness by 10%, down to the minimum."""
        current_value = self.slider.value()
        new_value = max(current_value - 10, self.slider.minimum())
        self.slider.setValue(new_value)
    
    def on_reset_clicked(self):
        """Resets the brightness to the default value (100%)."""
        self.slider.setValue(100)
    
    def on_bright_clicked(self):
        """Increases the brightness by 10%, up to the maximum."""
        current_value = self.slider.value()
        new_value = min(current_value + 10, self.slider.maximum())
        self.slider.setValue(new_value)
    
    def get_brightness(self):
        """Returns the current brightness value."""
        return self.slider.value()
    
    def set_brightness(self, value):
        """Sets the current brightness value."""
        self.slider.setValue(value)
