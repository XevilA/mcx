"""Handles image classification logic, including model loading and threaded processing.

This module provides the `ClassificationThread` for running image classification
tasks in a separate thread, and `load_model_safely` for loading TensorFlow/Keras
models with a workaround for potential DepthwiseConv2D issues.
"""
import os
import glob
import concurrent.futures
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image # Though not directly used, tf.keras.preprocessing.image might be intended for use by model
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

# Custom model loader to fix DepthwiseConv2D issue
def load_model_safely(model_path):
    """Loads a Keras model with a custom layer for DepthwiseConv2D if needed.
    
    This function attempts to load a Keras model normally. If it encounters
    a known issue with `DepthwiseConv2D` related to a 'groups' parameter,
    it retries loading with a custom `DepthwiseConv2D` layer that omits
    the problematic parameter.

    Args:
        model_path (str): The file path to the Keras model.

    Returns:
        A TensorFlow/Keras model object.
    
    Raises:
        Exception: If model loading fails for reasons other than the specific
                   DepthwiseConv2D issue, or if the custom loader also fails.
    """
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
    """A QThread subclass for performing image classification in the background.

    This thread processes images from input folders, classifies them using a
    provided model and labels, and saves the classified images to an output folder.
    It emits signals for progress updates, individual results, completion, and errors.
    """
    progress_update = pyqtSignal(int, int)
    result_update = pyqtSignal(str, str, str) # img_path, predicted_class, confidence_str
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model_path, label_path, input_folders, output_folder, batch_size=16):
        """Initializes the ClassificationThread."""
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
        """The main execution method of the thread, performing the classification task."""
        try:
            # Load the model using our safe loader
            model = load_model_safely(self.model_path)
            
            # Load labels
            with open(self.label_path, 'r') as f:
                labels = [line.strip() for line in f.readlines()]
            
            # Get all image files from input folders
            image_files = []
            for folder in self.input_folders:
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']: # Common image extensions
                    image_files.extend(glob.glob(os.path.join(folder, ext)))
                    image_files.extend(glob.glob(os.path.join(folder, '**', ext), recursive=True)) # Include subfolders
            
            # Remove duplicates
            image_files = list(set(image_files))
            total_files = len(image_files)
            processed_count = 0
            
            # Create output folders for all classes in advance
            for class_name in labels:
                class_folder = os.path.join(self.output_folder, class_name)
                os.makedirs(class_folder, exist_ok=True)
            
            # Process images in batches for better performance
            for i in range(0, total_files, self.batch_size):
                if not self.is_running:
                    break
                
                batch_files = image_files[i : i + self.batch_size]
                batch_results = [] # Store results for this batch
                
                # Process batch in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit image processing tasks
                    future_to_img_path = {executor.submit(self.process_image, img_path, model, labels): img_path for img_path in batch_files}
                    
                    for future in concurrent.futures.as_completed(future_to_img_path):
                        if not self.is_running:
                            # Cancel remaining futures if stop is requested
                            for f in future_to_img_path:
                                f.cancel()
                            break
                        
                        try:
                            result = future.result()
                            if result:
                                batch_results.append(result)
                        except Exception as exc:
                            img_path_for_error = future_to_img_path[future]
                            self.error.emit(f"Error processing {os.path.basename(img_path_for_error)}: {str(exc)}")
                
                # After processing a batch, update UI with results from that batch
                for result in batch_results:
                    if not self.is_running:
                        break
                    
                    # Unpack result: img_path, predicted_class, confidence, output_path (output_path not used by signal)
                    img_path, predicted_class, confidence, _ = result 
                    self.result_update.emit(img_path, predicted_class, f"{confidence:.2f}")
                    processed_count += 1
                    self.progress_update.emit(processed_count, total_files)
            
            self.finished.emit()
            
        except Exception as e:
            # Broad exception for issues like model loading, label file reading, etc.
            self.error.emit(f"Error in classification setup: {str(e)}")
            self.finished.emit() # Ensure finished is emitted even on setup error
    
    def process_image(self, img_path, model, labels):
        """Processes a single image: loads, preprocesses, predicts, and saves."""
        try:
            # Preprocess image
            # Standard model input size, adjust if your model differs
            img = Image.open(img_path).convert('RGB') 
            img_resized = img.resize((224, 224)) 
            img_array = np.array(img_resized) / 255.0  # Normalize
            img_array = np.expand_dims(img_array, axis=0) # Add batch dimension
            
            # Make prediction
            predictions = model.predict(img_array, verbose=0)
            predicted_class_idx = np.argmax(predictions[0])
            predicted_class = labels[predicted_class_idx]
            confidence = float(predictions[0][predicted_class_idx])
            
            # Prepare output path
            class_folder = os.path.join(self.output_folder, predicted_class)
            # os.makedirs(class_folder, exist_ok=True) # Already created in run()
            filename = os.path.basename(img_path)
            output_path = os.path.join(class_folder, filename)
            
            # Save the original (or resized, depending on preference) image to the output folder
            # Using original 'img' to save, not 'img_resized', to keep original quality.
            # If resized is preferred, change `img.save(output_path)` to `img_resized.save(output_path)`
            img.save(output_path)
            
            return (img_path, predicted_class, confidence, output_path)
        
        except Exception as e:
            # Emit error for this specific image, but allow thread to continue with others
            # self.error.emit(f"Error processing {os.path.basename(img_path)}: {str(e)}")
            # Raising exception to be caught by the ThreadPoolExecutor's future.result()
            raise e

    def stop(self):
        """Stops the classification thread safely."""
        self.is_running = False
