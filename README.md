# 🎥 FrameCut — Lightweight Region-Based Screen Recorder

![FrameCut Banner](https://your-image-link-here.gif) <!-- 🔄 Replace with your actual GIF URL -->

**FrameCut** is a simple, efficient, and resolution-customizable screen recording tool written in Python. With a clean GUI and precise region selection, it's ideal for tutorials, demos, bug tracking, or content creation without the bloat of full-screen recorders.

---

## ✨ Features

- 🖱️ **Drag to Select Custom Area** of the screen.
- ⚙️ **Choose Resolution** (720p, 1080p, 2160p).
- 🎞️ **Set Frame Rate** (10, 20, 30, 60 FPS).
- 🕒 **Live Recording Timer**.
- 💡 **Auto Black Padding** to maintain aspect ratio.
- 💾 **Output in `output.mp4`** using OpenCV.
- 🪟 **Simple GUI** using Tkinter.
- 🧵 Multi-threaded recording for performance.

---
## Setup and Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd your-repository-name
    ```
3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
4.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
5.  **Install the required dependencies:**
    ```bash
    pip install opencv-python mss pynput
    ```
6.  **Run the application:**
    ```bash
    python gemini_screen_recorder.py
    ```


## 📦 Requirements

- Python 3.7 or higher  
- Windows/macOS/Linux (MSS and Tkinter supported)

### 📥 Install Dependencies

```bash
pip install opencv-python mss numpy pynput
