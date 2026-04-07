<<<<<<< HEAD
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QHBoxLayout, QAbstractItemView, QFileDialog, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap, QPainter
import csv

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from qgis.utils import iface
import tempfile
import os

def human_friendly_time_hours(hours):
    if hours is None:
        return ""
    total_minutes = int(round(hours * 60))
    if total_minutes < 60:
        return f"{total_minutes} min"
    h, m = divmod(total_minutes, 60)
    if h < 24:
        return f"{h} h {m} min" if m else f"{h} h"
    d, h = divmod(h, 24)
    if d < 7:
        return f"{d} d {h} h {m} min" if m else f"{d} d {h} h"
    w, d = divmod(d, 7)
    if w < 4:
        return f"{w} w {d} d {h} h {m} min" if m else f"{w} w {d} d {h} h"
    mo, w = divmod(w, 4)
    if mo < 12:
        return f"{mo} mo {w} w {d} d {h} h {m} min" if m else f"{mo} mo {w} w {d} d {h} h"
    y, mo = divmod(mo, 12)
    return f"{y} y {mo} mo {w} w {d} d {h} h {m} min" if m else f"{y} y {mo} mo {w} w {d} d {h} h"

def render_map_canvas_to_pixmap(width, height):
    canvas = iface.mapCanvas()
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.white)
    painter = QPainter(pixmap)
    canvas.render(painter)
    painter.end()
    return pixmap
=======
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
                                QTableWidgetItem, QLabel, QPushButton,
                                QHBoxLayout, QFileDialog, QMessageBox,
                                QApplication)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import Qt
import csv
from datetime import datetime
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4

class ResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
<<<<<<< HEAD
        self.setWindowTitle("Historical Journey Results")
        self.resize(1200, 650)

        self.results = results

        layout = QVBoxLayout(self)

        # --- TRUE CALCULATIONS ---
        # Use per_segment_summary for days to ensure consistency
        rest_days = sum(seg.get('rest_days', 0) for seg in results['per_segment_summary'])
        travel_days = sum(seg.get('travel_days', 0) for seg in results['per_segment_summary'])
        total_days = travel_days + rest_days

        total_travel_hours = sum(seg.get('time_hours', 0) for seg in results['segments'] if seg.get('type', '') == 'travel')
        total_rest_hours = sum(seg.get('days', 0) * 24 for seg in results['segments'] if seg.get('type', '') == 'rest')
        total_hours = total_travel_hours + total_rest_hours

        summary = results
        summary_lines = [
            f"<b>Total Distance:</b> {summary['total_distance_km']:.2f} km",
            f"<b>Total Time (actual travel):</b> {human_friendly_time_hours(total_travel_hours)}",
        ]
        if rest_days > 0:
            summary_lines.append(f"<b>Total Time (including rest):</b> {human_friendly_time_hours(total_hours)}")
        summary_lines += [
            f"<b>Total Days:</b> {total_days:.2f}",
            f"<b>Travel Days:</b> {travel_days:.2f}",
            f"<b>Rest Days:</b> {rest_days:.2f}",
            f"<b>Average Speed:</b> {summary['average_km_day']:.2f} km/day "
            f"({summary['average_km_hour']:.2f} km/h)",
            f"<b>Hours per Day:</b> {summary.get('hours_per_day', 8)}",
            f"<b>Traveler Type:</b> {summary.get('traveler_type', '')}",
            f"<b>Surface:</b> {summary['params'].get('surface_type', '')}",
            f"<b>Height:</b> {summary['params'].get('height', '')} cm",
            f"<b>Horseback:</b> {summary['params'].get('horseback', False)}",
            f"<b>Horseback Gait:</b> {summary['params'].get('horseback_gait', '')}",
            f"<b>Custom Profile:</b> {summary['params'].get('custom_profile', False)}",
        ]
        self.summary_label = QLabel("<br>".join(summary_lines))
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setWordWrap(True)

        # Map thumbnail (right of summary)
        full_map_width, full_map_height = 1920, 1080
        thumbnail_width, thumbnail_height = 320, 180
        self.full_map_pixmap = render_map_canvas_to_pixmap(full_map_width, full_map_height)
        thumbnail_pixmap = self.full_map_pixmap.scaled(
            thumbnail_width, thumbnail_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.map_thumbnail_label = QLabel()
        self.map_thumbnail_label.setPixmap(thumbnail_pixmap)
        self.map_thumbnail_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # Place summary and thumbnail side by side
        summary_hlayout = QHBoxLayout()
        summary_hlayout.addWidget(self.summary_label, 2)
        summary_hlayout.addWidget(self.map_thumbnail_label, 1)
        layout.addLayout(summary_hlayout)

        # Segment Table (removed "Rest?" column)
        headers = [
            "Segment", "Type", "Distance (km)", "Speed (km/day)", "Speed (km/h)",
            "Time (h)", "Travel Time", "Fatigue", "Terrain", "Fraction of Day", "Travel/Rest Days", "Cumulative Days"
        ]
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(results['segments']))
        cumulative_days = 0.0

        for i, seg in enumerate(results['segments']):
            speed_km_day = seg.get('speed_km_per_day', 0)
            hours_per_day = summary.get('hours_per_day', 8)
            speed_km_hour = seg.get('speed_km_per_hour', speed_km_day / hours_per_day if hours_per_day else 0)
            time_hours = seg.get('time_hours', seg.get('time', 0))
            travel_days = seg.get('fraction_of_day', seg.get('days', 1.0))
            cumulative_days += travel_days if seg['type'] == 'travel' else seg.get('days', 1.0)
            row = [
                str(seg.get('segment', '')),
                seg.get('type', ''),
                f"{seg.get('distance', 0):.2f}",
                f"{speed_km_day:.2f}",
                f"{speed_km_hour:.2f}",
                f"{time_hours:.2f}",
                human_friendly_time_hours(time_hours),
                f"{seg.get('fatigue', 0):.2f}",
                seg.get('terrain', ''),
                f"{travel_days:.2f}",
                f"{seg.get('travel_days', seg.get('days', 1.0)):.2f}",
                f"{cumulative_days:.2f}"
            ]
            for col, value in enumerate(row):
                self.table.setItem(i, col, QTableWidgetItem(value))

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Per-segment summary
        seg_summary_label = QLabel("<b>Per-Segment Summary:</b>")
        layout.addWidget(seg_summary_label)
        self.seg_table = QTableWidget(self)
        self.seg_table.setColumnCount(4)
        self.seg_table.setHorizontalHeaderLabels([
            "Segment", "Distance (km)", "Travel Days", "Rest Days"
        ])
        self.seg_table.setRowCount(len(results['per_segment_summary']))
        for i, seg in enumerate(results['per_segment_summary']):
            self.seg_table.setItem(i, 0, QTableWidgetItem(str(seg['segment'])))
            self.seg_table.setItem(i, 1, QTableWidgetItem(f"{seg['distance_km']:.2f}"))
            self.seg_table.setItem(i, 2, QTableWidgetItem(f"{seg['travel_days']:.2f}"))
            self.seg_table.setItem(i, 3, QTableWidgetItem(f"{seg['rest_days']:.2f}"))
        self.seg_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.seg_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.seg_table)

        # Export and Close buttons
        btn_layout = QHBoxLayout()
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_full_img_btn = QPushButton("Export All as Image")
        export_full_img_btn.clicked.connect(self.export_full_image)
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(export_pdf_btn)
        btn_layout.addWidget(export_full_img_btn)
        btn_layout.addWidget(export_csv_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(self, "Export PDF", "ReportLab is not installed. Please install it to enable PDF export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export as PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # --- TRUE CALCULATIONS ---
        rest_days = sum(seg.get('rest_days', 0) for seg in self.results['per_segment_summary'])
        travel_days = sum(seg.get('travel_days', 0) for seg in self.results['per_segment_summary'])
        total_days = travel_days + rest_days

        total_travel_hours = sum(seg.get('time_hours', 0) for seg in self.results['segments'] if seg.get('type', '') == 'travel')
        total_rest_hours = sum(seg.get('days', 0) * 24 for seg in self.results['segments'] if seg.get('type', '') == 'rest')
        total_hours = total_travel_hours + total_rest_hours

        summary_lines = [
            f"Total Distance: {self.results['total_distance_km']:.2f} km",
            f"Total Time (actual travel): {human_friendly_time_hours(total_travel_hours)}",
        ]
        if rest_days > 0:
            summary_lines.append(f"Total Time (including rest): {human_friendly_time_hours(total_hours)}")
        summary_lines += [
            f"Total Days: {total_days:.2f}",
            f"Travel Days: {travel_days:.2f}",
            f"Rest Days: {rest_days:.2f}",
            f"Average Speed: {self.results['average_km_day']:.2f} km/day ({self.results['average_km_hour']:.2f} km/h)",
            f"Hours per Day: {self.results.get('hours_per_day', 8)}",
            f"Traveler Type: {self.results.get('traveler_type', '')}",
            f"Surface: {self.results['params'].get('surface_type', '')}",
            f"Height: {self.results['params'].get('height', '')} cm",
            f"Horseback: {self.results['params'].get('horseback', False)}",
            f"Horseback Gait: {self.results['params'].get('horseback_gait', '')}",
            f"Custom Profile: {self.results['params'].get('custom_profile', False)}",
        ]
        summary_text = "\n".join(summary_lines)
        elements.append(Paragraph("Historical Journey Results", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(summary_text.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))

        # Add full-res map image to PDF
        temp_img_path = tempfile.mktemp(suffix=".png")
        self.full_map_pixmap.save(temp_img_path, "PNG")
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Travel Path Map", styles['Heading2']))
        elements.append(RLImage(temp_img_path, width=400, height=225))  # Adjust as needed

        # Segment Table (removed "Rest?" column)
        headers = [
            "Segment", "Type", "Distance (km)", "Speed (km/day)", "Speed (km/h)",
            "Time (h)", "Travel Time", "Fatigue", "Terrain", "Fraction of Day", "Travel/Rest Days", "Cumulative Days"
        ]
        seg_data = [headers]
        cumulative_days = 0.0
        for seg in self.results['segments']:
            speed_km_day = seg.get('speed_km_per_day', 0)
            hours_per_day = self.results.get('hours_per_day', 8)
            speed_km_hour = seg.get('speed_km_per_hour', speed_km_day / hours_per_day if hours_per_day else 0)
            time_hours = seg.get('time_hours', seg.get('time', 0))
            travel_days = seg.get('fraction_of_day', seg.get('days', 1.0))
            cumulative_days += travel_days if seg['type'] == 'travel' else seg.get('days', 1.0)
            row = [
                str(seg.get('segment', '')),
                seg.get('type', ''),
                f"{seg.get('distance', 0):.2f}",
                f"{speed_km_day:.2f}",
                f"{speed_km_hour:.2f}",
                f"{time_hours:.2f}",
                human_friendly_time_hours(time_hours),
                f"{seg.get('fatigue', 0):.2f}",
                seg.get('terrain', ''),
                f"{travel_days:.2f}",
                f"{seg.get('travel_days', seg.get('days', 1.0)):.2f}",
                f"{cumulative_days:.2f}"
            ]
            seg_data.append(row)
        t = Table(seg_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(Paragraph("Segment Details", styles['Heading2']))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Per-segment summary
        segsum_headers = ["Segment", "Distance (km)", "Travel Days", "Rest Days"]
        segsum_data = [segsum_headers]
        for seg in self.results['per_segment_summary']:
            segsum_data.append([
                str(seg['segment']),
                f"{seg['distance_km']:.2f}",
                f"{seg['travel_days']:.2f}",
                f"{seg['rest_days']:.2f}"
            ])
        t2 = Table(segsum_data, repeatRows=1)
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(Paragraph("Per-Segment Summary", styles['Heading2']))
        elements.append(t2)
        doc.build(elements)
        QMessageBox.information(self, "Export PDF", f"PDF exported to:\n{path}")

    def export_full_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export All as Image", "", "PNG Files (*.png)")
        if not path:
            return

        summary_pixmap = QPixmap(self.summary_label.size())
        self.summary_label.render(summary_pixmap)

        seg_table = self.table
        seg_total_height = seg_table.horizontalHeader().height()
        for row in range(seg_table.rowCount()):
            seg_total_height += seg_table.rowHeight(row)
        seg_pixmap = QPixmap(seg_table.width(), seg_total_height)
        seg_table.resize(seg_table.width(), seg_total_height)
        seg_table.render(seg_pixmap)

        segsum_table = self.seg_table
        segsum_total_height = segsum_table.horizontalHeader().height()
        for row in range(segsum_table.rowCount()):
            segsum_total_height += segsum_table.rowHeight(row)
        segsum_pixmap = QPixmap(segsum_table.width(), segsum_total_height)
        segsum_table.resize(segsum_table.width(), segsum_total_height)
        segsum_table.render(segsum_pixmap)

        total_height = summary_pixmap.height() + seg_pixmap.height() + segsum_pixmap.height() + 40
        max_width = max(summary_pixmap.width(), seg_pixmap.width(), segsum_pixmap.width())
        final_pixmap = QPixmap(max_width, total_height)
        final_pixmap.fill(Qt.white)
        painter = QPainter(final_pixmap)
        y = 0
        painter.drawPixmap(0, y, summary_pixmap)
        y += summary_pixmap.height() + 10
        painter.drawPixmap(0, y, seg_pixmap)
        y += seg_pixmap.height() + 10
        painter.drawPixmap(0, y, segsum_pixmap)
        painter.end()

        final_pixmap.save(path, "PNG")
        QMessageBox.information(self, "Export Image", f"Image exported to:\n{path}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export as CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        # Ask user where to save the map image
        map_img_path, _ = QFileDialog.getSaveFileName(self, "Save Map Image", "", "PNG Files (*.png)")
        map_img_written = False
        if map_img_path:
            self.full_map_pixmap.save(map_img_path, "PNG")
            map_img_written = True

        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # --- TRUE CALCULATIONS ---
            rest_days = sum(seg.get('rest_days', 0) for seg in self.results['per_segment_summary'])
            travel_days = sum(seg.get('travel_days', 0) for seg in self.results['per_segment_summary'])
            total_days = travel_days + rest_days

            total_travel_hours = sum(seg.get('time_hours', 0) for seg in self.results['segments'] if seg.get('type', '') == 'travel')
            total_rest_hours = sum(seg.get('days', 0) * 24 for seg in self.results['segments'] if seg.get('type', '') == 'rest')
            total_hours = total_travel_hours + total_rest_hours

            writer.writerow(["Total Distance (km)", f"{self.results['total_distance_km']:.2f}"])
            writer.writerow(["Total Time (actual travel)", human_friendly_time_hours(total_travel_hours)])
            if rest_days > 0:
                writer.writerow(["Total Time (including rest)", human_friendly_time_hours(total_hours)])
            writer.writerow(["Total Days", f"{total_days:.2f}"])
            writer.writerow(["Travel Days", f"{travel_days:.2f}"])
            writer.writerow(["Rest Days", f"{rest_days:.2f}"])
            writer.writerow(["Average Speed (km/day)", f"{self.results['average_km_day']:.2f}"])
            writer.writerow(["Average Speed (km/h)", f"{self.results['average_km_hour']:.2f}"])
            writer.writerow(["Hours per Day", f"{self.results.get('hours_per_day', 8)}"])
            writer.writerow(["Traveler Type", self.results.get('traveler_type', '')])
            writer.writerow(["Surface", self.results['params'].get('surface_type', '')])
            writer.writerow(["Height (cm)", self.results['params'].get('height', '')])
            writer.writerow(["Horseback", self.results['params'].get('horseback', False)])
            writer.writerow(["Horseback Gait", self.results['params'].get('horseback_gait', '')])
            writer.writerow(["Custom Profile", self.results['params'].get('custom_profile', False)])
            if map_img_written:
                writer.writerow(["Map Image", map_img_path])
            writer.writerow([])

            headers = [
                "Segment", "Type", "Distance (km)", "Speed (km/day)", "Speed (km/h)",
                "Time (h)", "Travel Time", "Fatigue", "Terrain", "Fraction of Day", "Travel/Rest Days", "Cumulative Days"
            ]
            writer.writerow(headers)
            cumulative_days = 0.0
            for seg in self.results['segments']:
                speed_km_day = seg.get('speed_km_per_day', 0)
                hours_per_day = self.results.get('hours_per_day', 8)
                speed_km_hour = seg.get('speed_km_per_hour', speed_km_day / hours_per_day if hours_per_day else 0)
                time_hours = seg.get('time_hours', seg.get('time', 0))
                travel_days = seg.get('fraction_of_day', seg.get('days', 1.0))
                cumulative_days += travel_days if seg['type'] == 'travel' else seg.get('days', 1.0)
                row = [
                    str(seg.get('segment', '')),
                    seg.get('type', ''),
                    f"{seg.get('distance', 0):.2f}",
                    f"{speed_km_day:.2f}",
                    f"{speed_km_hour:.2f}",
                    f"{time_hours:.2f}",
                    human_friendly_time_hours(time_hours),
                    f"{seg.get('fatigue', 0):.2f}",
                    seg.get('terrain', ''),
                    f"{travel_days:.2f}",
                    f"{seg.get('travel_days', seg.get('days', 1.0)):.2f}",
                    f"{cumulative_days:.2f}"
                ]
                writer.writerow(row)
            writer.writerow([])

            writer.writerow(["Per-Segment Summary"])
            writer.writerow(["Segment", "Distance (km)", "Travel Days", "Rest Days"])
            for seg in self.results['per_segment_summary']:
                writer.writerow([
                    str(seg['segment']),
                    f"{seg['distance_km']:.2f}",
                    f"{seg['travel_days']:.2f}",
                    f"{seg['rest_days']:.2f}"
                ])
        QMessageBox.information(self, "Export CSV", f"CSV exported to:\n{path}")
=======
        self.setWindowTitle("Travel Time Results")
        self.setMinimumSize(1000, 700)
        self.results = results
        
        layout = QVBoxLayout()
        
        # Summary Section
        summary = self.create_summary_section()
        layout.addWidget(summary)
        
        # Table with detailed segment data
        self.table = self.create_results_table()
        layout.addWidget(self.table)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setToolTip("Export results to CSV file")
        self.export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_btn)
        
        self.copy_btn = QPushButton("Copy Summary")
        self.copy_btn.setToolTip("Copy summary to clipboard")
        self.copy_btn.clicked.connect(self.copy_summary)
        button_layout.addWidget(self.copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_summary_section(self):
        summary = QLabel()
        summary.setFont(QFont('Arial', 10))
        summary.setTextFormat(Qt.RichText)
        
        try:
            traveler_type = self.results.get('traveler_type', 'pedestrian').replace('_', ' ').title()
            total_distance_km = self.results['total_distance'] / 1000
            
            summary_text = f"""
            <div style='margin-bottom: 10px;'>
                <h3 style='color: #2c3e50;'>Travel Summary</h3>
                <table style='width:100%'>
                    <tr><td style='width:40%;'><b>Traveler Type:</b></td><td>{traveler_type}</td></tr>
                    <tr><td><b>Total Distance:</b></td><td>{total_distance_km:.2f} km ({self.results['total_distance']:.0f} m)</td></tr>
                    <tr><td><b>Total Time:</b></td><td>{self.results['formatted_time']}</td></tr>
                    {self.get_historical_text() if self.results.get('historical') else f"<tr><td><b>Estimated Days:</b></td><td>{self.results['days_required']:.1f}</td></tr>"}
                </table>
            </div>
            """
            
        except Exception as e:
            summary_text = f"<div style='color: red;'>Error generating summary: {str(e)}</div>"
        
        summary.setText(summary_text)
        return summary

    def get_historical_text(self):
        ha = self.results['params']['historical_analysis']
        season_effect = {
            'summer': "Normal conditions",
            'winter': "Severe conditions (-30% speed)",
            'spring': "Mild conditions (-10% speed)", 
            'fall': "Mild conditions (-10% speed)"
        }.get(ha['season'], "")
        
        march_effect = {
            'normal': "Standard march (5 days march, 2 days rest)",
            'forced': "Forced march (7 days march, 1 day rest)"
        }.get(ha['march_type'], "")
        
        supply_effect = "With additional supplies (-20% speed)" if ha['with_supply'] else ""
        
        recovery_rate = {
            'normal': "Standard recovery (2 rest days per week)",
            'forced': "Limited recovery (1 rest day per week)"
        }.get(ha['march_type'], "")
        
        return f"""
            <tr><td colspan='2'><hr></td></tr>
            <tr><td><b>Historical Analysis:</b></td><td></td></tr>
            <tr><td><b>March Type:</b></td><td>{ha['march_type'].capitalize()} ({march_effect})</td></tr>
            <tr><td><b>Season:</b></td><td>{ha['season'].capitalize()} ({season_effect})</td></tr>
            {f"<tr><td><b>Supplies:</b></td><td>{supply_effect}</td></tr>" if ha['with_supply'] else ""}
            <tr><td><b>Recovery Cycle:</b></td><td>{recovery_rate}</td></tr>
            <tr><td><b>Daily March Time:</b></td><td>{self.results.get('daily_march_hours', 8)} hours/day</td></tr>
            <tr><td><b>Total March Time:</b></td><td>{self.results['formatted_time']}</td></tr>
            <tr><td><b>Effective Days:</b></td><td>{self.results['days_required']:.1f} (including {self.results['rest_days']} rest days)</td></tr>
            <tr><td><b>Final Fatigue:</b></td><td>{self.results['fatigue']*100:.1f}% ({(100-self.results['fatigue']*100):.1f}% recovered)</td></tr>
            <tr><td><b>Health Impact:</b></td><td>{self.get_health_impact()}</td></tr>
        """

    def get_health_impact(self):
        fatigue = self.results['fatigue']
        if fatigue > 0.9:
            return "Minimal impact (well-rested)"
        elif fatigue > 0.7:
            return "Moderate fatigue (manageable)"
        elif fatigue > 0.5:
            return "Significant fatigue (recovery needed)"
        else:
            return "Severe fatigue (health risk)"

    def create_results_table(self):
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        
        if self.results.get('segments'):
            headers = ["Segment", "Type", "Distance (km)", "Speed (km/h)", 
                      "Time (min)", "Fatigue %", "Terrain"]
            
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(self.results['segments']))
            
            for i, segment in enumerate(self.results['segments']):
                bg_color = QColor(240, 240, 240) if i % 2 == 0 else QColor(255, 255, 255)
                
                def create_item(value, alignment=Qt.AlignRight|Qt.AlignVCenter):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(alignment)
                    item.setBackground(bg_color)
                    return item
                
                table.setItem(i, 0, create_item(i+1, Qt.AlignCenter))
                table.setItem(i, 1, create_item(segment['type'].title(), Qt.AlignCenter))
                table.setItem(i, 2, create_item(f"{segment['distance']:.3f}"))
                table.setItem(i, 3, create_item(f"{segment.get('speed', 0):.1f}"))
                table.setItem(i, 4, create_item(f"{(segment['distance'] / segment['speed'] * 60) if segment['type'] == 'travel' else 0:.1f}"))
                table.setItem(i, 5, create_item(f"{segment.get('fatigue', 0)*100:.1f}"))
                table.setItem(i, 6, create_item(segment.get('terrain', '').title(), Qt.AlignCenter))
            
            table.resizeColumnsToContents()
            
        return table

    def export_to_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"travel_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([self.table.horizontalHeaderItem(col).text() 
                               for col in range(self.table.columnCount())])
                
                for row in range(self.table.rowCount()):
                    writer.writerow([
                        self.table.item(row, col).text() 
                        for col in range(self.table.columnCount())
                    ])
                    
            QMessageBox.information(self, "Success", f"Exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def copy_summary(self):
        try:
            clipboard = QApplication.clipboard()
            text = f"""Travel Summary:
Traveler: {self.results.get('traveler_type', '').replace('_', ' ').title()}
Distance: {self.results['total_distance']/1000:.2f} km
Time: {self.results['formatted_time']}
Days Required: {self.results.get('days_required', 0):.1f} (including {self.results.get('rest_days', 0)} rest days)
Final Fatigue: {self.results.get('fatigue', 1.0)*100:.1f}%
Health Impact: {self.get_health_impact()}
"""
            clipboard.setText(text)
            QMessageBox.information(self, "Copied", "Summary copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Copy failed: {str(e)}")
>>>>>>> b6f3842c1e58bb1c19a7809f755bdfe08faa3cc4
