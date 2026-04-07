<<<<<<< HEAD
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (
    QgsProject, QgsWkbTypes, QgsPointXY
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker
import os
import sys

from .ui.results_dialog import ResultsDialog
from .ui.path_tracer_dock import PathTracerDock
from .calculator import HistoricalTravelCalculator

=======
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import (QAction, QDialog, QVBoxLayout, QFormLayout, QLabel, 
                                QLineEdit, QDoubleSpinBox, QPushButton, QDialogButtonBox, 
                                QMessageBox, QComboBox, QWidget, QTableWidget, QTableWidgetItem, 
                                QHBoxLayout, QFileDialog, QGroupBox, QToolButton, QCheckBox, 
                                QSpinBox, QToolTip)
from qgis.core import QgsProject, QgsWkbTypes, QgsRaster, QgsMapLayer, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsDockWidget
from datetime import datetime
import math
import os.path
import json
import csv
import sys
from qgis.PyQt.QtWidgets import QApplication
from .ui.results_dialog import ResultsDialog
from .ui.path_tracer_dock import PathTracerDock

# Add plugin directory to path
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

<<<<<<< HEAD
=======
class HistoricalTravelCalculator:
    def __init__(self):
        # Updated to historically accurate medieval speeds (km/day)
        self.BASE_SPEEDS = {
            'foot': {
                'pedestrian': 20,    # Average walking speed (3-4 km/h * 6-7 hours)
                'child': 15,         # Slower walking speed
                'elderly': 12,       # Reduced walking speed
                'merchant': 18,      # Merchant carrying goods
                'soldier': 25,       # Marching soldier
                'janissary': 28      # Elite marching troops
            },
            'horse': {
                'walk': 30,          # Horse walk (5-6 km/h * 6 hours)
                'trot': 50,          # Horse trot (8-10 km/h * 5 hours)
                'gallop': 80,        # Horse gallop (short bursts)
                'cavalry_walk': 32,  # Cavalry at walk
                'cavalry_trot': 55,  # Cavalry at trot
                'cavalry_gallop': 85, # Cavalry at gallop
                'sipahi_walk': 35,   # Ottoman cavalry at walk
                'sipahi_trot': 60,   # Ottoman cavalry at trot
                'sipahi_gallop': 90   # Ottoman cavalry at gallop
            },
            'cart': {
                'merchant_cart': 15, # Heavy merchant cart
                'supply_cart': 12,   # Military supply wagon
                'artillery': 8,       # Moving cannons
                'ottoman_supply': 14, # Ottoman supply train
                'ottoman_artillery': 7 # Ottoman artillery
            }
        }
        
        # Fatigue rates (per km traveled)
        self.FATIGUE_RATES = {
            'foot': {
                'pedestrian': 0.02,
                'child': 0.03,
                'elderly': 0.025,
                'merchant': 0.015,
                'soldier': 0.01,
                'janissary': 0.008
            },
            'horse': 0.006,  # Horses fatigue slower than humans
            'cart': 0.015    # Carts fatigue faster due to rough terrain
        }
        
        # Recovery rates (per rest day)
        self.RECOVERY_RATES = {
            'foot': {
                'pedestrian': 0.25,
                'child': 0.35,
                'elderly': 0.3,
                'merchant': 0.2,
                'soldier': 0.15,
                'janissary': 0.12
            },
            'horse': 0.1,   # Horses recover slower
            'cart': 0.15    # Carts recover faster (mechanical)
        }
        
        # Terrain modifiers (based on medieval road conditions)
        self.TERRAIN_MODIFIERS = {
            'paved': 0.9,    # Rare Roman roads (not as good as modern)
            'dirt': 0.7,      # Common dirt paths
            'grass': 0.6,     # Open fields
            'forest': 0.4,    # Dense woodland
            'marsh': 0.3,     # Wetlands
            'mountain': 0.35, # Mountain passes
            'desert': 0.5     # Sandy terrain
        }
        
        # Season modifiers (medieval travel was highly seasonal)
        self.SEASON_MODIFIERS = {
            'summer': 1.0,    # Best travel conditions
            'winter': 0.5,     # Severe reduction (snow, mud)
            'spring': 0.7,     # Spring rains
            'fall': 0.8        # Harvest season, better than spring
        }

    def calculate_journey(self, points, traveler_type, params):
        traveler_class, pace = self._classify_traveler(traveler_type)
        base_speed = self._get_base_speed(traveler_type, pace)
        fatigue_rate = self._get_fatigue_rate(traveler_type, traveler_class)
        recovery_rate = self._get_recovery_rate(traveler_type, traveler_class)
        
        # Apply seasonal modifier
        base_speed *= self.SEASON_MODIFIERS.get(params.get('season', 'summer'), 1.0)
        
        # Apply supply modifier if needed
        if params.get('with_supply', False):
            if traveler_class == 'horse': base_speed *= 0.8
            elif traveler_class == 'cart': base_speed *= 0.7
            else: base_speed *= 0.85

        total_distance = sum(p1.distance(p2) for p1, p2 in zip(points, points[1:])) / 1000
        remaining_distance = total_distance
        days = travel_days = rest_days = 0
        fatigue = 0
        segments = []
        
        # Historical march patterns
        march_cycle = 5 if params.get('march_type', 'normal') == 'normal' else 7
        rest_cycle = 2 if params.get('march_type', 'normal') == 'normal' else 1
        
        while remaining_distance > 0:
            # Check if need to rest (weekly cycle or high fatigue)
            if travel_days > 0 and (travel_days % march_cycle == 0 or fatigue > 0.7):
                rest_days += rest_cycle
                fatigue = max(0, fatigue - (recovery_rate * rest_cycle))
                segments.append({
                    'type': 'rest', 
                    'days': rest_cycle, 
                    'fatigue': fatigue, 
                    'distance': 0
                })
                days += rest_cycle
                continue
            
            # Calculate daily progress
            daily_distance = self._calculate_daily_distance(
                base_speed, 
                params.get('surface_type', 'dirt'), 
                fatigue
            )
            actual_distance = min(daily_distance, remaining_distance)
            remaining_distance -= actual_distance
            
            # Update fatigue
            fatigue = min(1.0, fatigue + (actual_distance / daily_distance) * fatigue_rate)
            segments.append({
                'type': 'travel',
                'distance': actual_distance,
                'speed': daily_distance,
                'fatigue': fatigue,
                'terrain': params.get('surface_type', 'dirt')
            })
            travel_days += 1
            days += 1
        
        return {
            'total_days': days,
            'travel_days': travel_days,
            'rest_days': rest_days,
            'segments': segments,
            'fatigue': fatigue,
            'average_km_day': total_distance / days if days > 0 else 0,
            'total_distance_km': total_distance,
            'traveler_type': traveler_type,
            'params': params
        }

    def _classify_traveler(self, traveler_type):
        if 'horse' in traveler_type or 'cavalry' in traveler_type or 'sipahi' in traveler_type:
            pace = 'walk'
            if '_trot' in traveler_type: pace = 'trot'
            elif '_gallop' in traveler_type: pace = 'gallop'
            return 'horse', pace
        elif 'cart' in traveler_type: return 'cart', None
        else: return 'foot', None

    def _get_base_speed(self, traveler_type, pace):
        if pace:
            key = traveler_type.split('_')[0] + '_' + pace if '_' in traveler_type else pace
            return self.BASE_SPEEDS['horse'].get(key, 30)
        elif traveler_type in self.BASE_SPEEDS['foot']:
            return self.BASE_SPEEDS['foot'][traveler_type]
        elif traveler_type in self.BASE_SPEEDS['cart']:
            return self.BASE_SPEEDS['cart'][traveler_type]
        return 20  # Default pedestrian speed

    def _get_fatigue_rate(self, traveler_type, traveler_class):
        if traveler_class == 'foot':
            return self.FATIGUE_RATES['foot'].get(traveler_type, 0.015)
        return self.FATIGUE_RATES.get(traveler_class, 0.01)

    def _get_recovery_rate(self, traveler_type, traveler_class):
        if traveler_class == 'foot':
            return self.RECOVERY_RATES['foot'].get(traveler_type, 0.2)
        return self.RECOVERY_RATES.get(traveler_class, 0.15)

    def _calculate_daily_distance(self, base_speed, terrain_type, current_fatigue):
        terrain_mod = self.TERRAIN_MODIFIERS.get(terrain_type, 0.6)
        fatigue_mod = 1 - (current_fatigue * 0.4)  # Fatigue has greater impact
        return base_speed * terrain_mod * fatigue_mod

>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
class WalkDistanceCalculator:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
<<<<<<< HEAD
        self.rubber_bands = []
        self.rest_markers = []
=======
        self.rubber_band = None
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        self.map_tool = None
        self.points = []
        self.dem_layer = None
        self.dock = None
        self.calculator = HistoricalTravelCalculator()

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), "Historical Travel Calculator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Historical Analysis", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Historical Analysis", self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
<<<<<<< HEAD
        self.cleanup_visuals()

    def cleanup_visuals(self):
        for rb in self.rubber_bands:
            rb.reset()
            self.iface.mapCanvas().scene().removeItem(rb)
        self.rubber_bands = []
        for marker in self.rest_markers:
            self.iface.mapCanvas().scene().removeItem(marker)
        self.rest_markers = []
