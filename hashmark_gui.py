import hashlib
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CHUNK_SIZE = 1024 * 1024  # 1 MiB
ALGORITHMS = ("sha256", "sha512", "sha3_256", "blake2b")


def hash_file(path: Path, algorithm: str) -> str:
    """Return the hexadecimal checksum for a file."""
    digest = hashlib.new(algorithm)

    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


class ChecksumApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Hashmark")
        self.geometry("620x330")
        self.minsize(500, 300)

        self.file_path = tk.StringVar()
        self.algorithm = tk.StringVar(value="sha256")
        self.expected_checksum = tk.StringVar()
        self.result = tk.StringVar(value="Choose a file to begin.")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="File:").grid(row=0, column=0, sticky="w", pady=6)

        ttk.Entry(frame, textvariable=self.file_path).grid(
            row=0, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(frame, text="Browse…", command=self._browse).grid(
            row=0, column=2, pady=6
        )

        ttk.Label(frame, text="Algorithm:").grid(
            row=1, column=0, sticky="w", pady=6
        )
        ttk.Combobox(
            frame,
            textvariable=self.algorithm,
            values=ALGORITHMS,
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(frame, text="Expected checksum (optional):").grid(
            row=2, column=0, sticky="w", pady=6
        )
        ttk.Entry(frame, textvariable=self.expected_checksum).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=6
        )

        self.check_button = ttk.Button(
            frame, text="Calculate / Verify", command=self._start_hash
        )
        self.check_button.grid(row=3, column=1, sticky="w", padx=8, pady=12)

        ttk.Label(frame, text="Result:").grid(row=4, column=0, sticky="nw", pady=6)
        ttk.Label(
            frame,
            textvariable=self.result,
            wraplength=460,
            justify="left",
        ).grid(row=4, column=1, columnspan=2, sticky="w", padx=8, pady=6)

    def _browse(self):
        selected = filedialog.askopenfilename(title="Choose a file")
        if selected:
            self.file_path.set(selected)
            self.result.set("Ready to calculate checksum.")

    def _start_hash(self):
        path_text = self.file_path.get().strip()
        if not path_text:
            messagebox.showerror("No file selected", "Choose a file first.")
            return

        path = Path(path_text)
        if not path.is_file():
            messagebox.showerror("File not found", f"Not a regular file:\n{path}")
            return

        self.check_button.config(state="disabled")
        self.result.set("Calculating…")

        # Hash in a worker thread so the window stays responsive.
        thread = threading.Thread(
            target=self._hash_worker,
            args=(path, self.algorithm.get(), self.expected_checksum.get().strip()),
            daemon=True,
        )
        thread.start()

    def _hash_worker(self, path: Path, algorithm: str, expected: str):
        try:
            actual = hash_file(path, algorithm)
            error = None
        except (OSError, ValueError) as exc:
            actual = None
            error = str(exc)

        # Tkinter UI updates must happen on the main thread.
        self.after(0, self._show_result, path, algorithm, expected, actual, error)

    def _show_result(
        self,
        path: Path,
        algorithm: str,
        expected: str,
        actual: str | None,
        error: str | None,
    ):
        self.check_button.config(state="normal")

        if error:
            self.result.set(f"Could not read or hash the file: {error}")
            return

        if not expected:
            self.result.set(f"{algorithm}:\n{actual}")
            return

        try:
            bytes.fromhex(expected)
        except ValueError:
            self.result.set(
                f"Calculated {algorithm}:\n{actual}\n\n"
                "Expected checksum is not valid hexadecimal."
            )
            return

        if len(expected) != len(actual):
            self.result.set(
                f"Calculated {algorithm}:\n{actual}\n\n"
                f"Expected checksum has the wrong length for {algorithm}."
            )
            return

        if actual.lower() == expected.lower():
            self.result.set(f"✓ Match\n{algorithm}: {actual}")
        else:
            self.result.set(
                f"✗ Mismatch\nExpected: {expected.lower()}\nActual:   {actual}"
            )


if __name__ == "__main__":
    app = ChecksumApp()
    app.mainloop()
