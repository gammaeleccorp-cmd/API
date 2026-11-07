from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

mobile_validator = RegexValidator(
    regex=r"^09[0-9]{9}$",
    message="Mobile must start with 09 and be 11 digits.",
)

national_id_format_validator = RegexValidator(
    regex=r"^[0-9]{10}$",
    message="National ID must be exactly 10 digits.",
)


def validate_national_id_checksum(value):
    """Check the control digit of a 10-digit Iranian national ID."""
    if not (len(value) == 10 and value.isascii() and value.isdigit()):
        return  # the format validator reports this case
    if len(set(value)) == 1:
        raise ValidationError("Invalid national ID.")
    digits = [int(c) for c in value]
    total = sum(digits[i] * (10 - i) for i in range(9))
    remainder = total % 11
    check = remainder if remainder < 2 else 11 - remainder
    if digits[9] != check:
        raise ValidationError("Invalid national ID checksum.")
