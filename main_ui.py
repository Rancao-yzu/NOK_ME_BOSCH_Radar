import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from data_processor import process_folder, save_output

ORANGE_PRIMARY = '#FF7F00'
ORANGE_DARK = '#D35400'
ORANGE_LIGHT = '#FFF0E0'
ORANGE_ACCENT = '#FF6B00'
ORANGE_HOVER = '#E65100'
BG_MAIN = '#FFFAF5'
BG_CARD = '#FFFFFF'
TEXT_DARK = '#3E2723'
TEXT_HINT = '#BF8040'
TEXT_SUCCESS = '#E67E22'


class DateTimePicker(ttk.Frame):
    def __init__(self, parent, default_dt=None, style_prefix='Card'):
        super().__init__(parent, style=f'{style_prefix}.TFrame')

        if default_dt is None:
            default_dt = datetime.now().replace(second=0)

        self._years = list(range(2020, 2031))
        self._months = list(range(1, 13))
        self._days = list(range(1, 32))
        self._hours = list(range(0, 24))
        self._minutes = list(range(0, 60))
        self._seconds = list(range(0, 60))

        self.year_var = tk.StringVar(value=str(default_dt.year))
        self.month_var = tk.StringVar(value=str(default_dt.month))
        self.day_var = tk.StringVar(value=str(default_dt.day))
        self.hour_var = tk.StringVar(value=f"{default_dt.hour:02d}")
        self.minute_var = tk.StringVar(value=f"{default_dt.minute:02d}")
        self.second_var = tk.StringVar(value=f"{default_dt.second:02d}")

        self._build_widgets(style_prefix)

        self.year_var.trace_add('write', self._on_date_change)
        self.month_var.trace_add('write', self._on_date_change)

    def _build_widgets(self, style_prefix):
        cb_width = 5
        hm_width = 3

        tk.Label(self, text="年", font=('Microsoft YaHei', 8),
                 bg=BG_CARD, fg=TEXT_HINT).pack(side=tk.LEFT)
        year_cb = ttk.Combobox(self, textvariable=self.year_var, values=self._years,
                                width=cb_width, state='readonly')
        year_cb.pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(self, text="月", font=('Microsoft YaHei', 8),
                 bg=BG_CARD, fg=TEXT_HINT).pack(side=tk.LEFT)
        month_cb = ttk.Combobox(self, textvariable=self.month_var, values=self._months,
                                 width=3, state='readonly')
        month_cb.pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(self, text="日", font=('Microsoft YaHei', 8),
                 bg=BG_CARD, fg=TEXT_HINT).pack(side=tk.LEFT)
        self.day_cb = ttk.Combobox(self, textvariable=self.day_var, values=self._days,
                                    width=3, state='readonly')
        self.day_cb.pack(side=tk.LEFT, padx=(2, 10))

        tk.Label(self, text="时", font=('Microsoft YaHei', 8),
                 bg=BG_CARD, fg=TEXT_HINT).pack(side=tk.LEFT)
        hour_cb = ttk.Combobox(self, textvariable=self.hour_var,
                                values=[f"{h:02d}" for h in self._hours],
                                width=hm_width, state='readonly')
        hour_cb.pack(side=tk.LEFT, padx=(2, 3))
        tk.Label(self, text=":", font=('Microsoft YaHei', 9),
                 bg=BG_CARD, fg=TEXT_DARK).pack(side=tk.LEFT)

        min_cb = ttk.Combobox(self, textvariable=self.minute_var,
                               values=[f"{m:02d}" for m in self._minutes],
                               width=hm_width, state='readonly')
        min_cb.pack(side=tk.LEFT, padx=(3, 3))
        tk.Label(self, text=":", font=('Microsoft YaHei', 9),
                 bg=BG_CARD, fg=TEXT_DARK).pack(side=tk.LEFT)

        sec_cb = ttk.Combobox(self, textvariable=self.second_var,
                               values=[f"{s:02d}" for s in self._seconds],
                               width=hm_width, state='readonly')
        sec_cb.pack(side=tk.LEFT, padx=(3, 0))

    def _on_date_change(self, *args):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except (ValueError, TypeError):
            return

        if month in (1, 3, 5, 7, 8, 10, 12):
            max_day = 31
        elif month in (4, 6, 9, 11):
            max_day = 30
        else:
            max_day = 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28

        new_days = list(range(1, max_day + 1))
        if self.day_cb['values'] != tuple(str(d) for d in new_days):
            self.day_cb['values'] = [str(d) for d in new_days]

        current_day = int(self.day_var.get()) if self.day_var.get().isdigit() else 1
        if current_day > max_day:
            self.day_var.set(str(max_day))

    def get_datetime_str(self):
        y = self.year_var.get()
        mo = self.month_var.get()
        d = self.day_var.get()
        h = self.hour_var.get()
        mi = self.minute_var.get()
        s = self.second_var.get()
        return f"{y}-{mo:0>2}-{d:0>2} {h}:{mi}:{s}"

    def set_datetime(self, dt_str):
        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            self.year_var.set(str(dt.year))
            self.month_var.set(str(dt.month))
            self.day_var.set(str(dt.day))
            self.hour_var.set(f"{dt.hour:02d}")
            self.minute_var.set(f"{dt.minute:02d}")
            self.second_var.set(f"{dt.second:02d}")
        except ValueError:
            pass


class DataMergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("测试数据合并工具")
        self.root.geometry("820x660")
        self.root.resizable(True, True)
        self.root.minsize(720, 580)
        self.root.configure(bg=BG_MAIN)

        self.folder_path = tk.StringVar()
        self.status_text = tk.StringVar(value="就绪")

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=BG_MAIN, foreground=TEXT_DARK, font=('Microsoft YaHei', 9))

        style.configure('Title.TLabel', font=('Microsoft YaHei', 18, 'bold'), foreground=ORANGE_DARK, background=BG_MAIN)
        style.configure('Subtitle.TLabel', font=('Microsoft YaHei', 9), foreground=TEXT_HINT, background=BG_MAIN)
        style.configure('Hint.TLabel', font=('Microsoft YaHei', 8), foreground=TEXT_HINT, background=BG_CARD)
        style.configure('Status.TLabel', font=('Microsoft YaHei', 9, 'bold'), foreground=ORANGE_ACCENT, background=BG_MAIN)
        style.configure('Output.TLabel', font=('Microsoft YaHei', 9), foreground=TEXT_SUCCESS, background=BG_MAIN)

        style.configure('Card.TLabelframe', background=BG_CARD, borderwidth=1, relief='solid')
        style.configure('Card.TLabelframe.Label', font=('Microsoft YaHei', 10, 'bold'), foreground=ORANGE_DARK, background=BG_CARD)

        style.configure('Card.TFrame', background=BG_CARD)
        style.configure('Card.TLabel', background=BG_CARD, foreground=TEXT_DARK, font=('Microsoft YaHei', 9))
        style.configure('Card.TEntry', fieldbackground='#FFF8F0', borderwidth=1, relief='solid', padding=6)

        style.configure('Primary.TButton', font=('Microsoft YaHei', 10, 'bold'),
                        background=ORANGE_PRIMARY, foreground='white',
                        borderwidth=0, relief='flat', padding=(20, 8))
        style.map('Primary.TButton',
                  background=[('active', ORANGE_HOVER), ('disabled', '#CCCCCC')],
                  foreground=[('disabled', '#999999')])

        style.configure('Browse.TButton', font=('Microsoft YaHei', 9),
                        background=ORANGE_ACCENT, foreground='white',
                        borderwidth=0, relief='flat', padding=(12, 6))
        style.map('Browse.TButton',
                  background=[('active', ORANGE_HOVER)])

        style.configure('Orange.TEntry', fieldbackground='#FFF8F0', borderwidth=1, relief='solid', padding=6)
        style.map('Orange.TEntry', fieldbackground=[('readonly', '#FFF5EB')])

        style.configure('TProgressbar', troughcolor=ORANGE_LIGHT, background=ORANGE_PRIMARY,
                        bordercolor=ORANGE_LIGHT, lightcolor=ORANGE_PRIMARY, darkcolor=ORANGE_PRIMARY)

        self.root.option_add('*TCombobox*Listbox.background', '#FFF8F0')
        self.root.option_add('*TCombobox*Listbox.selectBackground', ORANGE_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT_DARK)

        style.configure('Treeview', background='white', fieldbackground='white',
                        foreground=TEXT_DARK, rowheight=26, font=('Microsoft YaHei', 8))
        style.configure('Treeview.Heading', font=('Microsoft YaHei', 8, 'bold'),
                        background=ORANGE_PRIMARY, foreground='white', relief='flat')
        style.map('Treeview.Heading', background=[('active', ORANGE_HOVER)])
        style.map('Treeview', background=[('selected', ORANGE_LIGHT)], foreground=[('selected', TEXT_DARK)])

    def _build_ui(self):
        # ---- 顶部横幅 ----
        banner = tk.Frame(self.root, bg=ORANGE_PRIMARY, height=90)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)

        banner_inner = tk.Frame(banner, bg=ORANGE_PRIMARY)
        banner_inner.pack(expand=True)

        tk.Label(banner_inner, text="测试数据合并工具", font=('Microsoft YaHei', 18, 'bold'),
                 fg='white', bg=ORANGE_PRIMARY).pack(pady=(8, 0))

        mission_frame = tk.Frame(banner_inner, bg=ORANGE_PRIMARY)
        mission_frame.pack()


        tk.Label(mission_frame, text=' @', font=('Microsoft YaHei', 12),
                 fg='#FFCC80', bg=ORANGE_PRIMARY).pack(side=tk.LEFT, pady=(2, 0))

        link = tk.Label(mission_frame, text="威孚智感（无锡）科技有限公司",
                        font=('Microsoft YaHei', 12, 'underline'), fg='white',
                        bg=ORANGE_PRIMARY, cursor='hand2')
        link.pack(side=tk.LEFT, pady=(2, 0))
        link.bind('<Button-1>', lambda e: self._open_url('http://wfss.weifu.com.cn/index.html'))

        tk.Label(mission_frame, text=' 版权所有', font=('Microsoft YaHei', 12),
                 fg='#FFCC80', bg=ORANGE_PRIMARY).pack(side=tk.LEFT, pady=(2, 0))

        # ---- 主体内容区 ----
        main_frame = tk.Frame(self.root, bg=BG_MAIN)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # ---- 数据源卡片 ----
        folder_card = ttk.LabelFrame(main_frame, text="  数据源  ", style='Card.TLabelframe')
        folder_card.pack(fill=tk.X, pady=(0, 10))

        card_inner = ttk.Frame(folder_card, style='Card.TFrame')
        card_inner.pack(fill=tk.X, padx=14, pady=12)

        self.folder_entry = ttk.Entry(card_inner, textvariable=self.folder_path,
                                       style='Orange.TEntry')
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.folder_entry.bind('<Button-1>', lambda e: self._browse_folder())
        self._set_folder_placeholder()

        ttk.Button(card_inner, text="浏览...", style='Browse.TButton',
                   command=self._browse_folder).pack(side=tk.RIGHT)

        # ---- 时间范围卡片 ----
        time_card = ttk.LabelFrame(main_frame, text="  时间范围筛选  ", style='Card.TLabelframe')
        time_card.pack(fill=tk.X, pady=(0, 10))

        time_inner = ttk.Frame(time_card, style='Card.TFrame')
        time_inner.pack(fill=tk.X, padx=14, pady=12)

        ttk.Label(time_inner, text="开始时间:", style='Card.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 8), pady=8)
        self.start_picker = DateTimePicker(time_inner, default_dt=datetime(2025, 12, 3, 14, 3, 9))
        self.start_picker.grid(row=0, column=1, sticky=tk.W, pady=8)

        ttk.Label(time_inner, text="结束时间:", style='Card.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=(0, 8), pady=8)
        self.end_picker = DateTimePicker(time_inner, default_dt=datetime(2025, 12, 8, 14, 3, 10))
        self.end_picker.grid(row=1, column=1, sticky=tk.W, pady=8)

        # ---- 操作区 ----
        action_frame = tk.Frame(main_frame, bg=BG_MAIN)
        action_frame.pack(fill=tk.X, pady=(0, 8))

        self.process_btn = ttk.Button(action_frame, text="开始合并", style='Primary.TButton',
                                       command=self._start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 14))

        self.progress = ttk.Progressbar(action_frame, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        ttk.Label(action_frame, textvariable=self.status_text, style='Status.TLabel').pack(side=tk.RIGHT)

        # ---- 结果预览卡片 ----
        result_card = ttk.LabelFrame(main_frame, text="  合并结果预览  ", style='Card.TLabelframe')
        result_card.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        tree_inner = ttk.Frame(result_card, style='Card.TFrame')
        tree_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        columns = (
            '产品DMC', '产品料号（半成品/成品）', '测试站',
            '测试工位(StationID)', '测试时间(Start Date Time)',
            'failure mode(Test Step Name)', '测试值(Measurement Value)',
            '测试limit（Low Limit）', '测试limit（High Limit）'
        )

        self.tree = ttk.Treeview(tree_inner, columns=columns, show='headings', height=8)

        col_widths = [290, 170, 55, 140, 180, 200, 140, 130, 130]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(tree_inner, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_inner, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tree_inner.grid_rowconfigure(0, weight=1)
        tree_inner.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure('even', background='#FFF8F0')
        self.tree.tag_configure('odd', background='white')

        # ---- 输出信息 ----
        self.output_label = ttk.Label(main_frame, text="", style='Output.TLabel')
        self.output_label.pack(fill=tk.X, pady=(0, 2))

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="选择测试数据根文件夹")
        if path:
            self.folder_path.set(path)
            self._clear_folder_placeholder()

    def _set_folder_placeholder(self):
        self._folder_placeholder = True
        self.folder_path.set("例如: /home/weifu/NOK/NOK测试报告")
        self.folder_entry.configure(foreground=TEXT_HINT)
        self.folder_entry.bind('<FocusIn>', self._on_folder_focus_in)
        self.folder_entry.bind('<FocusOut>', self._on_folder_focus_out)

    def _clear_folder_placeholder(self):
        self._folder_placeholder = False
        self.folder_entry.configure(foreground=TEXT_DARK)
        self.folder_entry.unbind('<FocusIn>')
        self.folder_entry.unbind('<FocusOut>')

    def _on_folder_focus_in(self, event):
        if self._folder_placeholder:
            self.folder_path.set('')
            self.folder_entry.configure(foreground=TEXT_DARK)

    def _on_folder_focus_out(self, event):
        if not self.folder_path.get().strip():
            self.folder_path.set("例如: /home/weifu/NOK/NOK测试报告")
            self.folder_entry.configure(foreground=TEXT_HINT)
            self._folder_placeholder = True

    def _start_processing(self):
        if getattr(self, '_folder_placeholder', False):
            messagebox.showwarning("提示", "请先选择数据源文件夹")
            return

        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("提示", "请先选择数据源文件夹")
            return

        start = self.start_picker.get_datetime_str()
        end = self.end_picker.get_datetime_str()

        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        if start_dt >= end_dt:
            messagebox.showwarning("时间范围错误", "开始时间必须早于结束时间！")
            return

        self.process_btn.config(state=tk.DISABLED)
        self.status_text.set("正在处理...")
        self.progress['value'] = 0
        self._clear_tree()
        self.output_label.config(text="")
        self.root.update_idletasks()

        try:
            records = process_folder(folder, start, end, self._update_progress)
        except Exception as e:
            messagebox.showerror("错误", f"处理失败:\n{str(e)}")
            self.status_text.set("处理失败")
            self.process_btn.config(state=tk.NORMAL)
            return

        if not records:
            self.status_text.set("未找到匹配的数据")
            messagebox.showinfo("提示", "在指定时间范围内未找到匹配的失败记录")
            self.process_btn.config(state=tk.NORMAL)
            return

        if getattr(sys, 'frozen', False):
            out_folder = os.path.join(os.path.dirname(sys.executable), 'OUT')
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            out_folder = os.path.join(script_dir, 'OUT')
        try:
            output_path = save_output(records, out_folder, start, end)
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败:\n{str(e)}")
            self.status_text.set("保存失败")
            self.process_btn.config(state=tk.NORMAL)
            return

        for i, rec in enumerate(records):
            if i >= 500:
                break
            vals = [rec.get(col, '') for col in self.tree['columns']]
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert('', tk.END, values=vals, tags=(tag,))

        self.status_text.set(f"处理完成，共 {len(records)} 条失败记录")
        self.output_label.config(text=f"输出文件: {output_path}")
        self.progress['value'] = 100
        self.process_btn.config(state=tk.NORMAL)
        messagebox.showinfo("完成", f"合并完成!\n共处理 {len(records)} 条失败记录\n输出文件:\n{output_path}")

    def _update_progress(self, current, total):
        if total > 0:
            self.progress['value'] = (current / total) * 100
            self.status_text.set(f"处理中... {current}/{total}")
        self.root.update_idletasks()

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)


def main():
    root = tk.Tk()
    app = DataMergeApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
