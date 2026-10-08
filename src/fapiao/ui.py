"""窗口只收集参数，并调用与命令行相同的 run。"""

from __future__ import annotations

import os
from pathlib import Path

from fapiao.license import load_license

WINDOW_TITLE = "发票成表 — 数电票整理成 Excel"
BOUNDARY = (
    "文件只在这台电脑处理。结果用于整理，不代替税务局查验。"
    "本工具不核验数字签名，入账归档仍要保存原始 XML。"
)


def main() -> int:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox

    ctk.set_appearance_mode("system")
    app = ctk.CTk()
    app.title(WINDOW_TITLE)
    app.geometry("680x460")

    folder = ctk.StringVar(value="")
    tax_id = ctk.StringVar(value="")
    direction = ctk.StringVar(value="in")

    ctk.CTkLabel(app, text=BOUNDARY, wraplength=640, justify="left").pack(padx=16, pady=(16, 8), anchor="w")

    path_row = ctk.CTkFrame(app)
    path_row.pack(fill="x", padx=16, pady=8)
    ctk.CTkEntry(path_row, textvariable=folder).pack(side="left", fill="x", expand=True, padx=(0, 8))

    def choose_folder() -> None:
        selected = filedialog.askdirectory(title="选择发票文件夹")
        if selected:
            folder.set(selected)

    ctk.CTkButton(path_row, text="选择文件夹", command=choose_folder, width=120).pack(side="right")

    ctk.CTkLabel(app, text="本公司税号").pack(anchor="w", padx=16)
    tax_entry = ctk.CTkEntry(app, textvariable=tax_id)
    tax_entry.pack(fill="x", padx=16, pady=(0, 8))

    direction_row = ctk.CTkFrame(app)
    direction_row.pack(fill="x", padx=16, pady=8)
    ctk.CTkRadioButton(direction_row, text="进项", variable=direction, value="in").pack(side="left", padx=8)
    ctk.CTkRadioButton(direction_row, text="销项", variable=direction, value="out").pack(side="left", padx=8)

    start = ctk.CTkButton(app, text="开始", state="disabled")
    start.pack(anchor="w", padx=16, pady=12)

    def refresh_start(*_args: object) -> None:
        start.configure(state="normal" if tax_id.get().strip() and folder.get().strip() else "disabled")

    tax_id.trace_add("write", refresh_start)
    folder.trace_add("write", refresh_start)

    def start_run() -> None:
        from fapiao.pipeline import run

        try:
            result = run(Path(folder.get()), tax_id.get().strip(), direction.get())
        except (OSError, ValueError, FileNotFoundError) as exc:
            messagebox.showerror(WINDOW_TITLE, str(exc))
            return
        messagebox.showinfo(
            WINDOW_TITLE,
            f"合格 {result.qualified_count} 张，异常 {result.exception_count} 张",
        )
        os.startfile(result.output_path)  # type: ignore[attr-defined]

    start.configure(command=start_run)

    def show_about() -> None:
        status = load_license()
        messagebox.showinfo(WINDOW_TITLE, f"{BOUNDARY}\n\n授权状态：{status.label}")

    ctk.CTkButton(app, text="关于", command=show_about, width=80).pack(anchor="w", padx=16)

    app.mainloop()
    return 0
