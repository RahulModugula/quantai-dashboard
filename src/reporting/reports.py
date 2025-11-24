"""Reporting and report generation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Report types."""

    PERFORMANCE = "performance"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    COMPLIANCE = "compliance"
    TRADING = "trading"


class ReportFormat(str, Enum):
    """Report output formats."""

    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"


class Report:
    """Generated report."""

    def __init__(
        self,
        title: str,
        report_type: ReportType,
        data: Dict[str, Any],
    ):
        """Initialize report.

        Args:
            title: Report title
            report_type: Type of report
            data: Report data
        """
        self.report_id = f"report_{datetime.now().timestamp()}"
        self.title = title
        self.report_type = report_type
        self.data = data
        self.created_at = datetime.now()
        self.generated_at = None
        self.format = ReportFormat.JSON

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "type": self.report_type.value,
            "created_at": self.created_at.isoformat(),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "data": self.data,
        }


class ReportGenerator:
    """Generate reports."""

    def __init__(self):
        """Initialize report generator."""
        self.reports: Dict[str, Report] = {}
        self.templates = {}

    def create_report(
        self,
        title: str,
        report_type: ReportType,
        data: Dict[str, Any],
    ) -> Report:
        """Create a report.

        Args:
            title: Report title
            report_type: Report type
            data: Report data

        Returns:
            Created report
        """
        report = Report(title, report_type, data)
        self.reports[report.report_id] = report

        logger.info(f"Report created: {title} (ID: {report.report_id})")

        return report

    def generate_performance_report(self, metrics: Dict[str, Any]) -> Report:
        """Generate performance report.

        Args:
            metrics: Performance metrics

        Returns:
            Performance report
        """
        report = Report(
            "Performance Report",
            ReportType.PERFORMANCE,
            {
                "metrics": metrics,
                "generated_at": datetime.now().isoformat(),
            },
        )
        self.reports[report.report_id] = report

        logger.info(f"Performance report generated: {report.report_id}")

        return report

    def generate_risk_report(self, risk_data: Dict[str, Any]) -> Report:
        """Generate risk report.

        Args:
            risk_data: Risk metrics and data

        Returns:
            Risk report
        """
        report = Report(
            "Risk Report",
            ReportType.RISK,
            {
                "risk_data": risk_data,
                "generated_at": datetime.now().isoformat(),
            },
        )
        self.reports[report.report_id] = report

        logger.info(f"Risk report generated: {report.report_id}")

        return report

    def generate_portfolio_report(self, portfolio_data: Dict[str, Any]) -> Report:
        """Generate portfolio report.

        Args:
            portfolio_data: Portfolio information

        Returns:
            Portfolio report
        """
        report = Report(
            "Portfolio Report",
            ReportType.PORTFOLIO,
            {
                "portfolio": portfolio_data,
                "generated_at": datetime.now().isoformat(),
            },
        )
        self.reports[report.report_id] = report

        logger.info(f"Portfolio report generated: {report.report_id}")

        return report

    def export_report(
        self,
        report_id: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> Optional[str]:
        """Export report in specified format.

        Args:
            report_id: Report ID
            format: Export format

        Returns:
            Exported report data
        """
        if report_id not in self.reports:
            logger.error(f"Report not found: {report_id}")
            return None

        report = self.reports[report_id]
        report.format = format
        report.generated_at = datetime.now()

        logger.info(f"Report exported: {report_id} as {format.value}")

        return str(report.to_dict())

    def get_report(self, report_id: str) -> Optional[Dict]:
        """Get report by ID."""
        if report_id in self.reports:
            return self.reports[report_id].to_dict()

        return None

    def list_reports(self, report_type: Optional[ReportType] = None) -> List[Dict]:
        """List reports.

        Args:
            report_type: Filter by report type

        Returns:
            List of reports
        """
        reports = list(self.reports.values())

        if report_type:
            reports = [r for r in reports if r.report_type == report_type]

        return [
            r.to_dict()
            for r in sorted(
                reports,
                key=lambda r: r.created_at,
                reverse=True,
            )
        ]

    def get_stats(self) -> Dict:
        """Get report generation statistics."""
        return {
            "total_reports": len(self.reports),
            "by_type": {
                report_type.value: len(
                    [r for r in self.reports.values() if r.report_type == report_type]
                )
                for report_type in ReportType
            },
        }


# Global report generator
_generator = ReportGenerator()


def get_generator() -> ReportGenerator:
    """Get global report generator."""
    return _generator


def create_report(
    title: str,
    report_type: ReportType,
    data: Dict[str, Any],
) -> Report:
    """Create report globally."""
    generator = get_generator()
    return generator.create_report(title, report_type, data)
