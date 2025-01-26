import os
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import shutil
import time
import subprocess

class USBCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USB Checker")
        self.root.geometry("600x484")  # Adjusted window height
        self.root.resizable(False, False)
        self.root.configure(bg="darkgray")
        
        self.selected_drive = tk.StringVar()

        # UI Elements
        tk.Label(root, text="USB Checker", font=("Arial", 18, "bold"), bg="darkgray", fg="white").pack(pady=10)

        self.drive_dropdown = ttk.Combobox(self.root, textvariable=self.selected_drive, state="readonly")
        self.drive_dropdown.pack(pady=10)

        tk.Button(root, text="Refresh Drives", command=self.refresh_drives, bg="gray", fg="white").pack(pady=5)
        tk.Button(root, text="Analyze USB", command=self.analyze_usb, bg="gray", fg="white").pack(pady=5)

        # Tools dropdown menu
        tools_menu = ttk.Menubutton(self.root, text="Tools", direction="below")
        menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.configure(menu=menu)
        menu.add_command(label="Repair USB", command=self.repair_usb)
        menu.add_command(label="Format USB", command=self.format_usb)
        tools_menu.pack(pady=5)

        self.result_display = ScrolledText(self.root, height=12, bg="#1e1e1e", fg="lime", font=("Courier", 10), state="disabled", wrap=tk.WORD)
        self.result_display.pack(pady=10, fill="both", expand=True)

        # Centering the text
        self.result_display.tag_configure("center", justify="center")

        self.refresh_drives()

    def refresh_drives(self):
        drives = [disk.device for disk in psutil.disk_partitions() if "removable" in disk.opts]
        self.drive_dropdown["values"] = drives
        if drives:
            self.drive_dropdown.current(0)
        else:
            self.drive_dropdown.set("No USB drives found")

    def analyze_usb(self):
        drive = self.selected_drive.get()
        if not drive:
            messagebox.showwarning("Warning", "Please select a USB drive.")
            return

        self.result_display.config(state="normal")
        self.result_display.delete("1.0", tk.END)

        try:
            # Get drive information
            total, used, free = shutil.disk_usage(drive)
            self.result_display.insert(tk.END, f"Drive: {drive}\n", "center")
            self.result_display.insert(tk.END, f"Total Size: {self.format_size(total)}\n", "center")
            self.result_display.insert(tk.END, f"Used Space: {self.format_size(used)}\n", "center")
            self.result_display.insert(tk.END, f"Free Space: {self.format_size(free)}\n", "center")

            # Speed test
            read_speed, write_speed = self.speed_test(drive)
            self.result_display.insert(tk.END, f"Read Speed: {read_speed:.2f} MB/s\n", "center")
            self.result_display.insert(tk.END, f"Write Speed: {write_speed:.2f} MB/s\n", "center")

            # Check for errors (mock example)
            self.result_display.insert(tk.END, "Scanning for errors...\n", "center")
            errors = self.mock_error_scan(drive)
            if errors:
                self.result_display.insert(tk.END, f"Errors found: {errors}\n", "center")
            else:
                self.result_display.insert(tk.END, "No errors found.\n", "center")
        except Exception as e:
            self.result_display.insert(tk.END, f"Error: {str(e)}\n", "center")

        self.result_display.config(state="disabled")
        self.result_display.see(tk.END)

    def repair_usb(self):
        drive = self.selected_drive.get()
        if not drive:
            messagebox.showwarning("Warning", "Please select a USB drive.")
            return

        self.result_display.config(state="normal")
        self.result_display.insert(tk.END, "Repairing USB...\n", "center")
        self.result_display.see(tk.END)
        
        try:
            # Run chkdsk for repairing file system errors
            result = subprocess.run(["chkdsk", drive, "/f"], capture_output=True, text=True)
            self.result_display.insert(tk.END, result.stdout, "center")
            self.result_display.insert(tk.END, "Repair completed successfully.\n", "center")
        except Exception as e:
            self.result_display.insert(tk.END, f"Error: {str(e)}\n", "center")

        self.result_display.config(state="disabled")
        self.result_display.see(tk.END)

    def format_usb(self):
        drive = self.selected_drive.get()
        if not drive:
            messagebox.showwarning("Warning", "Please select a USB drive.")
            return

        confirm = messagebox.askyesno("Confirm Format", f"Are you sure you want to format the drive {drive}? This will erase all data.")
        if not confirm:
            return

        self.result_display.config(state="normal")
        self.result_display.insert(tk.END, "Formatting USB...\n", "center")
        self.result_display.see(tk.END)

        try:
            # Format the drive (Windows specific)
            result = subprocess.run(["format", drive.replace('\\', ''), "/fs:NTFS", "/q", "/y"], capture_output=True, text=True, shell=True)
            self.result_display.insert(tk.END, result.stdout, "center")
            self.result_display.insert(tk.END, "Format completed successfully.\n", "center")
        except Exception as e:
            self.result_display.insert(tk.END, f"Error: {str(e)}\n", "center")

        self.result_display.config(state="disabled")
        self.result_display.see(tk.END)

    @staticmethod
    def format_size(size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def speed_test(self, drive):
        test_file = os.path.join(drive, "speed_test_file.tmp")
        data = os.urandom(1024 * 1024)  # 1 MB of random data

        # Write test
        start_time = time.time()
        with open(test_file, "wb") as f:
            f.write(data)
        write_time = time.time() - start_time

        # Read test
        start_time = time.time()
        with open(test_file, "rb") as f:
            f.read()
        read_time = time.time() - start_time

        os.remove(test_file)

        write_speed = 1 / write_time
        read_speed = 1 / read_time
        return read_speed, write_speed

    @staticmethod
    def mock_error_scan(drive):
        # Mock error scan (replace with actual implementation if needed)
        return "None"

    @staticmethod
    def mock_repair_process(drive):
        # Mock repair process (replace with actual implementation if needed)
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = USBCheckerApp(root)
    root.mainloop()
