import json
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from collections import defaultdict
import numpy as np
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mticker

# ---------- 主题配置 ----------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#EEF2F7",
    "sidebar": "#1A1A2E",
    "sidebar_accent": "#16213E",
    "sidebar_input": "#2A2A4A",
    "card_bg": "#FFFFFF",
    "primary": "#4361EE",
    "primary_hover": "#3451DE",
    "primary_light": "#7B8FF7",
    "income": "#06D6A0",
    "income_hover": "#05B88A",
    "expense": "#EF476F",
    "expense_hover": "#D63D63",
    "text": "#1A1A2E",
    "text_light": "#8D99AE",
    "border": "#DEE2E6",
    "row_alt": "#F8F9FA",
    "tab_inactive": "#2A2A4A",
}

CATEGORIES = {
    "支出": ["餐饮", "文具", "零食", "交通", "娱乐", "购物", "其他"],
    "收入": ["红包", "奖励", "零花钱", "兼职", "利息", "其他"],
}

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money_data.json")


# ---------- 数据管理类 ----------
class DataManager:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"records": []}

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add_record(self, r_type, amount, category, note=""):
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": r_type,
            "amount": float(amount),
            "category": category,
            "note": note,
        }
        self.data["records"].append(record)
        self.save()

    def delete_record(self, index):
        if 0 <= index < len(self.data["records"]):
            self.data["records"].pop(index)
            self.save()

    def get_stats(self, filter_text=""):
        indexed = list(enumerate(self.data["records"]))
        if filter_text:
            ft = filter_text.lower()
            indexed = [
                (i, r) for i, r in indexed
                if ft in r["category"].lower() or ft in r.get("note", "").lower()
            ]

        income = sum(r["amount"] for _, r in indexed if r["type"] == "收入")
        expense = sum(r["amount"] for _, r in indexed if r["type"] == "支出")

        cat_map = {}
        for _, r in indexed:
            if r["type"] == "支出":
                cat_map[r["category"]] = cat_map.get(r["category"], 0) + r["amount"]

        return income, expense, cat_map, indexed


