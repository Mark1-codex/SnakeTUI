import sys
import tty
import termios
import keyboard
import os
import select
import time
import re
from pathlib import Path

VERSION = "1.1.0"

# Track the currently active file globally to allow quick-saving without re-prompting
CURRENT_FILE_PATH = None


def strip_ansi_codes(text):
    """Removes ANSI escape sequences from the string."""
    ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_regex.sub('', text)


def run_code_editor(initial_content=""):
    """
    Runs the raw terminal text editor.
    Accepts initial_content to populate the buffer when opening an existing file.
    """
    buffer = []
    current_line = []
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    # Flush old buffer garbage
    while select.select([sys.stdin], [], [], 0.0)[0]:
        sys.stdin.read(1)

    # Populate buffer if editing an existing file
    if initial_content:
        # Split content by lines, preserving structure
        lines = initial_content.splitlines()
        if lines:
            for line in lines[:-1]:
                buffer.append(line)
            # Put the last line directly into the active editing line
            current_line = list(lines[-1])

        # Display the pre-loaded content to the user
        sys.stdout.write(initial_content)
        sys.stdout.flush()

    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)
            if char == '\x13':  # Ctrl+S
                if current_line:
                    buffer.append("".join(current_line))
                break
            elif char in ('\r', '\n'):
                buffer.append("".join(current_line))
                current_line = []
                sys.stdout.write('\r\n')
                sys.stdout.flush()
            elif char in ('\x7f', '\x08'):
                if current_line:
                    current_line.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            else:
                current_line.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    final_text = "\n".join(buffer)
    # Sanitization step for leading control characters
    while final_text and ord(final_text[0]) < 32 and final_text[0] not in ('\n', '\r', '\t'):
        final_text = final_text[1:]

    return final_text


def raw_input_line(prompt):
    """Reads a single line of text in raw mode."""
    sys.stdout.write(prompt)
    sys.stdout.flush()

    current_line = []
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    while select.select([sys.stdin], [], [], 0.0)[0]:
        sys.stdin.read(1)

    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)
            if char in ('\r', '\n'):
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                break
            elif char in ('\x7f', '\x08'):
                if current_line:
                    current_line.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ord(char) >= 32:
                current_line.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(current_line).strip()


def handle_hotkey_trigger():
    """Triggers the text editor. Handles both brand new files and pre-loaded active files."""
    global CURRENT_FILE_PATH
    os.system('clear')
    print(f"Snake TUI v{VERSION}")

    initial_text = ""
    if CURRENT_FILE_PATH and os.path.exists(CURRENT_FILE_PATH):
        print(f"--- Editing: {CURRENT_FILE_PATH} (Press Ctrl+S to save and exit) ---")
        try:
            with open(CURRENT_FILE_PATH, "r") as f:
                initial_text = f.read()
        except Exception as e:
            print(f"Error loading file content: {e}")
            time.sleep(1.5)
            return
    else:
        print("--- Enter Code (Press Ctrl+S to save and exit) ---")

    result_text = run_code_editor(initial_content=initial_text)

    time.sleep(0.1)
    os.system('clear')

    # If we didn't open an existing file, ask where to save it
    if not CURRENT_FILE_PATH:
        base_name = raw_input_line("Please enter the file name without extension: ")
        if not base_name:
            print("Save cancelled. No filename provided.")
            return
        ext = raw_input_line("\nChoose the extension (e.g., .py): ")
        CURRENT_FILE_PATH = base_name + ext

    if CURRENT_FILE_PATH:
        clean_text = strip_ansi_codes(result_text)
        try:
            with open(CURRENT_FILE_PATH, "w") as f:
                f.write(clean_text)
            os.system('clear')
            print(f"Wrote code to {CURRENT_FILE_PATH}")
        except Exception as e:
            print(f"Failed to save file: {e}")
            CURRENT_FILE_PATH = None  # Reset tracking if write fails

    print("Press Ctrl+e to edit/resume, or Ctrl+o to open a different file.")


def open_file():
    """Opens an existing file from disk and tracks its path for editing."""
    global CURRENT_FILE_PATH
    os.system('clear')
    filename = raw_input_line("Enter the full path or filename to open: ")

    if filename:
        if os.path.exists(filename) and os.path.isfile(filename):
            CURRENT_FILE_PATH = filename
            print(f"\nSuccessfully loaded {filename} into memory.")
            print("Press Ctrl+e to start editing it.")
        else:
            print(f"\nError: File '{filename}' not found.")
    else:
        print("\nOperation cancelled.")


def changedir():
    os.system('clear')
    target_dir = raw_input_line("Please enter the directory path: ")
    if target_dir:
        try:
            os.chdir(target_dir)
            print(f"\nSuccessfully changed directory to: {os.getcwd()}")
        except Exception as e:
            print(f"\nFailed to change directory: {e}")


def runfile():
    global CURRENT_FILE_PATH
    os.system('clear')

    # Check if a file is already loaded to save the user a step
    if CURRENT_FILE_PATH:
        filename = CURRENT_FILE_PATH
    else:
        filename = raw_input_line("Please enter the file name (with extension if not .py): ")
        if not filename:
            return
        if not filename.endswith(('.py', '.sh', '.txt')) and not '.' in filename:
            filename = filename + ".py"

    venvdir = Path(__file__).resolve().parent / ".venv"
    python_bin = venvdir / "bin" / "python"

    if filename.endswith('.py'):
        if python_bin.exists():
            os.system(f'{python_bin} {filename}')
        else:
            os.system(f'python {filename}')
    else:
        # Fallback processing for shell or other formats executable natively
        os.system(f'bash {filename}')


def adlibs():
    os.system('clear')
    libname = raw_input_line("Enter the library name: ")
    if libname:
        venvdir = Path(__file__).resolve().parent / ".venv"
        pip_bin = venvdir / "bin" / "pip"

        if not pip_bin.exists():
            print(f"Error: Virtual environment not found at {venvdir}")
            return

        try:
            os.system(f'{pip_bin} install {libname}')
        except Exception as e:
            print(f'Something went wrong while installing {libname}: {e}')


helptoggled = False


def help_menu():
    os.system('clear')
    global helptoggled
    helptoggled = not helptoggled

    if helptoggled:
        print(
            "Help:\n"
            "Ctrl+e          - to start editing / resume active file\n"
            "Ctrl+o          - to open an existing file\n"
            "Ctrl+d          - to change current working directory\n"
            "Ctrl+r          - to run the active or specified file\n"
            "Ctrl+Shift+l    - to add libraries to the virtual environment"
        )
    else:
        print("Welcome to SnakeTUI, a python editor TUI tool. Press Ctrl+h for help.")


keyboard.add_hotkey('ctrl+e', handle_hotkey_trigger)
keyboard.add_hotkey('ctrl+o', open_file)
keyboard.add_hotkey('ctrl+d', changedir)
keyboard.add_hotkey('ctrl+r', runfile)
keyboard.add_hotkey('ctrl+shift+l', adlibs)
keyboard.add_hotkey('ctrl+h', help_menu)

os.system('clear')
print("Welcome to SnakeTUI, a python editor TUI tool. Press Ctrl+h for help.")
keyboard.wait()