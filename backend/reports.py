"""PDF compliance report generation (fpdf2)."""
import os
from datetime import datetime
from fpdf import FPDF
from sqlalchemy.orm import Session
from . import models
from . import app_config

REPORTS_DIR = app_config.REPORT_DIR


class ComplianceReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Restricted Zone Compliance Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Automated Contraband Detection System  |  Final Year Project - University of Lahore",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_pdf(db: Session, date_from=None, date_to=None, zone_id=None) -> str:
    """Aggregate incidents and write a PDF report. Returns the file path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    q = db.query(models.Incident).join(models.Zone)
    if date_from:
        q = q.filter(models.Incident.timestamp >= date_from)
    if date_to:
        q = q.filter(models.Incident.timestamp <= date_to)
    if zone_id:
        q = q.filter(models.Incident.zone_id == zone_id)
    incidents = q.order_by(models.Incident.timestamp.desc()).all()

    by_type, by_zone = {}, {}
    for inc in incidents:
        by_type[inc.violation_type] = by_type.get(inc.violation_type, 0) + 1
        by_zone[inc.zone.name] = by_zone.get(inc.zone.name, 0) + 1

    pdf = ComplianceReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    filt = f"Date: {date_from or 'all'} to {date_to or 'all'} | Zone: {zone_id or 'all'}"
    pdf.cell(0, 7, f"Filters - {filt}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Total incidents: {len(incidents)}", new_x="LMARGIN", new_y="NEXT")
    for vtype, n in by_type.items():
        pdf.cell(0, 7, f"  - {vtype}: {n}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Incidents by Zone", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for zone, n in by_zone.items():
        pdf.cell(0, 7, f"  - {zone}: {n}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Incident Log", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 8)
    col_w = [12, 34, 30, 34, 22, 58]
    for w, h in zip(col_w, ["ID", "Timestamp", "Type", "Zone", "Conf.", "Evidence"]):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    for inc in incidents[:500]:  # cap at 500 rows per report
        pdf.cell(col_w[0], 6, str(inc.id), border=1)
        pdf.cell(col_w[1], 6, inc.timestamp.strftime("%Y-%m-%d %H:%M"), border=1)
        pdf.cell(col_w[2], 6, inc.violation_type, border=1)
        pdf.cell(col_w[3], 6, inc.zone.name[:18], border=1)
        pdf.cell(col_w[4], 6, f"{inc.confidence:.2f}", border=1)
        pdf.cell(col_w[5], 6, os.path.basename(inc.evidence_path)[:32], border=1)
        pdf.ln()

    fname = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(REPORTS_DIR, fname)
    pdf.output(path)
    return path
