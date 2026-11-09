"""Portable four-interaction teaching UI connected to real loopback mock sockets."""
import json
import tkinter as tk
from tkinter import ttk
from .runtime import Simulator, request


def start():
    with Simulator('g1-a') as a, Simulator('g1-b') as b:
        window = tk.Tk(); window.title('G1 DevKit · 电脑模拟'); window.geometry('760x480')
        ttk.Label(window, text='双设备 UDP 实验：所有状态均为模拟值', font=('', 14)).pack(pady=12)
        target = tk.StringVar(value='all')
        ttk.Combobox(window, textvariable=target, values=('all', 'g1-a', 'g1-b'), state='readonly').pack()
        output = tk.Text(window, height=16); output.pack(fill='both', expand=True, padx=16, pady=12)

        def send(command):
            replies = request([a.endpoint, b.endpoint], target.get(), command, '界面通信测试')
            output.delete('1.0', 'end'); output.insert('end', json.dumps(replies, ensure_ascii=False, indent=2))

        buttons = ttk.Frame(window); buttons.pack(pady=12)
        for label, command in (('发现 / 状态', 'status'), ('发送回声', 'echo'), ('结束模拟动作', 'stop_demo')):
            ttk.Button(buttons, text=label, command=lambda value=command: send(value)).pack(side='left', padx=8)
        # Selection, discovery/state, echo and stop give the four required interactions.
        window.mainloop()
