import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QListWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terraria Translation Tool")
        self.setGeometry(100, 100, 800, 600)

        # Структуры данных
        self.lines = []  # Список кортежей (тег, текст)
        self.groups = {}  # Ключ: имя группы, Значение: список индексов в self.lines
        self.groups_order = []  # Порядок появления групп
        self.current_file = None

        # Настройка интерфейса
        self.setup_ui()

    def setup_ui(self):
        # Панель меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        open_action = file_menu.addAction("&Open")
        open_action.triggered.connect(self.open_file)
        save_action = file_menu.addAction("&Save")
        save_action.triggered.connect(self.save_file)

        # Центральный виджет с разделителем
        splitter = QSplitter()

        # Список групп слева
        self.group_list = QListWidget()
        self.group_list.itemSelectionChanged.connect(self.update_table)

        # Таблица переводов справа
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["TAG", "LOCALIZATION"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellChanged.connect(self.on_cell_changed)

        splitter.addWidget(self.group_list)
        splitter.addWidget(self.table)
        splitter.setSizes([200, 600])

        self.setCentralWidget(splitter)

    def get_group_name(self, tag):
        """Извлечение имени группы из тега"""
        if '_' in tag:
            return tag.rsplit('_', 1)[0]
        return tag

    def open_file(self):
        """Открытие и разбор файла локализации"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt)")
        if not path:
            return

        self.current_file = path
        self.lines.clear()
        self.groups.clear()
        self.groups_order.clear()

        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue

                    tag, text = line.split('=', 1)
                    self.lines.append((tag, text))
                    group = self.get_group_name(tag)

                    if group not in self.groups:
                        self.groups_order.append(group)
                        self.groups[group] = []
                    self.groups[group].append(len(self.lines) - 1)

            self.group_list.clear()
            self.group_list.addItems(self.groups_order)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def update_table(self):
        """Обновление таблицы при изменении выбора группы"""
        self.table.blockSignals(True)
        self.table.clearContents()

        selected = self.group_list.currentItem()
        if not selected:
            return

        group = selected.text()
        indices = self.groups.get(group, [])

        self.table.setRowCount(len(indices))
        for row, idx in enumerate(indices):
            tag, text = self.lines[idx]

            # Столбец тега (не редактируется)
            tag_item = QTableWidgetItem(tag)
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Столбец текста (редактируется)
            text_item = QTableWidgetItem(text)
            text_item.setData(Qt.ItemDataRole.UserRole, idx)

            self.table.setItem(row, 0, tag_item)
            self.table.setItem(row, 1, text_item)

        self.table.blockSignals(False)

    def on_cell_changed(self, row, column):
        """Обработка редактирования текста в таблице"""
        if column != 1:
            return

        item = self.table.item(row, column)
        if not item:
            return

        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is None or idx >= len(self.lines):
            return

        new_text = item.text()
        old_tag, _ = self.lines[idx]
        self.lines[idx] = (old_tag, new_text)

    def save_file(self):
        """Сохранение изменений обратно в файл"""
        if not self.current_file:
            self.save_file_as()
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                for tag, text in self.lines:
                    f.write(f"{tag}={text}\n")
            QMessageBox.information(self, "Success", "File saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

    def save_file_as(self):
        """Сохранение в новый файл"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt)")
        if path:
            self.current_file = path
            self.save_file()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
