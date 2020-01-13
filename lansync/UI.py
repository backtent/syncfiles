#!/usr/bin/python3
#-*-coding:utf-8-*-

import tkinter as tk

root = tk.Tk()
sb = tk.Scrollbar(root)
sb.pack(side=tk.RIGHT, fill=tk.Y)
lb = tk.Listbox(root, yscrollcommand=sb.set)
for i in range(1000):
    lb.insert(tk.END, str(i))

lb.pack(side=tk.LEFT, fill=tk.BOTH)
sb.config(command=lb.yview)

tk.mainloop()

            
if __name__ == '__main__':
    print("socket的小封装")
