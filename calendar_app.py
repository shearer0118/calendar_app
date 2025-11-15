import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import json
import os
import sys

# ===========================
# 儲存事件的 JSON 檔案
# ===========================
if getattr(sys, 'frozen', False):
    # 打包後的 exe，BASE_DIR 指向 exe 所在資料夾
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Python 原始執行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTS_FILE = os.path.join(BASE_DIR, "events.json")

# 讀取 JSON 檔案，如果檔案不存在則初始化空字典
# ===========================
if os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        events_raw = json.load(f)
    events = {}
    for k, v in events_raw.items():
        date_key = datetime.strptime(k, "%Y-%m-%d").date()
        if v and isinstance(v[0], str):
            events[date_key] = [{"name": name, "detail": ""} for name in v]
        else:
            events[date_key] = v
else:
    events = {}

# ===========================
# 統一字體
# ===========================
FONT_NAME = ("Arial", 11)

# ===========================
# 儲存事件到 JSON 檔案
# ===========================
def save_events():
    events_to_save = {k.strftime("%Y-%m-%d"): v for k, v in events.items()}
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events_to_save, f, ensure_ascii=False, indent=2)

# ===========================
# 新增事件
# ===========================
def add_event():
    event_date = date_entry.get_date()
    event_name = event_entry.get().strip()
    event_detail = detail_entry.get("1.0", tk.END).strip()

    if not event_name:
        messagebox.showerror("錯誤", "事件名稱不能為空")
        return

    if event_date not in events:
        events[event_date] = []

    events[event_date].append({"name": event_name, "detail": event_detail})

    event_entry.delete(0, tk.END)
    detail_entry.delete("1.0", tk.END)

    update_reminders()
    save_events()

# ===========================
# 顯示事件詳情
# ===========================
def show_detail(event, date):
    detail_win = tk.Toplevel(root)
    detail_win.title("事件詳情")
    detail_win.geometry("400x200")

    tk.Label(detail_win, text=f"事件名稱: {event['name']}", font=FONT_NAME).pack(anchor='w', padx=10, pady=(10,0))
    tk.Label(detail_win, text=f"事件日期: {date}", font=FONT_NAME).pack(anchor='w', padx=10, pady=(5,0))
    tk.Label(detail_win, text="詳細內容:", font=FONT_NAME).pack(anchor='w', padx=10, pady=(5,0))

    detail_text = tk.Text(detail_win, width=50, height=8, font=FONT_NAME)
    detail_text.pack(padx=10, pady=5)
    detail_text.insert(tk.END, event['detail'])
    detail_text.config(state=tk.DISABLED)

