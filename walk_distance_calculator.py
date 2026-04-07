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

plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

class WalkDistanceCalculator:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.rubber_bands = []
        self.rest_markers = []
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
        self.cleanup_visuals()

    def cleanup_visuals(self):
        for rb in self.rubber_bands:
            rb.reset()
            self.iface.mapCanvas().scene().removeItem(rb)
        self.rubber_bands = []
        for marker in self.rest_markers:
            self.iface.mapCanvas().scene().removeItem(marker)
        self.rest_markers = []

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
        
        self.cleanup_visuals()
        self.iface.mapCanvas().setMapTool(self.map_tool)
        self.points = []
        self.update_rubber_band()

    def handle_map_click(self, point, button):
        self.points.append(QgsPointXY(point))
        self.update_rubber_band()
        if self.dock:
            self.dock.update_point_count(len(self.points))

    def update_rubber_band(self):
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

    def show_results(self, params):
        if len(self.points) < 2:
            self.iface.messageBar().pushWarning("Warning", "You need at least 2 points to calculate a path")
            return
            
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
