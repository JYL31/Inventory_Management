# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 07:42:47 2023

@author: Jiayuan Liu
"""

import customtkinter as ctk
from UI import UI

if __name__ == '__main__':
    
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")    
    
    root = ctk.CTk()
    root.title("ANMA Inventory Management System")
    root.maxsize(1500,  1000)
    root.resizable(0, 0)
    
    app = UI(root)
    app.setup()
    
    root.mainloop()