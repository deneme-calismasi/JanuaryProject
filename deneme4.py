from tkinter import *

root = Tk()
var = StringVar()
label = Label(root, underline=2, wraplength=70, textvariable=var, relief="groove")
var.set("This example is about the anchor option of Python Tkinter Label")
label.pack()
root.mainloop()
