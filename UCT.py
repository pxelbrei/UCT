import os
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import shutil
import time
import subprocess
import threading
import webbrowser

class USBCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USB Checker (UCT)")
        self.root.geometry("500x500")  # Kompakteres Fenster
        self.root.resizable(False, False)
        self.root.configure(bg="darkgray")
        self.center_window()

        self.selected_drive = tk.StringVar()

        # Titel
        tk.Label(root, text="USB Checker (UCT)", font=("Arial", 14, "bold"), bg="darkgray", fg="white").pack(pady=5)

        # Laufwerksauswahl
        self.drive_dropdown = ttk.Combobox(self.root, textvariable=self.selected_drive, state="readonly")
        self.drive_dropdown.pack(pady=5)

        # Buttons mit Tooltips
        self.create_button("Refresh", self.refresh_drives, "Aktualisiert die Liste der verfügbaren USB-Laufwerke.")
        self.create_button("Analyze", self.analyze_usb, "Analysiert das ausgewählte USB-Laufwerk auf Speicherplatz und Geschwindigkeit.")

        # Tools-Menü
        tools_menu = ttk.Menubutton(self.root, text="Tools", direction="below")
        menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.configure(menu=menu)
        menu.add_command(label="Repair USB", command=self.run_repair_in_thread)
        menu.add_command(label="Format USB", command=self.run_format_in_thread)
        tools_menu.pack(pady=3)

        # Ausgabefenster (kleiner)
        self.result_display = ScrolledText(self.root, height=10, bg="#1e1e1e", fg="lime", font=("Courier", 9), state="disabled", wrap=tk.WORD)
        self.result_display.pack(pady=5, fill="both", expand=True)
        self.result_display.tag_configure("center", justify="center")

        # GitHub-Link
        github_link = tk.Label(self.root, text="Visit UCT on GitHub", fg="blue", cursor="hand2", bg="darkgray")
        github_link.pack(pady=5)
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/pxelbrei/UCT"))

        # Laufwerke aktualisieren
        self.refresh_drives()

    def create_button(self, text, command, tooltip_text):
        button = tk.Button(self.root, text=text, command=command, bg="gray", fg="white")
        button.pack(pady=3)
        self.create_tooltip(button, tooltip_text)

    def create_tooltip(self, widget, text):
        tooltip = tk.Label(self.root, text=text, bg="yellow", fg="black", relief="solid", borderwidth=1)
        tooltip.pack_forget()

        def enter(event):
            tooltip.place(x=widget.winfo_rootx(), y=widget.winfo_rooty() + widget.winfo_height())

        def leave(event):
            tooltip.place_forget()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def refresh_drives(self):
        drives = [disk.device for disk in psutil.disk_partitions() if "removable" in disk.opts]
        self.drive_dropdown["values"] = drives
        if drives:
            self.drive_dropdown.set(drives[0])
        else:
            self.drive_dropdown.set("")

    def analyze_usb(self):
        drive = self.validate_drive()
        if not drive:
            return

        self.result_display.config(state="normal")
        self.result_display.delete("1.0", tk.END)

        try:
            total, used, free = shutil.disk_usage(drive)
            self.result_display.insert(tk.END, f"Drive: {drive}\n", "center")
            self.result_display.insert(tk.END, f"Total: {self.format_size(total)}\n", "center")
            self.result_display.insert(tk.END, f"Used: {self.format_size(used)}\n", "center")
            self.result_display.insert(tk.END, f"Free: {self.format_size(free)}\n", "center")
            read_speed, write_speed = self.speed_test(drive)
            self.result_display.insert(tk.END, f"Read: {read_speed:.2f} MB/s\n", "center")
            self.result_display.insert(tk.END, f"Write: {write_speed:.2f} MB/s\n", "center")
            self.result_display.insert(tk.END, "No errors found.\n", "center")
        except Exception as e:
            self.result_display.insert(tk.END, f"Error: {str(e)}\n", "center")

        self.result_display.config(state="disabled")

    def speed_test(self, drive):
        test_file = os.path.join(drive, "speed_test.tmp")
        data = os.urandom(1024 * 1024)  # 1 MB zufällige Daten

        try:
            start_time = time.time()
            with open(test_file, "wb") as f:
                f.write(data)
            write_time = time.time() - start_time

            start_time = time.time()
            with open(test_file, "rb") as f:
                f.read()
            read_time = time.time() - start_time

            write_speed = 1 / write_time
            read_speed = 1 / read_time
            return read_speed, write_speed
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def run_repair_in_thread(self):
        drive = self.validate_drive()
        if not drive:
            return

        thread = threading.Thread(target=self.repair_usb, args=(drive,))
        thread.start()

    def repair_usb(self, drive):
        try:
            process = subprocess.Popen(["chkdsk", drive, "/f"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.result_display.config(state="normal")
            self.result_display.insert(tk.END, "Repairing USB...\n", "center")
            self.result_display.config(state="disabled")
            
            for line in iter(process.stdout.readline, ""):
                self.root.after(0, self.update_result_display, line)

            self.root.after(0, self.update_result_display, "\nRepair completed.\n")
        except Exception as e:
            self.root.after(0, self.update_result_display, f"Error: {str(e)}\n")

    def run_format_in_thread(self):
        drive = self.validate_drive()
        if not drive:
            return

        thread = threading.Thread(target=self.format_usb, args=(drive,))
        thread.start()

    def format_usb(self, drive):
        try:
            # Erstellen eines temporären Skripts für diskpart
            script_path = os.path.join(os.getenv("TEMP"), "format_usb_script.txt")
            with open(script_path, "w") as script_file:
                script_file.write(f"select volume {drive[0]}\n")  # Laufwerksbuchstabe ohne Doppelpunkt
                script_file.write("clean\n")
                script_file.write("create partition primary\n")
                script_file.write("format fs=fat32 quick\n")
                script_file.write("assign\n")

            # Ausführen von diskpart mit dem Skript
            process = subprocess.Popen(
                ["diskpart", "/s", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # Verhindert das Öffnen eines externen CMD-Fensters
            )

            self.root.after(0, self.update_result_display, "Formatting USB...\n")

            # Ausgabe des Prozesses in Echtzeit lesen
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    self.root.after(0, self.update_result_display, output)

            # Überprüfen, ob der Prozess erfolgreich abgeschlossen wurde
            return_code = process.poll()
            if return_code == 0:
                self.root.after(0, self.update_result_display, "\nFormat completed successfully.\n")
            else:
                self.root.after(0, self.update_result_display, f"\nFormat failed with return code {return_code}.\n")

        except Exception as e:
            self.root.after(0, self.update_result_display, f"Error: {str(e)}\n")
        finally:
            # Temporäre Skriptdatei löschen
            if os.path.exists(script_path):
                os.remove(script_path)

    def update_result_display(self, text):
        self.result_display.config(state="normal")
        self.result_display.insert(tk.END, text, "center")
        self.result_display.see(tk.END)
        self.result_display.config(state="disabled")

    def validate_drive(self):
        drive = self.selected_drive.get()
        if not drive or not os.path.exists(drive):
            messagebox.showwarning("Warning", "Please select a valid USB drive.")
            return None
        return drive

    @staticmethod
    def format_size(size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

if __name__ == "__main__":
    root = tk.Tk()
    app = USBCheckerApp(root)
    root.mainloop()
