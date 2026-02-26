import json
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- 样式配置 ----------
COLORS = {
    "bg": "#F8F9FA",
    "sidebar": "#2C3E50",
    "card_bg": "#FFFFFF",
    "primary": "#3498DB",
    "income": "#27AE60",
    "expense": "#E74C3C",
    "warning": "#F1C40F",
    "text": "#2C3E50",
    "text_light": "#95A5A6"
}

DATA_FILE = "money_data.json"

# ---------- 数据管理类 ----------
class DataManager:
    def __init__(self):
        self.data = self.load()
        if "budget" not in self.data: self.data["budget"] = 500.0 # 默认预算

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"records": [], "budget": 500.0}

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add_record(self, r_type, amount, category, note=""):
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": r_type,
            "amount": float(amount),
            "category": category,
            "note": note
        }
        self.data["records"].append(record)
        self.save()

    def get_stats(self, filter_text=""):
        records = self.data["records"]
        # 搜索过滤
        if filter_text:
            records = [r for r in records if filter_text.lower() in r['category'].lower() or filter_text.lower() in r.get('note','').lower()]
        
        income = sum(r['amount'] for r in records if r['type'] == '收入')
        expense = sum(r['amount'] for r in records if r['type'] == '支出')
        
        cat_map = {}
        for r in records:
            if r['type'] == '支出':
                cat_map[r['category']] = cat_map.get(r['category'], 0) + r['amount']
        
        return income, expense, cat_map, records

