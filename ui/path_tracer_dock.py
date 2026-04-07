<<<<<<< HEAD
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QToolButton, QDialog, QDialogButtonBox, QDoubleSpinBox, QHBoxLayout, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy
)
from qgis.PyQt.QtCore import pyqtSignal, Qt, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.gui import QgsDockWidget
from qgis.core import QgsApplication

import json

from .traveler_defaults import TRAVELER_DEFAULTS
from .help_dialog import HelpDialog

class CustomProfileDialog(QDialog):
    DEFAULTS = {
        'custom_foot_speed_kmh': 3.5,
        'custom_foot_fatigue': 0.018,
        'custom_foot_recovery': 0.2,
        'custom_horse_walk_speed_kmh': 5.0,
        'custom_horse_trot_speed_kmh': 8.0,
        'custom_horse_gallop_speed_kmh': 12.0,
        'custom_horse_fatigue': 0.012,
        'custom_horse_recovery': 0.15
    }

    def __init__(self, parent=None, initial=None, traveler_type=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Traveler Profile")
        self.setModal(True)
        self.traveler_type = traveler_type or "pedestrian"
        self.init_values = initial if initial else {}
        self.setup_ui()
        self.set_fields_for_traveler(self.traveler_type)
        self.load_initial_values(self.init_values, self.traveler_type)

    def setup_ui(self):
        layout = QVBoxLayout()
        self.form = QFormLayout()

        self.foot_speed = QDoubleSpinBox()
        self.foot_speed.setRange(1, 10)
        self.foot_speed.setDecimals(2)
        self.foot_speed.setSuffix(" km/h")
        self.foot_speed.setToolTip("Average walking speed on foot in kilometers per hour.")
        self.form.addRow("On Foot Speed:", self.foot_speed)

        self.foot_fatigue = QDoubleSpinBox()
        self.foot_fatigue.setRange(0.001, 0.1)
        self.foot_fatigue.setDecimals(3)
        self.foot_fatigue.setSingleStep(0.001)
        self.foot_fatigue.setToolTip("Fatigue rate per hour for walking. Higher values mean fatigue accumulates faster.")
        self.form.addRow("On Foot Fatigue Rate:", self.foot_fatigue)

        self.foot_recovery = QDoubleSpinBox()
        self.foot_recovery.setRange(0.01, 1.0)
        self.foot_recovery.setDecimals(3)
        self.foot_recovery.setSingleStep(0.01)
        self.foot_recovery.setToolTip("Fatigue recovery rate per hour of rest.")
        self.form.addRow("On Foot Recovery Rate:", self.foot_recovery)

        self.horse_walk_speed = QDoubleSpinBox()
        self.horse_walk_speed.setRange(1, 20)
        self.horse_walk_speed.setDecimals(2)
        self.horse_walk_speed.setSuffix(" km/h")
        self.horse_walk_speed.setToolTip("Average walking speed of a horse in kilometers per hour.")
        self.form.addRow("Horse Walk Speed:", self.horse_walk_speed)

        self.horse_trot_speed = QDoubleSpinBox()
        self.horse_trot_speed.setRange(1, 25)
        self.horse_trot_speed.setDecimals(2)
        self.horse_trot_speed.setSuffix(" km/h")
        self.horse_trot_speed.setToolTip("Average trotting speed of a horse in kilometers per hour.")
        self.form.addRow("Horse Trot Speed:", self.horse_trot_speed)

        self.horse_gallop_speed = QDoubleSpinBox()
        self.horse_gallop_speed.setRange(1, 40)
        self.horse_gallop_speed.setDecimals(2)
        self.horse_gallop_speed.setSuffix(" km/h")
        self.horse_gallop_speed.setToolTip("Average galloping speed of a horse in kilometers per hour.")
        self.form.addRow("Horse Gallop Speed:", self.horse_gallop_speed)

        self.horse_fatigue = QDoubleSpinBox()
        self.horse_fatigue.setRange(0.001, 0.1)
        self.horse_fatigue.setDecimals(3)
        self.horse_fatigue.setSingleStep(0.001)
        self.horse_fatigue.setToolTip("Fatigue rate per hour for riding a horse.")
        self.form.addRow("Horse Fatigue Rate:", self.horse_fatigue)

        self.horse_recovery = QDoubleSpinBox()
        self.horse_recovery.setRange(0.01, 1.0)
        self.horse_recovery.setDecimals(3)
        self.horse_recovery.setSingleStep(0.01)
        self.horse_recovery.setToolTip("Fatigue recovery rate per hour of rest for a horse.")
        self.form.addRow("Horse Recovery Rate:", self.horse_recovery)

        layout.addLayout(self.form)

        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setToolTip("Reset all values to their default settings.")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        btn_layout.addWidget(self.reset_btn)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setToolTip("Save these custom profile values.")
        self.button_box.button(QDialogButtonBox.Cancel).setToolTip("Cancel and discard changes.")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        btn_layout.addWidget(self.button_box)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def set_fields_for_traveler(self, traveler_type):
        cart_types = {"merchant_cart", "supply_cart", "artillery", "ottoman_supply", "ottoman_artillery"}
        cavalry_types = {"cavalry", "sipahi"}

        def set_row_visible(row_widget, visible):
            row_widget[1].setVisible(visible)
            label = self.form.labelForField(row_widget[1])
            if label:
                label.setVisible(visible)

        self._rows = [
            (self.form.itemAt(i, QFormLayout.LabelRole), self.form.itemAt(i, QFormLayout.FieldRole).widget())
            for i in range(self.form.rowCount())
        ]

        if traveler_type in cart_types:
            for i, (label, widget) in enumerate(self._rows):
                set_row_visible((label, widget), i < 3)
        elif traveler_type in cavalry_types:
            for i, (label, widget) in enumerate(self._rows):
                set_row_visible((label, widget), i >= 3)
        else:
            for i, (label, widget) in enumerate(self._rows):
                set_row_visible((label, widget), True)

    def load_initial_values(self, values, traveler_type):
        defaults = dict(self.DEFAULTS)
        defaults.update(TRAVELER_DEFAULTS.get(traveler_type, {}))
        self.foot_speed.setValue(values.get('custom_foot_speed_kmh', defaults['custom_foot_speed_kmh']))
        self.foot_fatigue.setValue(values.get('custom_foot_fatigue', defaults['custom_foot_fatigue']))
        self.foot_recovery.setValue(values.get('custom_foot_recovery', defaults['custom_foot_recovery']))
        self.horse_walk_speed.setValue(values.get('custom_horse_walk_speed_kmh', defaults['custom_horse_walk_speed_kmh']))
        self.horse_trot_speed.setValue(values.get('custom_horse_trot_speed_kmh', defaults['custom_horse_trot_speed_kmh']))
        self.horse_gallop_speed.setValue(values.get('custom_horse_gallop_speed_kmh', defaults['custom_horse_gallop_speed_kmh']))
        self.horse_fatigue.setValue(values.get('custom_horse_fatigue', defaults['custom_horse_fatigue']))
        self.horse_recovery.setValue(values.get('custom_horse_recovery', defaults['custom_horse_recovery']))

    def reset_to_defaults(self):
        self.load_initial_values({}, self.traveler_type)

    def get_values(self):
        return {
            'custom_foot_speed_kmh': self.foot_speed.value(),
            'custom_foot_fatigue': self.foot_fatigue.value(),
            'custom_foot_recovery': self.foot_recovery.value(),
            'custom_horse_walk_speed_kmh': self.horse_walk_speed.value(),
            'custom_horse_trot_speed_kmh': self.horse_trot_speed.value(),
            'custom_horse_gallop_speed_kmh': self.horse_gallop_speed.value(),
            'custom_horse_fatigue': self.horse_fatigue.value(),
            'custom_horse_recovery': self.horse_recovery.value()
        }
=======
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                                QComboBox, QSpinBox, QCheckBox, QGroupBox, 
                                QFormLayout, QToolButton)
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.gui import QgsDockWidget
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

