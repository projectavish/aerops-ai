"""PDF report export for aviation operations."""
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st


def generate_pdf_report(ops_df: pd.DataFrame, delays_df: pd.DataFrame,
                        metrics: dict, filters: dict) -> bytes | None:
    """Generate a PDF operations report."""
    try:
        from fpdf import FPDF

        class AerOpsPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 16)
                self.set_text_color(14, 165, 233)
                self.cell(0, 10, "AeroOps AI - Operations Intelligence Report", 0, 1, "C")
                self.set_font("Helvetica", "", 10)
                self.set_text_color(100, 116, 139)
                self.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC", 0, 1, "C")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f"Page {self.page_no()} | AeroOps AI", 0, 0, "C")

        pdf = AerOpsPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Executive Summary
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, "Executive Summary", 0, 1)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)

        pdf.multi_cell(0, 6, (
            f"Analyzing {metrics['total_flights']:,} flights. "
            f"OTP: {metrics['otp_rate']:.1f}% | "
            f"Delayed: {metrics['delayed']:,} ({metrics['delay_rate']:.1f}%) | "
            f"Avg delay: {metrics['avg_delay_min']:.0f}min | "
            f"Critical (>60min): {metrics['critical_delays']:,}"
        ))
        pdf.ln(5)

        # Active Filters
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Active Filters", 0, 1)
        pdf.set_font("Helvetica", "", 10)
        for key, val in filters.items():
            pdf.cell(0, 6, f"  {key}: {val}", 0, 1)
        pdf.ln(5)

        # Top delay routes
        if delays_df is not None and not delays_df.empty and "route" in delays_df.columns:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Top Delay Routes", 0, 1)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(14, 165, 233)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(40, 7, "Route", 1, 0, "C", True)
            pdf.cell(30, 7, "Delays", 1, 0, "C", True)
            pdf.cell(35, 7, "Avg Min", 1, 0, "C", True)
            pdf.cell(35, 7, "Total Min", 1, 0, "C", True)
            pdf.cell(50, 7, "Category", 1, 1, "C", True)

            pdf.set_text_color(71, 85, 105)
            pdf.set_font("Helvetica", "", 9)

            route_stats = delays_df.groupby("route").agg(
                count=("is_delayed", "count"),
                avg_delay=("arr_delay_minutes", "mean"),
                total_delay=("arr_delay_minutes", "sum"),
            ).sort_values("total_delay", ascending=False)

            for route, row in route_stats.head(15).iterrows():
                cat = ""
                route_data = delays_df[delays_df["route"] == route]
                if "iata_delay_category" in route_data.columns:
                    top_cat = route_data["iata_delay_category"].dropna().value_counts()
                    cat = top_cat.index[0] if len(top_cat) > 0 else ""

                pdf.cell(40, 6, str(route)[:15], 1)
                pdf.cell(30, 6, str(int(row["count"])), 1, 0, "C")
                pdf.cell(35, 6, f"{row['avg_delay']:.0f}", 1, 0, "C")
                pdf.cell(35, 6, f"{row['total_delay']:.0f}", 1, 0, "C")
                pdf.cell(50, 6, str(cat)[:20], 1)
                pdf.ln()

        return pdf.output(dest="BYTES")

    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        with st.expander("Error details"):
            st.code(traceback.format_exc())
        return None
