import tkinter as tk
from tkinter import messagebox
import threading
import time
import cv2
import mss
import numpy as np
from pynput import mouse
from queue import Queue
import os

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
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter("output.mp4", fourcc, self.selected_fps, (self.output_width, self.output_height))
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

class ScreenRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FrameCut")

        self.region = None
        self.recording_manager = None

        self.setup_ui()

    def setup_ui(self):
        self.root.geometry("422x57")
        self.root.resizable(False, False)

        self.selected_resolution = tk.StringVar(self.root)
        self.selected_resolution.set("1080p")
        self.resolutions = {"720p": (1280, 720), "1080p": (1920, 1080), "2160p": (3840, 2160)}

        self.fps_options = [10, 20, 30, 60]
        self.selected_fps = tk.IntVar(self.root)
        self.selected_fps.set(30)

        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.timer_label = tk.Label(main_frame, text="00:00", font=("Arial", 12))
        self.timer_label.pack(side=tk.LEFT, padx=(0, 10))

        self.res_menu = tk.OptionMenu(main_frame, self.selected_resolution, *self.resolutions.keys())
        self.res_menu.pack(side=tk.LEFT, padx=5)

        self.fps_menu = tk.OptionMenu(main_frame, self.selected_fps, *self.fps_options)
        self.fps_menu.pack(side=tk.LEFT, padx=5)

        self.btn_new = tk.Button(main_frame, text="New", command=self.select_area)
        self.btn_new.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(main_frame, text="Start", command=self.start_recording, state=tk.DISABLED)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(main_frame, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_exit = tk.Button(main_frame, text="Exit", command=self.root.quit)
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

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.start_x, self.start_y = x, y
                if self.rect:
                    self.canvas.delete(self.rect)
                self.rect = None
            else:
                end_x, end_y = x, y
                self.mouse_listener.stop()
                self.selection_window.destroy()
                self.root.deiconify()

                self.region = {
                    "top": min(self.start_y, end_y),
                    "left": min(self.start_x, end_x),
                    "width": abs(end_x - self.start_x),
                    "height": abs(end_y - self.start_y)
                }

                if self.region["width"] > 0 and self.region["height"] > 0:
                    self.btn_start.config(state=tk.NORMAL)
                else:
                    messagebox.showerror("Error", "Invalid area selected.")

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
            messagebox.showinfo("Success", "Recording saved as output.mp4")

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
