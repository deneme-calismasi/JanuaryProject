import math
from pyModbusTCP.client import ModbusClient
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import *
import pymongo
import datetime as dt
import numpy
import csv
import pandas as pd
import openpyxl

root = tk.Tk()


def window_unit():
    root.title("Sensor's Temperatures °C")
    root.geometry("850x650")
    root.grid()


class EaeSens:
    L1 = 0
    L2 = 0
    L3 = 0
    EXT = 0
    OUT = 0
    line_no = 0
    sens_no = 0

    def __init__(self, L1, L2, L3, EXT, OUT, line_no, sens_no):
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.EXT = EXT
        self.OUT = OUT
        self.line_no = line_no
        self.sens_no = sens_no


# obj1 = EaeSens(3, 3, 3)

sensArray = numpy.ndarray((32,), dtype=EaeSens)

for i in range(0, 16):
    sensArray[i] = EaeSens(0.0, 0.0, 0.0, 0, 0, 110, i + 1)

for a in range(16, 32):
    sensArray[a] = EaeSens(0.0, 0.0, 0.0, 0, 0, 400, a + 1)


class ModBus:
    sensor_min_num = 0
    sensor_max_num = 2
    lineNo = 0
    sensorTypeNo = 0

    def __init__(self, sensorTypeNo, lineNo, sensor_min_num, sensor_max_num):

        self.sensor_min_num = sensor_min_num
        self.sensor_max_num = sensor_max_num
        self.lineNo = lineNo
        self.sensorTypeNo = sensorTypeNo
        self.resultList = []
        self.finalResultList = []
        self.regNoList = []
        self.reg_list = list(range(self.sensor_min_num, self.sensor_max_num + 1))
        self.style = ttk.Style()
        self.style.map("Treeview", foreground=self.fixed_map("foreground"), background=self.fixed_map("background"))

    def fixed_map(self, option):
        return [elm for elm in self.style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    def connect_modbus(self):

        for i in self.reg_list:
            groupNo = math.floor(((self.lineNo - 1) / 256)) + 1
            self.portNo = 10000 + (self.sensorTypeNo - 1) * 10 + groupNo - 1
            regNo = (((self.lineNo - 1) * 128 + (int(i) - 1)) * 2) % 65536
            self.regNoList.append(regNo)
            print("groupNo", groupNo)
            print("portNo", self.portNo)
            print("regNo", regNo)

        for x in self.regNoList:
            sensor_no = ModbusClient(host="192.40.50.107", port=self.portNo, unit_id=1, auto_open=True)
            sensor_no.open()
            regs = sensor_no.read_holding_registers(x, 2)
            if regs:
                print(regs)
            else:
                print("read error")

            regs[0], regs[1] = regs[1], regs[0]
            data_bytes = np.array(regs, dtype=np.uint16)
            result = data_bytes.view(dtype=np.float32)
            self.resultList.append(result[0])

        print("REG_LIST", self.reg_list)
        self.data_as_float = self.resultList
        print("Result_Temp", self.resultList)
        self.finalResultList = self.resultList
        self.regNoList = []
        self.resultList = []
        return self.data_as_float

    def list_to_dict(self):
        self.connect_modbus()
        self.regs_count = len(self.reg_list)

        value = [[num for num in range(1, 1 + self.regs_count)], self.reg_list, self.data_as_float]

        data = np.array(value).T.tolist()

        products = data
        self.arr = []
        for product in products:
            vals = {}
            vals["Sensor Type No"] = str(int(self.sensorTypeNo))
            vals["Line No"] = str(int(self.lineNo))
            vals["Sensor No"] = str(int(product[1]))
            vals["Temp"] = str(round(product[2], 4))
            vals["Time"] = str(dt.datetime.now().strftime('%Y-%m-%d %X'))
            self.arr.append(vals)
        return self.arr

    def record_mongo(self):
        lst = self.list_to_dict()
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["Modbus_Database"]
        mycol = mydb["collection5"]

        mycol.insert_many(lst)

        documents = list(mycol.find({}, {'_id': 0}))
        res = [list(idx.values()) for idx in documents]

        for index1, row in enumerate(res):
            for index2, item in enumerate(row):
                try:
                    res[index1][index2] = (float(item))
                except ValueError:
                    pass
        return res

    def drag_start(self, event):
        widget = event.widget
        widget.startX = event.x
        widget.startY = event.y

    def drag_motion(self, event):
        widget = event.widget
        x = widget.winfo_x() - widget.startX + event.x
        y = widget.winfo_y() - widget.startY + event.y
        widget.place(x=x, y=y)

    def table_insert(self, x, y):

        if self.sensorTypeNo == 1:
            self.head_text = "L1"
        elif self.sensorTypeNo == 2:
            self.head_text = "L2"
        elif self.sensorTypeNo == 3:
            self.head_text = "L3"
        elif self.sensorTypeNo == 7:
            self.head_text = "OUT"
        elif self.sensorTypeNo == 8:
            self.head_text = "EXT"
        else:
            self.head_text = "NULL"

        self.tree = ttk.Treeview(root)
        verscrlbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)

        self.tree.configure(xscrollcommand=verscrlbar.set)

        self.tree["columns"] = ("1", "2", "3", "4")

        self.tree['show'] = 'headings'

        self.tree.column("1", width=65, minwidth=30, anchor='c')
        self.tree.column("2", width=125, minwidth=30, anchor='c')
        self.tree.column("3", width=65, minwidth=30, anchor='c')
        self.tree.column("4", width=115, minwidth=30, anchor='c')

        self.tree.heading("1", text=self.head_text)
        self.tree.heading("2", text="Time")
        self.tree.heading("3", text="Sensor No")
        self.tree.heading("4", text="Temperature °C")

        self.tree.place(x=x, y=y)

        self.tree.tag_configure('high', foreground='red')
        self.tree.tag_configure('low', foreground='black')

        start_range = 0
        id_count = 1

        for record in self.record_mongo()[-(self.regs_count):]:
            sensor_id = record[2]
            temperature = record[3]
            date_time = record[4]

            if float(temperature) > 30.0:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=start_range,
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('high',))
            else:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=start_range,
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('low',))

            start_range += 1
            id_count += 1

        self.tree.bind("<Button-1>", self.drag_start)
        self.tree.bind("<B1-Motion>", self.drag_motion)

        self.update_window_table()
        self.tree.after(20000, self.update_window_table)

    def update_window_table(self):

        for i in self.tree.get_children():
            self.tree.delete(i)

        start_range = 0
        id_count = 1

        for record in self.record_mongo()[-(self.regs_count):]:
            sensor_id = record[2]
            temperature = record[3]
            date_time = record[4]

            if float(temperature) > 30.0:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=start_range,
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('high',))

            else:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=start_range,
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('low',))

            start_range += 1
            id_count += 1

        root.update()
        root.update_idletasks()
        self.tree.after(20000, self.update_window_table)


