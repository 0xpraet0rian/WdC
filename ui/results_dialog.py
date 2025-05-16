from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
                                QTableWidgetItem, QLabel, QPushButton,
                                QHBoxLayout, QFileDialog, QMessageBox,
                                QApplication)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import Qt
import csv
from datetime import datetime

class ResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
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