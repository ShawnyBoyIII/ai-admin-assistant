import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import numpy as np
import sounddevice as sd
import soundfile as sf


@dataclass
class RecorderConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_seconds: int = 5
    output_dir: Path = Path("recordings")


class RecorderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Admin Assistant - Recorder")
        self.geometry("620x420")

        self.config_obj = RecorderConfig()
        self.audio_queue = queue.Queue()
        self.frames = []
        self.recording = False
        self.session_seconds = 900
        self.start_time = None

        self._build_ui()

    def _build_ui(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.status_label = ctk.CTkLabel(self, text="Idle")
        self.status_label.pack(pady=12)

        self.duration_label = ctk.CTkLabel(self, text="Session Minutes")
        self.duration_label.pack()

        self.duration_entry = ctk.CTkEntry(self, width=140)
        self.duration_entry.insert(0, "15")
        self.duration_entry.pack(pady=8)

        self.start_btn = ctk.CTkButton(self, text="Start Recording", command=self.start_recording)
        self.start_btn.pack(pady=10)

        self.stop_btn = ctk.CTkButton(self, text="Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_btn.pack(pady=10)

        self.log = ctk.CTkTextbox(self, width=560, height=200)
        self.log.pack(padx=20, pady=12)

    def append_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            self.append_log(f"Audio warning: {status}")
        self.audio_queue.put(indata.copy())

    def _record_worker(self):
        self.frames = []
        with sd.InputStream(
            samplerate=self.config_obj.sample_rate,
            channels=self.config_obj.channels,
            callback=self._audio_callback,
            dtype="float32",
        ):
            while self.recording:
                try:
                    data = self.audio_queue.get(timeout=0.2)
                    self.frames.append(data)
                except queue.Empty:
                    pass

                elapsed = int(time.time() - self.start_time)
                remaining = max(0, self.session_seconds - elapsed)
                self.status_label.configure(text=f"Recording... {remaining}s left")
                if elapsed >= self.session_seconds:
                    self.append_log("Session time reached. Auto-stopping.")
                    self.after(0, self.stop_recording)
                    break

    def start_recording(self):
        try:
            mins = int(self.duration_entry.get().strip())
            if mins <= 0:
                raise ValueError
            self.session_seconds = mins * 60
        except ValueError:
            self.append_log("Please enter a valid positive number of minutes.")
            return

        self.config_obj.output_dir.mkdir(parents=True, exist_ok=True)
        self.recording = True
        self.start_time = time.time()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.append_log("Microphone recording started.")
        threading.Thread(target=self._record_worker, daemon=True).start()

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Saving...")

        if not self.frames:
            self.append_log("No audio captured.")
            self.status_label.configure(text="Idle")
            return

        audio = np.concatenate(self.frames, axis=0)
        filename = datetime.now().strftime("session_%Y%m%d_%H%M%S.wav")
        path = self.config_obj.output_dir / filename
        sf.write(path, audio, self.config_obj.sample_rate)
        self.append_log(f"Saved recording to {path}")
        self.status_label.configure(text="Idle")


if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()