class PathTracerDock(QgsDockWidget):
    calculateRequested = pyqtSignal(dict)
    clearRequested = pyqtSignal()
    editProfileRequested = pyqtSignal(str)
    
<<<<<<< HEAD
    CART_TYPES = {
        "Merchant with Cart", "Supply Cart", "Artillery", "Ottoman Supply", "Ottoman Artillery"
    }
    CAVALRY_TYPES = {"Cavalry", "Ottoman Sipahi"}

    PROFILE_SETTINGS_KEY = "WalkDistanceCalculator/CustomProfiles"

=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setObjectName("HistoricalTravelCalculatorDock")
        self.setWindowTitle("Historical Travel Calculator")
<<<<<<< HEAD
        self.custom_profile_params = None
        self.current_traveler_type = "pedestrian"
        self.setup_ui()

    def setup_ui(self):
        # --- Main content widget ---
        content_widget = QWidget()
        layout = QVBoxLayout()
        content_widget.setLayout(layout)
        content_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # --- Help Button at the top right ---
        help_btn_layout = QHBoxLayout()
        help_btn_layout.addStretch()
        self.help_btn = QToolButton()
        self.help_btn.setIcon(QgsApplication.getThemeIcon("mActionHelpContents.svg"))
        self.help_btn.setToolTip("Show help and explanation for this tool.")
        self.help_btn.clicked.connect(self.show_help_dialog)
        help_btn_layout.addWidget(self.help_btn)
        layout.addLayout(help_btn_layout)
        # --- End Help Button ---

