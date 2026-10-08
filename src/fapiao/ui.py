"""窗口只收集参数，并调用与命令行相同的 run。"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from fapiao.license import FREE_INVOICE_LIMIT, load_license

WINDOW_TITLE = "发票成表 — 数电票整理成 Excel"
BOUNDARY = (
    "文件只在这台电脑处理。结果用于整理，不代替税务局查验。"
    "本工具不核验数字签名，入账归档仍要保存原始 XML。"
)

# 浅色工作区 + 深色侧栏，接近当前常见的桌面工具布局。
BG = "#F4F5F7"
SURFACE = "#FFFFFF"
LINE = "#E6E8EE"
TEXT = "#18181B"
MUTED = "#71717A"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_SOFT = "#E8F0FE"
SIDEBAR = "#14161C"
SIDEBAR_RAISED = "#22252E"
SIDEBAR_TEXT = "#FAFAFA"
SIDEBAR_MUTED = "#A1A1AA"
SUCCESS_BG = "#F0FDF4"
SUCCESS_LINE = "#BBF7D0"
SUCCESS_TEXT = "#166534"
DANGER_BG = "#FEF2F2"
DANGER_LINE = "#FECACA"
DANGER_TEXT = "#991B1B"
FONT_FAMILY = "Microsoft YaHei UI"


def main() -> int:
    import customtkinter as ctk

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    def font(size: int, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    app = ctk.CTk()
    app.title(WINDOW_TITLE)
    app.configure(fg_color=BG)
    app.minsize(880, 620)

    width, height = 1040, 680
    screen_w = app.winfo_screenwidth()
    screen_h = app.winfo_screenheight()
    width = min(width, max(880, screen_w - 80))
    height = min(height, max(620, screen_h - 90))
    app.geometry(f"{width}x{height}+{(screen_w - width) // 2}+{(screen_h - height) // 2}")

    folder = ctk.StringVar(value="")
    tax_id = ctk.StringVar(value="")
    direction = ctk.StringVar(value="in")

    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(0, weight=1)

    sidebar = ctk.CTkFrame(app, width=248, corner_radius=0, fg_color=SIDEBAR)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.grid_columnconfigure(0, weight=1)
    sidebar.grid_rowconfigure(2, weight=1)

    brand = ctk.CTkFrame(sidebar, fg_color="transparent")
    brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 8))
    mark = ctk.CTkFrame(brand, width=40, height=40, corner_radius=12, fg_color=ACCENT)
    mark.grid(row=0, column=0, rowspan=2, padx=(0, 12))
    mark.grid_propagate(False)
    ctk.CTkLabel(mark, text="票", text_color="#FFFFFF", font=font(18, "bold")).place(
        relx=0.5, rely=0.5, anchor="center"
    )
    ctk.CTkLabel(brand, text="发票成表", text_color=SIDEBAR_TEXT, font=font(16, "bold")).grid(
        row=0, column=1, sticky="w"
    )
    ctk.CTkLabel(brand, text="数电票整理成 Excel", text_color=SIDEBAR_MUTED, font=font(12)).grid(
        row=1, column=1, sticky="w", pady=(2, 0)
    )

    nav = ctk.CTkFrame(sidebar, fg_color="transparent")
    nav.grid(row=1, column=0, sticky="ew", padx=14, pady=(18, 8))
    ctk.CTkLabel(nav, text="工作台", text_color="#6B7280", font=font(12)).pack(anchor="w", padx=10, pady=(0, 8))

    ctk.CTkButton(
        nav,
        text="整理",
        anchor="w",
        height=40,
        corner_radius=10,
        fg_color=SIDEBAR_RAISED,
        hover_color=SIDEBAR_RAISED,
        text_color=SIDEBAR_TEXT,
        font=font(14),
    ).pack(fill="x", pady=(0, 4))

    license_card = ctk.CTkFrame(sidebar, fg_color=SIDEBAR_RAISED, corner_radius=14)
    license_card.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 20))
    status = load_license()
    dot_color = "#34D399" if status.active else "#FBBF24"
    license_head = ctk.CTkFrame(license_card, fg_color="transparent")
    license_head.pack(fill="x", padx=14, pady=(14, 4))
    ctk.CTkFrame(license_head, width=8, height=8, corner_radius=4, fg_color=dot_color).pack(
        side="left", padx=(0, 8), pady=4
    )
    license_title = "已授权" if status.active else "免费版"
    ctk.CTkLabel(license_head, text=license_title, text_color=SIDEBAR_TEXT, font=font(13, "bold")).pack(side="left")
    if status.active:
        license_detail = status.label if not status.licensee else f"{status.licensee}\n{status.label}"
    else:
        license_detail = f"每次最多 {FREE_INVOICE_LIMIT} 张合格票进入汇总"
    ctk.CTkLabel(
        license_card,
        text=license_detail,
        text_color=SIDEBAR_MUTED,
        font=font(12),
        justify="left",
        wraplength=190,
    ).pack(anchor="w", padx=14, pady=(0, 14))

    main = ctk.CTkFrame(app, fg_color=BG, corner_radius=0)
    main.grid(row=0, column=1, sticky="nsew")
    main.grid_columnconfigure(0, weight=1)
    main.grid_rowconfigure(1, weight=1)

    header = ctk.CTkFrame(main, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=28, pady=(26, 0))
    ctk.CTkLabel(header, text="整理数电发票", text_color=TEXT, font=font(24, "bold")).pack(anchor="w")
    ctk.CTkLabel(
        header,
        text="把已经下载到本机的发票，整理成汇总、商品明细和异常三张表。",
        text_color=MUTED,
        font=font(13),
    ).pack(anchor="w", pady=(6, 12))
    chips = ctk.CTkFrame(header, fg_color="transparent")
    chips.pack(anchor="w")
    for name in ("发票汇总", "商品明细", "异常"):
        ctk.CTkLabel(
            chips,
            text=name,
            text_color=ACCENT,
            fg_color=ACCENT_SOFT,
            corner_radius=999,
            font=font(12),
            padx=10,
            pady=2,
        ).pack(side="left", padx=(0, 8))

    content = ctk.CTkFrame(main, fg_color="transparent")
    content.grid(row=1, column=0, sticky="nsew", padx=28, pady=(18, 8))
    content.grid_columnconfigure(0, weight=3)
    content.grid_columnconfigure(1, weight=2)
    content.grid_rowconfigure(0, weight=1)

    source = ctk.CTkFrame(content, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=LINE)
    source.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    source.grid_columnconfigure(0, weight=1)
    source.grid_rowconfigure(1, weight=1)
    ctk.CTkLabel(source, text="来源", text_color=MUTED, font=font(12)).grid(
        row=0, column=0, sticky="w", padx=22, pady=(18, 0)
    )

    source_body = ctk.CTkFrame(source, fg_color="transparent")
    source_body.grid(row=1, column=0, sticky="nsew", padx=22, pady=(8, 18))
    source_body.grid_columnconfigure(0, weight=1)
    source_body.grid_rowconfigure(0, weight=1)
    source_body.grid_rowconfigure(2, weight=1)
    source_center = ctk.CTkFrame(source_body, fg_color="transparent")
    source_center.grid(row=1, column=0, sticky="ew")

    badge = ctk.CTkFrame(source_center, width=56, height=56, corner_radius=16, fg_color=ACCENT_SOFT)
    badge.pack()
    badge.pack_propagate(False)
    badge_label = ctk.CTkLabel(badge, text="＋", text_color=ACCENT, font=font(26))
    badge_label.place(relx=0.5, rely=0.5, anchor="center")

    source_title = ctk.CTkLabel(source_center, text="选择文件夹或压缩包", text_color=TEXT, font=font(18, "bold"))
    source_title.pack(pady=(14, 4))
    source_hint = ctk.CTkLabel(
        source_center,
        text="支持 XML、OFD、PDF，以及已经下载好的压缩包。",
        text_color=MUTED,
        font=font(13),
        wraplength=360,
    )
    source_hint.pack()

    path_row = ctk.CTkFrame(source_center, fg_color="transparent")
    path_row.pack(fill="x", pady=(18, 0))
    path_entry = ctk.CTkEntry(
        path_row,
        textvariable=folder,
        height=42,
        corner_radius=10,
        border_width=1,
        border_color="#D4D4D8",
        fg_color="#FFFFFF",
        text_color=TEXT,
        placeholder_text="粘贴路径，或点击右侧选择",
        placeholder_text_color="#71717A",
        font=font(13),
    )
    path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def choose_folder() -> None:
        from tkinter import filedialog

        selected = filedialog.askdirectory(title="选择发票文件夹")
        if selected:
            folder.set(selected)

    browse = ctk.CTkButton(
        path_row,
        text="选择文件夹",
        command=choose_folder,
        width=112,
        height=42,
        corner_radius=10,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        font=font(13, "bold"),
    )
    browse.pack(side="right")

    settings = ctk.CTkFrame(content, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=LINE)
    settings.grid(row=0, column=1, sticky="nsew")
    settings.grid_columnconfigure(0, weight=1)

    form = ctk.CTkFrame(settings, fg_color="transparent")
    form.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
    form.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(form, text="本公司税号", text_color=TEXT, font=font(13, "bold")).grid(row=0, column=0, sticky="w")
    tax_entry = ctk.CTkEntry(
        form,
        textvariable=tax_id,
        height=42,
        corner_radius=10,
        border_width=1,
        border_color="#D4D4D8",
        fg_color="#FFFFFF",
        text_color=TEXT,
        placeholder_text="统一社会信用代码",
        placeholder_text_color="#71717A",
        font=font(13),
    )
    tax_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    ctk.CTkLabel(form, text="用来判断发票是不是本公司的。", text_color=MUTED, font=font(12)).grid(
        row=2, column=0, sticky="w", pady=(6, 16)
    )
    ctk.CTkLabel(form, text="整理方向", text_color=TEXT, font=font(13, "bold")).grid(row=3, column=0, sticky="w")

    direction_cards: dict[str, ctk.CTkFrame] = {}
    direction_fills: dict[str, list[ctk.CTkFrame]] = {}
    direction_titles: dict[str, ctk.CTkLabel] = {}
    direction_marks: dict[str, ctk.CTkLabel] = {}

    def paint_direction() -> None:
        current = direction.get()
        for key, card in direction_cards.items():
            selected = key == current
            fill = ACCENT_SOFT if selected else SURFACE
            card.configure(fg_color=fill, border_color=ACCENT if selected else LINE)
            for widget in direction_fills[key]:
                widget.configure(fg_color=fill)
            direction_titles[key].configure(text_color=ACCENT if selected else TEXT)
            direction_marks[key].configure(text="●" if selected else "○", text_color=ACCENT if selected else "#C4C4CC")

    def choose_direction(value: str) -> None:
        direction.set(value)
        paint_direction()

    choices = ctk.CTkFrame(form, fg_color="transparent")
    choices.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    choices.grid_columnconfigure(0, weight=1)
    for index, (value, title, subtitle) in enumerate(
        (
            ("in", "进项", "按购买方税号，整理收到的发票"),
            ("out", "销项", "按销售方税号，整理开出的发票"),
        )
    ):
        card = ctk.CTkFrame(choices, fg_color=SURFACE, corner_radius=12, border_width=2, border_color=LINE)
        card.grid(row=index, column=0, sticky="ew", pady=(0, 8))
        inner = ctk.CTkFrame(card, fg_color=SURFACE)
        inner.pack(fill="x", padx=12, pady=10)
        mark_label = ctk.CTkLabel(inner, text="○", width=16, height=18, text_color="#C4C4CC", font=font(13))
        mark_label.pack(side="left", anchor="n", padx=(0, 8), pady=(3, 0))
        texts = ctk.CTkFrame(inner, fg_color=SURFACE)
        texts.pack(side="left", fill="x", expand=True)
        title_label = ctk.CTkLabel(texts, text=title, text_color=TEXT, font=font(14, "bold"))
        title_label.pack(anchor="w")
        sub_label = ctk.CTkLabel(texts, text=subtitle, text_color=MUTED, font=font(12), anchor="w", justify="left")
        sub_label.pack(anchor="w", pady=(2, 0))
        direction_cards[value] = card
        direction_fills[value] = [inner, texts]
        direction_titles[value] = title_label
        direction_marks[value] = mark_label

        def bind_choose(widget: ctk.CTkBaseClass, picked: str = value) -> None:
            widget.bind("<Button-1>", lambda _event: choose_direction(picked))
            widget.configure(cursor="hand2")

        for widget in (card, inner, texts, mark_label, title_label, sub_label):
            bind_choose(widget)

    paint_direction()

    action = ctk.CTkFrame(settings, fg_color="transparent")
    action.grid(row=1, column=0, sticky="sew", padx=20, pady=(8, 18))
    ctk.CTkFrame(action, height=1, fg_color=LINE).pack(fill="x", pady=(0, 14))
    ready_hint = ctk.CTkLabel(action, text="", text_color=MUTED, font=font(12))
    ready_hint.pack(anchor="w", pady=(0, 8))
    start = ctk.CTkButton(
        action,
        text="开始整理",
        height=46,
        corner_radius=12,
        fg_color="#E4E6EB",
        hover_color=ACCENT_HOVER,
        text_color="#FFFFFF",
        text_color_disabled="#A1A1AA",
        font=font(15, "bold"),
        state="disabled",
    )
    start.pack(fill="x")

    banner = ctk.CTkFrame(main, fg_color=SUCCESS_BG, corner_radius=14, border_width=1, border_color=SUCCESS_LINE)
    banner.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 8))
    banner.grid_remove()
    banner_title = ctk.CTkLabel(banner, text="", font=font(14, "bold"), anchor="w", justify="left")
    banner_title.pack(anchor="w", padx=16, pady=(12, 2))
    banner_body = ctk.CTkLabel(banner, text="", font=font(12), anchor="w", justify="left")
    banner_body.pack(anchor="w", padx=16, pady=(0, 12))

    note = ctk.CTkFrame(main, fg_color="transparent")
    note.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 18))
    boundary_label = ctk.CTkLabel(
        note,
        text=BOUNDARY,
        text_color=MUTED,
        font=font(12),
        justify="left",
        wraplength=680,
        anchor="w",
    )
    boundary_label.pack(anchor="w")

    def fit_copy(event: object) -> None:
        widget = getattr(event, "widget", None)
        if widget is main:
            boundary_label.configure(wraplength=max(280, widget.winfo_width() - 56))
        elif widget is source:
            source_hint.configure(wraplength=max(220, widget.winfo_width() - 80))

    main.bind("<Configure>", fit_copy)
    source.bind("<Configure>", fit_copy)

    def show_banner(kind: str, title: str, body: str) -> None:
        if kind == "success":
            banner.configure(fg_color=SUCCESS_BG, border_color=SUCCESS_LINE)
            title_color, body_color = SUCCESS_TEXT, SUCCESS_TEXT
        else:
            banner.configure(fg_color=DANGER_BG, border_color=DANGER_LINE)
            title_color, body_color = DANGER_TEXT, DANGER_TEXT
        banner_title.configure(text=title, text_color=title_color)
        banner_body.configure(text=body, text_color=body_color)
        banner.grid()

    def refresh_source(*_args: object) -> None:
        path = folder.get().strip()
        if not path:
            badge.configure(fg_color=ACCENT_SOFT)
            badge_label.configure(text="＋", text_color=ACCENT)
            source_title.configure(text="选择文件夹或压缩包")
            source_hint.configure(text="支持 XML、OFD、PDF，以及已经下载好的压缩包。")
            return
        name = Path(path).name or path
        exists = Path(path).exists()
        badge.configure(fg_color="#DCFCE7" if exists else DANGER_BG)
        badge_label.configure(text="✓" if exists else "!", text_color=SUCCESS_TEXT if exists else DANGER_TEXT)
        source_title.configure(text=name)
        source_hint.configure(text=path if exists else "这个路径目前不存在，请重新选择。")

    def refresh_start(*_args: object) -> None:
        label = "进项" if direction.get() == "in" else "销项"
        filename = f"{label}_{date.today():%Y%m%d}.xlsx"
        ready = bool(tax_id.get().strip() and folder.get().strip())
        if ready:
            ready_hint.configure(text=f"将生成 {filename}")
            start.configure(state="normal", fg_color=ACCENT, text_color="#FFFFFF")
        else:
            ready_hint.configure(text=f"选择文件夹并填写税号后，生成 {filename}")
            start.configure(state="disabled", fg_color="#E4E6EB")

    def start_run() -> None:
        if start.cget("state") != "normal":
            return
        from fapiao.pipeline import run

        start.configure(state="disabled", text="正在整理…")
        app.update_idletasks()
        try:
            result = run(Path(folder.get()), tax_id.get().strip(), direction.get())
        except (OSError, ValueError, FileNotFoundError) as exc:
            show_banner("error", "没有完成", str(exc))
            return
        finally:
            start.configure(text="开始整理")
            refresh_start()

        opened = False
        try:
            os.startfile(result.output_path)  # type: ignore[attr-defined]
            opened = True
        except OSError:
            opened = False
        detail = f"合格 {result.qualified_count} 张，异常 {result.exception_count} 张"
        detail += "\n表格已打开。" if opened else "\n表格已生成，但没能自动打开。"
        detail += f"\n{result.output_path}"
        show_banner("success", "整理完成", detail)

    start.configure(command=start_run)
    tax_entry.bind("<Return>", lambda _event: start_run())
    path_entry.bind("<Return>", lambda _event: start_run())

    def bind_pick(widget: ctk.CTkBaseClass) -> None:
        widget.bind("<Button-1>", lambda _event: choose_folder())
        widget.configure(cursor="hand2")

    for widget in (badge, badge_label, source_title, source_hint):
        bind_pick(widget)

    folder.trace_add("write", refresh_source)
    folder.trace_add("write", refresh_start)
    tax_id.trace_add("write", refresh_start)
    direction.trace_add("write", refresh_start)
    refresh_source()
    refresh_start()

    def show_about() -> None:
        current = load_license()
        dialog = ctk.CTkToplevel(app)
        dialog.title("关于")
        dialog.resizable(False, False)
        dialog.transient(app)
        dialog.configure(fg_color=BG)
        dialog.withdraw()

        shell = ctk.CTkFrame(dialog, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=LINE)
        shell.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(shell, text="发票成表", text_color=TEXT, font=font(18, "bold")).pack(anchor="w", padx=20, pady=(18, 6))
        ctk.CTkLabel(
            shell,
            text=BOUNDARY,
            text_color=MUTED,
            font=font(13),
            justify="left",
            wraplength=380,
        ).pack(anchor="w", padx=20)
        ctk.CTkFrame(shell, height=1, fg_color=LINE).pack(fill="x", padx=20, pady=14)
        license_text = current.label if current.active else f"免费版 · 每次最多 {FREE_INVOICE_LIMIT} 张合格票"
        if current.active and current.licensee:
            license_text = f"{current.licensee} · {current.label}"
        ctk.CTkLabel(shell, text=license_text, text_color=TEXT, font=font(13)).pack(anchor="w", padx=20)
        ctk.CTkButton(
            shell,
            text="关闭",
            width=88,
            height=36,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=font(13),
            command=dialog.destroy,
        ).pack(anchor="e", padx=20, pady=(16, 18))

        dialog.update_idletasks()
        dialog_w, dialog_h = 460, dialog.winfo_reqheight() + 8
        origin_x = app.winfo_rootx() + max(0, (app.winfo_width() - dialog_w) // 2)
        origin_y = app.winfo_rooty() + max(0, (app.winfo_height() - dialog_h) // 2)
        dialog.geometry(f"{dialog_w}x{dialog_h}+{origin_x}+{origin_y}")
        dialog.deiconify()
        dialog.grab_set()
        dialog.focus()

    ctk.CTkButton(
        nav,
        text="关于",
        anchor="w",
        height=40,
        corner_radius=10,
        fg_color="transparent",
        hover_color=SIDEBAR_RAISED,
        text_color=SIDEBAR_MUTED,
        font=font(14),
        command=show_about,
    ).pack(fill="x")

    app.mainloop()
    return 0
