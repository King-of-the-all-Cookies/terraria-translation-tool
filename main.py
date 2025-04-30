import re
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QListWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QMenuBar, QMenu, QMessageBox,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor


class SearchDialog(QDialog):
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout()
        self.label = QLabel(label)
        self.input = QLineEdit()
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
    
    def get_text(self):
        return self.input.text().strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terraria Translation Tool")
        self.setGeometry(100, 100, 800, 600)

        # Data structures
        self.lines = []  # List of tuples (tag, text)
        self.groups = {}  # Key: group name, Value: list of indices in self.lines
        self.groups_order = []  # Order of group appearance
        self.current_file = None
        self.highlighted_groups = set()  # Groups with search matches
        self.highlighted_rows = defaultdict(set)  # Rows with matches per group

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        open_action = file_menu.addAction("&Open")
        open_action.triggered.connect(self.open_file)
        save_action = file_menu.addAction("&Save")
        save_action.triggered.connect(self.save_file)
        save_as_action = file_menu.addAction("Save &As")
        save_as_action.triggered.connect(self.save_file_as)

        # Search menu
        search_menu = menubar.addMenu("&Search")
        
        # Tags submenu
        tags_submenu = search_menu.addMenu("Search in Tags")
        go_to_tag_action = tags_submenu.addAction("Go to Tag")
        go_to_tag_action.triggered.connect(self.go_to_tag_dialog)
        go_to_group_action = tags_submenu.addAction("Go to Group")
        go_to_group_action.triggered.connect(self.go_to_group_dialog)
        search_tags_action = tags_submenu.addAction("Search Tags")
        search_tags_action.triggered.connect(self.search_tags_dialog)
        
        # Localizations action
        search_localizations_action = search_menu.addAction("Search in Localizations")
        search_localizations_action.triggered.connect(self.search_localizations_dialog)

        # Clear highlights action
        clear_highlights_action = search_menu.addAction("Clear Highlights")
        clear_highlights_action.triggered.connect(self.clear_highlights)

        # Main interface
        splitter = QSplitter()

        # Group list on the left
        self.group_list = QListWidget()
        self.group_list.itemSelectionChanged.connect(self.update_table)

        # Translation table on the right
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
        """Extract group name from tag"""
        if '_' in tag:
            return tag.rsplit('_', 1)[0]
        return tag

    def open_file(self):
        """Open and parse localization file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt)")
        if not path:
            return

        self.current_file = path
        self.lines.clear()
        self.groups.clear()
        self.groups_order.clear()
        self.clear_highlights()

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
        """Update table when group selection changes"""
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

            # Tag column (not editable)
            tag_item = QTableWidgetItem(tag)
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Text column (editable)
            text_item = QTableWidgetItem(text)
            text_item.setData(Qt.ItemDataRole.UserRole, idx)

            self.table.setItem(row, 0, tag_item)
            self.table.setItem(row, 1, text_item)

        self.table.blockSignals(False)
        self.update_table_highlight()

    def on_cell_changed(self, row, column):
        """Handle text editing in table"""
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
        """Save changes back to file"""
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
        """Save to new file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt)")
        if path:
            self.current_file = path
            self.save_file()

    # Search and highlight functionality
    def clear_highlights(self):
        """Clear all search highlights"""
        self.highlighted_groups.clear()
        self.highlighted_rows.clear()
        for i in range(self.group_list.count()):
            self.group_list.item(i).setBackground(QBrush(Qt.GlobalColor.white))
        self.update_table_highlight()

    def update_group_list_highlight(self):
        """Update group list highlighting"""
        for i in range(self.group_list.count()):
            item = self.group_list.item(i)
            item.setBackground(QBrush(
                QColor(255, 255, 150) if item.text() in self.highlighted_groups 
                else Qt.GlobalColor.white
            ))

    def update_table_highlight(self):
        """Update table row highlighting"""
        current_group = self.group_list.currentItem()
        if not current_group:
            return
            
        group = current_group.text()
        rows_to_highlight = self.highlighted_rows.get(group, set())
        
        for row in range(self.table.rowCount()):
            color = QBrush(QColor(255, 255, 150) if row in rows_to_highlight else Qt.GlobalColor.white)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)

    def search_tags(self, query):
        """Search for text in tags"""
        self.clear_highlights()
        if not query:
            return
            
        for idx, (tag, _) in enumerate(self.lines):
            if query.lower() in tag.lower():
                group = self.get_group_name(tag)
                self.highlighted_groups.add(group)
                if idx in self.groups[group]:
                    pos = self.groups[group].index(idx)
                    self.highlighted_rows[group].add(pos)
        
        self.update_group_list_highlight()
        self.update_table_highlight()

    def search_localizations(self, query):
        """Search for text in localizations"""
        self.clear_highlights()
        if not query:
            return
            
        for idx, (tag, text) in enumerate(self.lines):
            if query.lower() in text.lower():
                group = self.get_group_name(tag)
                self.highlighted_groups.add(group)
                if idx in self.groups[group]:
                    pos = self.groups[group].index(idx)
                    self.highlighted_rows[group].add(pos)
        
        self.update_group_list_highlight()
        self.update_table_highlight()

    def go_to_tag(self, tag):
        """Navigate to specific tag"""
        for idx, (t, _) in enumerate(self.lines):
            if t == tag:
                group = self.get_group_name(tag)
                if group in self.groups_order:
                    group_index = self.groups_order.index(group)
                    self.group_list.setCurrentRow(group_index)
                    row = self.groups[group].index(idx)
                    self.table.scrollToItem(self.table.item(row, 0))
                    return
        QMessageBox.warning(self, "Not Found", f"Tag '{tag}' not found.")

    def go_to_group(self, group):
        """Navigate to specific group"""
        if group in self.groups_order:
            index = self.groups_order.index(group)
            self.group_list.setCurrentRow(index)
        else:
            QMessageBox.warning(self, "Not Found", f"Group '{group}' not found.")

    # Dialog methods
    def go_to_tag_dialog(self):
        dialog = SearchDialog("Go to Tag", "Enter exact tag name:", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.go_to_tag(dialog.get_text())

    def go_to_group_dialog(self):
        dialog = SearchDialog("Go to Group", "Enter group name:", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.go_to_group(dialog.get_text())

    def search_tags_dialog(self):
        dialog = SearchDialog("Search Tags", "Enter search query:", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.search_tags(dialog.get_text())

    def search_localizations_dialog(self):
        dialog = SearchDialog("Search Localizations", "Enter search query:", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.search_localizations(dialog.get_text())


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
