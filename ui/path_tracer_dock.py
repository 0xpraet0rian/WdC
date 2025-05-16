from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                                QComboBox, QSpinBox, QCheckBox, QGroupBox, 
                                QFormLayout, QToolButton)
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.gui import QgsDockWidget

class PathTracerDock(QgsDockWidget):
    calculateRequested = pyqtSignal(dict)
    clearRequested = pyqtSignal()
    editProfileRequested = pyqtSignal(str)
    
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setObjectName("HistoricalTravelCalculatorDock")
        self.setWindowTitle("Historical Travel Calculator")
        self.setup_ui()

    def setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Traveler Profile Group
        traveler_group = QGroupBox("Traveler Profile")
        traveler_layout = QFormLayout()
        
        self.traveler_combo = QComboBox()
        self.traveler_combo.addItems([
            "Pedestrian", "Child", "Elderly", 
            "Merchant", "Merchant with Cart",
            "Soldier", "Cavalry (Walk)", "Cavalry (Trot)", "Cavalry (Gallop)",
            "Supply Cart", "Artillery",
            "Ottoman Janissary", "Ottoman Sipahi (Walk)", "Ottoman Sipahi (Trot)", "Ottoman Sipahi (Gallop)",
            "Ottoman Supply", "Ottoman Artillery",
            "Horseback (Walk)", "Horseback (Trot)", "Horseback (Gallop)"
        ])
        
        self.edit_profile_btn = QToolButton()
        self.edit_profile_btn.setIcon(QIcon(":/images/themes/default/mActionEdit.svg"))
        self.edit_profile_btn.clicked.connect(self.on_edit_profile)
        
        traveler_layout.addRow("Traveler Type:", self.traveler_combo)
        traveler_layout.addRow("Customize Profile:", self.edit_profile_btn)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 250)
        self.height_spin.setValue(170)
        traveler_layout.addRow("Height (cm):", self.height_spin)
        
        self.surface_combo = QComboBox()
        self.surface_combo.addItems(["Paved", "Dirt", "Grass", "Forest", "Marsh", "Mountain", "Desert"])
        traveler_layout.addRow("Surface Type:", self.surface_combo)
        
        traveler_group.setLayout(traveler_layout)
        layout.addWidget(traveler_group)

        # Historical Analysis Group
        hist_group = QGroupBox("Historical March Parameters")
        hist_layout = QFormLayout()
        
        self.historical_check = QCheckBox("Enable Historical March Patterns")
        self.historical_check.stateChanged.connect(self.toggle_historical_options)
        hist_layout.addRow(self.historical_check)
        
        self.march_combo = QComboBox()
        self.march_combo.addItems(["Normal March (5/2)", "Forced March (7/1)"])
        self.march_combo.setEnabled(False)
        hist_layout.addRow("March Type:", self.march_combo)
        
        self.season_combo = QComboBox()
        self.season_combo.addItems(["Summer", "Winter", "Spring", "Fall"])
        self.season_combo.setEnabled(False)
        hist_layout.addRow("Season:", self.season_combo)
        
        self.supply_check = QCheckBox("With Additional Supplies")
        self.supply_check.setEnabled(False)
        hist_layout.addRow(self.supply_check)
        
        hist_group.setLayout(hist_layout)
        layout.addWidget(hist_group)

        # Status and buttons
        self.status_label = QLabel("Click on map to add route points (minimum 2)")
        self.point_count_label = QLabel("Points: 0")
        layout.addWidget(self.status_label)
        layout.addWidget(self.point_count_label)

        self.clear_btn = QPushButton("Clear Route")
        self.clear_btn.clicked.connect(self.clear_path)
        layout.addWidget(self.clear_btn)
        
        self.calculate_btn = QPushButton("Calculate Historical Journey")
        self.calculate_btn.setEnabled(False)
        self.calculate_btn.clicked.connect(self.on_calculate)
        layout.addWidget(self.calculate_btn)
        
        widget.setLayout(layout)
        self.setWidget(widget)

    def toggle_historical_options(self, state):
        enabled = state == Qt.Checked
        self.march_combo.setEnabled(enabled)
        self.season_combo.setEnabled(enabled)
        self.supply_check.setEnabled(enabled)

    def update_point_count(self, count):
        self.point_count_label.setText(f"Points: {count}")
        self.calculate_btn.setEnabled(count >= 2)

    def clear_path(self):
        self.clearRequested.emit()
        self.update_point_count(0)

    def on_edit_profile(self):
        traveler_type_map = {
            "Pedestrian": "pedestrian",
            "Child": "child",
            "Elderly": "elderly",
            "Merchant": "merchant",
            "Merchant with Cart": "merchant_cart",
            "Soldier": "soldier",
            "Cavalry (Walk)": "cavalry_walk",
            "Cavalry (Trot)": "cavalry_trot",
            "Cavalry (Gallop)": "cavalry_gallop",
            "Supply Cart": "supply_cart",
            "Artillery": "artillery",
            "Ottoman Janissary": "janissary",
            "Ottoman Sipahi (Walk)": "sipahi_walk",
            "Ottoman Sipahi (Trot)": "sipahi_trot",
            "Ottoman Sipahi (Gallop)": "sipahi_gallop",
            "Ottoman Supply": "ottoman_supply",
            "Ottoman Artillery": "ottoman_artillery",
            "Horseback (Walk)": "horse_walk",
            "Horseback (Trot)": "horse_trot",
            "Horseback (Gallop)": "horse_gallop"
        }
        current_text = self.traveler_combo.currentText()
        self.editProfileRequested.emit(traveler_type_map[current_text])

    def on_calculate(self):
        traveler_type_map = {
            "Pedestrian": "pedestrian",
            "Child": "child",
            "Elderly": "elderly",
            "Merchant": "merchant",
            "Merchant with Cart": "merchant_cart",
            "Soldier": "soldier",
            "Cavalry (Walk)": "cavalry_walk",
            "Cavalry (Trot)": "cavalry_trot",
            "Cavalry (Gallop)": "cavalry_gallop",
            "Supply Cart": "supply_cart",
            "Artillery": "artillery",
            "Ottoman Janissary": "janissary",
            "Ottoman Sipahi (Walk)": "sipahi_walk",
            "Ottoman Sipahi (Trot)": "sipahi_trot",
            "Ottoman Sipahi (Gallop)": "sipahi_gallop",
            "Ottoman Supply": "ottoman_supply",
            "Ottoman Artillery": "ottoman_artillery",
            "Horseback (Walk)": "horse_walk",
            "Horseback (Trot)": "horse_trot",
            "Horseback (Gallop)": "horse_gallop"
        }
        
        params = {
            'traveler_type': traveler_type_map[self.traveler_combo.currentText()],
            'height': self.height_spin.value(),
            'surface_type': self.surface_combo.currentText().lower(),
            'historical_analysis': {
                'enabled': self.historical_check.isChecked(),
                'march_type': self.march_combo.currentText().lower().split()[0],
                'season': self.season_combo.currentText().lower(),
                'with_supply': self.supply_check.isChecked()
            }
        }
        self.calculateRequested.emit(params)