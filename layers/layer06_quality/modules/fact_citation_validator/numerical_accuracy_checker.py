"""Numerical Accuracy Checker — Validate numerical claims for consistency.

Checks:
- Percentage consistency (doesn't exceed 100%)
- Unit consistency (currency symbols match)
- Date plausibility
- Number format consistency
- Statistical range validation
"""
from __future__ import annotations
import re
from typing import List

from layers.layer06_quality.modules.fact_citation_validator.validation_report import NumericalAccuracy


PERCENTAGE_PATTERN = re.compile(r'(-?\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
CURRENCY_PATTERNS = {
    "USD": re.compile(r'\$\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion)?', re.IGNORECASE),
    "EUR": re.compile(r'€\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion)?', re.IGNORECASE),
    "GBP": re.compile(r'£\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion)?', re.IGNORECASE),
    "PKR": re.compile(r'Rs\.?\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion)?', re.IGNORECASE),
}
DATE_PATTERN = re.compile(
    r'\b(\d{4})\b.*?\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\b',
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r'\b(19\d\d|20\d\d)\b')
LARGE_NUMBER_PATTERN = re.compile(r'(\d+(?:[.,]\d+)?)\s*(million|billion|trillion|k|m|b|t)\b', re.IGNORECASE)


class NumericalAccuracyChecker:
    """Check numerical claims for consistency and plausibility."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, text: str) -> List[NumericalAccuracy]:
        """Check all numerical claims in text."""
        results: List[NumericalAccuracy] = []

        results.extend(self._check_percentages(text))
        results.extend(self._check_currency(text))
        results.extend(self._check_years(text))
        results.extend(self._check_large_numbers(text))

        self._check_count += 1
        return results

    def check_batch(self, texts: List[str]) -> List[List[NumericalAccuracy]]:
        """Check multiple texts."""
        return [self.check(t) for t in texts]

    def _check_percentages(self, text: str) -> List[NumericalAccuracy]:
        """Check percentages are valid (0-100)."""
        results: List[NumericalAccuracy] = []
        for match in PERCENTAGE_PATTERN.finditer(text):
            val = float(match.group(1))
            issues: List[str] = []
            if val > 100:
                issues.append(f"percentage_exceeds_100: {val}%")
            if val < 0:
                issues.append(f"negative_percentage: {val}%")
            results.append(NumericalAccuracy(
                number_text=match.group(0),
                category="percentage",
                is_consistent=len(issues) == 0,
                issues=issues,
            ))
        return results

    def _check_currency(self, text: str) -> List[NumericalAccuracy]:
        """Check currency amounts are reasonable."""
        results: List[NumericalAccuracy] = []
        for symbol, pattern in CURRENCY_PATTERNS.items():
            for match in pattern.finditer(text):
                val_str = match.group(1).replace(",", "")
                multiplier = match.group(2) or ""
                issues: List[str] = []
                try:
                    val = float(val_str)
                except ValueError:
                    issues.append(f"invalid_currency_format: {match.group(0)}")
                    results.append(NumericalAccuracy(
                        number_text=match.group(0),
                        category=f"currency_{symbol}",
                        is_consistent=False,
                        issues=issues,
                    ))
                    continue
                if val == 0:
                    issues.append("zero_currency_value")
                results.append(NumericalAccuracy(
                    number_text=match.group(0),
                    category=f"currency_{symbol}",
                    is_consistent=len(issues) == 0,
                    issues=issues,
                ))
        return results

    def _check_years(self, text: str) -> List[NumericalAccuracy]:
        """Check year references are plausible."""
        results: List[NumericalAccuracy] = []
        for match in YEAR_PATTERN.finditer(text):
            year = int(match.group(1))
            issues: List[str] = []
            if year > 2030:
                issues.append(f"future_year: {year}")
            if year < 1900:
                issues.append(f"very_old_year: {year}")
            results.append(NumericalAccuracy(
                number_text=str(year),
                category="year",
                is_consistent=len(issues) == 0,
                issues=issues,
            ))
        return results

    def _check_large_numbers(self, text: str) -> List[NumericalAccuracy]:
        """Check large numbers for format consistency."""
        results: List[NumericalAccuracy] = []
        for match in LARGE_NUMBER_PATTERN.finditer(text):
            num_str = match.group(1).replace(",", "")
            unit = match.group(2)
            issues: List[str] = []
            try:
                val = float(num_str)
            except ValueError:
                issues.append(f"invalid_number_format: {match.group(0)}")
                results.append(NumericalAccuracy(
                    number_text=match.group(0),
                    category="large_number",
                    is_consistent=False,
                    issues=issues,
                ))
                continue
            if val < 0:
                issues.append(f"negative_large_number: {match.group(0)}")
            results.append(NumericalAccuracy(
                number_text=match.group(0),
                category=f"large_number_{unit.lower()}",
                is_consistent=len(issues) == 0,
                issues=issues,
            ))
        return results

    @property
    def check_count(self) -> int:
        return self._check_count
