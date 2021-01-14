#! python3  # noqa: E265

"""
    Dialog for setting up the plugin.
"""

# Standard library
from functools import partial
import logging

# PyQGIS
from qgis.core import QgsApplication
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QRect, Qt
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QAction,
    QComboBox,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QTableWidgetItem,
    QToolButton,
)

# project
from menu_from_project.__about__ import DIR_PLUGIN_ROOT, __title__, __version__
from menu_from_project.logic.tools import guess_type_from_location, icon_per_type

# ############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# load ui
FORM_CLASS, _ = uic.loadUiType(DIR_PLUGIN_ROOT / "ui/conf_dialog.ui")

# ############################################################################
# ########## Classes ###############
# ##################################


class MenuConfDialog(QDialog, FORM_CLASS):
    def __init__(self, parent, plugin):
        self.plugin = plugin
        self.parent = parent
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.defaultcursor = self.cursor
        self.setWindowTitle(
            self.windowTitle() + " - {} v{}".format(__title__, __version__)
        )
        self.setWindowIcon(
            QIcon(str(DIR_PLUGIN_ROOT / "resources/gear.svg")),
        )

        self.LOCATIONS = {
            "new": {
                "index": 0,
                "label": QgsApplication.translate("ConfDialog", "New menu", None),
            },
            "layer": {
                "index": 1,
                "label": QgsApplication.translate("ConfDialog", "Add layer menu", None),
            },
            "merge": {
                "index": 2,
                "label": QgsApplication.translate(
                    "ConfDialog", "Merge with previous", None
                ),
            },
        }

        # -- Configured projects (table and related buttons)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.tableWidget.setRowCount(len(self.plugin.projects))
        self.buttonBox.accepted.connect(self.onAccepted)
        self.btnDelete.clicked.connect(self.onDelete)
        self.btnDelete.setText(None)
        self.btnDelete.setIcon(
            QIcon(QgsApplication.iconPath("mActionDeleteSelected.svg"))
        )
        self.btnUp.clicked.connect(self.onMoveUp)
        self.btnUp.setText(None)
        self.btnUp.setIcon(QIcon(QgsApplication.iconPath("mActionArrowUp.svg")))
        self.btnDown.clicked.connect(self.onMoveDown)
        self.btnDown.setText(None)
        self.btnDown.setIcon(QIcon(QgsApplication.iconPath("mActionArrowDown.svg")))

        # add button
        self.btnAdd.setIcon(QIcon(QgsApplication.iconPath("mActionAdd.svg")))
        self.addMenu = QMenu(self.btnAdd)
        add_option_file = QAction(
            QIcon(QgsApplication.iconPath("mIconFile.svg")),
            self.tr("Add from file"),
            self.addMenu,
        )
        add_option_pgdb = QAction(
            QIcon(QgsApplication.iconPath("mIconPostgis.svg")),
            self.tr("Add from PostgreSQL database"),
            self.addMenu,
        )
        add_option_http = QAction(
            QIcon(str(DIR_PLUGIN_ROOT / "resources/globe.svg")),
            self.tr("Add from URL"),
            self.addMenu,
        )
        add_option_file.triggered.connect(partial(self.onAdd, "file"))
        add_option_http.triggered.connect(partial(self.onAdd, "remote_url"))
        add_option_pgdb.triggered.connect(partial(self.onAdd, "database"))
        self.addMenu.addAction(add_option_file)
        self.addMenu.addAction(add_option_pgdb)
        self.addMenu.addAction(add_option_http)
        self.btnAdd.setMenu(self.addMenu)

        for idx, project in enumerate(self.plugin.projects):
            # edit project
            pushButton = QToolButton(self.tableWidget)
            pushButton.setGeometry(QRect(0, 0, 20, 20))
            pushButton.setObjectName("x")
            pushButton.setIcon(QIcon(str(DIR_PLUGIN_ROOT / "resources/edit.svg")))
            pushButton.setToolTip((self.tr("Edit this project")))
            self.tableWidget.setCellWidget(idx, 0, pushButton)
            pushButton.clicked.connect(
                lambda checked, idx=idx: self.onFileSearchPressed(idx)
            )

            # project name
            itemName = QTableWidgetItem(project.get("name"))
            itemName.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(idx, 1, itemName)
            le = QLineEdit()
            le.setText(project.get("name"))
            le.setPlaceholderText(self.tr("Use project title"))
            self.tableWidget.setCellWidget(idx, 1, le)

            # project location type
            qgs_location_type = project.get(
                "type", guess_type_from_location(project.get("location"))
            )
            lbl_location_type = QLabel(self.tableWidget)
            lbl_location_type.setPixmap(QPixmap(icon_per_type(qgs_location_type)))
            lbl_location_type.setAlignment(Qt.AlignCenter)
            lbl_location_type.setTextInteractionFlags(Qt.NoTextInteraction)
            lbl_location_type.setToolTip(qgs_location_type)
            self.tableWidget.setCellWidget(idx, 2, lbl_location_type)

            # project menu location
            location_combo = QComboBox()
            for pk in self.LOCATIONS:
                if not (pk == "merge" and idx == 0):
                    location_combo.addItem(self.LOCATIONS[pk]["label"], pk)

            try:
                location_combo.setCurrentIndex(
                    self.LOCATIONS[project["location"]]["index"]
                )
            except Exception:
                location_combo.setCurrentIndex(0)
            self.tableWidget.setCellWidget(idx, 3, location_combo)

            # project path
            itemFile = QTableWidgetItem(project.get("file"))
            itemFile.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(idx, 4, itemFile)
            le = QLineEdit()
            le.setText(project.get("file"))
            try:
                le.setStyleSheet(
                    "color: {};".format("black" if project["valid"] else "red")
                )
            except Exception:
                le.setStyleSheet("color: {};".format("black"))

            self.tableWidget.setCellWidget(idx, 4, le)
            le.textChanged.connect(self.onTextChanged)

        # -- Options
        self.cbxLoadAll.setChecked(self.plugin.optionLoadAll)
        self.cbxLoadAll.setTristate(False)

        self.cbxCreateGroup.setCheckState(self.plugin.optionCreateGroup)
        self.cbxCreateGroup.setTristate(False)

        self.cbxShowTooltip.setCheckState(self.plugin.optionTooltip)
        self.cbxShowTooltip.setTristate(False)

        self.tableTunning()

    def onFileSearchPressed(self, row):
        item = self.tableWidget.item(row, 1)

        filePath = QFileDialog.getOpenFileName(
            self,
            QgsApplication.translate(
                "menu_from_project", "Projects configuration", None
            ),
            item.text(),
            QgsApplication.translate(
                "menu_from_project", "QGIS projects (*.qgs *.qgz)", None
            ),
        )

        if filePath:
            try:
                file_widget = self.tableWidget.cellWidget(row, 1)
                file_widget.setText(filePath[0])

                name_widget = self.tableWidget.cellWidget(row, 2)
                name = name_widget.text()
                if not name:
                    try:
                        name = filePath[0].split("/")[-1]
                        name = name.split(".")[0]
                    except Exception:
                        name = ""

                    name_widget.setText(name)

            except Exception:
                pass

    def onAccepted(self):
        self.plugin.projects = []
        # self.plugin.log("count : {}".format(self.tableWidget.rowCount()))
        for row in range(self.tableWidget.rowCount()):
            file_widget = self.tableWidget.cellWidget(row, 1)
            # self.plugin.log("row : {}".format(row))
            if file_widget and file_widget.text():
                # self.plugin.log("row {} : {}".format(row, file_widget.text()))

                name_widget = self.tableWidget.cellWidget(row, 0)
                name = name_widget.text()
                filename = file_widget.text()

                location_widget = self.tableWidget.cellWidget(row, 2)
                location = location_widget.itemData(location_widget.currentIndex())

                self.plugin.projects.append(
                    {"file": filename, "name": name, "location": location}
                )

        self.plugin.optionTooltip = self.cbxShowTooltip.isChecked()
        self.plugin.optionLoadAll = self.cbxLoadAll.isChecked()
        self.plugin.optionCreateGroup = self.cbxCreateGroup.isChecked()

        self.plugin.store()

    def onAdd(self, qgs_location_type: str = "file"):
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(row + 1)

        # edit button
        pushButton = QToolButton(self.parent)
        pushButton.setGeometry(QRect(0, 0, 20, 20))
        pushButton.setObjectName("x")
        pushButton.setIcon(QIcon(str(DIR_PLUGIN_ROOT / "resources/edit.svg")))
        self.tableWidget.setCellWidget(row, 0, pushButton)
        pushButton.clicked.connect(
            lambda checked, row=row: self.onFileSearchPressed(row)
        )

        # project name
        itemName = QTableWidgetItem()
        itemName.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(row, 1, itemName)
        name_lineedit = QLineEdit()
        name_lineedit.setPlaceholderText(self.tr("Use project title"))
        self.tableWidget.setCellWidget(row, 1, name_lineedit)

        # project location type
        lbl_location_type = QLabel(self.tableWidget)
        lbl_location_type.setPixmap(QPixmap(icon_per_type(qgs_location_type)))
        lbl_location_type.setMaximumSize(20, 20)
        lbl_location_type.setAlignment(Qt.AlignHCenter)
        lbl_location_type.setScaledContents(True)
        lbl_location_type.setTextInteractionFlags(Qt.NoTextInteraction)
        lbl_location_type.setToolTip(qgs_location_type)
        self.tableWidget.setCellWidget(row, 2, lbl_location_type)

        # menu location
        location_combo = QComboBox()
        for pk in self.LOCATIONS:
            if not (pk == "merge" and row == 0):
                location_combo.addItem(self.LOCATIONS[pk]["label"], pk)

        location_combo.setCurrentIndex(0)
        self.tableWidget.setCellWidget(row, 3, location_combo)

        # project file path
        itemFile = QTableWidgetItem()
        itemFile.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(row, 4, itemFile)
        filepath_lineedit = QLineEdit()
        filepath_lineedit.textChanged.connect(self.onTextChanged)
        self.tableWidget.setCellWidget(row, 4, filepath_lineedit)

        # apply table styling
        self.tableTunning()

    def onDelete(self):
        sr = self.tableWidget.selectedRanges()
        try:
            self.tableWidget.removeRow(sr[0].topRow())
        except Exception:
            pass

    def onMoveUp(self):
        sr = self.tableWidget.selectedRanges()
        try:
            r = sr[0].topRow()
            if r > 0:
                fileA = self.tableWidget.cellWidget(r - 1, 1).text()
                fileB = self.tableWidget.cellWidget(r, 1).text()
                self.tableWidget.cellWidget(r - 1, 1).setText(fileB)
                self.tableWidget.cellWidget(r, 1).setText(fileA)

                nameA = self.tableWidget.cellWidget(r - 1, 2).text()
                nameB = self.tableWidget.cellWidget(r, 2).text()
                self.tableWidget.cellWidget(r - 1, 2).setText(nameB)
                self.tableWidget.cellWidget(r, 2).setText(nameA)

                locA = self.tableWidget.cellWidget(r - 1, 3).currentIndex()
                locB = self.tableWidget.cellWidget(r, 3).currentIndex()
                if locB == 2 and r == 1:
                    locB = 0
                self.tableWidget.cellWidget(r - 1, 3).setCurrentIndex(locB)
                self.tableWidget.cellWidget(r, 3).setCurrentIndex(locA)

                self.tableWidget.setCurrentCell(r - 1, 1)
        except Exception:
            pass

    def onMoveDown(self):
        sr = self.tableWidget.selectedRanges()
        nbRows = self.tableWidget.rowCount()
        try:
            r = sr[0].topRow()
            if r < nbRows - 1:
                fileA = self.tableWidget.cellWidget(r, 1).text()
                fileB = self.tableWidget.cellWidget(r + 1, 1).text()
                self.tableWidget.cellWidget(r, 1).setText(fileB)
                self.tableWidget.cellWidget(r + 1, 1).setText(fileA)

                nameA = self.tableWidget.cellWidget(r, 2).text()
                nameB = self.tableWidget.cellWidget(r + 1, 2).text()
                self.tableWidget.cellWidget(r, 2).setText(nameB)
                self.tableWidget.cellWidget(r + 1, 2).setText(nameA)

                locA = self.tableWidget.cellWidget(r, 3).currentIndex()
                locB = self.tableWidget.cellWidget(r + 1, 3).currentIndex()
                if locB == 2 and r == 0:
                    locB = 0
                self.tableWidget.cellWidget(r, 3).setCurrentIndex(locB)
                self.tableWidget.cellWidget(r + 1, 3).setCurrentIndex(locA)

                self.tableWidget.setCurrentCell(r + 1, 1)
        except Exception:
            pass

    def onTextChanged(self, text):
        file_widget = self.sender()
        try:
            self.plugin.getQgsDoc(text)
            file_widget.setStyleSheet("color: {};".format("black"))
        except Exception:
            file_widget.setStyleSheet("color: {};".format("red"))
            pass

    def tableTunning(self):
        """Prettify table aspect"""
        # edit button
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().resizeSection(0, 20)

        # project name
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Interactive
        )

        # project type
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().resizeSection(2, 10)

        # project menu location
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Interactive
        )

        # project path
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.Interactive
        )

        # fit to content
        self.tableWidget.resizeColumnToContents(1)
        self.tableWidget.resizeColumnToContents(3)
        self.tableWidget.resizeColumnToContents(4)
