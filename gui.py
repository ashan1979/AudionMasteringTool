import tkinter as tk
from threading import Thread
from tkinter import filedialog, messagebox
import  main
import threading
import os

class MasteringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Audio Mastering Tool")
        self.root.geometry("400x300")

        # File Selection
        self.input_path = tk.StringVar()
        tk.Label(root, text="Select Audio Files:").pack(pady=5)
        tk.Entry(root, textvariable=self.input_path, width=40).pack()
        tk.Button(root, text="Browse", command=self.browse_file).pack(pady=5)

        # Snipping Controls
        tk.Label(root, text="Start Time (sec):").pack()
        self.start_entry = tk.Entry(root)
        self.start_entry.insert(0, "0")
        self.start_entry.pack()

        tk.Label(root, text="End Time (sec):").pack()
        self.end_entry = tk.Entry(root)
        self.end_entry.insert(0, "30")
        self.end_entry.pack()

        # Action Button
        self.master_btn = tk.Button(root, text="MASTER & VISUALIZE", bg="#d79921", fg="black", command=self.run_mastering)
        self.master_btn.pack(pady=20)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.flac")])
        self.input_path.set(filename)

    def run_mastering(self):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select a file first")
            return
        def task():
            self.master_btn.config(state="disabled", text="Processing...")
            try:
                start = float(self.start_entry.get())
                end = float(self.end_entry.get())

                input_filename = os.path.basename(self.input_path.get())
                output_file = f"mastered_{input_filename}"

            # Calling main function
                main.snip_audio(self.input_path.get(), start, end, output_file)
                messagebox.showinfo("Success", f"Mastering Complete!\nSaved as {output_file}")
            except Exception as e:
                 messagebox.showerror("Mastering Error", str(e))
            finally:
                self.master_btn.config(state="normal", text="MASTER & VISUALIZE")

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MasteringApp(root)
    root.mainloop()