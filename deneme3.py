from tkinter import *

root = Tk()
string = 'L'
nums = ['1', '2', '3']
labels = []  # creates an empty list for your labels
for x in nums:  # iterates over your nums
    jk = string + x
    label = Label(root, text=jk)  # set your text
    label.pack()
    labels.append(label)  # appends the label to the list for further use

root.mainloop()
