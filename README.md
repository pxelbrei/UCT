<p align="center">
  <h1 align="center">USB Checker (UCT)</h1>
</p>

<p align="center">
  USB Checker (UCT) is a user-friendly desktop application designed to help users manage and troubleshoot USB drives efficiently. Built with Python and the Tkinter library, this tool provides a range of features to analyze, repair, benchmark, and back up USB drives. It is particularly useful for diagnosing issues, optimizing performance, and ensuring data safety.
</p>

---

## **Key Features**

### **Drive Analysis**
- Displays detailed information about the selected USB drive, including:
  - Total storage capacity.
  - Used and free space.
- Helps users understand the current state of their USB drive.

### **Drive Repair**
- Runs the `chkdsk` utility to repair file system errors on the selected USB drive.
- Requires administrator privileges to ensure proper execution.
- Provides real-time progress updates during the repair process.

### **Benchmark Test**
- Measures the read and write speeds of the USB drive.
- Performs a 100 MB file write and read test to calculate speed in MB/s.
- Informs the user about the progress and results of the benchmark.

### **Data Backup**
- Allows users to back up data from the USB drive to a selected folder on their computer.
- Preserves the directory structure during the backup process.
- Provides progress updates during the backup operation.

### **Drive Selection**
- Automatically detects and lists all available USB drives.
- Allows users to refresh the list of drives with a single click.

### **Real-Time Output**
- Displays real-time progress and results in a scrollable output window.
- Keeps users informed about the status of ongoing operations.

### **Progress Bar**
- Visualizes the progress of operations like repair, benchmark, and backup.
- Provides a clear indication of how much of the task is completed.

---

## **How It Works**

1. **Select a USB Drive**:
   - Choose the desired USB drive from the dropdown menu.

2. **Perform Actions**:
   - Use the buttons to analyze, repair, benchmark, or back up the selected drive.
   - Each operation runs in a separate thread to keep the interface responsive.

3. **View Results**:
   - Results and progress are displayed in the output window in real-time.
   - Detailed logs are saved to a file (`usb_checker.log`) for future reference.

---

## **System Requirements**

- **Operating System**: Windows (due to the use of `chkdsk` and `diskpart`).
- **Python Version**: Python 3.x.
- **Libraries**: `tkinter`, `psutil`, `shutil`, `subprocess`, `threading`, `webbrowser`, `ctypes`, `logging`.

---

## **Why Use USB Checker (UCT)?**

- **User-Friendly Interface**: Simple and intuitive design for easy navigation.
- **Comprehensive Tools**: Combines multiple USB management features in one application.
- **Real-Time Feedback**: Keeps users informed about the status of operations.
- **Open Source**: Freely available on GitHub for customization and improvement.

---

## **Screenshots**

<p align="center">
  <img src="https://storage.ko-fi.com/cdn/useruploads/display/2f90d7b9-4849-429a-8898-828f91d86b3e_uct.png" alt="USB Checker (UCT) Screenshot"/>
</p>

---

## **License**

The tool is open-source and released under the **BSD-3-Clause License**.

---

## **Support Me**

<p align="center">
  <img src="https://user-images.githubusercontent.com/74038190/213866269-5d00981c-7c98-46d7-8a8e-16f462f15227.gif" width="80" height="80"/> 
  <a href="https://ko-fi.com/pxelbrei">Support me on Ko-fi</a> 
  <img src="https://user-images.githubusercontent.com/74038190/213866269-5d00981c-7c98-46d7-8a8e-16f462f15227.gif" width="80" height="80"/>
</p>
