# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 07:46:27 2023

@author: Jiayuan Liu
"""

import tkinter as tk
import customtkinter as ctk
from Database import Database

class UI:
    
    def __init__(self, root):
        self.container = root

    def setup(self):
        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        self.content_frame = ctk.CTkFrame(self.container, width=1400, height=900)
        
        self.tab = ctk.CTkTabview(self.content_frame, anchor="nw")
        self.inventory_tab = self.tab.add("Inventory")
        self.purchase_tab = self.tab.add("Purchase History")
        self.outflow_tab = self.tab.add("Outflow History")
        
    def setup_layout(self):
        self.content_frame.grid(row=0, column=0, padx=20, pady=20)
        
        self.tab.pack()
        self.inventory_tab_view = Tab_UI(self.inventory_tab)
        self.inventory_tab_view.setup_tab()
        self.purchase_tab_view = Tab_UI(self.purchase_tab)
        self.purchase_tab_view.setup_tab()
        self.outflow_tab_view = Tab_UI(self.outflow_tab)
        self.outflow_tab_view.setup_tab()
        

class Tab_UI:
    
    def __init__(self, tab):
        self.tab_container = tab
        
    def setup_tab(self):
        self.create_tab_widgets()
        self.setup_tab_layout()
    
    def create_tab_widgets(self):
        self.menu_frame = ctk.CTkFrame(self.tab_container, width=1400, height=100)
        self.table_frame = ctk.CTkFrame(self.tab_container, width=1400, height=800)
        
        self.search_box = ctk.CTkEntry(self.menu_frame, width=500, placeholder_text="Search")
        self.search_button = ctk.CTkButton(self.menu_frame, text="Search")#, command=button_event)
        
        self.add_button = ctk.CTkButton(self.menu_frame, text="Add")#, command=button_event)
        self.edit_button = ctk.CTkButton(self.menu_frame, text="Edit")#, command=button_event)
        self.outflow_button = ctk.CTkButton(self.menu_frame, text="Outflow")#, command=button_event)
        
        self.table = Database(self.table_frame)
        
        
        
    def setup_tab_layout(self):
        self.menu_frame.grid(row=0, column=0, padx=10, pady=10)
        self.table_frame.grid(row=1, column=0, padx=10, pady=10)
        
        self.search_box.grid(row=0, column=0, padx=5, pady=5)
        self.search_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.add_button.grid(row=0, column=4, padx=5, pady=5)
        self.edit_button.grid(row=0, column=5, padx=5, pady=5)
        self.outflow_button.grid(row=0, column=6, padx=5, pady=5)
