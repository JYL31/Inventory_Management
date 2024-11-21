# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 07:46:27 2023

@author: Jiayuan Liu
"""

import tkinter as tk
import customtkinter as ctk
from Database import Database
from Buttons import add_data, outflow, search, clear, export, delete
from functools import partial

class UI:
    """Object of UI setup
    """    
    def __init__(self, root):
        """initialize UI object

        Args:
            root (tkinter object): root window
        """        
        self.container = root

    def setup(self):
        """function to setup GUI layout
        """        
        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """function to create tkinter widgets in GUI layout
        """        
        self.search_frame = ctk.CTkFrame(self.container, width=1300, height=120) # frames
        self.tap_frame = ctk.CTkFrame(self.container, width=1300, height=700)
        self.button_frame = ctk.CTkFrame(self.container, width=170, height=800)
        self.verbose_frame = ctk.CTkFrame(self.container, width=1400, height=40)
        
        self.tab = ctk.CTkTabview(self.tap_frame, anchor="nw", corner_radius=15) # tabs for tables
        self.tab._segmented_button.configure(border_width=5, corner_radius=15, font=(None, 16, 'bold'))
        self.inventory_tab = self.tab.add("Inventory")
        self.purchase_tab = self.tab.add("Purchase History")
        self.outflow_tab = self.tab.add("Outflow History")
        
        self.verbose = ctk.CTkLabel(self.verbose_frame, text='', font=('None', 14, 'bold')) # label to display program status
        
        self.tab.pack()
        self.tab.pack_propagate(False)
        self.inventory_tab_view = Tab_UI(self.inventory_tab)
        self.inventory_tab_view.setup_tab("inv", self.verbose)
        self.purchase_tab_view = Tab_UI(self.purchase_tab)
        self.purchase_tab_view.setup_tab("pur", self.verbose)
        self.outflow_tab_view = Tab_UI(self.outflow_tab)
        self.outflow_tab_view.setup_tab("out", self.verbose)
        
        self.inventory_table = self.inventory_tab_view.get_table()
        self.purchase_table = self.purchase_tab_view.get_table()
        self.outflow_table = self.outflow_tab_view.get_table()
        
        self.search_box = ctk.CTkEntry(self.search_frame, width=400, placeholder_text="Search") # buttons, entries, etc
        
        type_var = tk.StringVar(value='All')
        self.radio1 = ctk.CTkRadioButton(self.search_frame, text="Bearing", variable=type_var, value='Bearing')
        self.radio2 = ctk.CTkRadioButton(self.search_frame, text="Consumables", variable=type_var, value="Consumables")
        self.radio3 = ctk.CTkRadioButton(self.search_frame, text="Electronics", variable=type_var, value="Electronics")
        self.radio4 = ctk.CTkRadioButton(self.search_frame, text="Lubricant", variable=type_var, value="Lubricant")
        self.radio5 = ctk.CTkRadioButton(self.search_frame, text="Miscellaneous", variable=type_var, value="Miscellaneous")
        self.radio6 = ctk.CTkRadioButton(self.search_frame, text="Pneumatics", variable=type_var, value="Pneumatics")
        self.radio7 = ctk.CTkRadioButton(self.search_frame, text="Tools", variable=type_var, value="Tools")
        
        stock_var = tk.IntVar(value=0)
        self.radio8 = ctk.CTkRadioButton(self.search_frame, text="In Stock", variable=stock_var, value=1)
        self.radio9 = ctk.CTkRadioButton(self.search_frame, text="Out of Stock", variable=stock_var, value=2)
        
        search_args = [self.search_box, type_var, stock_var, self.inventory_table, self.purchase_table, self.outflow_table, self.verbose]
        
        self.search_button = ctk.CTkButton(self.search_frame, text="Search",command=partial(search, search_args))
        
        self.clear_button = ctk.CTkButton(self.search_frame, text="Clear", command=partial(clear, search_args))
        
        args = [self.container, self.inventory_table, self.purchase_table, self.outflow_table, self.verbose]
        
        args1 = [self.inventory_table, self.purchase_table, self.outflow_table, self.tab, self.verbose]
        
        self.add_button = ctk.CTkButton(self.button_frame, text="Add", font=('None', 14), command=partial(add_data, args))
        self.outflow_button = ctk.CTkButton(self.button_frame, text="Outflow", font=('None', 14), command=partial(outflow, args))
        self.export_button = ctk.CTkButton(self.button_frame, text="Export to Excel", font=('None', 14), command=partial(export, self.verbose))
        self.delete_button = ctk.CTkButton(self.button_frame, text="Delete Entry", font=('None', 14), command=partial(delete, args1))
        
        self.title = ctk.CTkLabel(self.button_frame, text="ANMA Inventory Management", font=('None', 30, 'bold'), wraplength=200)
        
    def setup_layout(self):
        """function to position tkinter widgets
        """        
        self.search_frame.grid(row=0, column=1, padx=20, pady=10)
        self.tap_frame.grid(row=1, column=1, padx=20, pady=10)
        self.button_frame.grid(row=0, column=0, padx=20, pady=10, rowspan=2)
        self.verbose_frame.grid(row=2, column=0, padx=20, pady=10, columnspan=2)
        
        self.search_frame.grid_propagate(False)
        self.tap_frame.grid_propagate(False)
        self.button_frame.grid_propagate(False)
        self.verbose_frame.grid_propagate(False)
        
        self.verbose.grid(row=0, column=0, padx=5, pady=5)
        
        self.search_box.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
        self.search_button.grid(row=0, column=3, padx=5, pady=5)
        self.clear_button.grid(row=0, column=4, padx=5, pady=5)
        self.radio1.grid(row=1, column=0, padx=10, pady=5)
        self.radio2.grid(row=1, column=1, padx=10, pady=5)
        self.radio3.grid(row=1, column=2, padx=10, pady=5)
        self.radio4.grid(row=1, column=3, padx=10, pady=5)
        self.radio5.grid(row=1, column=4, padx=10, pady=10)
        self.radio6.grid(row=1, column=5, padx=10, pady=10)
        self.radio7.grid(row=1, column=6, padx=10, pady=10)
        self.radio8.grid(row=2, column=0, padx=10, pady=10)
        self.radio9.grid(row=2, column=1, padx=10, pady=10)
        
        self.title.grid(row=0, column=0, padx=5, pady=5)
        
        self.button_frame.rowconfigure(1, minsize=150)

        self.add_button.grid(row=2, column=0, padx=5, pady=20)
        self.outflow_button.grid(row=3, column=0, padx=5, pady=20)
        self.export_button.grid(row=4, column=0, padx=5, pady=20)
        self.delete_button.grid(row=5, column=0, padx=5, pady=20)

class Tab_UI:
    """Object for each tab
    """    
    def __init__(self, tab):
        """initialize a tab object

        Args:
            tab (tkinter tabview): tabview window
        """        
        self.tab_container = tab
        
    def setup_tab(self, tab_name, verbose):
        """function to setup tabview layout

        Args:
            tab_name (str): string to specifify which tab
            verbose (tkinter label): label to display program status
        """        
        self.create_tab_widgets()
        self.setup_tab_layout()
        
        self.table_setup = Database(verbose)
        self.table_setup.setup_table(self.table_frame, tab_name)
        self.table = self.table_setup.get_table()
    
    def create_tab_widgets(self):
        """function to create widgets in tabview
        """        
        self.table_frame = ctk.CTkFrame(self.tab_container, width=1300, height=600)
        
    def setup_tab_layout(self):
        """function to position widgets in tabview
        """        
        self.table_frame.pack()
        self.table_frame.pack_propagate(False)
    
    def get_table(self):
        """function to return database object

        Returns:
            Database object: table to display database content
        """        
        return self.table
        