**🚀 Dotmini MCX**
==================

**Dotmini MCX** เป็นแอปพลิเคชัน macOS ที่พัฒนาด้วย Python โดยใช้ PyInstaller เพื่อสร้างแอปแบบ Universal2 ซึ่งสามารถทำงานได้ทั้งบนเครื่อง Mac ที่ใช้ชิป Intel และ Apple Silicon

**🧰 คุณสมบัติ**
----------------

-   ✅ รองรับสถาปัตยกรรม Universal2 (x86_64 และ arm64)

-   🎨 อินเทอร์เฟซผู้ใช้ที่ทันสมัยและเป็นมิตรกับผู้ใช้

-   🐍 พัฒนาโดยใช้ Python 3.10 หรือใหม่กว่า

-   🧱 บรรจุแอปพลิเคชันด้วย PyInstaller

-   📦 แจกจ่ายในรูปแบบ .app และ .dmg

**📦 การติดตั้ง**
-----------------

### **🔧 ข้อกำหนดเบื้องต้น**

-   macOS 10.15 Catalina หรือใหม่กว่า

-   Python 3.10 หรือใหม่กว่า (Universal2)

-   ติดตั้ง PyInstaller

### **🛠️ การติดตั้ง PyInstaller**

ติดตั้ง PyInstaller ด้วยคำสั่ง: 

```
pip install pyinstaller
```

---

**🚀 Dotmini MCX (English)**
=======================

**Dotmini MCX** is a macOS application developed in Python for image classification tasks. It is bundled using PyInstaller to create a Universal2 application, enabling it to run on both Intel and Apple Silicon Macs.

**🧰 Features**
--------------

-   ✅ **Universal2 Support**: Runs natively on both x86_64 (Intel) and arm64 (Apple Silicon) architectures.
-   🎨 **Modern UI**: Features a user-friendly and modern interface for ease of use.
-   🐍 **Python-Based**: Developed using Python 3.10 or newer.
-   🧱 **PyInstaller Bundled**: Packaged into a standalone application using PyInstaller.
-   📦 **Distribution**: Intended for distribution as a `.app` bundle and potentially a `.dmg` disk image.

**📦 Setup and Usage**
--------------------

### **🔧 Prerequisites**

-   macOS 10.15 Catalina or later.
-   Python 3.10 or newer (Universal2 build recommended if building from source).
-   PyInstaller (if building from source).

### **🛠️ Installing PyInstaller (for building from source)**

If you intend to build the application from its Python source code, you will need PyInstaller. Install it using pip:

```bash
pip install pyinstaller
```

### **🚀 Running the Application**

1.  **Input Folders**: Add one or more folders containing the images you want to classify.
2.  **Model Files**:
    *   Select your machine learning model file (e.g., `.h5`, `.tflite`).
    *   Select the corresponding labels file (usually a `.txt` file with class names).
3.  **Output Folder**: Choose a folder where the classified images will be saved. Images will be organized into subfolders named after their predicted class.
4.  **Start Classification**: Click the "Start Classification" button to begin the process.
5.  **Results**: View the classification progress and results in the application window. Results can also be exported.

**📝 License Key Note**
----------------------
The application may include a pre-filled license key or provide one for demonstration purposes (e.g., `D1QE80fxUUVcNs4VAAOvNNkJvHHy0dWM`). This key is intended **for trial and demonstration use only**. For any production, commercial, or widespread use, please ensure you have a valid license or replace it according to the software's licensing terms.
