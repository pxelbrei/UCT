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
from queue import Queue, Empty


class USBCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USB Checker (UCT)")
        self.root.geometry("500x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#2e2e2e")
        self.center_window()  # Center the window on the screen

        self.selected_drive = tk.StringVar()
        self.process_queue = Queue()
        self.check_queue()

        # Custom style for buttons
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5, relief="flat", background="gray", foreground="black", font=("Arial", 10))
        self.style.map("TButton", background=[("active", "#666")])

        # Title
        title_frame = tk.Frame(root, bg="#2e2e2e")
        title_frame.pack(pady=5)
        tk.Label(title_frame, text="USB Checker (UCT)", font=("Arial", 14, "bold"),
                 bg="#2e2e2e", fg="white").pack()

        # Drive selection
        drive_frame = tk.Frame(root, bg="#2e2e2e")
        drive_frame.pack(pady=5)
        self.drive_dropdown = ttk.Combobox(drive_frame, textvariable=self.selected_drive,
                                           state="readonly", width=30)
        self.drive_dropdown.pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = tk.Frame(root, bg="#2e2e2e")
        button_frame.pack(pady=5)
        self.create_button(button_frame, "Refresh", self.refresh_drives,
                           "Aktualisiert die Liste der verfügbaren USB-Laufwerke")
        self.create_button(button_frame, "Analyze", self.analyze_usb,
                           "Analysiert das ausgewählte USB-Laufwerk auf Speicherplatz und Geschwindigkeit")

        # Tools menu
        tools_menu = ttk.Menubutton(button_frame, text="Tools", style="TButton")
        menu = tk.Menu(tools_menu, tearoff=0, bg="#444", fg="white")
        tools_menu.configure(menu=menu)
        menu.add_command(label="Repair USB", command=self.run_repair_in_thread)
        menu.add_command(label="Format USB", command=self.show_format_dialog)
        tools_menu.pack(side=tk.LEFT, padx=5)

        # Output window
        self.result_display = ScrolledText(root, height=10, bg="#1e1e1e", fg="lime",
                                           font=("Consolas", 9), state="disabled", wrap=tk.WORD)
        self.result_display.pack(pady=5, padx=10, fill="both", expand=True)
        self.result_display.tag_configure("center", justify="center")

        # GitHub link
        github_frame = tk.Frame(root, bg="#2e2e2e")
        github_frame.pack(pady=5)
        github_link = tk.Label(github_frame, text="Visit UCT on GitHub", fg="#4af",
                               cursor="hand2", bg="#2e2e2e")
        github_link.pack()
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/pxelbrei/UCT"))

        # Initial drive refresh
        self.refresh_drives()

    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_button(self, parent, text, command, tooltip_text):
        """Create a styled button with a tooltip."""
        button = ttk.Button(parent, text=text, command=command, style="TButton")
        button.pack(side=tk.LEFT, padx=5)
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
        """Refresh the list of available USB drives."""
        drives = [disk.device for disk in psutil.disk_partitions() if "removable" in disk.opts]
        self.drive_dropdown["values"] = drives
        if drives:
            self.drive_dropdown.set(drives[0])
        else:
            self.drive_dropdown.set("")
            self.process_queue.put("No USB drives found.\n")

    def analyze_usb(self):
        """Analyze the selected USB drive."""
        selected_drive = self.selected_drive.get()
        if not selected_drive:
            self.process_queue.put("No drive selected.\n")
            return

        try:
            usage = shutil.disk_usage(selected_drive)
            message = (f"Drive: {selected_drive}\n"
                       f"Total: {usage.total / (1024**3):.2f} GB\n"
                       f"Used: {usage.used / (1024**3):.2f} GB\n"
                       f"Free: {usage.free / (1024**3):.2f} GB\n")
            self.process_queue.put(message)
        except Exception as e:
            self.process_queue.put(f"Error analyzing drive: {e}\n")

    def run_repair_in_thread(self):
        """Run the USB repair process in a separate thread."""
        drive = self.validate_drive()
        if not drive:
            return

        thread = threading.Thread(target=self.repair_usb, args=(drive,))
        thread.start()

    def repair_usb(self, drive):
        """Repair the selected USB drive."""
        try:
            process = subprocess.Popen(["chkdsk", drive, "/f"], stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, shell=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW)

            self.process_queue.put("Repairing USB...\n")

            for line in iter(process.stdout.readline, ""):
                self.process_queue.put(line)

            self.process_queue.put("\nRepair completed.\n")
        except Exception as e:
            self.process_queue.put(f"Error: {str(e)}\n")

    def show_format_dialog(self):
        """Show a dialog to select the filesystem for formatting."""
        drive = self.validate_drive()
        if not drive:
            return

        # Create a new dialog window
        format_dialog = tk.Toplevel(self.root)
        format_dialog.title("Select Filesystem")
        format_dialog.geometry("300x150")
        format_dialog.resizable(False, False)
        format_dialog.configure(bg="#2e2e2e")

        # Label
        tk.Label(format_dialog, text="Select filesystem:", bg="#2e2e2e", fg="white").pack(pady=10)

        # Filesystem selection
        filesystem_var = tk.StringVar(value="FAT32")  # Default selection
        filesystems = ["FAT", "FAT32", "NTFS", "exFAT"]
        for fs in filesystems:
            tk.Radiobutton(format_dialog, text=fs, variable=filesystem_var, value=fs,
                           bg="#2e2e2e", fg="white", selectcolor="#444").pack(anchor="w", padx=20)

        # Format button
        tk.Button(format_dialog, text="Format", command=lambda: self.run_format_in_thread(drive, filesystem_var.get()),
                  bg="gray", fg="black").pack(pady=10)

    def run_format_in_thread(self, drive, filesystem):
        """Run the USB format process in a separate thread."""
        thread = threading.Thread(target=self.format_usb, args=(drive, filesystem))
        thread.start()

    def format_usb(self, drive, filesystem):
        """Format the selected USB drive with the specified filesystem."""
        try:
            # Create a temporary script for diskpart
            script_path = os.path.join(os.getenv("TEMP"), "format_usb_script.txt")
            with open(script_path, "w") as script_file:
                script_file.write(f"select volume {drive[0]}\n")  # Drive letter without colon
                script_file.write("clean\n")
                script_file.write("create partition primary\n")
                script_file.write(f"format fs={filesystem} quick\n")
                script_file.write("assign\n")

            # Run diskpart with the script
            process = subprocess.Popen(
                ["diskpart", "/s", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # Prevent external CMD window
            )

            self.process_queue.put(f"Formatting USB with {filesystem}...\n")

            # Read process output in real-time
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    self.process_queue.put(output)

            # Check if the process completed successfully
            return_code = process.poll()
            if return_code == 0:
                self.process_queue.put("\nFormat completed successfully.\n")
            else:
                self.process_queue.put(f"\nFormat failed with return code {return_code}.\n")

        except Exception as e:
            self.process_queue.put(f"Error: {str(e)}\n")
        finally:
            # Delete the temporary script file
            if os.path.exists(script_path):
                os.remove(script_path)

    def update_result_display(self, text):
        """Update the result display with new text."""
        self.result_display.config(state="normal")
        self.result_display.insert(tk.END, text, "center")
        self.result_display.see(tk.END)
        self.result_display.config(state="disabled")

    def validate_drive(self):
        """Validate the selected drive."""
        drive = self.selected_drive.get()
        if not drive or not os.path.exists(drive):
            messagebox.showwarning("Warning", "Please select a valid USB drive.")
            return None
        return drive


if __name__ == "__main__":
    root = tk.Tk()
    app = USBCheckerApp(root)
    root.mainloop()
