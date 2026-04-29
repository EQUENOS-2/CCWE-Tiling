import tkinter as tk
from tkinter import ttk

from tiling import TilerDurden


def apply_values():
    width = width_entry.get()
    length = length_entry.get()

    try:
        width_val = int(width)
        length_val = int(length)
        if width_val <= 0 or length_val <= 0:
            raise ValueError("Values must be positive")

        tiler = TilerDurden(width_val, length_val)

        width_entry.config(state="disabled")
        length_entry.config(state="disabled")
        result_label.config(
            text=f"Generating {width_val}x{length_val} schematic...",
            foreground="green",
            state="disabled",
        )
        schem = tiler.stack_world_eater()
        schem.save(f"{schem.name}.litematic")
        # print(f"Saved to '{path}'")
        root.destroy()

    except ValueError:
        result_label.config(
            text="Please enter valid positive numbers", foreground="red"
        )
    except AssertionError as err:
        result_label.config(text=str(err), foreground="red")


root = tk.Tk()
root.title("Contraption Adjuster")
root.geometry("320x220")

instruction_label = ttk.Label(
    root, text="Input the size of the contraption (in blocks)"
)
instruction_label.pack(pady=10)

input_frame = ttk.Frame(root)
input_frame.pack(pady=5)

ttk.Label(input_frame, text="Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
width_entry = ttk.Entry(input_frame)
width_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Length:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
length_entry = ttk.Entry(input_frame)
length_entry.grid(row=1, column=1, padx=5, pady=5)

apply_button = ttk.Button(root, text="Apply", command=apply_values)
apply_button.pack(pady=10)

result_label = ttk.Label(root, text="")
result_label.pack(pady=5)


if __name__ == "__main__":
    root.mainloop()
