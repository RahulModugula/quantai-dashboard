"""Data quality monitoring and validation."""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class DataQualityCheck:
    """Check results for data quality."""

    def __init__(self, name: str, passed: bool, message: str):
        """Initialize check result."""
        self.name = name
        self.passed = passed
        self.message = message
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class DataQualityMonitor:
    """Monitor data quality across the system."""

    def __init__(self):
        """Initialize quality monitor."""
        self.checks: List[DataQualityCheck] = []
        self.thresholds = {
            "null_rate": 0.05,  # 5% max null values
            "duplicate_rate": 0.01,  # 1% max duplicates
            "outlier_rate": 0.05,  # 5% max outliers
            "missing_fields_rate": 0.02,  # 2% max missing fields
        }

    def check_null_values(self, data: List[Dict], name: str = "null_check") -> DataQualityCheck:
        """Check for excessive null values."""
        if not data:
            return DataQualityCheck(name, True, "No data to check")

        total_fields = len(data) * len(data[0])
        null_count = sum(
            sum(1 for v in row.values() if v is None) for row in data
        )
        null_rate = null_count / total_fields if total_fields > 0 else 0

        passed = null_rate <= self.thresholds["null_rate"]
        message = f"Null value rate: {null_rate:.2%}"

        check = DataQualityCheck(name, passed, message)
        self.checks.append(check)
        return check

    def check_duplicates(self, data: List[Dict], key: str, name: str = "duplicate_check") -> DataQualityCheck:
        """Check for duplicate values."""
        if not data:
            return DataQualityCheck(name, True, "No data to check")

        keys = [row.get(key) for row in data]
        unique_count = len(set(k for k in keys if k is not None))
        duplicate_rate = 1 - (unique_count / len(keys)) if keys else 0

        passed = duplicate_rate <= self.thresholds["duplicate_rate"]
        message = f"Duplicate rate: {duplicate_rate:.2%}"

        check = DataQualityCheck(name, passed, message)
        self.checks.append(check)
        return check

    def check_outliers(self, values: List[float], name: str = "outlier_check") -> DataQualityCheck:
        """Check for outliers using IQR method."""
        if len(values) < 4:
            return DataQualityCheck(name, True, "Insufficient data for outlier detection")

        values_array = np.array(values)
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = sum(1 for v in values if v < lower_bound or v > upper_bound)
        outlier_rate = outliers / len(values) if values else 0

        passed = outlier_rate <= self.thresholds["outlier_rate"]
        message = f"Outlier rate: {outlier_rate:.2%} (bounds: {lower_bound:.2f} - {upper_bound:.2f})"

        check = DataQualityCheck(name, passed, message)
        self.checks.append(check)
        return check

    def check_missing_fields(self, data: List[Dict], required_fields: List[str], name: str = "missing_check") -> DataQualityCheck:
        """Check for missing required fields."""
        if not data:
            return DataQualityCheck(name, True, "No data to check")

        missing_count = 0
        for row in data:
            for field in required_fields:
                if field not in row:
                    missing_count += 1

        missing_rate = missing_count / (len(data) * len(required_fields)) if data else 0
        passed = missing_rate <= self.thresholds["missing_fields_rate"]
        message = f"Missing field rate: {missing_rate:.2%}"

        check = DataQualityCheck(name, passed, message)
        self.checks.append(check)
        return check

    def check_data_consistency(self, data: List[Dict], field_types: Dict[str, type], name: str = "consistency_check") -> DataQualityCheck:
        """Check data type consistency."""
        inconsistencies = 0

        for row in data:
            for field, expected_type in field_types.items():
                if field in row:
                    value = row[field]
                    if value is not None and not isinstance(value, expected_type):
                        inconsistencies += 1

        total_checks = len(data) * len(field_types)
        consistency_rate = 1 - (inconsistencies / total_checks) if total_checks > 0 else 1

        passed = consistency_rate >= 0.95  # Allow 5% inconsistency
        message = f"Data consistency rate: {consistency_rate:.2%}"

        check = DataQualityCheck(name, passed, message)
        self.checks.append(check)
        return check

    def get_report(self) -> Dict:
        """Get data quality report."""
        if not self.checks:
            return {"status": "no_checks", "message": "No checks performed"}

        passed_checks = sum(1 for c in self.checks if c.passed)
        total_checks = len(self.checks)
        pass_rate = passed_checks / total_checks if total_checks > 0 else 0

        return {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "pass_rate": round(pass_rate * 100, 2),
            "status": "pass" if pass_rate == 1.0 else "warn" if pass_rate >= 0.8 else "fail",
            "checks": [c.to_dict() for c in self.checks[-20:]],  # Last 20 checks
        }

    def reset(self):
        """Reset all checks."""
        self.checks = []
        logger.info("Data quality checks reset")


# Global data quality monitor
_monitor = DataQualityMonitor()


def get_monitor() -> DataQualityMonitor:
    """Get global data quality monitor."""
    return _monitor