=======
        self.cleanup_rubber_band()

    def cleanup_rubber_band(self):
        if self.rubber_band:
            self.rubber_band.reset()
            self.iface.mapCanvas().scene().removeItem(self.rubber_band)
            self.rubber_band = None
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def run(self):
        if not self.dock:
            self.dock = PathTracerDock(self.iface, self.iface.mainWindow())
            self.dock.calculateRequested.connect(self.show_results)
            self.dock.clearRequested.connect(self.clear_path)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.show()
        self.activate_tracing()

    def activate_tracing(self):
        if not self.map_tool:
            self.map_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            self.map_tool.canvasClicked.connect(self.handle_map_click)
        
<<<<<<< HEAD
        self.cleanup_visuals()
=======
        if not self.rubber_band:
            self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
            self.rubber_band.setColor(QColor(255, 0, 0))
            self.rubber_band.setWidth(2)
        
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
        self.iface.mapCanvas().setMapTool(self.map_tool)
        self.points = []
        self.update_rubber_band()

    def handle_map_click(self, point, button):
        self.points.append(QgsPointXY(point))
        self.update_rubber_band()
        if self.dock:
            self.dock.update_point_count(len(self.points))

    def update_rubber_band(self):
<<<<<<< HEAD
        self.cleanup_visuals()
        if len(self.points) < 2:
            rb = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
            rb.setColor(QColor(255, 0, 0))
            rb.setWidth(2)
            for pt in self.points:
                rb.addPoint(pt)
            self.rubber_bands.append(rb)
            rb.show()
            return

        rb = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        rb.setColor(QColor(0, 0, 255, 180))
        rb.setWidth(3)
        for pt in self.points:
            rb.addPoint(pt)
        self.rubber_bands.append(rb)
        rb.show()

    def clear_path(self):
        self.points = []
        self.cleanup_visuals()
        self.update_rubber_band()
        if self.dock:
            self.dock.update_point_count(0)
            self.dock.update_summary_panel(None)
