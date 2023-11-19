# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 09:54:56 2023

@author: Jiayuan Liu
"""

import tkinter as tk
import customtkinter as ctk
import sqlite3 as sql

class Database:
    
    def __init__(self, frame):

        self.scrolly = tk.Scrollbar(frame, orient="vertical")
        self.scrollx = tk.Scrollbar(frame, orient="horizontal")
        self.scrollx.pack(side="bottom", fill="x") 
        self.scrolly.pack(side="right", fill="y")
        
        self.table = tk.ttk.Treeview(frame, yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set, selectmode="extended")
        self.table.pack()
        
        self.scrollx.config(command=self.table.xview)
        self.scrolly.config(command=self.table.yview)
        
        self.setup_table()
        self.read_database()
        
    def setup_table(self):
        self.table['column'] = ["Name", "Specification", "Type", "Quantity", "Last Update"]
        self.table.column("#0", width=0, stretch="NO")
        self.table.column("Name", anchor="w", width=200)
        self.table.column("Specification", anchor="w", width=200)
        self.table.column("Type", anchor="w", width=200)
        self.table.column("Quantity", anchor="center", width=200)
        self.table.column("Last Update", anchor="center", width=200)
        
        self.table.heading("#0", text="", anchor="w")
        self.table.heading("Name", text="Name", anchor="w")
        self.table.heading("Specification", text="Specification", anchor="w")
        self.table.heading("Type", text="Type", anchor="w")
        self.table.heading("Quantity", text="Quantity", anchor="center")
        self.table.heading("Last Update", text="Last Update", anchor="center")
    
    def read_database(self):
        self.database = sql.connect("Inventory.db")
        self.db_cursor = self.database.cursor()
        
        self.db_cursor.execute("SELECT * FROM Inventory")
        data = self.db_cursor.fetchall()
        
        for record in data:
            self.table.insert("", index="end", values=record)
        