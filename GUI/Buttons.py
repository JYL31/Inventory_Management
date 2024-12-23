# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 09:15:27 2023

@author: Jiayuan Liu
"""
import tkinter as tk
import customtkinter as ctk
import sqlite3 as sql
from datetime import date
import pandas as pd
import os
    
def add_data(args):
    """function to add item to database

    Args:
        args (list): list of arguments:
            args[0] (tkinter frame object)
            args[1] (database object of inventory table)
            args[2] (database object of purchase table)
            args[4] (tkinter label object)
    """    
    window = args[0]
    main_verbose = args[-1]
    inventory_table = args[1]
    purchase_table = args[2]
        
    def submit():
        """function to update the item to database
        """        
        database = sql.connect("Inventory.db")
        db_cursor = database.cursor()
        
        widgets = add_form.winfo_children() # get entry values
        raw = []
        for i in widgets:
            if isinstance(i, ctk.CTkEntry) or isinstance(i, ctk.CTkOptionMenu):
                raw.append(i.get())
        
        entries = [i if i != '' else None for i in raw] # error checking
        if entries[0] == None or entries[5] == None:
            verbose_label.configure(text='Field with * cannot be null.')
            main_verbose.configure(text='Field with * cannot be null.', text_color='red')
            database.close()
            return
        try:
            int(entries[5])
        except:
            verbose_label.configure(text='Quantity has to be an integer.')
            main_verbose.configure(text='Quantity has to be an integer.', text_color='red')
            database.close()
            return
        
        if entries[2] == 'Select a Type':
            verbose_label.configure(text='Type has not been selected.')
            main_verbose.configure(text='Type has not been selected.', text_color='red')
            database.close()
            return
        
        if entries[6] != None:
            try:
                float(entries[6])
            except:
                verbose_label.configure(text='Unit Price has to be a number.')
                main_verbose.configure(text='Unit Price has to be a number.', text_color='red')
                database.close()
                return
                
        if entries[7] != None:
            try:
                float(entries[7])
            except:
                verbose_label.configure(text='Shipping has to be a number.')
                main_verbose.configure(text='Shipping has to be a number.', text_color='red')
                database.close()
                return
        
        entries = [i if i != None else '' for i in entries]
        
        # sql statement to update database
        insert_inv_sql = """INSERT INTO Inventory(Name, Specification, Type, Usage, Quantity, "Last Update") 
                        VALUES(?, ?, ?, ?, COALESCE((SELECT Quantity FROM Inventory WHERE Name=? AND Specification=?), 0) + ?, ?)
                        ON CONFLICT("Name", "Specification") DO UPDATE SET "Quantity" = excluded.Quantity, "Last Update" = ?
                        RETURNING *;"""
        
        insert_order_sql = """INSERT INTO "Purchase History"(Name, Specification, Type, Usage, Supplier, Quantity, "Unit Price", Shipping, "Total Price", "Received Date", "Applied By", "Responsible By") 
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        RETURNING *;"""               
        
        today = date.today()
        inv_data = [entries[0], entries[1], entries[2], entries[3], entries[0], entries[1], entries[5], str(today), str(today)]
        raw_updated_data = db_cursor.execute(insert_inv_sql, inv_data)
        raw_updated_data = list(raw_updated_data)
        updated_data = [str(i or '') if i!=0 else str(i) for i in raw_updated_data[0]] # update table content after executing sql
        updated_data[0] = int(updated_data[0])

        if updated_data[0] > len(inventory_table.get_children()):
            inventory_table.insert("", index="end", iid=updated_data[0], values=updated_data)
        else:
            inventory_table.item(updated_data[0], values=updated_data)
        
        database.commit()
        
        order_data = entries
        if entries[6] != '':
            if entries[7] != '':
                order_data.insert(8, float(entries[5])*float(entries[6])+float(entries[7]))
            else:
                entries[7] = None
                order_data.insert(8, float(entries[5])*float(entries[6]))
        else:
            entries[6] = None
            entries[7] = None
            order_data.insert(8, None)
        raw_order_table_data = db_cursor.execute(insert_order_sql, order_data)
        raw_order_table_data = list(raw_order_table_data)
        order_table_data = [str(i or '') if i!=0 else str(i) for i in raw_order_table_data[0]] # update table content after executing sql
        order_table_data[0] = int(order_table_data[0])
        purchase_table.insert("", index="end", iid=order_table_data[0], values=order_table_data)
        
        database.commit()
        
        database.close()
        
        main_verbose.configure(text='Record Updated.', text_color='green')
        
        add_form.destroy()
        
    # entry form to enter values for new item
    add_form = ctk.CTkToplevel(window)
    add_form.attributes('-topmost', True)
    add_form.geometry("320x500+500+300")
    add_form.resizable(0, 0)
    
    verbose_label = ctk.CTkLabel(add_form, text="", text_color='red')
    verbose_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
    
    name_label = ctk.CTkLabel(add_form, text="*Name")
    name_label.grid(row=1, column=0, padx=5, pady=5)
    name_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    name_entry.grid(row=1, column=1, padx=5, pady=5)
        
    spec_label = ctk.CTkLabel(add_form, text="Specification")
    spec_label.grid(row=2, column=0, padx=5, pady=5)
    spec_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    spec_entry.grid(row=2, column=1, padx=5, pady=5)
    
    type_label = ctk.CTkLabel(add_form, text="Type")
    type_label.grid(row=3, column=0, padx=5, pady=5)
    type_var = ctk.StringVar(value="Select a Type")
    type_entry = ctk.CTkOptionMenu(add_form, width=200, values=["Bearing", "Consumables","Electronics","Lubricant","Miscellaneous","Pneumatics","Tools"], variable=type_var)
    type_entry.grid(row=3, column=1, padx=5, pady=5)
    
    use_label = ctk.CTkLabel(add_form, text="Usage")
    use_label.grid(row=4, column=0, padx=5, pady=5)
    use_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    use_entry.grid(row=4, column=1, padx=5, pady=5)
        
    supplier_label = ctk.CTkLabel(add_form, text="Supplier")
    supplier_label.grid(row=5, column=0, padx=5, pady=5)
    supplier_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    supplier_entry.grid(row=5, column=1, padx=5, pady=5)
        
    num_label = ctk.CTkLabel(add_form, text="*Quantity")
    num_label.grid(row=6, column=0, padx=5, pady=5)
    num_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    num_entry.grid(row=6, column=1, padx=5, pady=5)
        
    unit_label = ctk.CTkLabel(add_form, text="Unit Price")
    unit_label.grid(row=7, column=0, padx=5, pady=5)
    unit_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    unit_entry.grid(row=7, column=1, padx=5, pady=5)
        
    ship_label = ctk.CTkLabel(add_form, text="Shipping")
    ship_label.grid(row=8, column=0, padx=5, pady=5)
    ship_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    ship_entry.grid(row=8, column=1, padx=5, pady=5)
        
    rec_label = ctk.CTkLabel(add_form, text="Received Date")
    rec_label.grid(row=9, column=0, padx=5, pady=5)
    rec_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    rec_entry.grid(row=9, column=1, padx=5, pady=5)
        
    applied_label = ctk.CTkLabel(add_form, text="Applied By")
    applied_label.grid(row=10, column=0, padx=5, pady=5)
    applied_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    applied_entry.grid(row=10, column=1, padx=5, pady=5)
        
    resp_label = ctk.CTkLabel(add_form, text="Responsible By")
    resp_label.grid(row=11, column=0, padx=5, pady=5)
    resp_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    resp_entry.grid(row=11, column=1, padx=5, pady=5)
        
    submit_button = ctk.CTkButton(add_form, text="Submit", command=submit)
    submit_button.grid(row=12, column=1, padx=5, pady=5)
    
    
def outflow(args):
    """function to remove item to database

    Args:
        args (list): list of arguments:
            args[0] (tkinter frame object)
            args[1] (database object of inventory table)
            args[3] (database object of outflow table)
            args[4] (tkinter label object)
    """    
    window = args[0]
    main_verbose = args[-1]
    inventory_table = args[1]
    outflow_table = args[3]
        
    def submit():
        """function to update the item to database
        """ 
        database = sql.connect("Inventory.db")
        db_cursor = database.cursor()
        
        widgets = add_form.winfo_children() # get entry values
        raw = []
        for i in widgets:
            if isinstance(i, ctk.CTkEntry) or isinstance(i, ctk.CTkOptionMenu):
                raw.append(i.get())
        
        entries = [i if i != '' else None for i in raw]
        if entries[0] == None or entries[3] == None: # error checking
            verbose_label.configure(text='Field with * cannot be null.')
            main_verbose.configure(text='Field with * cannot be null.', text_color='red')
            database.close()
            return
        try:
            int(entries[3])
        except:
            verbose_label.configure(text='Quantity has to be an integer.')
            main_verbose.configure(text='Quantity has to be an integer.', text_color='red')
            database.close()
            return
        
        if entries[2] == 'Select a Type':
            verbose_label.configure(text='Type has not been selected.')
            main_verbose.configure(text='Type has not been selected.', text_color='red')
            database.close()
            return
        
        entries = [i if i != None else '' for i in entries]
        
        # sql statement to update database
        check_sql = """SELECT COUNT(*) FROM Inventory WHERE Name = '{}' AND Specification = '{}'""".format(entries[0], entries[1])
        db_cursor.execute(check_sql)
        count = db_cursor.fetchone()
        if count == None:
            verbose_label.configure(text='No such item in inventory.')
            main_verbose.configure(text='No such item in inventory.', text_color='red')
            database.close()
            return
        
        insert_inv_sql = """INSERT INTO Inventory(Name, Specification, Quantity, "Last Update") 
                        VALUES(?, ?, COALESCE((SELECT Quantity FROM Inventory WHERE Name=? AND Specification=?), 0) - ?, ?)
                        ON CONFLICT("Name", "Specification") DO UPDATE SET "Quantity" = excluded.Quantity, "Last Update" = ?
                        RETURNING *;"""
        
        insert_out_sql = """INSERT INTO "Outflow History"(Name, Specification, Type, Quantity, Description, Date) 
                        VALUES(?, ?, ?, ?, ?, ?)
                        RETURNING *;"""               
        
        today = date.today()
        inv_data = [entries[0], entries[1], entries[0], entries[1], int(entries[3]), str(today), str(today)]
        raw_updated_data = db_cursor.execute(insert_inv_sql, inv_data)
        raw_updated_data = list(raw_updated_data)
        updated_data = [str(i or '') if i!=0 else str(i) for i in raw_updated_data[0]] # update table content after executing sql
        updated_data[0] = int(updated_data[0])
        
        if updated_data[0] > len(inventory_table.get_children()):
            inventory_table.insert("", index="end", iid=updated_data[0], values=updated_data)
        else:
            inventory_table.item(updated_data[0], values=updated_data)
        
        database.commit()
        
        out_data = entries
        raw_out_table_data = db_cursor.execute(insert_out_sql, out_data)
        raw_out_table_data = list(raw_out_table_data)
        out_table_data = [str(i or '') if i!=0 else str(i) for i in raw_out_table_data[0]] # update table content after executing sql
        out_table_data[0] = int(out_table_data[0])
        outflow_table.insert("", index="end", iid=out_table_data[0], values=out_table_data)
        
        database.commit()
        
        database.close()
        
        main_verbose.configure(text='Record Updated.', text_color='green')
        
        add_form.destroy()
        
    # entry form to enter values for new item
    add_form = ctk.CTkToplevel(window)
    add_form.attributes('-topmost', True)
    add_form.geometry("400x500+500+300")
    add_form.resizable(0, 0)
    
    verbose_label = ctk.CTkLabel(add_form, text="", text_color='red')
    verbose_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
    
    name_label = ctk.CTkLabel(add_form, text="*Name")
    name_label.grid(row=1, column=0, padx=5, pady=5)
    name_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    name_entry.grid(row=1, column=1, padx=5, pady=5)
        
    spec_label = ctk.CTkLabel(add_form, text="Specification")
    spec_label.grid(row=2, column=0, padx=5, pady=5)
    spec_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    spec_entry.grid(row=2, column=1, padx=5, pady=5)
    
    type_label = ctk.CTkLabel(add_form, text="Type")
    type_label.grid(row=3, column=0, padx=5, pady=5)
    type_var = ctk.StringVar(value="Select a Type")
    type_entry = ctk.CTkOptionMenu(add_form, width=200, values=["Bearing", "Consumables","Electronics","Lubricant","Miscellaneous","Pneumatics","Tools"], variable=type_var)
    type_entry.grid(row=3, column=1, padx=5, pady=5)
        
    num_label = ctk.CTkLabel(add_form, text="*Quantity")
    num_label.grid(row=4, column=0, padx=5, pady=5)
    num_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    num_entry.grid(row=4, column=1, padx=5, pady=5)
        
    des_label = ctk.CTkLabel(add_form, text="Description")
    des_label.grid(row=5, column=0, padx=5, pady=5)
    des_entry = ctk.CTkEntry(add_form, width=200, height=200, placeholder_text="")
    des_entry.grid(row=5, column=1, padx=5, pady=5)
        
    date_label = ctk.CTkLabel(add_form, text="Date")
    date_label.grid(row=6, column=0, padx=5, pady=5)
    date_entry = ctk.CTkEntry(add_form, width=200, placeholder_text="")
    date_entry.grid(row=6, column=1, padx=5, pady=5)
        
    submit_button = ctk.CTkButton(add_form, text="Submit", command=submit)
    submit_button.grid(row=7, column=1, padx=5, pady=5)
    
    
def search(args):
    """function to search items in database

    Args:
        args (list): list of arguments:
            args[0] (tkinter entry box object)
            args[1] (database object of inventory table)
            args[2] (database object of purchase table)
            args[3] (database object of outflow table)
            args[4] (tkinter label object)
    """    
    entry = args[0]
    type = args[1]
    stock = args[2]
    inventory_table = args[3]
    purchase_table = args[4]
    outflow_table = args[5]
    main_verbose = args[6]
    
    inventory_table.delete(*inventory_table.get_children()) # clear table content
    purchase_table.delete(*purchase_table.get_children())
    outflow_table.delete(*outflow_table.get_children())
    
    entry_value = entry.get()
    type_value = type.get()
    stock_value = stock.get()

    # fetch items in database that matches searched name/specification
    if type_value == 'All' and stock_value == 0:
        search_inv_sql = """SELECT * FROM Inventory
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)

        search_pur_sql = """SELECT * FROM 'Purchase History'
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM 'Outflow History' 
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(entry_value, entry_value)
    
    elif type_value == 'All' and stock_value == 1:
        search_inv_sql = """SELECT * FROM (SELECT * FROM Inventory WHERE Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)

        search_pur_sql = """SELECT * FROM (SELECT * FROM 'Purchase History' WHERE Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM (SELECT * FROM 'Outflow History' WHERE Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(entry_value, entry_value)                    
    
    elif type_value == 'All' and stock_value == 2:
        search_inv_sql = """SELECT * FROM (SELECT * FROM Inventory WHERE Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)

        search_pur_sql = """SELECT * FROM (SELECT * FROM 'Purchase History' WHERE Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM (SELECT * FROM 'Outflow History' WHERE Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(entry_value, entry_value) 
    
    elif type_value != 'All' and stock_value == 0:
        search_inv_sql = """SELECT * FROM (SELECT * FROM Inventory WHERE Type = '{}')
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_pur_sql = """SELECT * FROM (SELECT * FROM 'Purchase History' WHERE Type = '{}')
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM (SELECT * FROM 'Outflow History' WHERE Type = '{}')
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(type_value, entry_value, entry_value)
    
    elif type_value != 'All' and stock_value == 1:
        search_inv_sql = """SELECT * FROM (SELECT * FROM Inventory WHERE Type = '{}' AND Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_pur_sql = """SELECT * FROM (SELECT * FROM 'Purchase History' WHERE Type = '{}' AND Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM (SELECT * FROM 'Outflow History' WHERE Type = '{}' AND Quantity >= 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(type_value, entry_value, entry_value)
    
    elif type_value != 'All' and stock_value == 2:
        search_inv_sql = """SELECT * FROM (SELECT * FROM Inventory WHERE Type = '{}' AND Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_pur_sql = """SELECT * FROM (SELECT * FROM 'Purchase History' WHERE Type = '{}' AND Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%' OR Usage Like '%{}%';""".format(type_value, entry_value, entry_value, entry_value)
        
        search_out_sql = """SELECT * FROM (SELECT * FROM 'Outflow History' WHERE Type = '{}' AND Quantity < 1)
                        WHERE Name LIKE '%{}%' OR Specification LIKE '%{}%';""".format(type_value, entry_value, entry_value)                 
    
    database = sql.connect("Inventory.db")
    db_cursor = database.cursor()
    
    db_cursor.execute(search_inv_sql)
    inv_data = db_cursor.fetchall()
    i=1
    for record in inv_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        inventory_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    db_cursor.execute(search_pur_sql)
    pur_data = db_cursor.fetchall()
    i=1
    for record in pur_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        purchase_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    db_cursor.execute(search_out_sql)
    out_data = db_cursor.fetchall()
    i=1
    for record in out_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        outflow_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    database.commit()
    
    main_verbose.configure(text='Database Filtered.', text_color='green')
    
    database.close()
    
def clear(args):
    """function to clear search results

    Args:
        args (list): list of arguments:
            args[0] (tkinter entry box object)
            args[1] (database object of inventory table)
            args[2] (database object of purchase table)
            args[3] (database object of outflow table)
            args[4] (tkinter label object)
    """   
    entry = args[0]
    main_verbose = args[-1]
    
    entry.delete(0, 'end')
    entry.insert(0, '')
    
    radio1 = args[1]
    radio1.set('All')
    radio2 = args[2]
    radio2.set(0)
    
    inventory_table = args[3]
    purchase_table = args[4]
    outflow_table = args[5]
    
    inventory_table.delete(*inventory_table.get_children()) # clear table content
    purchase_table.delete(*purchase_table.get_children())
    outflow_table.delete(*outflow_table.get_children())
    
    search_inv_sql = """SELECT * FROM Inventory""" # fetch all items from database
    
    search_pur_sql = """SELECT * FROM 'Purchase History'"""
    
    search_out_sql = """SELECT * FROM 'Outflow History'"""
                        
    database = sql.connect("Inventory.db")
    db_cursor = database.cursor()
    
    db_cursor.execute(search_inv_sql)
    inv_data = db_cursor.fetchall()
    i=1
    for record in inv_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        inventory_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    db_cursor.execute(search_pur_sql)
    pur_data = db_cursor.fetchall()
    i=1
    for record in pur_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        purchase_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    db_cursor.execute(search_out_sql)
    out_data = db_cursor.fetchall()
    i=1
    for record in out_data:
        record = [str(i or '') if i!=0 else str(i) for i in record]
        outflow_table.insert("", index="end", iid=i, values=record)
        i += 1
    
    database.commit()
    
    main_verbose.configure(text='Database Unfiltered.', text_color='green')
        
    database.close()


def export(verbose):
    """function to export database content to excel file

    Args:
        verbose (tkinter label object): label to display program status
    """
    file = tk.filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel file', '.xlsx')]) # ask for where to save file
    if not file:
        verbose.configure(text='No file was selected to export the database as excel.', text_color='red')
        return
    
    database = sql.connect('Inventory.db')
    if os.path.exists(file):
        os.chmod(file, 0o777) # grant access to write, read ...
    
    inv_df = pd.read_sql_query("SELECT * FROM Inventory", database) # get items from database to write to excel file
    order_df = pd.read_sql_query("SELECT * FROM 'Purchase History'", database)
    out_df = pd.read_sql_query("SELECT * FROM 'Outflow History'", database)
    
    with pd.ExcelWriter(file) as writer:  
        order_df.to_excel(writer, sheet_name='Purchase History', index=False)
        inv_df.to_excel(writer, sheet_name='Inventory', index=False)
        out_df.to_excel(writer, sheet_name='Outflow History', index=False)
    
    database.close()
    
    verbose.configure(text='File saved to {}'.format(file), text_color='green')
    
def delete(args):
    """function to delete item in database

    Args:
        args (list): list of arguments:
            args[0] (database object of inventory table)
            args[1] (database object of purchase table)
            args[2] (database object of outflow table)
            args[3] (tkinter tabview object)
            args[4] (tkinter label object)
    """  
    inventory_table = args[0]
    purchase_table = args[1]
    outflow_table = args[2]
    tab = args[3]
    verbose = args[4]
    tab_name = str(tab.focus_get())
    
    database = sql.connect("Inventory.db")
    db_cursor = database.cursor()
    
    if tab_name == str(inventory_table):
        iid = inventory_table.focus()
        database_ID = inventory_table.item(iid).get('values')[0]
        sql_statement = """DELETE FROM 'Inventory' WHERE ID = ?;"""
        
        db_cursor.execute(sql_statement, [database_ID])
        
        sql_statement = """UPDATE 'Inventory' SET ID = i.RowNum
                            FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY rowid) AS RowNum FROM 'Inventory') AS i
                            WHERE 'Inventory'.ID = i.ID"""
        
        db_cursor.execute(sql_statement)
        database.commit()
        
        inventory_table.delete(*inventory_table.get_children())
        db_cursor.execute("SELECT * FROM Inventory") 
        data = db_cursor.fetchall()
        
        i=1
        for record in data:
            record = [str(i or '') if i!=0 else str(i) for i in record]
            inventory_table.insert("", index="end", iid=i, values=record)
            i += 1
        
        database.close()
    elif tab_name == str(purchase_table):
        iid = purchase_table.focus()
        database_ID = purchase_table.item(iid).get('values')[0]
        check_sql = """SELECT COUNT(*) FROM (SELECT Name, Specification FROM 'Purchase History' WHERE ID = '{}' INTERSECT SELECT Name, Specification FROM Inventory);""".format(database_ID)
        db_cursor.execute(check_sql)
        count = db_cursor.fetchone()[0]
        if count != 0:
            sql_statement = """UPDATE Inventory SET Quantity = Inventory.Quantity - i.Quantity, "Last Update" = ?
                                FROM (SELECT * FROM 'Purchase History' WHERE ID = ?) AS i
                                WHERE Inventory.Name = i.Name AND Inventory.Specification = i.Specification
                                RETURNING *"""
            today = date.today()
            var = [str(today), database_ID]
            raw = db_cursor.execute(sql_statement, var)
            raw = list(raw)
            updated = [str(i or '') if i!=0 else str(i) for i in raw[0]]
            updated[0] = int(updated[0])
            inventory_table.item(updated[0], values=updated)
        
        sql_statement = """DELETE FROM 'Purchase History' WHERE ID = ?;"""
        
        db_cursor.execute(sql_statement, [database_ID])
        
        sql_statement = """UPDATE 'Purchase History' SET ID = i.RowNum
                            FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY rowid) AS RowNum FROM 'Purchase History') AS i
                            WHERE 'Purchase History'.ID = i.ID"""
        
        db_cursor.execute(sql_statement)
        database.commit()
        
        purchase_table.delete(*purchase_table.get_children())
        db_cursor.execute("SELECT * FROM 'Purchase History'") 
        data = db_cursor.fetchall()
        
        i=1
        for record in data:
            record = [str(i or '') if i!=0 else str(i) for i in record]
            purchase_table.insert("", index="end", iid=i, values=record)
            i += 1
        
        database.close()
    elif tab_name == str(outflow_table):
        iid = outflow_table.focus()
        database_ID = outflow_table.item(iid).get('values')[0]
        
        check_sql = """SELECT COUNT(*) FROM (SELECT Name, Specification FROM 'Outflow History' WHERE ID = '{}' INTERSECT SELECT Name, Specification FROM Inventory);""".format(database_ID)
        db_cursor.execute(check_sql)
        count = db_cursor.fetchone()[0]
        if count != 0:
            sql_statement = """UPDATE Inventory SET Quantity = Inventory.Quantity + i.Quantity, "Last Update" = ?
                                FROM (SELECT * FROM 'Outflow History' WHERE ID = ?) AS i
                                WHERE Inventory.Name = i.Name AND Inventory.Specification = i.Specification
                                RETURNING *"""
            today = date.today()
            var = [str(today), database_ID]
            raw = db_cursor.execute(sql_statement, var)
            raw = list(raw)
            updated = [str(i or '') if i!=0 else str(i) for i in raw[0]]
            updated[0] = int(updated[0])
            inventory_table.item(updated[0], values=updated)
        
        sql_statement = """DELETE FROM 'Outflow History' WHERE ID = ?;"""
        
        db_cursor.execute(sql_statement, [database_ID])
        
        sql_statement = """UPDATE 'Outflow History' SET ID = i.RowNum
                            FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY rowid) AS RowNum FROM 'Outflow History') AS i
                            WHERE 'Outflow History'.ID = i.ID"""
        
        db_cursor.execute(sql_statement)
        database.commit()
        
        outflow_table.delete(*outflow_table.get_children())
        db_cursor.execute("SELECT * FROM 'Outflow History'") 
        data = db_cursor.fetchall()
        
        i=1
        for record in data:
            record = [str(i or '') if i!=0 else str(i) for i in record]
            outflow_table.insert("", index="end", iid=i, values=record)
            i += 1
        
        database.close()
    
    verbose.configure(text='Entry Deleted.', text_color='green')