=======
        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        for pt in self.points:
            self.rubber_band.addPoint(pt)
        self.rubber_band.show()

    def clear_path(self):
        self.points = []
        self.update_rubber_band()
        if self.dock:
            self.dock.update_point_count(0)
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

    def show_results(self, params):
        if len(self.points) < 2:
            self.iface.messageBar().pushWarning("Warning", "You need at least 2 points to calculate a path")
            return
            
<<<<<<< HEAD
        try:
            hist = params.get('historical_analysis', {})
            results = self.calculator.calculate_journey(self.points, params['traveler_type'], {
                'surface_type': params['surface_type'],
                'season': hist.get('season', 'summer'),
                'march_type': hist.get('march_type', 'normal'),
                'with_supply': hist.get('with_supply', False),
                'supply_weight_kg': hist.get('supply_weight_kg', params.get('supply_weight_kg', 0)),
                'historical': True,
                'height': params.get('height', 170),
                'hours_per_day': params.get('hours_per_day', 8),
                'horseback': params.get('horseback', False),
                'horseback_gait': params.get('horseback_gait', 'Walk'),
                **{k: v for k, v in params.items() if k.startswith('custom_') or k == 'custom_profile'}
            })
        except Exception as e:
            self.iface.messageBar().pushCritical("Calculation Error", str(e))
            return
        
        if results:
            # --- Visualization: Color-coded segments and rest markers ---
            self.cleanup_visuals()
            segments = results['segments']
            max_fatigue = 0
            min_speed = float('inf')
            max_speed = 0
            rest_points = []
            for seg in segments:
                if seg['type'] == 'travel':
                    idx = seg['segment'] - 1
                    if idx < 0 or idx + 1 >= len(self.points):
                        continue
                    p1 = self.points[idx]
                    p2 = self.points[idx + 1]
                    speed = seg.get('speed_km_per_hour', 0)
                    fatigue = seg.get('fatigue', 0)
                    color = self._color_for_speed_fatigue(speed, fatigue)
                    rb = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
                    rb.setColor(color)
                    rb.setWidth(5)
                    rb.addPoint(p1)
                    rb.addPoint(p2)
                    self.rubber_bands.append(rb)
                    rb.show()
                    max_fatigue = max(max_fatigue, fatigue)
                    if speed > 0:
                        min_speed = min(min_speed, speed)
                        max_speed = max(max_speed, speed)
                elif seg['type'] == 'rest':
                    idx = seg['segment'] - 1
                    if 0 <= idx < len(self.points):
                        rest_points.append(self.points[idx])
            # Draw rest markers
            for pt in rest_points:
                marker = QgsVertexMarker(self.iface.mapCanvas())
                marker.setCenter(pt)
                marker.setColor(QColor(255, 200, 0))
                marker.setIconType(QgsVertexMarker.ICON_X)
                marker.setIconSize(16)
                marker.setPenWidth(4)
                self.rest_markers.append(marker)
            # --- End Visualization ---

            # --- Update summary panel ---
            stats = {
                'total_distance_km': results['total_distance_km'],
                'total_days': results['total_days'],
                'travel_days': results['travel_days'],
                'rest_days': results['rest_days'],
                'average_km_day': results['average_km_day'],
                'average_km_hour': results['average_km_hour'],
                'max_fatigue': max_fatigue,
                'num_rests': len(rest_points)
            }
            if self.dock:
                self.dock.update_summary_panel(stats)
            # --- End summary panel update ---

            # --- Results dialog ---
            dialog = ResultsDialog(results, self.iface.mainWindow())
            dialog.exec_()

    def _color_for_speed_fatigue(self, speed, fatigue):
        # Green for fast/low fatigue, Red for slow/high fatigue
        min_speed, max_speed = 2.0, 8.0
        min_fatigue, max_fatigue = 0.01, 0.8
        speed_norm = min(max((speed - min_speed) / (max_speed - min_speed), 0), 1)
        fatigue_norm = min(max((fatigue - min_fatigue) / (max_fatigue - min_fatigue), 0), 1)
        r = int(255 * fatigue_norm)
        g = int(255 * (1 - fatigue_norm))
        b = int(100 * (1 - speed_norm))
        return QColor(r, g, b, 200)
=======
        results = self.calculator.calculate_journey(self.points, params['traveler_type'], {
            'surface_type': params['surface_type'],
            'season': params['historical_analysis']['season'],
            'march_type': params['historical_analysis']['march_type'],
            'with_supply': params['historical_analysis']['with_supply'],
            'historical': True
        })
        
        if results:
            # Format results for the dialog
            days = results['total_days']
            hours = int((results['average_km_day'] / results['total_distance_km']) * 24)
            results['formatted_time'] = f"{days} days, {hours} hours"
            results['days_required'] = days
            results['total_distance'] = results['total_distance_km'] * 1000
            results['daily_march_hours'] = 8  # Default march hours per day
            
            # Prepare segments for display
            for i, segment in enumerate(results['segments']):
                segment['segment'] = i + 1
                segment['elevation_start'] = 0  # Placeholder values
                segment['elevation_end'] = 0
                segment['slope'] = 0
                segment['time'] = (segment['distance'] / segment['speed']) * 60 if segment['type'] == 'travel' else 0
                segment['is_rest_day'] = segment['type'] == 'rest'
            
            dialog = ResultsDialog(results, self.iface.mainWindow())
            dialog.exec_()
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
