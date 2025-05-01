import cv2 as cv
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from time import time, strftime
import os

class CameraApp:
    def __init__(self, window, window_title, video_source='http://192.168.1.6/mjpeg'):
        self.window = window
        self.window.title(window_title)
        
        self.video_source = video_source
        self.cap = cv.VideoCapture(self.video_source)
        self.vid_writer = None
        self.recording = False
        
        self.canvas = tk.Canvas(window, width=800, height=600)
        self.canvas.pack(padx=10, pady=10)
        
        btn_frame = ttk.Frame(window)
        btn_frame.pack(pady=10)
        
        self.btn_snapshot = ttk.Button(
            btn_frame, text="Сделать скриншот", command=self.snapshot)
        self.btn_snapshot.pack(side=tk.LEFT, padx=5)
        
        self.btn_rec = ttk.Button(
            btn_frame, text="Начать запись", command=self.toggle_recording)
        self.btn_rec.pack(side=tk.LEFT, padx=5)
        
        self.status = ttk.Label(window, text="Статус: подключение...")
        self.status.pack(pady=5)
        
        if not self.cap.isOpened():
            self.status.config(text="Ошибка подключения к камере!")
            return
        
        self.status.config(text="Статус: подключено")
        
        self.delay = 15
        self.update()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def update(self):
        ret, frame = self.cap.read()
        
        if ret:
            if self.recording and self.vid_writer is not None:
                self.vid_writer.write(frame)
            
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        else:
            self.status.config(text="Ошибка получения кадра")
        
        self.window.after(self.delay, self.update)
    
    def snapshot(self):
        ret, frame = self.cap.read()
        if ret:
            filename = strftime("%Y%m%d-%H%M%S") + "_screenshot.jpg"
            cv.imwrite(filename, frame)
            self.status.config(text=f"Скриншот сохранен: {filename}")
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.btn_rec.config(text="Остановить запись")
            
            fourcc = cv.VideoWriter_fourcc(*'XVID')
            # filename = strftime("%Y%m%d-%H%M%S") + "_recording.avi"
            filename = "input.mp4"
            fps = 30.0
            frame_size = (int(self.cap.get(3)), int(self.cap.get(4)))
            self.vid_writer = cv.VideoWriter(filename, fourcc, fps, frame_size)
            self.status.config(text=f"Запись: {filename}")
        else:
            self.recording = False
            self.btn_rec.config(text="Начать запись")
            if self.vid_writer is not None:
                self.vid_writer.release()
                self.vid_writer = None
            self.status.config(text="Запись остановлена")
    
    def on_close(self):
        if self.cap.isOpened():
            self.cap.release()
        if self.vid_writer is not None:
            self.vid_writer.release()
        self.window.destroy()

root = tk.Tk()
app = CameraApp(root, "Camera Recorder")

# if not os.access(os.getcwd(), os.W_OK):
#     app.status.config(text="Ошибка: нет прав записи в рабочую директорию!")

root.mainloop()