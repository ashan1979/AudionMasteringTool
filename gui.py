import tkinter as tk
from threading import Thread
from tkinter import filedialog, messagebox, ttk
import  main
import threading
import os

class MasteringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ashan's Python Audio Mastering Tool v1.1")
        self.root.geometry("450x550")
        self.root.configure(bg="#1e1e1e")

        # Custom styling
        style = ttk.Style()
        style.theme_use('clam')

        # File Selection Section
        self.input_path = tk.StringVar()
        tk.Label(root, text="AUDIO SOURCE", bg="#1e1e1e", fg="#d79921", font=("Arial", 10, "bold")).pack(pady=10)

        file_frame = tk.Frame(root, bg="#1e1e1e")
        file_frame.pack(pady=5, padx=20, fill="x")
        tk.Entry(file_frame, textvariable=self.input_path, bg="#2d2d2d", fg="white", insertbackground="white").pack(side="left", expand=True, fill="x")
        tk.Button(file_frame, text="Browse", command=self.browse_file, bg="#458588", fg="white").pack(side="right", padx=5)

        # Settings Container
        settings_frame = tk.LabelFrame(root, text=" Processing Parameters", bg="#1e1e1e", fg="gray", padx=10, pady=10)
        settings_frame.pack(pady=10, padx=20, fill="x")

        # Snipping Row
        tk.Label(settings_frame, text="Start / End (sec):", bg="#1e1e1e", fg="white").grid(row=0, column=0, sticky="w")
        self.start_entry = tk.Entry(settings_frame, width=8)
        self.start_entry.insert(0, "0")
        self.start_entry.grid(row=0, column=1, pady=5)

        self.end_entry = tk.Entry(settings_frame, width=8)
        self.end_entry.insert(0, "30")
        self.end_entry.grid(row=0, column=2, pady=5)

        # EQ Eow (Snip Audio Parameters)
        tk.Label(settings_frame, text="HP / LP Cutoff (Hz):", bg="#1e1e1e", fg="white").grid(row=1, column=0, sticky="w")
        self.hp_entry = tk.Entry(settings_frame, width=8)
        self.hp_entry.insert(0, "40")
        self.hp_entry.grid(row=1, column=1, pady=5)

        self.lp_entry = tk.Entry(settings_frame, width=8)
        self.lp_entry.insert(0, "15000")
        self.lp_entry.grid(row=1, column=2, pady=5)

        # Processing Options
        self.use_clipper = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="Enable Soft Clipper (Warmth)", variable=self.use_clipper,
                       bg="#1e1e1e", fg="#d79921", selectcolor="#1e1e1e", activebackground="#1e1e1e").grid(row=2, column=0, columnspan=3, pady=10)

        # Progress and Action
        self.master_btn = tk.Button(root, text="RENDER MASTER", bg="#d79921", fg="black",
                                    font=("Arial", 12, "bold"), height=2, command=self.run_mastering)
        self.master_btn.pack(pady=15, padx=20, fill="x")

        # Log Box (Console Feedback)
        tk.Label(root, text="PROCESS LOG", bg="#1e1e1e", fg="gray", font=("Arial", 8)).pack()
        self.log_box = tk.Text(root, height=6, bg="#000000", fg="#00ff00", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20, fill="x")
    def log(self, message):
        self.log_box.insert(tk.END, f"> {message}\n")
        self.log_box.see(tk.END)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.flac")])
        if filename:
            self.input_path.set(filename)
            self.log(f"Loaded: {os.path.basename(filename)}")

    def run_mastering(self):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select a file first")
            return

        def task():
            self.master_btn.config(state="disabled", text="PROCESSING...")
            self.log("Initializing engine...")
            try:
                # Gather UI data
                start = float(self.start_entry.get())
                end = float(self.end_entry.get())
                hp = int(self.hp_entry.get())
                lp = int(self.lp_entry.get())
                clipper_status = self.use_clipper.get()

                input_file = self.input_path.get()
                output_file = f"mastered_{os.path.basename(input_file)}"

                self.log(f"Snipping: {start}s to {end}s")
                self.log(f"EQ: HP {hp}Hz | LP {lp}Hz")

                # Execute engine
                main.snip_audio(input_file, start, end, output_file,
                                 use_clipper=clipper_status,
                                hp_cutoff=hp,
                                lp_cutoff=lp)

                self.log("Generating visual analysis...")
                self.log(f"SUCCESS {output_file}")
                messagebox.showinfo("Success", f"Mastering Complete!\nSaved as {output_file}")

            except Exception as e:
                self.log(f"ERROR: {str(e)}")
                messagebox.showerror("Mastering Error", str(e))
            finally:
                self.master_btn.config(state="normal", text="RENDER MASTER")

        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MasteringApp(root)
    root.mainloop()
