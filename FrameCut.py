import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import cv2
import mss
import numpy as np
from pynput import mouse
from queue import Queue
import os
import subprocess

class RecordingManager:
    def __init__(self, selected_resolution, selected_fps, region):
        self.selected_resolution = selected_resolution
        self.selected_fps = selected_fps
        self.region = region

        self.is_recording = False
        self.frame_queue = Queue(maxsize=120)
        self.start_time = None

        self.resolutions = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "2160p": (3840, 2160)
        }
        self.output_width, self.output_height = self.resolutions[self.selected_resolution]

    def start_recording(self):
        self.is_recording = True
        self.start_time = time.time()

        self.capture_thread = threading.Thread(target=self._capture_screen)
        self.processing_thread = threading.Thread(target=self._process_and_save_frames)
        self.capture_thread.start()
        self.processing_thread.start()

    def stop_recording(self):
        self.is_recording = False

    def _capture_screen(self):
        with mss.mss() as sct:
            frame_interval = 1 / self.selected_fps
            while self.is_recording:
                start_time = time.time()
                img = np.array(sct.grab(self.region))
                try:
                    self.frame_queue.put_nowait(img)
                except:
                    pass
                elapsed = time.time() - start_time
                sleep_time = frame_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _process_and_save_frames(self):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v") # Use a common codec for temporary file
        self.temp_video_filename = "video_temp.mp4"
        out = cv2.VideoWriter(self.temp_video_filename, fourcc, self.selected_fps, (self.output_width, self.output_height))
        frame_duration = 1 / self.selected_fps
        black_frame = np.zeros((self.output_height, self.output_width, 3), dtype=np.uint8)

        while self.is_recording or not self.frame_queue.empty():
            try:
                img = self.frame_queue.get(timeout=1)
            except:
                continue

            frame_start_time = time.time()
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            black_frame.fill(0)

            h, w = frame.shape[:2]
            aspect_ratio_frame = w / h
            aspect_ratio_output = self.output_width / self.output_height

            if aspect_ratio_frame > aspect_ratio_output:
                new_w = self.output_width
                new_h = int(new_w / aspect_ratio_frame)
            else:
                new_h = self.output_height
                new_w = int(new_h * aspect_ratio_frame)

            resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            x_offset = (self.output_width - new_w) // 2
            y_offset = (self.output_height - new_h) // 2

            black_frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_frame
            out.write(black_frame)

            elapsed_time = time.time() - frame_start_time
            sleep_time = frame_duration - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

        out.release()

    def _post_process_video(self):
        output_filename = "output.mp4"
        try:
            # Use ffmpeg to re-encode for wider compatibility
            cmd = [
                "ffmpeg",
                "-i", self.temp_video_filename,
                "-c:v", "libx264",  # H.264 codec
                "-preset", "medium", # Encoding preset (e.g., ultrafast, superfast, medium, slow)
                "-crf", "23",       # Constant Rate Factor (lower is higher quality, larger file)
                "-pix_fmt", "yuv420p", # Pixel format for broad compatibility
                "-movflags", "+faststart", # Optimize for streaming
                output_filename
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(self.temp_video_filename) # Clean up temporary file
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            # If ffmpeg fails, try to rename the temp file to output.mp4
            if os.path.exists(self.temp_video_filename):
                os.rename(self.temp_video_filename, output_filename)
        except FileNotFoundError:
            print("FFmpeg not found. Please ensure it's installed and in your system's PATH.")
            if os.path.exists(self.temp_video_filename):
                os.rename(self.temp_video_filename, output_filename)
        except Exception as e:
            print(f"Error during post-processing: {e}")
            if os.path.exists(self.temp_video_filename):
                os.rename(self.temp_video_filename, output_filename)

class ScreenRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FrameCut")

        self.region = None
        self.recording_manager = None

        self.setup_ui()

    def setup_ui(self):
        self.root.geometry("600x65")
        self.root.resizable(False, False)
        self.root.configure(bg='#2B2B2B')

        # --- Style Configuration ---
        style = ttk.Style(self.root)
        style.theme_use('clam')

        # General theme settings
        style.configure('.', 
                        background='#2B2B2B', 
                        foreground='#F0F0F0', 
                        font=('Segoe UI', 10))

        # --- Button Styles ---
        style.configure('TButton', 
                        borderwidth=0, 
                        padding=(10, 5), 
                        font=('Segoe UI', 10, 'bold'))
        style.map('TButton',
                  background=[('active', '#454545')],
                  foreground=[('active', '#FFFFFF')])

        # Specific button colors
        style.configure('Area.TButton', background='#555555', foreground='#FFFFFF')
        style.configure('Start.TButton', background='#4CAF50', foreground='#FFFFFF')
        style.configure('Stop.TButton', background='#F44336', foreground='#FFFFFF')
        style.configure('Exit.TButton', background='#555555', foreground='#FFFFFF')
        
        style.map('Area.TButton', background=[('active', '#656565')])
        style.map('Start.TButton', background=[('active', '#5cb85c')])
        style.map('Stop.TButton', background=[('active', '#d9534f')])
        style.map('Exit.TButton', background=[('active', '#656565')])

        # --- Combobox Style ---
        style.configure('TCombobox', 
                        fieldbackground='#3C3F41',
                        background='#3C3F41',
                        foreground='#F0F0F0',
                        arrowcolor='#F0F0F0',
                        selectbackground='#454545',
                        selectforeground='#F0F0F0',
                        borderwidth=0)
        style.map('TCombobox',
                  fieldbackground=[('readonly', '#3C3F41')],
                  selectbackground=[('readonly', '#454545')],
                  selectforeground=[('readonly', '#F0F0F0')])

        # To make the dropdown menu dark as well
        self.root.option_add('*TCombobox*Listbox.background', '#3C3F41')
        self.root.option_add('*TCombobox*Listbox.foreground', '#F0F0F0')
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#555555')
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')

        # --- UI Widget Creation ---
        self.selected_resolution = tk.StringVar(self.root)
        self.selected_resolution.set("1080p")
        self.resolutions = {"720p": (1280, 720), "1080p": (1920, 1080), "2160p": (3840, 2160)}

        self.fps_options = [10, 20, 30, 60]
        self.selected_fps = tk.IntVar(self.root)
        self.selected_fps.set(30)

        main_frame = tk.Frame(self.root, bg='#2B2B2B')
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.timer_label = tk.Label(main_frame, text="00:00", font=("Segoe UI", 12, "bold"), bg='#2B2B2B', fg='#F0F0F0')
        self.timer_label.pack(side=tk.LEFT, padx=(0, 10))

        self.res_menu = ttk.Combobox(main_frame, textvariable=self.selected_resolution, values=list(self.resolutions.keys()), state='readonly', width=8)
        self.res_menu.pack(side=tk.LEFT, padx=5)

        self.fps_menu = ttk.Combobox(main_frame, textvariable=self.selected_fps, values=self.fps_options, state='readonly', width=5)
        self.fps_menu.pack(side=tk.LEFT, padx=5)

        self.btn_new = ttk.Button(main_frame, text="Area", command=self.select_area, style='Area.TButton')
        self.btn_new.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(main_frame, text="Start", command=self.start_recording, state=tk.DISABLED, style='Start.TButton')
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(main_frame, text="Stop", command=self.stop_recording, state=tk.DISABLED, style='Stop.TButton')
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_exit = ttk.Button(main_frame, text="Exit", command=self.root.quit, style='Exit.TButton')
        self.btn_exit.pack(side=tk.LEFT, padx=5)

    def select_area(self):
        self.root.withdraw()
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes("-fullscreen", True)
        self.selection_window.attributes("-alpha", 0.3)
        self.selection_window.configure(bg="grey")
        self.canvas = tk.Canvas(self.selection_window, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x, self.start_y = None, None
        self.rect = None

        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

        self.selection_window.bind("<B1-Motion>", self.on_drag)
        self.selection_window.bind("<Escape>", self._on_escape_key)

    def _on_escape_key(self, event):
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.selection_window.destroy()
        self.root.deiconify()
        self.btn_start.config(state=tk.DISABLED)
        messagebox.showinfo("Selection Cancelled", "Area selection cancelled.")

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.start_x, self.start_y = x, y
                if self.rect:
                    self.canvas.delete(self.rect)
                self.rect = None
            else:
                end_x, end_y = x, y

                self.region = {
                    "top": min(self.start_y, end_y),
                    "left": min(self.start_x, end_x),
                    "width": abs(end_x - self.start_x),
                    "height": abs(end_y - self.start_y)
                }

                if self.region["width"] > 0 and self.region["height"] > 0:
                    self.btn_start.config(state=tk.NORMAL)
                else:
                    self.btn_start.config(state=tk.DISABLED)

                self.mouse_listener.stop()
                self.selection_window.destroy()
                self.root.deiconify()

    def on_drag(self, event):
        if self.start_x is not None and self.start_y is not None:
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline='red', width=2)

    def start_recording(self):
        self.recording_manager = RecordingManager(
            self.selected_resolution.get(),
            self.selected_fps.get(),
            self.region
        )
        self.recording_manager.start_recording()

        self.btn_start.config(state=tk.DISABLED)
        self.btn_new.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.res_menu.config(state=tk.DISABLED)
        self.fps_menu.config(state=tk.DISABLED)

        self.update_timer()

    def stop_recording(self):
        if self.recording_manager:
            self.recording_manager.stop_recording()
            # Start a new thread for post-processing to avoid freezing the UI
            threading.Thread(target=self._complete_stop_process).start()

    def _complete_stop_process(self):
        # Wait for processing thread to finish
        self.recording_manager.processing_thread.join()
        self.recording_manager._post_process_video()
        messagebox.showinfo("Success", "Recording saved as output.mp4")

        # Update UI elements in the main thread after processing is complete
        self.root.after(0, self._reset_ui_after_stop)

        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_new.config(state=tk.NORMAL)
        self.res_menu.config(state=tk.NORMAL)
        self.fps_menu.config(state=tk.NORMAL)
        self.timer_label.config(text="00:00")

    def _reset_ui_after_stop(self):
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_new.config(state=tk.NORMAL)
        self.res_menu.config(state=tk.NORMAL)
        self.fps_menu.config(state=tk.NORMAL)
        self.timer_label.config(text="00:00")

    def update_timer(self):
        if self.recording_manager and self.recording_manager.is_recording:
            elapsed_time = time.time() - self.recording_manager.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorderGUI(root)
    root.mainloop()
