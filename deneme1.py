import tkinter as tk
from tkinter.ttk import Label

root = tk.Tk()
# root.geometry('300x200')
# root.resizable(False, False)
root.title('Label Widget Demo')

# show a label
label1 = Label(root, text='This is a label')
label1.pack(ipadx=5, ipady=5)

label2 = Label(root, text='This is a label')
label2.pack(ipadx=5, ipady=5)

label3 = Label(root, text='This is a label')
label3.pack(ipadx=5, ipady=5)

root.mainloop()

