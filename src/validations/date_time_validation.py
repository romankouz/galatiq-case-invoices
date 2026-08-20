from datetime import datetime

def validate_datetime_str(datetime_str: str) -> bool:
    try:
        valid_formats = [
            "%Y-%m-%d",            # 2026-01-25
            "%Y/%m/%d",            # 2026/01/25
            "%d-%m-%Y",            # 25-01-2026
            "%d/%m/%Y",            # 25/01/2026
            "%Y-%m-%dT%H:%M:%S",   # 2026-01-25T13:45:00
            "%Y-%m-%d %H:%M:%S",   # 2026-01-25 13:45:00
        ]
        for fmt in valid_formats:
            try:
                datetime.strptime(datetime_str, fmt)
                return True
            except ValueError:
                continue
    except ValueError:
        return False