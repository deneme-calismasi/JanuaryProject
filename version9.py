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

root = tk.Tk()


def window_unit():
    root.title("Sensor's Temperatures °C")
    root.geometry("850x650")
    root.grid()


class EaeSens:

    def __init__(self, line_1, line_2, line_3, ext, out, line_no, sens_no):
        self.line_1 = line_1
        self.line_2 = line_2
        self.line_3 = line_3
        self.ext = ext
        self.out = out
        self.line_no = line_no
        self.sens_no = sens_no


sens_array = numpy.ndarray((32,), dtype=EaeSens)

for i in range(0, 16):
    sens_array[i] = EaeSens(0.0, 0.0, 0.0, 0, 0, 110, i + 1)

for a in range(16, 32):
    sens_array[a] = EaeSens(0.0, 0.0, 0.0, 0, 0, 400, a + 1)


class ModBus:

    def __init__(self, sensor_type_no, line_no, sensor_min_num, sensor_max_num):

        self.sensor_min_num = sensor_min_num
        self.sensor_max_num = sensor_max_num
        self.line_no = line_no
        self.sensor_type_no = sensor_type_no
        self.result_list = []
        self.final_result_list = []
        self.reg_no_list = []
        self.reg_list = list(range(self.sensor_min_num, self.sensor_max_num + 1))
        self.style = ttk.Style()
        self.style.map("Treeview", foreground=self.fixed_map("foreground"), background=self.fixed_map("background"))
        self.port_no = None
        self.data_as_float = None
        self.regs_count = None
        self.arr = None
        self.head_text = None
        self.tree = None

    def fixed_map(self, option):
        return [elm for elm in self.style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    def connect_modbus(self):

        for inc in self.reg_list:
            group_no = math.floor(((self.line_no - 1) / 256)) + 1
            self.port_no = 10000 + (self.sensor_type_no - 1) * 10 + group_no - 1
            reg_no = (((self.line_no - 1) * 128 + (int(inc) - 1)) * 2) % 65536
            self.reg_no_list.append(reg_no)
            print("group_no", group_no)
            print("portNo", self.port_no)
            print("reg_no", reg_no)

        for x in self.reg_no_list:
            sensor_no = ModbusClient(host="192.40.50.107", port=self.port_no, unit_id=1, auto_open=True)
            sensor_no.open()
            regs = sensor_no.read_holding_registers(x, 2)
            if regs:
                print(regs)
            else:
                print("read error")

            regs[0], regs[1] = regs[1], regs[0]
            data_bytes = np.array(regs, dtype=np.uint16)
            result = data_bytes.view(dtype=np.float32)
            self.result_list.append(result[0])

        print("REG_LIST", self.reg_list)
        self.data_as_float = self.result_list
        print("Result_Temp", self.result_list)
        self.final_result_list = self.result_list
        self.reg_no_list = []
        self.result_list = []
        return self.data_as_float

    def list_to_dict(self):
        self.connect_modbus()
        self.regs_count = len(self.reg_list)

        value = [[num for num in range(1, 1 + self.regs_count)], self.reg_list, self.data_as_float]

        data = np.array(value).T.tolist()

        products = data
        self.arr = []
        for product in products:
            vals = {"Sensor Type No": str(int(self.sensor_type_no)), "Line No": str(int(self.line_no)),
                    "Sensor No": str(int(product[1])), "Temp": str(round(product[2], 4)),
                    "Time": str(dt.datetime.now().strftime('%Y-%m-%d %X'))}
            self.arr.append(vals)
        return self.arr

    def record_mongo(self):
        lst = self.list_to_dict()
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["Modbus_Database"]
        mycol = mydb["collection6"]

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

    @staticmethod
    def drag_start(event):
        widget = event.widget
        widget.startX = event.x
        widget.startY = event.y

    @staticmethod
    def drag_motion(event):
        widget = event.widget
        x = widget.winfo_x() - widget.startX + event.x
        y = widget.winfo_y() - widget.startY + event.y
        widget.place(x=x, y=y)

    def table_insert(self, x, y):

        if self.sensor_type_no == 1:
            self.head_text = "L1"
        elif self.sensor_type_no == 2:
            self.head_text = "L2"
        elif self.sensor_type_no == 3:
            self.head_text = "L3"
        elif self.sensor_type_no == 7:
            self.head_text = "OUT"
        elif self.sensor_type_no == 8:
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

        for record in self.record_mongo()[-self.regs_count:]:
            sensor_id = record[2]
            temperature = record[3]
            date_time = record[4]

            if float(temperature) > 30.0:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=str(start_range),
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('high',))
            else:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=str(start_range),
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('low',))

            start_range += 1
            id_count += 1

        self.tree.bind("<Button-1>", self.drag_start)
        self.tree.bind("<B1-Motion>", self.drag_motion)

        self.update_window_table()
        self.tree.after(20000, self.update_window_table)

    def update_window_table(self):

        for ite in self.tree.get_children():
            self.tree.delete(ite)

        start_range = 0
        id_count = 1

        for record in self.record_mongo()[-self.regs_count:]:
            sensor_id = record[2]
            temperature = record[3]
            date_time = record[4]

            if float(temperature) > 30.0:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=str(start_range),
                                 values=(str(self.head_text), str(date_time), int(sensor_id), float(temperature)),
                                 tags=('high',))

            else:
                self.tree.insert("", index='end', text="%s" % int(sensor_id), iid=str(start_range),
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
        if sens_array[count].line_no == 400:
            sens_array[count].line_1 = app1.final_result_list[count - 16]
            sens_array[count].line_2 = app2.final_result_list[count - 16]
            sens_array[count].line_3 = app3.final_result_list[count - 16]

        elif sens_array[count].line_no == 110:
            sens_array[count].ext = app4.final_result_list[count]
            sens_array[count].out = app5.final_result_list[count]

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
        print(sens_array[y].line_no)

    for num in range(16):
        if sens_array[num].line_1 or sens_array[num].line_2 or sens_array[num].line_3 > 30.0:
            tree.insert(parent='', index='end', iid=str(num), text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sens_array[num].line_no, sens_array[num].sens_no,
                round(sens_array[num].line_1, 4), round(sens_array[num].line_2, 4), round(sens_array[num].line_3, 4),
                round(float(sens_array[num].ext), 4), round(float(sens_array[num].out), 4)),
                        tags=('high',))
        else:
            tree.insert(parent='', index='end', iid=str(num), text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sens_array[num].line_no, sens_array[num].sens_no,
                round(sens_array[num].line_1, 4), round(sens_array[num].line_2, 4), round(sens_array[num].line_3, 4),
                round(float(sens_array[num].ext), 4), round(float(sens_array[num].out), 4)),
                        tags=('low',))
    for num in range(16, 32):
        if sens_array[num].line_1 or sens_array[num].line_2 or sens_array[num].line_3 > 30.0:
            tree.insert(parent='', index='end', iid=str(num), text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sens_array[num].line_no, (sens_array[num].sens_no - 16),
                round(sens_array[num].line_1, 4), round(sens_array[num].line_2, 4), round(sens_array[num].line_3, 4),
                round(float(sens_array[num].ext), 4), round(float(sens_array[num].out), 4)),
                        tags=('high',))
        else:
            tree.insert(parent='', index='end', iid=str(num), text='', values=(
                dt.datetime.now().strftime('%Y-%m-%d %X'), sens_array[num].line_no, (sens_array[num].sens_no - 16),
                round(sens_array[num].line_1, 4), round(sens_array[num].line_2, 4), round(sens_array[num].line_3, 4),
                round(float(sens_array[num].ext), 4), round(float(sens_array[num].out), 4)),
                        tags=('low',))

    def get_value_mongo():
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["Modbus_Database"]
        mycol = mydb["collection6"]
        mydoc_all = mycol.find()
        df = pd.DataFrame(list(mydoc_all))
        return df.to_csv("xyz.csv", sep=",")

    def save_csv():
        with open("new.csv", "w", newline='') as myfile:
            csvwriter = csv.writer(myfile, delimiter=',')
            csvwriter.writerow(["Time", "Port No", "Sensor No", "L1", "L2", "L3", "EXT", "OUT"])
            for row_id in tree.get_children():
                row = tree.item(row_id)['values']
                print('save row:', row)
                csvwriter.writerow(row)

        df_new = pd.read_csv('new.csv')

        table_datas = pd.ExcelWriter('table_excel_data.xlsx')
        df_new.to_excel(table_datas, index=False)

        table_datas.save()
        get_value_mongo()

    button_save = tk.Button(root, text='Save', command=save_csv)
    button_save.pack()

    tree.pack()
    mainloop()


if __name__ == '__main__':
    main()
