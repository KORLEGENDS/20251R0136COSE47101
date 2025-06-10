#!/usr/bin/env python3
import re

def convert_year_month(korean_str):
    """Convert Korean date strings to 'YYYY-MM'. Supports 'YYYY년 M월' and 'YYYY.MM 월'."""
    s = str(korean_str)
    # Pattern: 'YYYY년 M월'
    m = re.match(r"(\d{4})년\s*(\d{1,2})월", s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}"
    # Pattern: 'YYYY.MM 월'
    parts = s.split()
    if parts:
        dot = parts[0]
        m2 = re.match(r"(\d{4})\.(\d{1,2})", dot)
        if m2:
            return f"{m2.group(1)}-{m2.group(2).zfill(2)}"
    return None 