# ---------- 主界面 ----------
class PocketTrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DataManager()
        self.title("PocketTrack Pro")
        self.geometry("1150x720")
        self.minsize(820, 600)

        # 整体布局: 左侧边栏 + 右主内容
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self.refresh_ui()

    # ================================================================
    #  侧边栏
    # ================================================================
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar"])
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_rowconfigure(10, weight=1)  # 弹性间距

        # ---- Logo ----
        logo_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["sidebar_accent"], corner_radius=0)
        logo_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(logo_frame, text="PocketTrack", font=("Helvetica", 20, "bold"),
                     text_color=COLORS["primary_light"]).pack(pady=(16, 2))
        ctk.CTkLabel(logo_frame, text="智慧零花钱管理", font=("Helvetica", 10),
                     text_color=COLORS["text_light"]).pack(pady=(0, 14))

        # ---- 支出/收入 Tab 切换 ----
        self.record_type = "支出"
        tab_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["tab_inactive"], corner_radius=8, height=36)
        tab_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(12, 0))
        tab_frame.grid_columnconfigure((0, 1), weight=1)

        self._type_tabs = {}
        for col, (rtype, label, color) in enumerate([
            ("支出", "支出", COLORS["expense"]),
            ("收入", "收入", COLORS["income"]),
        ]):
            btn = ctk.CTkButton(
                tab_frame, text=label, height=34, corner_radius=6,
                font=("Helvetica", 12, "bold"),
                fg_color=color if rtype == "支出" else "transparent",
                text_color="white" if rtype == "支出" else COLORS["text_light"],
                hover_color=color,
                command=lambda t=rtype, c=color: self._switch_type(t, c),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=3, pady=3)
            self._type_tabs[rtype] = (btn, color)

        # ---- 表单 ----
        form = ctk.CTkFrame(sidebar, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=14, pady=(12, 0))

        ctk.CTkLabel(form, text="金额", text_color=COLORS["text_light"], font=("Helvetica", 11)).pack(anchor="w")
        self.amt_ent = ctk.CTkEntry(form, placeholder_text="输入金额...", height=38,
                                    font=("Helvetica", 14), fg_color=COLORS["sidebar_input"],
                                    border_width=0, text_color="white")
        self.amt_ent.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(form, text="分类", text_color=COLORS["text_light"], font=("Helvetica", 11)).pack(anchor="w")
        self.cat_combo = ctk.CTkComboBox(
            form, values=CATEGORIES["支出"],
            height=34, font=("Helvetica", 12), dropdown_font=("Helvetica", 12),
            state="readonly",
        )
        self.cat_combo.set(CATEGORIES["支出"][0])
        self.cat_combo.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(form, text="备注 (选填)", text_color=COLORS["text_light"], font=("Helvetica", 11)).pack(anchor="w")
        self.note_ent = ctk.CTkEntry(form, placeholder_text="可选备注...", height=34,
                                     font=("Helvetica", 12), fg_color=COLORS["sidebar_input"],
                                     border_width=0, text_color="white")
        self.note_ent.pack(fill="x", pady=(4, 20))

        # ---- 提交按钮 (跟随当前 Tab) ----
        btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=14)

        self.submit_btn = ctk.CTkButton(
            btn_frame, text="确认支出", height=42, corner_radius=8,
            font=("Helvetica", 13, "bold"),
            fg_color=COLORS["expense"], hover_color=COLORS["expense_hover"],
            command=self._on_submit_click,
        )
        self.submit_btn.pack(fill="x")

        # ---- 底部工具按钮 ----
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.grid(row=11, column=0, sticky="sew", padx=14, pady=(0, 14))

        ctk.CTkButton(bottom, text="导出 CSV 账单", height=34, corner_radius=8,
                      font=("Helvetica", 11), fg_color="#34495E", hover_color="#4A6278",
                      command=self.export_data).pack(fill="x")

    # ================================================================
    #  支出/收入 Tab 切换
    # ================================================================
    def _switch_type(self, rtype, color):
        self.record_type = rtype
        # 更新 Tab 高亮
        for t, (btn, c) in self._type_tabs.items():
            if t == rtype:
                btn.configure(fg_color=c, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_light"])
        # 更新分类下拉
        cats = CATEGORIES[rtype]
        self.cat_combo.configure(values=cats)
        self.cat_combo.set(cats[0])
        # 更新提交按钮样式和文字
        if rtype == "支出":
            self.submit_btn.configure(text="确认支出", fg_color=COLORS["expense"], hover_color=COLORS["expense_hover"])
        else:
            self.submit_btn.configure(text="确认收入", fg_color=COLORS["income"], hover_color=COLORS["income_hover"])

    def _on_submit_click(self):
        self.on_submit(self.record_type)

    # ================================================================
    #  右侧主内容
    # ================================================================
    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nswe")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=3)  # 图表区域
        self.main_frame.grid_rowconfigure(2, weight=2)  # 列表区域

        # ---- 顶部卡片 ----
        top_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 10))
        top_row.grid_columnconfigure(0, weight=1)

        card_row = ctk.CTkFrame(top_row, fg_color="transparent")
        card_row.grid(row=0, column=0, sticky="ew")
        card_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_balance = self._create_card(card_row, "当前余额", "￥0.00", COLORS["primary"], 0)
        self.lbl_income = self._create_card(card_row, "累计收入", "￥0.00", COLORS["income"], 1)
        self.lbl_expense = self._create_card(card_row, "累计支出", "￥0.00", COLORS["expense"], 2)

        # ---- 中部：图表 ----
        chart_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        chart_container.grid(row=1, column=0, sticky="nswe", padx=28, pady=(0, 10))
        chart_container.grid_columnconfigure(0, weight=1)
        chart_container.grid_rowconfigure(0, weight=1)

        self._build_chart_panel(chart_container)

        # ---- 底部：流水列表 ----
        list_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        list_container.grid(row=2, column=0, sticky="nswe", padx=28, pady=(0, 22))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)

        self._build_list_panel(list_container)

    # ---- 流水列表面板 ----
    def _build_list_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="white", corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=0, sticky="nswe")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # 标题栏 + 搜索 + 删除
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 5))

        ctk.CTkLabel(header, text="收支流水", font=("Helvetica", 15, "bold"),
                     text_color=COLORS["text"]).pack(side="left")

        # 搜索框
        self.search_ent = ctk.CTkEntry(header, placeholder_text="搜索分类/备注...", width=220,
                                       fg_color=COLORS["row_alt"], border_width=0,
                                       font=("Helvetica", 12), height=30)
        self.search_ent.pack(side="left", padx=15)
        self.search_ent.bind("<KeyRelease>", lambda e: self.refresh_ui())

        # 删除按钮
        ctk.CTkButton(
            header, text="删除选中", width=80, height=30, corner_radius=6,
            font=("Helvetica", 12), fg_color=COLORS["row_alt"],
            text_color=COLORS["expense"], hover_color=COLORS["border"],
            command=self._delete_selected,
        ).pack(side="right")

        # Treeview
        tree_frame = ctk.CTkFrame(panel, fg_color="white", corner_radius=0)
        tree_frame.grid(row=1, column=0, sticky="nswe", padx=1, pady=(0, 1))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Pocket.Treeview", background="white", fieldbackground="white",
                        foreground=COLORS["text"], rowheight=32, font=("Helvetica", 11), borderwidth=0)
        style.configure("Pocket.Treeview.Heading", background=COLORS["row_alt"], foreground=COLORS["text_light"],
                        font=("Helvetica", 11, "bold"), borderwidth=0, relief="flat")
        style.map("Pocket.Treeview", background=[("selected", COLORS["primary_light"])],
                  foreground=[("selected", "white")])
        style.layout("Pocket.Treeview", [("Pocket.Treeview.treearea", {"sticky": "nswe"})])

        self.tree = ttk.Treeview(tree_frame, columns=("time", "cat", "note", "amt"),
                                 show="headings", height=8, style="Pocket.Treeview")
        self.tree.heading("time", text="时间")
        self.tree.heading("cat", text="分类")
        self.tree.heading("note", text="备注")
        self.tree.heading("amt", text="金额")
        
        self.tree.column("time", width=140, anchor="center")
        self.tree.column("cat", width=100, anchor="center")
        self.tree.column("note", width=200, anchor="w")
        self.tree.column("amt", width=100, anchor="e")
        
        self.tree.grid(row=0, column=0, sticky="nswe", padx=(5, 0), pady=5)

        # 自定义滚动条
        sb = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=self.tree.yview,
                              fg_color="transparent", button_color=COLORS["text_light"], 
                              button_hover_color=COLORS["primary"])
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns", pady=5, padx=(0, 5))

        self.tree.tag_configure("income_row", foreground=COLORS["income"])
        self.tree.tag_configure("expense_row", foreground=COLORS["expense"])
        self.tree.tag_configure("alt", background=COLORS["row_alt"])

        # 右键菜单
        self.ctx_menu = tk.Menu(self, tearoff=0, font=("Helvetica", 10))
        self.ctx_menu.add_command(label="删除该记录", command=self._delete_selected)
        self.tree.bind("<Button-2>", self._show_ctx_menu)
        self.tree.bind("<Button-3>", self._show_ctx_menu)

    # ---- 图表面板 ----
    def _build_chart_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="white", corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=0, sticky="nswe")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Tab 切换
        tab_bar = ctk.CTkFrame(panel, fg_color="transparent", height=36)
        tab_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))

        self.chart_mode = "pie"
        self._tab_buttons = {}
        for mode, label in [("pie", "支出构成"), ("bar", "每日趋势"), ("compare", "收支对比")]:
            btn = ctk.CTkButton(
                tab_bar, text=label, width=90, height=30, corner_radius=6,
                font=("Helvetica", 11),
                fg_color=COLORS["primary"] if mode == "pie" else "transparent",
                text_color="white" if mode == "pie" else COLORS["text_light"],
                hover_color=COLORS["primary_hover"],
                command=lambda m=mode: self._switch_chart(m),
            )
            btn.pack(side="left", padx=(0, 6))
            self._tab_buttons[mode] = btn

        # Matplotlib 画布
        chart_container = ctk.CTkFrame(panel, fg_color="white", corner_radius=0)
        chart_container.grid(row=1, column=0, sticky="nswe", padx=8, pady=(0, 8))

        self.fig, self.ax = plt.subplots(figsize=(4.2, 4.2), dpi=90)
        self.fig.patch.set_facecolor("white")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---- 卡片组件 ----
    def _create_card(self, parent, title, value, color, col):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))

        # 顶部彩条
        bar = ctk.CTkFrame(card, fg_color=color, height=4, corner_radius=2)
        bar.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(card, text=title, font=("Helvetica", 11),
                     text_color=COLORS["text_light"]).pack(anchor="w", padx=18)
        val_lbl = ctk.CTkLabel(card, text=value, font=("Helvetica", 22, "bold"),
                               text_color=color)
        val_lbl.pack(anchor="w", padx=18, pady=(2, 14))
        return val_lbl

    # ================================================================
    #  图表 Tab 切换
    # ================================================================
    def _switch_chart(self, mode):
        self.chart_mode = mode
        for m, btn in self._tab_buttons.items():
            if m == mode:
                btn.configure(fg_color=COLORS["primary"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_light"])
        self.refresh_ui()

    # ================================================================
    #  事件处理
    # ================================================================
    def on_submit(self, r_type):
        try:
            amt = float(self.amt_ent.get())
            if amt <= 0:
                raise ValueError
            self.db.add_record(r_type, amt, self.cat_combo.get(), self.note_ent.get())
            self.amt_ent.delete(0, "end")
            self.note_ent.delete(0, "end")
            self.refresh_ui()
        except (ValueError, TypeError):
            messagebox.showerror("错误", "请输入有效的正数金额！")

    def export_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "类型", "分类", "金额", "备注"])
                for r in self.db.data["records"]:
                    writer.writerow([r["date"], r["type"], r["category"], r["amount"], r.get("note", "")])
            messagebox.showinfo("成功", "账单已导出！")

    def _show_ctx_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx_str = self.tree.item(sel[0], "tags")
        if idx_str:
            real_idx = int(idx_str[-1])
            if messagebox.askyesno("确认", "确定删除该记录？"):
                self.db.delete_record(real_idx)
                self.refresh_ui()

    # ================================================================
    #  刷新界面
    # ================================================================
    def refresh_ui(self):
        s_text = self.search_ent.get().strip()

        # 全局统计 (卡片 + 图表不受搜索影响)
        total_income, total_expense, all_cat_stats, all_indexed = self.db.get_stats("")
        balance = total_income - total_expense

        self.lbl_balance.configure(text=f"￥{balance:.2f}")
        self.lbl_income.configure(text=f"￥{total_income:.2f}")
        self.lbl_expense.configure(text=f"￥{total_expense:.2f}")

        # 搜索仅影响列表
        if s_text:
            _, _, _, filtered = self.db.get_stats(s_text)
        else:
            filtered = all_indexed

        # 图表始终使用全量数据
        cat_stats = all_cat_stats
        indexed = all_indexed

        # ---- 更新列表 ----
        for i in self.tree.get_children():
            self.tree.delete(i)

        display = list(reversed(filtered))
        for row_idx, (real_idx, r) in enumerate(display):
            prefix = "+" if r["type"] == "收入" else "-"
            color_tag = "income_row" if r["type"] == "收入" else "expense_row"
            alt_tag = "alt" if row_idx % 2 == 1 else ""
            tags = (color_tag, alt_tag, str(real_idx))
            self.tree.insert("", "end",
                             values=(r["date"], r["category"], r.get("note", ""), f"{prefix}{r['amount']:.2f}"),
                             tags=tags)

        # ---- 更新图表 ----
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("white")
        chart_colors = ["#4361EE", "#EF476F", "#FFD166", "#06D6A0", "#9B59B6", "#E67E22", "#1ABC9C"]
        mode = self.chart_mode

        if mode == "pie":
            if cat_stats:
                labels = list(cat_stats.keys())
                sizes = list(cat_stats.values())
                total = sum(sizes)
                wedges, _, _ = ax.pie(
                    sizes, labels=None, autopct="", startangle=140,
                    colors=chart_colors[:len(labels)],
                    wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2.5},
                    pctdistance=0.78,
                )
                ax.text(0, 0, f"￥{total:.0f}", ha="center", va="center",
                        fontsize=16, fontweight="bold", color=COLORS["text"])
                ax.text(0, -0.25, "总支出", ha="center", va="center",
                        fontsize=9, color=COLORS["text_light"])
                legend_labels = [f"{l}  ￥{s:.0f} ({s/total*100:.1f}%)" for l, s in zip(labels, sizes)]
                ax.legend(wedges, legend_labels, loc="lower center",
                          bbox_to_anchor=(0.5, -0.12), fontsize=8, frameon=False, ncol=2)
            else:
                ax.text(0.5, 0.5, "暂无支出数据", ha="center", va="center",
                        fontsize=13, color=COLORS["text_light"], transform=ax.transAxes)
                ax.axis("off")

        elif mode == "bar":
            daily = defaultdict(float)
            for _, r in indexed:
                if r["type"] == "支出":
                    daily[r["date"][:10]] += r["amount"]
            if daily:
                sorted_days = sorted(daily.keys())[-7:]
                amounts = [daily[d] for d in sorted_days]
                short_labels = [d[5:] for d in sorted_days]
                bars = ax.bar(short_labels, amounts, color=COLORS["primary"], width=0.55,
                              edgecolor="white", linewidth=0.8, zorder=3)
                for bar, val in zip(bars, amounts):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(amounts) * 0.03,
                            f"￥{val:.0f}", ha="center", va="bottom", fontsize=8, color=COLORS["text"])
                ax.set_ylabel("支出 (￥)", fontsize=9, color=COLORS["text_light"])
                self._style_bar_axes(ax)
            else:
                ax.text(0.5, 0.5, "暂无支出记录", ha="center", va="center",
                        fontsize=13, color=COLORS["text_light"], transform=ax.transAxes)
                ax.axis("off")

        elif mode == "compare":
            daily_in = defaultdict(float)
            daily_out = defaultdict(float)
            all_days = set()
            for _, r in indexed:
                day = r["date"][:10]
                all_days.add(day)
                if r["type"] == "收入":
                    daily_in[day] += r["amount"]
                else:
                    daily_out[day] += r["amount"]
            if all_days:
                sorted_days = sorted(all_days)[-7:]
                incomes = [daily_in.get(d, 0) for d in sorted_days]
                expenses = [daily_out.get(d, 0) for d in sorted_days]
                short_labels = [d[5:] for d in sorted_days]
                x = np.arange(len(sorted_days))
                w = 0.32
                ax.bar(x - w / 2, incomes, w, label="收入", color=COLORS["income"], edgecolor="white", zorder=3)
                ax.bar(x + w / 2, expenses, w, label="支出", color=COLORS["expense"], edgecolor="white", zorder=3)
                ax.set_xticks(x)
                ax.set_xticklabels(short_labels, fontsize=8)
                ax.legend(fontsize=8, frameon=False, loc="upper right")
                ax.set_ylabel("金额 (￥)", fontsize=9, color=COLORS["text_light"])
                self._style_bar_axes(ax)
            else:
                ax.text(0.5, 0.5, "暂无记录数据", ha="center", va="center",
                        fontsize=13, color=COLORS["text_light"], transform=ax.transAxes)
                ax.axis("off")

        self.fig.tight_layout()
        if mode == "pie" and cat_stats:
            # 给图例留出空间，避免小窗口被裁切
            self.fig.subplots_adjust(bottom=0.26)
        self.canvas.draw()
        self.ax = ax

    def _style_bar_axes(self, ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COLORS["border"])
        ax.spines["bottom"].set_color(COLORS["border"])
        ax.tick_params(colors=COLORS["text_light"], labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, linestyle="--", alpha=0.3, color=COLORS["border"])


# ================================================================
#  启动
# ================================================================
if __name__ == "__main__":
    import platform
    if platform.system() == "Darwin":
        plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "STHeiti"]
    elif platform.system() == "Windows":
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    else:
        plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Noto Sans CJK SC"]
    plt.rcParams["axes.unicode_minus"] = False

    app = PocketTrackApp()
    app.mainloop()
