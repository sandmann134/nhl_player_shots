
import datetime

def get_current_season():
    """
    Determines the current NHL season based on the current date.
    The NHL season typically starts in October.
    Returns the season in YYYYYYYY format (e.g., 20252026).
    """
    now = datetime.datetime.now()
    if now.month >= 10:
        return f"{now.year}{now.year + 1}"
    else:
        return f"{now.year - 1}{now.year}"
