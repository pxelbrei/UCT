import os
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import shutil
import subprocess
import threading
import webbrowser
from queue import Queue, Empty
import ctypes
import sys
import time
import logging


class USBCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USB Checker (UCT)")
        self.root.geometry("600x500")  # Fixed window size
        self.root.resizable(False, False)  # Window not resizable
        self.root.configure(bg="#2e2e2e")
        self.center_window(self.root)

        self.selected_drive = tk.StringVar()
        self.process_queue = Queue()
        self.check_queue()
        self.is_running = False

        # Setup logging
        self.setup_logging()

        # Custom style for buttons (square and flat)
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5, relief="flat", background="#444", foreground="black",
                            font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[("active", "#666")])

        # Title
        title_frame = tk.Frame(root, bg="#2e2e2e")
        title_frame.pack(pady=5)
        tk.Label(title_frame, text="USB Checker (UCT)", font=("Arial", 16, "bold"),
                 bg="#2e2e2e", fg="white").pack()

        # Drive selection
        drive_frame = tk.Frame(root, bg="#2e2e2e")
        drive_frame.pack(pady=5)
        self.drive_dropdown = ttk.Combobox(drive_frame, textvariable=self.selected_drive,
                                           state="readonly", width=25)  # Adjusted width
        self.drive_dropdown.pack(side=tk.LEFT, padx=5)

        # Refresh button
        refresh_button = ttk.Button(drive_frame, text="Refresh", command=self.refresh_drives, style="TButton")
        refresh_button.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(refresh_button, "Refresh the list of available USB drives")

        # Open Log File Button (next to the Refresh button)
        open_log_button = ttk.Button(drive_frame, text="Open Log File", command=self.open_log_file, style="TButton")
        open_log_button.pack(side=tk.LEFT, padx=5)

        # Buttons (square and flat, placed side by side)
        button_frame = tk.Frame(root, bg="#2e2e2e")
        button_frame.pack(pady=5)
        self.create_button(button_frame, "Analyze", self.analyze_usb,
                           "Analyze the selected USB drive for storage and speed")
        self.create_button(button_frame, "Repair", self.run_repair_in_thread,
                           "Repair the selected USB drive")
        self.create_button(button_frame, "Benchmark", self.run_benchmark_in_thread,
                           "Measure the read/write speed of the USB drive")
        self.create_button(button_frame, "Backup", self.run_backup_in_thread,
                           "Backup data from the USB drive")

        # Output window
        self.result_display = ScrolledText(root, height=10, bg="#1e1e1e", fg="lime",
                                           font=("Consolas", 9), state="disabled", wrap=tk.WORD)
        self.result_display.pack(pady=5, padx=10, fill="both", expand=True)
        self.result_display.tag_configure("center", justify="center")

        # Progress bar (animated)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5)

        # GitHub link
        github_frame = tk.Frame(root, bg="#2e2e2e")
        github_frame.pack(pady=5)
        github_link = tk.Label(github_frame, text="Visit UCT on GitHub", fg="#4af",
                               cursor="hand2", bg="#2e2e2e", font=("Arial", 9, "underline"))
        github_link.pack()
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/pxelbrei/UCT"))

        # Initial drive refresh
        self.refresh_drives()

    def setup_logging(self):
        """Set up logging to a file with a maximum size of 10 MB."""
        log_file = "usb_checker.log"
        max_size = 10 * 1024 * 1024  # 10 MB

        # Check if the log file exceeds the maximum size
        if os.path.exists(log_file) and os.path.getsize(log_file) > max_size:
            os.remove(log_file)  # Delete the log file if it's too large

        logging.basicConfig(filename=log_file, level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")
        logging.info("USB Checker started.")

    def open_log_file(self):
        """Open the log file in the default text editor."""
        log_file = "usb_checker.log"
        if os.path.exists(log_file):
            if sys.platform == "win32":
                os.startfile(log_file)  # Windows
            elif sys.platform == "darwin":
                subprocess.run(["open", log_file])  # macOS
            else:
                subprocess.run(["xdg-open", log_file])  # Linux
        else:
            messagebox.showinfo("Info", "Log file does not exist yet.")

    def center_window(self, window):
        """Center the given window on the screen."""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def create_button(self, parent, text, command, tooltip_text=None):
        """Create a styled button with a tooltip."""
        button = ttk.Button(parent, text=text, command=command, style="TButton")
        button.pack(side=tk.LEFT, padx=5)
        if tooltip_text:
            self.create_tooltip(button, tooltip_text)

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        tooltip = tk.Label(self.root, text=text, bg="#ffeb3b", fg="black",
                           relief="solid", borderwidth=1, font=("Arial", 8))
        tooltip.pack_forget()

        def enter(event):
            tooltip.place(x=widget.winfo_rootx(), y=widget.winfo_rooty() + widget.winfo_height())

        def leave(event):
            tooltip.place_forget()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def check_queue(self):
        """Check the process queue for updates."""
        try:
            while True:
                message = self.process_queue.get_nowait()
                self.update_result_display(message)
        except Empty:
            pass
        self.root.after(100, self.check_queue)

    def refresh_drives(self):
        """Refresh the list of available USB drives with additional information."""
        try:
            drives = []
            for partition in psutil.disk_partitions():
                # Check if the drive is a USB drive
                if self.is_usb_drive(partition.device):
                    drive_letter = partition.device
                    drive_label = self.get_drive_label(drive_letter)  # Get drive label
                    drive_info = f"{drive_letter} - {drive_label} ({partition.fstype})"  # Combined description
                    drives.append((drive_letter, drive_info))  # Store drive letter and description

            # Update dropdown values
            self.drive_dropdown["values"] = [drive_info for _, drive_info in drives]
            if drives:
                self.drive_dropdown.set(drives[0][1])  # Select the first entry
            else:
                self.drive_dropdown.set("")
                self.process_queue.put("No USB drives found.\n")
        except psutil.Error as e:
            self.process_queue.put(f"Error refreshing drives: {e}\n")
            logging.error(f"Error refreshing drives: {e}")

    def is_usb_drive(self, drive_letter):
        """Check if the drive is a USB drive."""
        try:
            # Windows: Check if the drive is removable
            if sys.platform == "win32":
                import ctypes
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive_letter))
                return drive_type == 2  # DRIVE_REMOVABLE = 2
            else:
                # Linux/macOS: Check if the drive is removable
                return "removable" in psutil.disk_partitions(all=True)[0].opts
        except Exception as e:
            logging.error(f"Error checking if drive is USB: {e}")
            return False

    def get_drive_label(self, drive_letter):
        """Get the label of the drive (if available)."""
        try:
            # Use `ctypes` to retrieve the drive label (Windows-specific)
            if sys.platform == "win32":
                volume_name_buffer = ctypes.create_unicode_buffer(1024)
                file_system_buffer = ctypes.create_unicode_buffer(1024)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive_letter),
                    volume_name_buffer,
                    ctypes.sizeof(volume_name_buffer),
                    None,
                    None,
                    None,
                    file_system_buffer,
                    ctypes.sizeof(file_system_buffer)
                )
                return volume_name_buffer.value.strip() or "No Label"
            else:
                # For Linux/macOS: Use `os.statvfs` or similar methods
                return "No Label"
        except Exception as e:
            logging.error(f"Error getting drive label: {e}")
            return "No Label"

    def extract_drive_letter(self, drive_info):
        """Extract the drive letter from the combined drive info string."""
        if drive_info:
            return drive_info.split(" - ")[0]  # Extract the part before " - "
        return None

    def validate_drive(self):
        """Validate the selected drive."""
        drive_info = self.selected_drive.get()
        if not drive_info:
            messagebox.showwarning("Warning", "Please select a valid USB drive.")
            return None

        # Extract the drive letter from the combined description
        drive_letter = self.extract_drive_letter(drive_info)
        if not drive_letter:
            messagebox.showwarning("Warning", "Invalid drive selection.")
            return None

        # Check if the drive exists and is accessible
        if not os.path.exists(drive_letter):
            messagebox.showwarning("Warning", f"The drive {drive_letter} is not available or does not exist.")
            return None

        # Check if the drive is a USB drive
        if not self.is_usb_drive(drive_letter):
            messagebox.showwarning("Warning", f"The drive {drive_letter} is not a USB drive.")
            return None

        return drive_letter

    def analyze_usb(self):
        """Analyze the selected USB drive."""
        selected_drive = self.validate_drive()
        if not selected_drive:
            self.process_queue.put("No drive selected.\n")
            return

        try:
            usage = shutil.disk_usage(selected_drive)
            partitions = psutil.disk_partitions()
            drive_info = next((p for p in partitions if p.device == selected_drive), None)

            if drive_info:
                message = (f"Drive: {selected_drive}\n"
                           f"File System: {drive_info.fstype}\n"
                           f"Total: {usage.total / (1024**3):.2f} GB\n"
                           f"Used: {usage.used / (1024**3):.2f} GB\n"
                           f"Free: {usage.free / (1024**3):.2f} GB\n")
            else:
                message = (f"Drive: {selected_drive}\n"
                           f"Total: {usage.total / (1024**3):.2f} GB\n"
                           f"Used: {usage.used / (1024**3):.2f} GB\n"
                           f"Free: {usage.free / (1024**3):.2f} GB\n")

            self.process_queue.put(message)
            logging.info(f"Analyzed drive: {selected_drive}")
        except OSError as e:
            self.process_queue.put(f"Error accessing drive: {e}\n")
            logging.error(f"Error accessing drive: {e}")
        except shutil.Error as e:
            self.process_queue.put(f"Error analyzing drive usage: {e}\n")
            logging.error(f"Error analyzing drive usage: {e}")

    def run_repair_in_thread(self):
        """Run the USB repair process in a separate thread."""
        if self.is_running:
            self.process_queue.put("Another operation is already running.\n")
            return

        drive = self.validate_drive()
        if not drive:
            return

        self.is_running = True
        self.progress["value"] = 0
        thread = threading.Thread(target=self.repair_usb, args=(drive,))
        thread.start()

    def repair_usb(self, drive):
        """Repair the selected USB drive."""
        try:
            drive_letter = drive[0]
            if not drive_letter.isalpha():
                self.process_queue.put(f"Invalid drive letter: {drive_letter}\n")
                return

            # Run chkdsk with administrator privileges
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.process_queue.put("Error: Please run the program as an administrator.\n")
                return

            # Use the full path to chkdsk
            chkdsk_path = os.path.join(os.getenv("SystemRoot"), "System32", "chkdsk.exe")
            process = subprocess.Popen([chkdsk_path, f"{drive_letter}:", "/f"], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, shell=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW)

            self.process_queue.put("Repairing USB...\n")

            for line in iter(process.stdout.readline, ""):
                self.process_queue.put(line)
                self.progress["value"] += 10  # Simulate progress

            self.process_queue.put("\nRepair completed.\n")
            self.progress["value"] = 100
            logging.info(f"Repaired drive: {drive}")
        except subprocess.CalledProcessError as e:
            self.process_queue.put(f"Error running chkdsk: {e}\n")
            logging.error(f"Error running chkdsk: {e}")
        except OSError as e:
            self.process_queue.put(f"Error accessing drive: {e}\n")
            logging.error(f"Error accessing drive: {e}")
        except ctypes.WinError as e:
            self.process_queue.put(f"Error with administrator privileges: {e}\n")
            logging.error(f"Error with administrator privileges: {e}")
        finally:
            self.is_running = False

    def run_benchmark_in_thread(self):
        """Run the USB benchmark process in a separate thread."""
        if self.is_running:
            self.process_queue.put("Another operation is already running.\n")
            return

        drive = self.validate_drive()
        if not drive:
            return

        self.is_running = True
        self.progress["value"] = 0
        self.process_queue.put("Starting benchmark... This may take a few moments.\n")
        thread = threading.Thread(target=self.benchmark_usb, args=(drive,))
        thread.start()

    def benchmark_usb(self, drive):
        """Benchmark the selected USB drive."""
        try:
            self.process_queue.put("Running benchmark... Please wait.\n")

            # Write test
            start_time = time.time()
            test_file = os.path.join(drive, "test_file.bin")
            with open(test_file, "wb") as f:
                f.write(os.urandom(100 * 1024 * 1024))  # Write 100 MB of random data
            write_time = time.time() - start_time
            write_speed = (100 / write_time)  # MB/s

            # Read test
            start_time = time.time()
            with open(test_file, "rb") as f:
                while f.read(1024 * 1024):  # Read in 1 MB chunks
                    pass
            read_time = time.time() - start_time
            read_speed = (100 / read_time)  # MB/s

            # Clean up
            os.remove(test_file)

            self.process_queue.put(f"Write speed: {write_speed:.2f} MB/s\n")
            self.process_queue.put(f"Read speed: {read_speed:.2f} MB/s\n")
            self.progress["value"] = 100
            logging.info(f"Benchmarked drive: {drive} - Write: {write_speed:.2f} MB/s, Read: {read_speed:.2f} MB/s")
        except OSError as e:
            self.process_queue.put(f"Error accessing drive: {e}\n")
            logging.error(f"Error accessing drive: {e}")
        except IOError as e:
            self.process_queue.put(f"Error during benchmark: {e}\n")
            logging.error(f"Error during benchmark: {e}")
        finally:
            self.is_running = False

    def run_backup_in_thread(self):
        """Run the USB backup process in a separate thread."""
        if self.is_running:
            self.process_queue.put("Another operation is already running.\n")
            return

        drive = self.validate_drive()
        if not drive:
            return

        backup_folder = filedialog.askdirectory(title="Select Backup Folder")
        if not backup_folder:
            return

        self.is_running = True
        self.progress["value"] = 0
        thread = threading.Thread(target=self.backup_usb, args=(drive, backup_folder))
        thread.start()

    def backup_usb(self, drive, backup_folder):
        """Backup data from the selected USB drive."""
        try:
            self.process_queue.put("Starting backup...\n")

            for root, dirs, files in os.walk(drive):
                relative_path = os.path.relpath(root, drive)
                dest_path = os.path.join(backup_folder, relative_path)
                os.makedirs(dest_path, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_path, file)
                    shutil.copy2(src_file, dest_file)
                    self.progress["value"] += 1  # Simulate progress

            self.process_queue.put("\nBackup completed successfully.\n")
            self.progress["value"] = 100
            logging.info(f"Backed up drive: {drive} to {backup_folder}")
        except OSError as e:
            self.process_queue.put(f"Error accessing drive: {e}\n")
            logging.error(f"Error accessing drive: {e}")
        except shutil.Error as e:
            self.process_queue.put(f"Error copying files: {e}\n")
            logging.error(f"Error copying files: {e}")
        except FileNotFoundError as e:
            self.process_queue.put(f"File not found: {e}\n")
            logging.error(f"File not found: {e}")
        finally:
            self.is_running = False

    def update_result_display(self, text):
        """Update the result display with new text."""
        self.result_display.config(state="normal")
        self.result_display.insert(tk.END, text, "center")
        self.result_display.see(tk.END)
        self.result_display.config(state="disabled")


if __name__ == "__main__":
    # Minimize the console window
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)  # 6 = SW_MINIMIZE

    # Check if the script is run as administrator
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    root = tk.Tk()
    app = USBCheckerApp(root)
    root.mainloop()
