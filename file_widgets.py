"""Provides custom PyQt6 widgets for selecting files and folders.

This module contains:
- FolderSelectionWidget: For selecting one or multiple folders, with drag & drop.
- FileSelectionWidget: For selecting a single file, with filtering and drag & drop.
"""
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFileDialog, QListWidget, QFrame)
from PyQt6.QtCore import Qt, QMimeData, QUrl # Added QMimeData and QUrl explicitly

class FolderSelectionWidget(QWidget):
    """A custom widget for selecting one or more folders.
    
    Supports browsing for folders and drag-and-drop functionality.
    Can be configured for single or multiple folder selection.
    """
    def __init__(self, title, multiple=False, placeholder_text="Select folder..."):
        """Initializes the FolderSelectionWidget."""
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
            # dragEnterEvent, dragMoveEvent, dropEvent are overridden methods, not signals to connect here.
            
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
            drop_zone.setObjectName("card") # For styling if needed
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
        """Opens a dialog to browse and select folder(s)."""
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
        """Removes the selected folder(s) from the list (multiple selection mode)."""
        if self.multiple:
            for item in self.folder_list.selectedItems():
                self.folder_list.takeItem(self.folder_list.row(item))
    
    def clear_all(self):
        """Clears all selected folders from the list (multiple selection mode)."""
        if self.multiple:
            self.folder_list.clear()
    
    def get_paths(self):
        """Returns the selected folder path(s)."""
        if self.multiple:
            return [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        else:
            return self.path_input.text()
    
    def set_paths(self, paths):
        """Sets the selected folder path(s) in the widget."""
        if self.multiple and isinstance(paths, list):
            self.folder_list.clear()
            for path in paths:
                self.folder_list.addItem(path)
        elif not self.multiple and isinstance(paths, str):
            self.path_input.setText(paths)
    
    def dragEnterEvent(self, event):
        """Handles drag enter events to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handles drag move events to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handles drop events to add folder paths from URLs."""
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
    """A custom widget for selecting a single file.
    
    Supports browsing for a file with filters and drag-and-drop functionality.
    """
    def __init__(self, title, file_filter="All Files (*)", placeholder_text="Select file..."):
        """Initializes the FileSelectionWidget."""
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
        drop_zone.setObjectName("card") # For styling if needed
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
        """Opens a dialog to browse and select a file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.file_filter)
        if file:
            self.path_input.setText(file)
    
    def get_path(self):
        """Returns the selected file path."""
        return self.path_input.text()
    
    def set_path(self, path):
        """Sets the selected file path in the widget."""
        self.path_input.setText(path)
    
    def dragEnterEvent(self, event):
        """Handles drag enter events to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handles drag move events to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handles drop events to set the file path from a URL, respecting filters."""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    # Check if file matches the filter
                    file_ext = os.path.splitext(path)[1].lower()
                    
                    # Extract extensions from filter
                    filter_exts = []
                    if self.file_filter == "All Files (*)": # Common case
                         self.path_input.setText(path)
                         event.acceptProposedAction()
                         return

                    for filter_part in self.file_filter.split(';;'):
                        # Handle cases like "Model Files (*.h5 *.tflite *.pb)"
                        if '(' in filter_part and ')' in filter_part:
                            ext_part = filter_part[filter_part.find('(')+1 : filter_part.find(')')]
                            exts = [e.strip().lower() for e in ext_part.split() if e.startswith('*.')]
                            filter_exts.extend([e[1:] for e in exts]) # Remove the '*'
                    
                    if not filter_exts or file_ext in filter_exts:
                        self.path_input.setText(path)
                        break # Process only the first valid file
            
            event.acceptProposedAction()
