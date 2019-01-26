# -*- coding: utf-8 -*-
"""
Dialog for setting up the plugin.
"""

from os.path import join, dirname

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (Qt, QRect)
from qgis.PyQt.QtWidgets import (QHeaderView, QApplication, QTableWidgetItem,
                             QToolButton, QLineEdit, QDialog, QFileDialog)

from qgis.core import (QgsMessageLog)

FORM_CLASS, _ = uic.loadUiType(join(dirname(__file__), 'conf_dialog.ui'))


class MenuConfDialog(QDialog, FORM_CLASS):

    def __init__(self, parent, plugin):
        self.plugin = plugin
        self.parent = parent
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.defaultcursor = self.cursor

        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.tableWidget.setRowCount(len(self.plugin.projects))
        self.buttonBox.accepted.connect(self.onAccepted)
        self.btnAdd.clicked.connect(self.onAdd)
        self.btnDelete.clicked.connect(self.onDelete)

        for idx, project in enumerate(self.plugin.projects):
            pushButton = QToolButton(self.parent)
            pushButton.setGeometry(QRect(0, 0, 20, 20))
            pushButton.setObjectName(("x"))
            pushButton.setText("...")

            itemName = QTableWidgetItem(project["name"])
            itemName.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(idx, 2, itemName)

            itemFile = QTableWidgetItem((project["file"]))
            itemFile.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(idx, 1, itemFile)

            # button
            self.tableWidget.setCellWidget(idx, 0, pushButton)

            # uri
            le = QLineEdit()
            le.setText((project["file"]))
            self.tableWidget.setCellWidget(idx, 1, le)

            # name
            le = QLineEdit()
            le.setText((project["name"]))
            self.tableWidget.setCellWidget(idx, 2, le)

            # helper = lambda _idx: (lambda: self.onFileSearchPressed(_idx))
            pushButton.clicked.connect(lambda checked, idx=idx: self.onFileSearchPressed(idx))

        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().resizeSection(0, 20)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)

        self.cbxLoadAll.setChecked(self.plugin.optionLoadAll)
        self.cbxLoadAll.setTristate(False)

        self.cbxCreateGroup.setCheckState(self.plugin.optionCreateGroup)
        self.cbxCreateGroup.setTristate(False)

        self.cbxShowTooltip.setCheckState(self.plugin.optionTooltip)
        self.cbxShowTooltip.setTristate(False)

    def onFileSearchPressed(self, row):
        item = self.tableWidget.item(row, 1)

        filePath = QFileDialog.getOpenFileName(self, QApplication.translate(
            "menu_from_project",
            "Projects configuration", None
            ), item.text(),
            QApplication.translate("menu_from_project", "QGis projects (*.qgs)", None))

        if filePath:
            try:
                file_widget = self.tableWidget.cellWidget(row, 1)
                file_widget.setText(filePath[0])

                name_widget = self.tableWidget.cellWidget(row, 2)
                name = name_widget.text()
                if not name:
                    try:
                        name = filePath[0].split('/')[-1]
                        name = name.split('.')[0]
                    except:
                        name = ""

                    name_widget.setText(name)
            except:
                pass

    def onAccepted(self):
        self.plugin.projects = []
        #QgsMessageLog.logMessage("count : {}".format(self.tableWidget.rowCount()), 'Extensions')
        for row in range(self.tableWidget.rowCount()):
            file_widget = self.tableWidget.cellWidget(row, 1)
            #QgsMessageLog.logMessage("row : {}".format(row), 'Extensions')
            if file_widget and file_widget.text():
                #QgsMessageLog.logMessage("row {} : {}".format(row, file_widget.text()), 'Extensions')

                name_widget = self.tableWidget.cellWidget(row, 2)
                name = name_widget.text()
                filename = file_widget.text()
                if not name:
                    try:
                        name = filename.split('/')[-1]
                        name = name.split('.')[0]
                    except:
                        name = ""

                self.plugin.projects.append({"file": filename, "name": name})

        self.plugin.optionTooltip = (self.cbxShowTooltip.isChecked())
        self.plugin.optionLoadAll = (self.cbxLoadAll.isChecked())
        self.plugin.optionCreateGroup = (self.cbxCreateGroup.isChecked())

        self.plugin.store()

    def onAdd(self):
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(row+1)

        pushButton = QToolButton(self.parent)
        pushButton.setGeometry(QRect(0, 0, 20, 20))
        pushButton.setObjectName(("x"))
        pushButton.setText("...")

        itemName = QTableWidgetItem("")
        itemName.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(row, 2, itemName)

        itemFile = QTableWidgetItem("")
        itemFile.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(row, 1, itemFile)

        self.tableWidget.setCellWidget(row, 0, pushButton)
        self.tableWidget.setCellWidget(row, 1, QLineEdit())
        self.tableWidget.setCellWidget(row, 2, QLineEdit())

        pushButton.clicked.connect(lambda checked,
                                   row=row: self.onFileSearchPressed(row))

    def onDelete(self):
        sr = self.tableWidget.selectedRanges()
        try:
            self.tableWidget.removeRow(sr[0].topRow())
        except:
            pass