=======
        self.setup_ui()

    def setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Traveler Profile Group
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        traveler_group = QGroupBox("Traveler Profile")
        traveler_layout = QFormLayout()
        
        self.traveler_combo = QComboBox()
        self.traveler_combo.addItems([
            "Pedestrian", "Child", "Elderly", 
            "Merchant", "Merchant with Cart",
<<<<<<< HEAD
            "Soldier", "Cavalry", "Supply Cart", "Artillery",
            "Ottoman Janissary", "Ottoman Sipahi", "Ottoman Supply", "Ottoman Artillery"
        ])
        self.traveler_combo.setToolTip("Select the type of traveler for the route.")

        self.horseback_checkbox = QCheckBox("Horseback (Mounted)")
        self.horseback_checkbox.setToolTip("Check if the traveler is mounted (on horseback).")
        self.horseback_checkbox.stateChanged.connect(self.on_horseback_checked)

        self.gait_combo = QComboBox()
        self.gait_combo.addItems(["Walk", "Trot", "Gallop"])
        self.gait_combo.setEnabled(False)
        self.gait_combo.setToolTip("Select the gait for horseback travel.")
        gait_layout = QHBoxLayout()
        gait_layout.addWidget(QLabel("Horseback Gait:"))
        gait_layout.addWidget(self.gait_combo)
        gait_widget = QWidget()
        gait_widget.setLayout(gait_layout)

        self.edit_profile_btn = QToolButton()
        self.edit_profile_btn.setIcon(QgsApplication.getThemeIcon("mActionOptions.svg"))
        self.edit_profile_btn.setToolTip("Customize travel speeds and fatigue rates for the selected traveler type.")
        self.edit_profile_btn.clicked.connect(self.on_edit_profile)
        
        # --- Save/Load Profile Buttons ---
        self.save_profile_btn = QToolButton()
        self.save_profile_btn.setIcon(QgsApplication.getThemeIcon("mActionFileSave.svg"))
        self.save_profile_btn.setToolTip("Save the current custom profile for this traveler type.")
        self.save_profile_btn.clicked.connect(self.save_profile)

        self.load_profile_btn = QToolButton()
        self.load_profile_btn.setIcon(QgsApplication.getThemeIcon("mActionFileOpen.svg"))
        self.load_profile_btn.setToolTip("Load a previously saved custom profile for this traveler type.")
        self.load_profile_btn.clicked.connect(self.load_profile)

        profile_btn_layout = QHBoxLayout()
        profile_btn_layout.addWidget(self.edit_profile_btn)
        profile_btn_layout.addWidget(self.save_profile_btn)
        profile_btn_layout.addWidget(self.load_profile_btn)
        profile_btn_widget = QWidget()
        profile_btn_widget.setLayout(profile_btn_layout)
        # --- End Save/Load Profile Buttons ---

        traveler_layout.addRow("Traveler Type:", self.traveler_combo)
        traveler_layout.addRow("Horseback:", self.horseback_checkbox)
        traveler_layout.addRow(gait_widget)
        traveler_layout.addRow("Customize Profile:", profile_btn_widget)
