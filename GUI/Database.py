# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 09:54:56 2023

@author: Jiayuan Liu
"""

import tkinter as tk
import sqlite3 as sql
import customtkinter as ctk
from datetime import date

class Database:
    """Object to display database in tkinter treeview
    """
    def __init__(self, verbose):
        """Initialize class object

        Args:
            verbose (tkinter label object): label to display program status
        """
        self.verbose = verbose
        pass
    
    def on_double_click(self, event):
        """function for double click action

        Args:
            event (tkinter event): event recorded by tkinter widget
        """
        region = self.table.identify_region(event.x, event.y)
        if region != 'cell':
            return
        column = self.table.identify_column(event.x)
        column = int(column[1:]) - 1
        iid = self.table.focus()
        database_ID = self.table.item(iid).get('values')[0]
        selected = self.table.item(iid).get('values')[column]
        column_box = self.table.bbox(iid, column)
        entry = tk.ttk.Entry(self.frame)
        entry.place(x=column_box[0], y=column_box[1], w=column_box[2], h=column_box[3])
        entry.editing_column_index = column
        entry.editing_item_iid = iid
        
        entry.insert(0, selected)
        entry.select_range(0, tk.END)
        entry.focus()
        
        entry.bind("<FocusOut>", self.on_focus_out)
        entry.bind("<Return>", lambda event: self.on_enter_press(event, ID=database_ID))
    
    def on_enter_press(self, event, ID):
        """function when enter key is pressed

        Args:
            event (tkinter event): _description_
            ID (int): ID of item in database
        """        
        value = event.widget.get()
        if value == '':
            db_value = None
        else:
            db_value = value
        iid = event.widget.editing_item_iid
        column = event.widget.editing_column_index
        
        database = sql.connect("Inventory.db")
        db_cursor = database.cursor()
        
        heading = self.table.heading(column).get('text')
        
        today = str(date.today())
        
        if self.tab_name == "inv":
            sql_statement = """UPDATE Inventory SET '{}' = '{}', 'Last Update' = '{}' WHERE ID = {}""".format(heading, db_value, today, ID)
            try:
                db_cursor.execute(sql_statement)
            except sql.Error as er:
                txt = 'SQLite Error: %s' % (' '.join(er.args))
                self.verbose.configure(text=txt, text_color='red')
                database.close()
                return

        elif self.tab_name == "pur":
            sql_statement = """UPDATE 'Purchase History' SET '{}' = '{}' WHERE ID = {}""".format(heading, db_value, ID)
            try:
                db_cursor.execute(sql_statement)
            except sql.Error as er:
                txt = 'SQLite Error: %s' % (' '.join(er.args))
                self.verbose.configure(text=txt, text_color='red')
                database.close()
                return

        elif self.tab_name == "out":
            sql_statement = """UPDATE 'Outflow History' SET '{}' = '{}' WHERE ID = {}""".format(heading, db_value, ID)
            try:
                db_cursor.execute(sql_statement)
            except sql.Error as er:
                txt = 'SQLite Error: %s' % (' '.join(er.args))
                self.verbose.configure(text=txt, text_color='red')
                database.close()
                return
        
        new_values = self.table.item(iid).get('values')
        new_values[column] = value
        self.table.item(iid, values=new_values)
        
        database.commit()
        database.close()
        self.verbose.configure(text='Record Updated.', text_color='green')
        event.widget.destroy()
    
    def on_focus_out(self, event):
        """function when mouse move away from the widget

        Args:
            event (tkinter event): event recorded by tkinter widget
        """
        event.widget.destroy()
    
    def setup_table(self, frame, tab_name):
        """setup tkinter treeview layout

        Args:
            frame (tkinter frame object): frame UI
            tab_name (tkinter tabview object): tab UI
        """        
        self.frame = frame
        self.tab_name = tab_name
        
        self.scrolly = tk.Scrollbar(frame, orient="vertical")
        self.scrollx = tk.Scrollbar(frame, orient="horizontal")
        self.scrollx.pack(side="bottom", fill="x") 
        self.scrolly.pack(side="right", fill="y")
        
        self.scrollx.pack_propagate(False)
        self.scrolly.pack_propagate(False)
        
        self.table = tk.ttk.Treeview(frame, yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set, selectmode="browse")
        
        self.table.bind("<Double-1>", self.on_double_click)
        
        self.table.pack(fill='both', expand=True)
        self.table.pack_propagate(False)
        
        self.scrollx.config(command=self.table.xview)
        self.scrolly.config(command=self.table.yview)
        
        style = tk.ttk.Style()
        style.configure("Treeview.Heading", font=(None, 12, 'bold'))
        style.configure("Treeview", font=(None, 11))
        
        if tab_name == "inv":
            self.table['column'] = ["ID", "Name", "Specification", "Quantity", "Location", "Last Update"]
            self.table.column("#0", width=0, stretch=False)
            self.table.column("ID", anchor="center", width=50)
            self.table.column("Name", anchor="w", width=200)
            self.table.column("Specification", anchor="w", width=200)
            self.table.column("Quantity", anchor="center", width=100)
            self.table.column("Location", anchor="w", width=150)
            self.table.column("Last Update", anchor="center", width=150)
            
            self.table.heading("#0", text="", anchor="center")
            self.table.heading("ID", text="ID", anchor="center")
            self.table.heading("Name", text="Name", anchor="center")
            self.table.heading("Specification", text="Specification", anchor="center")
            self.table.heading("Quantity", text="Quantity", anchor="center")
            self.table.heading("Location", text="Location", anchor="center")
            self.table.heading("Last Update", text="Last Update", anchor="center")
        
        elif tab_name == "pur":
            self.table['column'] = ["ID", "Name", "Specification", "Supplier", "Quantity", "Unit Price", "Shipping", 
                                    "Total Price", "Received Date", "Applied By", "Responsible By"]
            self.table.column("#0", width=0, stretch=False)
            self.table.column("ID", anchor="center", width=50)
            self.table.column("Name", anchor="w", width=200)
            self.table.column("Specification", anchor="w", width=200)
            self.table.column("Supplier", anchor="w", width=150)
            self.table.column("Quantity", anchor="center", width=100)
            self.table.column("Unit Price", anchor="center", width=100)
            self.table.column("Shipping", anchor="center", width=100)
            self.table.column("Total Price", anchor="center", width=100)
            self.table.column("Received Date", anchor="center", width=150)
            self.table.column("Applied By", anchor="w", width=100)
            self.table.column("Responsible By", anchor="w", width=100)
            
            self.table.heading("#0", text="", anchor="center")
            self.table.heading("ID", text="ID", anchor="center")
            self.table.heading("Name", text="Name", anchor="center")
            self.table.heading("Specification", text="Specification", anchor="center")
            self.table.heading("Supplier", text="Supplier", anchor="center")
            self.table.heading("Quantity", text="Quantity", anchor="center")
            self.table.heading("Unit Price", text="Unit Price", anchor="center")
            self.table.heading("Shipping", text="Shipping", anchor="center")
            self.table.heading("Total Price", text="Total Price", anchor="center")
            self.table.heading("Received Date", text="Receieved Date", anchor="center")
            self.table.heading("Applied By", text="Applied By", anchor="center")
            self.table.heading("Responsible By", text="Responsible By", anchor="center")
            
        elif tab_name == "out":
            self.table['column'] = ["ID", "Name", "Specification", "Quantity", "Description", "Date"]
            self.table.column("#0", width=0, stretch=False)
            self.table.column("ID", anchor="center", width=50)
            self.table.column("Name", anchor="w", width=200)
            self.table.column("Specification", anchor="w", width=200)
            self.table.column("Quantity", anchor="center", width=150)
            self.table.column("Description", anchor="w", width=200)
            self.table.column("Date", anchor="center", width=150)
            
            self.table.heading("#0", text="", anchor="center")
            self.table.heading("ID", text="ID", anchor="center")
            self.table.heading("Name", text="Name", anchor="center")
            self.table.heading("Specification", text="Specification", anchor="center")
            self.table.heading("Quantity", text="Quantity", anchor="center")
            self.table.heading("Description", text="Description", anchor="center")
            self.table.heading("Date", text="Date", anchor="center")
        
        self.database = sql.connect("Inventory.db")
        self.db_cursor = self.database.cursor()
        self.read_database(tab_name)
    
    def read_database(self, tab_name):
        """function to display database items to tkinter treeview

        Args:
            tab_name (str): name to specify tabs corresponding to databases
        """        
        if tab_name == "inv":
            self.db_cursor.execute("SELECT * FROM Inventory")

        elif tab_name == "pur":
            self.db_cursor.execute("SELECT * FROM 'Purchase History'")

        elif tab_name == "out":
            self.db_cursor.execute("SELECT * FROM 'Outflow History'")
        
        data = self.db_cursor.fetchall()
        
        i=1
        for record in data:
            record = [str(i or '') if i!=0 else str(i) for i in record]
            self.table.insert("", index="end", iid=i, values=record)
            i += 1
        
        self.database.close()
    
    def get_table(self):
        """function to return tkinter treeview

        Returns:
            tkinter treeview: table to display database items
        """
        return self.table