# ===========================
# 顯示全部事件
# ===========================
def show_all_events_gui():
    if not events:
        messagebox.showinfo("全部事件", "目前沒有任何事件")
        return

    all_events_window = tk.Toplevel(root)
    all_events_window.title("全部事件")
    all_events_window.geometry("500x500")

    canvas = tk.Canvas(all_events_window)
    scrollbar = tk.Scrollbar(all_events_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    today = datetime.today().date()

    # 刷新事件
    def refresh_all_events(frame):
        for widget in frame.winfo_children():
            widget.destroy()

        for event_date, event_list in sorted(events.items()):
            for idx, event in enumerate(event_list):
                event_frame = tk.Frame(frame, bd=1, relief="solid", padx=5, pady=5)
                event_frame.pack(fill='x', padx=10, pady=5)

                # 名稱與日期並排
                top_row = tk.Frame(event_frame)
                top_row.pack(anchor='w', fill='x')

                display_name = event['name']
                if event_date < today:
                    display_name = "(已過期) " + display_name

                tk.Label(top_row, text="事件名稱:", font=FONT_NAME).pack(side='left')
                tk.Label(top_row, text=display_name, font=FONT_NAME).pack(side='left', padx=(0,10))
                tk.Label(top_row, text="日期:", font=FONT_NAME).pack(side='left')
                tk.Label(top_row, text=str(event_date), font=FONT_NAME).pack(side='left')

                # 詳細內容換行
                tk.Label(event_frame, text="詳細內容:", font=FONT_NAME).pack(anchor='w', pady=(5,0))
                tk.Label(event_frame, text=event['detail'], anchor='w', justify='left',
                         wraplength=450, font=FONT_NAME).pack(anchor='w', padx=5, pady=(0,5))

                # 按鈕放左下角
                btn_frame = tk.Frame(event_frame)
                btn_frame.pack(anchor='w', pady=(0,2))
                del_btn = tk.Button(btn_frame, text="刪除", fg="red",
                                    command=lambda d=event_date, i=idx: delete_event(d, i, frame), font=FONT_NAME)
                del_btn.pack(side='left', padx=(0,5))
                edit_btn = tk.Button(btn_frame, text="編輯", fg="blue",
                                     command=lambda d=event_date, i=idx: open_edit_window(d, i, frame), font=FONT_NAME)
                edit_btn.pack(side='left')

                # 分隔線
                tk.Label(frame, text="-"*60, fg="gray", font=FONT_NAME).pack(fill='x', padx=10, pady=2)

    # 刪除事件
    def delete_event(date, index, frame):
        if messagebox.askyesno("刪除確認", "確定要刪除此事件嗎？"):
            events[date].pop(index)
            if not events[date]:
                del events[date]
            save_events()
            update_reminders()
            refresh_all_events(frame)

    # 編輯事件
    def open_edit_window(date, index, frame):
        event = events[date][index]
        edit_win = tk.Toplevel(all_events_window)
        edit_win.title("編輯事件")
        edit_win.geometry("500x400")  # 改大視窗大小

        tk.Label(edit_win, text="事件名稱:", font=FONT_NAME).pack(anchor='w', padx=10, pady=(10,0))
        text_entry = tk.Entry(edit_win, width=50, font=FONT_NAME)  # 寬度加大
        text_entry.pack(anchor='w', padx=10)
        text_entry.insert(0, event['name'])

        tk.Label(edit_win, text="事件日期:", font=FONT_NAME).pack(anchor='w', padx=10, pady=(10,0))
        date_picker = DateEntry(edit_win, width=25, background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')
        date_picker.pack(anchor='w', padx=10)
        date_picker.set_date(date)

        tk.Label(edit_win, text="詳細內容:", font=FONT_NAME).pack(anchor='w', padx=10, pady=(10,0))
        detail_text = tk.Text(edit_win, width=50, height=10, font=FONT_NAME)  # 高度增加
        detail_text.pack(anchor='w', padx=10)
        detail_text.insert(tk.END, event['detail'])

        # 將儲存按鈕固定在底部
        button_frame = tk.Frame(edit_win)
        button_frame.pack(side="bottom", fill="x", pady=10)
        save_button = tk.Button(button_frame, text="儲存修改", command=lambda: save_edit(), font=FONT_NAME)
        save_button.pack()

        def save_edit():
            new_name = text_entry.get().strip()
            new_date = date_picker.get_date()
            new_detail = detail_text.get("1.0", tk.END).strip()
            if not new_name:
                messagebox.showerror("錯誤", "事件名稱不能為空")
                return
            events[date].pop(index)
            if not events[date]:
                del events[date]
            if new_date not in events:
                events[new_date] = []
            events[new_date].append({"name": new_name, "detail": new_detail})
            save_events()
            update_reminders()
            refresh_all_events(frame)
            edit_win.destroy()

    refresh_all_events(scrollable_frame)

# ===========================
# 主視窗
# ===========================
root = tk.Tk()
root.title("個人行事曆")
root.geometry("850x400")

# 左側新增事件區
left_frame = tk.Frame(root, padx=10, pady=10, bg="#f0f0f0")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk.Label(left_frame, text="事件名稱:", font=FONT_NAME).pack(anchor='w')
event_entry = tk.Entry(left_frame, width=40, font=FONT_NAME)
event_entry.pack(anchor='w')

tk.Label(left_frame, text="事件日期:", font=FONT_NAME).pack(anchor='w', pady=(10,0))
date_entry = DateEntry(left_frame, width=20, background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')
date_entry.pack(anchor='w')

tk.Label(left_frame, text="詳細內容:", font=FONT_NAME).pack(anchor='w', pady=(10,0))
detail_entry = tk.Text(left_frame, width=40, height=5, font=FONT_NAME)
detail_entry.pack(anchor='w')

tk.Button(left_frame, text="新增事件", command=add_event, font=FONT_NAME).pack(anchor='w', pady=10)
tk.Button(left_frame, text="顯示全部事件", command=show_all_events_gui, font=FONT_NAME).pack(side='bottom', anchor='w', pady=10)

# 右側提醒事件區
right_frame = tk.Frame(root, padx=10, pady=10, bg="#e0e0e0")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Label(right_frame, text="一週內提醒事件:", font=FONT_NAME).pack(anchor='w')

canvas = tk.Canvas(right_frame)
scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# ===========================
# 更新提醒事件
# ===========================
def update_reminders():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    today = datetime.today().date()
    week_later = today + timedelta(days=7)

    for event_date, event_list in sorted(events.items()):
        if today <= event_date <= week_later:
            for event in event_list:
                event_row = tk.Frame(scrollable_frame)
                event_row.pack(fill='x', pady=2)

                detail_btn = tk.Button(event_row, text="顯示詳情",
                                       command=lambda e=event, d=event_date: show_detail(e, d), font=FONT_NAME)
                detail_btn.pack(side='left')
                tk.Label(event_row, text=f"{event_date}: {event['name']}", anchor='w', font=FONT_NAME).pack(side='left', padx=5)

update_reminders()
root.mainloop()