=======
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
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 250)
        self.height_spin.setValue(170)
<<<<<<< HEAD
        self.height_spin.setToolTip("Enter the traveler's height in centimeters.")
        traveler_layout.addRow("Height (cm):", self.height_spin)

        self.hours_per_day_spin = QSpinBox()
        self.hours_per_day_spin.setRange(1, 24)
        self.hours_per_day_spin.setValue(8)
        self.hours_per_day_spin.setToolTip("Number of hours per day spent traveling.")
        traveler_layout.addRow("Hours per Day:", self.hours_per_day_spin)
        
        self.surface_combo = QComboBox()
        self.surface_combo.addItems(["Paved", "Dirt", "Grass", "Forest", "Marsh", "Mountain", "Desert"])
        self.surface_combo.setToolTip("Select the predominant surface type for the route.")
=======
        traveler_layout.addRow("Height (cm):", self.height_spin)
        
        self.surface_combo = QComboBox()
        self.surface_combo.addItems(["Paved", "Dirt", "Grass", "Forest", "Marsh", "Mountain", "Desert"])
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        traveler_layout.addRow("Surface Type:", self.surface_combo)
        
        traveler_group.setLayout(traveler_layout)
        layout.addWidget(traveler_group)

<<<<<<< HEAD
=======
        # Historical Analysis Group
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        hist_group = QGroupBox("Historical March Parameters")
        hist_layout = QFormLayout()
        
        self.historical_check = QCheckBox("Enable Historical March Patterns")
<<<<<<< HEAD
        self.historical_check.setToolTip("Enable simulation of historical march/rest patterns (e.g., 5/2 or 7/1).")
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        self.historical_check.stateChanged.connect(self.toggle_historical_options)
        hist_layout.addRow(self.historical_check)
        
        self.march_combo = QComboBox()
        self.march_combo.addItems(["Normal March (5/2)", "Forced March (7/1)"])
        self.march_combo.setEnabled(False)
<<<<<<< HEAD
        self.march_combo.setToolTip("Select the historical march/rest pattern.")
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        hist_layout.addRow("March Type:", self.march_combo)
        
        self.season_combo = QComboBox()
        self.season_combo.addItems(["Summer", "Winter", "Spring", "Fall"])
        self.season_combo.setEnabled(False)
<<<<<<< HEAD
        self.season_combo.setToolTip("Select the season for the historical march.")
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        hist_layout.addRow("Season:", self.season_combo)
        
        self.supply_check = QCheckBox("With Additional Supplies")
        self.supply_check.setEnabled(False)
<<<<<<< HEAD
        self.supply_check.setToolTip("Check if the traveler is carrying additional supplies.")
        self.supply_check.stateChanged.connect(self.on_supply_checked)
        hist_layout.addRow(self.supply_check)

        self.supply_weight_spin = QSpinBox()
        self.supply_weight_spin.setRange(1, 200)
        self.supply_weight_spin.setValue(20)
        self.supply_weight_spin.setSuffix(" kg")
        self.supply_weight_spin.setEnabled(False)
        self.supply_weight_spin.setToolTip("Weight of additional supplies in kilograms.")
        hist_layout.addRow("Supply Weight:", self.supply_weight_spin)
