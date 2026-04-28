from datetime import date

def calculate_age(birth_date_str: str) -> int:
    """
    Calculates age from a DOB string in YYYY-MM-DD format.
    """
    if not birth_date_str:
        return 25 # Default if unknown
    try:
        birth_date = date.fromisoformat(birth_date_str)
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception:
        return 25