# ---------- 主界面类 ----------
class PocketTrackApp:
    def __init__(self, root):
        self.root = root
        self.db = DataManager()
        self.root.title("PocketTrack Pro - 智慧零花钱管理")
        self.root.geometry("1100x700")
        self.root.configure(bg=COLORS["bg"])
        
        self.setup_ui()
        self.refresh_ui()

    def setup_ui(self):
        # 1. 侧边栏 (录入)
        self.sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="PocketTrack", fg="white", bg=COLORS["sidebar"], font=("Arial", 20, "bold"), pady=30).pack()

        form_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"], padx=25)
        form_frame.pack(fill="x")

        # 金额输入
        tk.Label(form_frame, text="输入金额 (￥)", fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        self.amt_ent = tk.Entry(form_frame, font=("Arial", 14), bd=0)
        self.amt_ent.pack(fill="x", pady=(5, 15))

        # 分类选择
        tk.Label(form_frame, text="消费分类", fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        self.cat_combo = ttk.Combobox(form_frame, values=["餐饮", "文具", "零食", "交通", "娱乐", "红包", "其他"], font=("微软雅黑", 10))
        self.cat_combo.set("餐饮")
        self.cat_combo.pack(fill="x", pady=(5, 15))

        # 备注
        tk.Label(form_frame, text="备注信息", fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        self.note_ent = tk.Entry(form_frame, font=("Arial", 10), bd=0)
        self.note_ent.pack(fill="x", pady=(5, 25))

        # 录入按钮
        tk.Button(self.sidebar, text="确认支出", bg=COLORS["expense"], fg="white", bd=0, cursor="hand2",
                  font=("微软雅黑", 11, "bold"), height=2, command=lambda: self.on_submit("支出")).pack(fill="x", padx=25, pady=5)
        tk.Button(self.sidebar, text="确认收入", bg=COLORS["income"], fg="white", bd=0, cursor="hand2",
                  font=("微软雅黑", 11, "bold"), height=2, command=lambda: self.on_submit("收入")).pack(fill="x", padx=25, pady=5)

        # 底部功能
        tk.Button(self.sidebar, text="⚙ 设置月度预算", bg="#576574", fg="white", bd=0, command=self.set_budget).pack(side="bottom", fill="x", padx=25, pady=10)
        tk.Button(self.sidebar, text="📤 导出 CSV 账单", bg="#576574", fg="white", bd=0, command=self.export_data).pack(side="bottom", fill="x", padx=25, pady=5)

        # 2. 右侧主内容区
        self.main = tk.Frame(self.root, bg=COLORS["bg"], padx=30, pady=20)
        self.main.pack(side="right", fill="both", expand=True)

        # 看板卡片
        self.card_frame = tk.Frame(self.main, bg=COLORS["bg"])
        self.card_frame.pack(fill="x")
        self.lbl_balance = self.create_card(self.card_frame, "当前余额", "￥0.00", COLORS["primary"], 0)
        self.lbl_expense = self.create_card(self.card_frame, "本期总支出", "￥0.00", COLORS["expense"], 1)
        self.lbl_budget = self.create_card(self.card_frame, "预算剩余", "￥0.00", COLORS["warning"], 2)

        # 下方列表与图表
        self.bottom_frame = tk.Frame(self.main, bg=COLORS["bg"], pady=20)
        self.bottom_frame.pack(fill="both", expand=True)

        # 列表区 (带搜索)
        self.list_frame = tk.Frame(self.bottom_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#E0E0E0")
        self.list_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

        search_bar = tk.Frame(self.list_frame, bg="white")
        search_bar.pack(fill="x", pady=(0, 10))
        tk.Label(search_bar, text="🔍 搜索:", bg="white").pack(side="left")
        self.search_ent = tk.Entry(search_bar, width=20)
        self.search_ent.pack(side="left", padx=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self.refresh_ui())

        self.tree = ttk.Treeview(self.list_frame, columns=("time", "cat", "amt"), show="headings", height=12)
        self.tree.heading("time", text="时间")
        self.tree.heading("cat", text="分类")
        self.tree.heading("amt", text="金额")
        self.tree.column("amt", anchor="e", width=100)
        self.tree.pack(fill="both", expand=True)

        # 图表区
        self.chart_frame = tk.Frame(self.bottom_frame, bg="white", highlightthickness=1, highlightbackground="#E0E0E0")
        self.chart_frame.pack(side="right", fill="both")
        self.fig, self.ax = plt.subplots(figsize=(4, 4.5), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack()

    def create_card(self, parent, title, value, color, col):
        f = tk.Frame(parent, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#E0E0E0")
        f.grid(row=0, column=col, sticky="nsew", padx=10)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(f, text=title, bg="white", fg=COLORS["text_light"], font=("微软雅黑", 10)).pack(anchor="w")
        val_lbl = tk.Label(f, text=value, bg="white", fg=color, font=("Arial", 18, "bold"))
        val_lbl.pack(anchor="w")
        return val_lbl

    def on_submit(self, r_type):
        try:
            amt = float(self.amt_ent.get())
            if amt <= 0: raise ValueError
            self.db.add_record(r_type, amt, self.cat_combo.get(), self.note_ent.get())
            self.amt_ent.delete(0, tk.END)
            self.note_ent.delete(0, tk.END)
            self.refresh_ui()
        except:
            messagebox.showerror("错误", "请输入有效的数字金额！")

    def set_budget(self):
        new_b = filedialog.askstring="输入新预算" # 简化版输入
        from tkinter import simpledialog
        res = simpledialog.askfloat("设置预算", "请输入本月预期的消费上限 (￥):", initialvalue=self.db.data["budget"])
        if res:
            self.db.data["budget"] = res
            self.db.save()
            self.refresh_ui()

    def export_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "类型", "分类", "金额", "备注"])
                for r in self.db.data["records"]:
                    writer.writerow([r['date'], r['type'], r['category'], r['amount'], r.get('note','')])
            messagebox.showinfo("成功", "账单已导出！")

    def refresh_ui(self):
        s_text = self.search_ent.get()
        income, expense, cat_stats, records = self.db.get_stats(s_text)
        
        # 更新卡片与预算预警
        balance = income - expense
        remain_budget = self.db.data["budget"] - expense
        
        self.lbl_balance.config(text=f"￥{balance:.2f}")
        self.lbl_expense.config(text=f"￥{expense:.2f}")
        
        # 预算预警逻辑
        budget_color = COLORS["warning"]
        if remain_budget < 0: budget_color = COLORS["expense"]
        elif remain_budget < self.db.data["budget"] * 0.2: budget_color = "#E67E22"
        
        self.lbl_budget.config(text=f"￥{remain_budget:.2f}", fg=budget_color)

        # 更新列表
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in reversed(records[-20:]):
            prefix = "+" if r['type'] == '收入' else "-"
            self.tree.insert("", "end", values=(r['date'], r['category'], f"{prefix}{r['amount']:.2f}"))

        # 更新绘图
        
        self.ax.clear()
        if cat_stats:
            self.ax.pie(cat_stats.values(), labels=cat_stats.keys(), autopct='%1.1f%%', 
                        colors=['#3498DB', '#E74C3C', '#F1C40F', '#27AE60', '#9B59B6'], wedgeprops={'width': 0.5})
            self.ax.set_title("支出构成", fontproperties="SimHei")
        else:
            self.ax.text(0.5, 0.5, "尚无消费数据", ha='center', fontproperties="SimHei")
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    # 尝试设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei'] 
    plt.rcParams['axes.unicode_minus'] = False
    app = PocketTrackApp(root)
    root.mainloop()