=======
        hist_layout.addRow(self.supply_check)
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        
        hist_group.setLayout(hist_layout)
        layout.addWidget(hist_group)

<<<<<<< HEAD
        self.status_label = QLabel("Click on map to add route points (minimum 2)")
        self.status_label.setToolTip("Instructions for adding route points on the map.")
        self.point_count_label = QLabel("Points: 0")
        self.point_count_label.setToolTip("Number of route points currently selected.")
=======
        # Status and buttons
        self.status_label = QLabel("Click on map to add route points (minimum 2)")
        self.point_count_label = QLabel("Points: 0")
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        layout.addWidget(self.status_label)
        layout.addWidget(self.point_count_label)

        self.clear_btn = QPushButton("Clear Route")
<<<<<<< HEAD
        self.clear_btn.setToolTip("Clear all route points and reset the map.")
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        self.clear_btn.clicked.connect(self.clear_path)
        layout.addWidget(self.clear_btn)
        
        self.calculate_btn = QPushButton("Calculate Historical Journey")
        self.calculate_btn.setEnabled(False)
<<<<<<< HEAD
        self.calculate_btn.setToolTip("Calculate the historical journey based on the selected parameters and route.")
        self.calculate_btn.clicked.connect(self.on_calculate)
        layout.addWidget(self.calculate_btn)

        # --- Summary Panel ---
        self.summary_label = QLabel("<b>Summary:</b><br>No calculation yet.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setToolTip("Summary of the calculated journey will appear here.")
        layout.addWidget(self.summary_label)
        # --- End Summary Panel ---

        # --- Make the dock scrollable ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)
        # Set a reasonable minimum and maximum height for the dock
        scroll.setMinimumHeight(350)
        scroll.setMaximumHeight(600)
        self.setWidget(scroll)
        # --- End scrollable dock ---

        self.traveler_combo.currentIndexChanged.connect(self.on_traveler_type_changed)
        self.on_traveler_type_changed(self.traveler_combo.currentIndex())
=======
        self.calculate_btn.clicked.connect(self.on_calculate)
        layout.addWidget(self.calculate_btn)
        
        widget.setLayout(layout)
        self.setWidget(widget)
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def toggle_historical_options(self, state):
        enabled = state == Qt.Checked
        self.march_combo.setEnabled(enabled)
        self.season_combo.setEnabled(enabled)
        self.supply_check.setEnabled(enabled)
<<<<<<< HEAD
        self.supply_weight_spin.setEnabled(enabled and self.supply_check.isChecked())

    def on_supply_checked(self, state):
        self.supply_weight_spin.setEnabled(state == Qt.Checked)
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def update_point_count(self, count):
        self.point_count_label.setText(f"Points: {count}")
        self.calculate_btn.setEnabled(count >= 2)

    def clear_path(self):
        self.clearRequested.emit()
        self.update_point_count(0)
<<<<<<< HEAD
        self.update_summary_panel(None)
=======
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def on_edit_profile(self):
        traveler_type_map = {
            "Pedestrian": "pedestrian",
            "Child": "child",
            "Elderly": "elderly",
            "Merchant": "merchant",
            "Merchant with Cart": "merchant_cart",
            "Soldier": "soldier",
<<<<<<< HEAD
            "Cavalry": "cavalry",
            "Supply Cart": "supply_cart",
            "Artillery": "artillery",
            "Ottoman Janissary": "janissary",
            "Ottoman Sipahi": "sipahi",
            "Ottoman Supply": "ottoman_supply",
            "Ottoman Artillery": "ottoman_artillery"
        }
        traveler_type = traveler_type_map[self.traveler_combo.currentText()]
        defaults = TRAVELER_DEFAULTS.get(traveler_type, {})
        initial = dict(defaults)
        if self.custom_profile_params:
            initial.update(self.custom_profile_params)
        dlg = CustomProfileDialog(self, initial, traveler_type=traveler_type)
        if dlg.exec_() == QDialog.Accepted:
            self.custom_profile_params = dlg.get_values()
        else:
            self.custom_profile_params = None

    def on_traveler_type_changed(self, idx):
        traveler = self.traveler_combo.currentText()
        traveler_type_map = {
            "Pedestrian": "pedestrian",
            "Child": "child",
            "Elderly": "elderly",
            "Merchant": "merchant",
            "Merchant with Cart": "merchant_cart",
            "Soldier": "soldier",
            "Cavalry": "cavalry",
            "Supply Cart": "supply_cart",
            "Artillery": "artillery",
            "Ottoman Janissary": "janissary",
            "Ottoman Sipahi": "sipahi",
            "Ottoman Supply": "ottoman_supply",
            "Ottoman Artillery": "ottoman_artillery"
        }
        self.current_traveler_type = traveler_type_map[traveler]
        if traveler in self.CART_TYPES:
            self.horseback_checkbox.setChecked(False)
            self.horseback_checkbox.setEnabled(False)
            self.gait_combo.setEnabled(False)
        elif traveler in self.CAVALRY_TYPES:
            self.horseback_checkbox.setChecked(True)
            self.horseback_checkbox.setEnabled(False)
            self.gait_combo.setEnabled(True)
        else:
            self.horseback_checkbox.setEnabled(True)
            self.gait_combo.setEnabled(self.horseback_checkbox.isChecked())

    def on_horseback_checked(self, state):
        traveler = self.traveler_combo.currentText()
        if traveler in self.CART_TYPES:
            self.gait_combo.setEnabled(False)
        elif traveler in self.CAVALRY_TYPES:
            self.gait_combo.setEnabled(True)
        else:
            self.gait_combo.setEnabled(state == Qt.Checked)

    def show_error_dialog(self, message, title="Input Error"):
        QMessageBox.critical(self, title, message)
=======
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
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def on_calculate(self):
        traveler_type_map = {
            "Pedestrian": "pedestrian",
            "Child": "child",
            "Elderly": "elderly",
            "Merchant": "merchant",
            "Merchant with Cart": "merchant_cart",
            "Soldier": "soldier",
<<<<<<< HEAD
            "Cavalry": "cavalry",
            "Supply Cart": "supply_cart",
            "Artillery": "artillery",
            "Ottoman Janissary": "janissary",
            "Ottoman Sipahi": "sipahi",
            "Ottoman Supply": "ottoman_supply",
            "Ottoman Artillery": "ottoman_artillery"
        }
        
        # --- Input Validation ---
        errors = []
        hours = self.hours_per_day_spin.value()
        if hours <= 0:
            errors.append("Hours per day must be greater than zero.")
        if self.supply_check.isChecked():
            supply_weight = self.supply_weight_spin.value()
            if supply_weight <= 0:
                errors.append("Supply weight must be greater than zero.")
        height = self.height_spin.value()
        if height < 100 or height > 250:
            errors.append("Height must be between 100 and 250 cm.")
        # Add more checks as needed

        if errors:
            self.show_error_dialog("\n".join(errors))
            return
        # --- End Input Validation ---

        params = {
            'traveler_type': traveler_type_map[self.traveler_combo.currentText()],
            'horseback': self.horseback_checkbox.isChecked(),
            'horseback_gait': self.gait_combo.currentText(),
            'height': self.height_spin.value(),
            'hours_per_day': self.hours_per_day_spin.value(),
            'surface_type': self.surface_combo.currentText().lower(),
            'historical_analysis': {
                'season': self.season_combo.currentText().lower(),
                'march_type': self.march_combo.currentText().lower().split()[0],
                'with_supply': self.supply_check.isChecked(),
                'supply_weight_kg': self.supply_weight_spin.value() if self.supply_check.isChecked() else 0
            },
            'with_supply': self.supply_check.isChecked(),
            'supply_weight_kg': self.supply_weight_spin.value() if self.supply_check.isChecked() else 0
        }
        if self.custom_profile_params:
            hours = self.hours_per_day_spin.value()
            params.update({
                'custom_foot_speed': self.custom_profile_params.get('custom_foot_speed_kmh', 3.0) * hours,
                'custom_horse_walk_speed': self.custom_profile_params.get('custom_horse_walk_speed_kmh', 5.0) * hours,
                'custom_horse_trot_speed': self.custom_profile_params.get('custom_horse_trot_speed_kmh', 8.0) * hours,
                'custom_horse_gallop_speed': self.custom_profile_params.get('custom_horse_gallop_speed_kmh', 12.0) * hours,
                'custom_foot_fatigue': self.custom_profile_params.get('custom_foot_fatigue', 0.018),
                'custom_foot_recovery': self.custom_profile_params.get('custom_foot_recovery', 0.2),
                'custom_horse_fatigue': self.custom_profile_params.get('custom_horse_fatigue', 0.012),
                'custom_horse_recovery': self.custom_profile_params.get('custom_horse_recovery', 0.15),
                'custom_profile': True
            })
        self.calculateRequested.emit(params)

    def show_help_dialog(self):
        dlg = HelpDialog(self)
        dlg.exec_()

    # --- Save/Load Profile Logic ---

    def save_profile(self):
        if not self.custom_profile_params:
            QMessageBox.warning(self, "No Custom Profile", "There is no custom profile to save. Please customize a profile first.")
            return
        traveler_type = self.current_traveler_type
        settings = QSettings()
        all_profiles = settings.value(self.PROFILE_SETTINGS_KEY, {}, type=dict)
        all_profiles[traveler_type] = self.custom_profile_params
        settings.setValue(self.PROFILE_SETTINGS_KEY, all_profiles)
        QMessageBox.information(self, "Profile Saved", f"Custom profile for '{traveler_type}' saved successfully.")

        # Optionally, allow export to JSON file
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Profile to JSON", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.custom_profile_params, f, indent=2)
                QMessageBox.information(self, "Profile Exported", f"Profile exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export profile: {e}")

    def load_profile(self):
        traveler_type = self.current_traveler_type
        settings = QSettings()
        all_profiles = settings.value(self.PROFILE_SETTINGS_KEY, {}, type=dict)
        loaded = None

        # Try to load from QGIS settings first
        if traveler_type in all_profiles:
            loaded = all_profiles[traveler_type]
        else:
            # Optionally, allow import from JSON file
            file_path, _ = QFileDialog.getOpenFileName(self, "Import Profile from JSON", "", "JSON Files (*.json)")
            if file_path:
                try:
                    with open(file_path, "r") as f:
                        loaded = json.load(f)
                except Exception as e:
                    QMessageBox.critical(self, "Import Failed", f"Could not import profile: {e}")
                    return

        if loaded:
            self.custom_profile_params = loaded
            QMessageBox.information(self, "Profile Loaded", f"Custom profile for '{traveler_type}' loaded.")
        else:
            QMessageBox.warning(self, "No Profile Found", f"No saved profile found for '{traveler_type}'.")

    def update_summary_panel(self, stats: dict):
        if not stats:
            self.summary_label.setText("<b>Summary:</b><br>No calculation yet.")
            return
        html = (
            f"<b>Summary:</b><br>"
            f"Total Distance: <b>{stats['total_distance_km']:.2f}</b> km<br>"
            f"Total Days: <b>{stats['total_days']:.2f}</b><br>"
            f"Travel Days: <b>{stats['travel_days']:.2f}</b><br>"
            f"Rest Days: <b>{stats['rest_days']:.2f}</b><br>"
            f"Average Speed: <b>{stats['average_km_day']:.2f}</b> km/day "
            f"({stats['average_km_hour']:.2f} km/h)<br>"
            f"Max Fatigue: <b>{stats.get('max_fatigue', 0):.3f}</b><br>"
            f"Rest Points: <b>{stats.get('num_rests', 0)}</b>"
        )
        self.summary_label.setText(html)
=======
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
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
