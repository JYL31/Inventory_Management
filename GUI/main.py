# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 07:42:47 2023

@author: Jiayuan Liu
"""

import sys

from PySide6.QtWidgets import QApplication

from inventory_app.main_window import InventoryWindow

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ANMA Inventory Management System")
    window = InventoryWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
