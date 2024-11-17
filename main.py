# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
import database

if __name__ == '__main__':
    # Inicializa o banco de dados
    database.setup_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())