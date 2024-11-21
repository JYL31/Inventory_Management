# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 07:42:47 2023

@author: Jiayuan Liu
"""

import customtkinter as ctk
from UI import UI

if __name__ == '__main__':
    
    ctk.set_appearance_mode("Dark") #set GUI theme
    ctk.set_default_color_theme("blue")    
    
    root = ctk.CTk() #create GUI object
    root.title("ANMA Inventory Management System")
    root.geometry("1600x900+100+100") #set window size
    root.resizable(0, 0) #window not resizable
    
    app = UI(root)
    app.setup()
    
    root.mainloop()