def main():
    window_unit()
    app1 = ModBus(1, 400, 1, 16)
    app1.connect_modbus()
    app2 = ModBus(2, 400, 1, 16)
    app2.connect_modbus()
    app3 = ModBus(3, 400, 1, 16)
    app3.connect_modbus()
    app4 = ModBus(7, 110, 1, 16)
    app4.connect_modbus()
    app5 = ModBus(8, 110, 1, 16)
    app5.connect_modbus()

    for count in range(32):
        if sensArray[count].line_no == 400:
            sensArray[count].L1 = app1.finalResultList[count - 16]
            sensArray[count].L2 = app2.finalResultList[count - 16]
            sensArray[count].L3 = app3.finalResultList[count - 16]

        elif sensArray[count].line_no == 110:
            sensArray[count].EXT = app4.finalResultList[count]
            sensArray[count].OUT = app5.finalResultList[count]

    tree = ttk.Treeview(root)
    verscrlbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    tree.configure(xscrollcommand=verscrlbar.set)

    tree["columns"] = ("1", "2", "3", "4", "5", "6", "7", "8")
    tree.column("#0", width=0, stretch=NO)
    tree.column("1", width=125, minwidth=30, anchor='c')
    tree.column("2", width=100, minwidth=30, anchor='c')
    tree.column("3", width=100, minwidth=30, anchor='c')
    tree.column("4", width=100, minwidth=30, anchor='c')
    tree.column("5", width=100, minwidth=30, anchor='c')
    tree.column("6", width=100, minwidth=30, anchor='c')
    tree.column("7", width=100, minwidth=30, anchor='c')
    tree.column("8", width=100, minwidth=30, anchor='c')

    tree.heading("1", text="Time")
    tree.heading("2", text="Line No")
    tree.heading("3", text="Sensor No")
    tree.heading("4", text="L1")
    tree.heading("5", text="L2")
    tree.heading("6", text="L3")
    tree.heading("7", text="EXT")
    tree.heading("8", text="OUT")
    tree.place()

    tree.tag_configure('high', foreground='red')
    tree.tag_configure('low', foreground='black')

    for y in range(32):
        print(sensArray[y].line_no)

    for l in range(16):
        if sensArray[l].L1 or sensArray[l].L2 or sensArray[l].L3 > 30.0:
            tree.insert(parent='', index='end', iid=l, text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sensArray[l].line_no, sensArray[l].sens_no,
                round(sensArray[l].L1, 4), round(sensArray[l].L2, 4), round(sensArray[l].L3, 4),
                round(float(sensArray[l].EXT), 4), round(float(sensArray[l].OUT), 4)),
                        tags=('high',))
        else:
            tree.insert(parent='', index='end', iid=l, text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sensArray[l].line_no, sensArray[l].sens_no,
                round(sensArray[l].L1, 4), round(sensArray[l].L2, 4), round(sensArray[l].L3, 4),
                round(float(sensArray[l].EXT), 4), round(float(sensArray[l].OUT), 4)),
                        tags=('low',))
    for l in range(16, 32):
        if sensArray[l].L1 or sensArray[l].L2 or sensArray[l].L3 > 30.0:
            tree.insert(parent='', index='end', iid=l, text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sensArray[l].line_no, (sensArray[l].sens_no - 16),
                round(sensArray[l].L1, 4), round(sensArray[l].L2, 4), round(sensArray[l].L3, 4),
                round(float(sensArray[l].EXT), 4), round(float(sensArray[l].OUT), 4)),
                        tags=('high',))
        else:
            tree.insert(parent='', index='end', iid=l, text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sensArray[l].line_no, (sensArray[l].sens_no - 16),
                round(sensArray[l].L1, 4), round(sensArray[l].L2, 4), round(sensArray[l].L3, 4),
                round(float(sensArray[l].EXT), 4), round(float(sensArray[l].OUT), 4)),
                        tags=('low',))

    def save_csv():
        with open("new.csv", "w", newline='') as myfile:
            csvwriter = csv.writer(myfile, delimiter=',')
            csvwriter.writerow(["Time", "Port No", "Sensor No", "L1", "L2", "L3", "EXT", "OUT"])
            for row_id in tree.get_children():
                row = tree.item(row_id)['values']
                print('save row:', row)
                csvwriter.writerow(row)

        df_new = pd.read_csv('new.csv')

        GFG = pd.ExcelWriter('table_excel_data.xlsx')
        df_new.to_excel(GFG, index=False)

        GFG.save()

    button_save = tk.Button(root, text='Save', command=save_csv)
    button_save.pack()

    tree.pack()
    mainloop()


if __name__ == '__main__':
    main()
