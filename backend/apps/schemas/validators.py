import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class ValidationErrorDetail:
    def __init__(self, field_name, error_code, error_message, row_number=None):
        self.field_name = field_name
        self.error_code = error_code
        self.error_message = error_message
        self.row_number = row_number

    def to_dict(self):
        return {
            "field_name": self.field_name,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "row_number": self.row_number,
        }


def parse_and_validate_value(field, raw_value, row_number=None):
    """
    Parses and validates a single value against a DatasetField specification.
    Returns (cleaned_value, error_or_none).
    """
    field_name = field.field_name
    rules = field.validation_rules or {}

    # Check empty/null
    is_empty = raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == "")
    if is_empty:
        if field.default_value is not None and field.default_value != "":
            raw_value = field.default_value
            is_empty = False
        elif field.is_required:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="REQUIRED_FIELD_MISSING",
                error_message=f"Field '{field.display_name or field_name}' is required.",
                row_number=row_number,
            )
        else:
            return None, None

    cleaned_value = raw_value

    # Type Validation
    f_type = field.field_type
    if f_type == "string":
        cleaned_value = str(raw_value).strip()
        length = len(cleaned_value)
        if "min_length" in rules and length < rules["min_length"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="STRING_TOO_SHORT",
                error_message=f"Length {length} is less than required minimum {rules['min_length']}.",
                row_number=row_number,
            )
        if "max_length" in rules and length > rules["max_length"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="STRING_TOO_LONG",
                error_message=f"Length {length} exceeds allowed maximum {rules['max_length']}.",
                row_number=row_number,
            )
        if "allowed_values" in rules and cleaned_value not in rules["allowed_values"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="VALUE_NOT_ALLOWED",
                error_message=f"Value '{cleaned_value}' is not in permitted choices {rules['allowed_values']}.",
                row_number=row_number,
            )
        if "regex" in rules:
            try:
                pattern = re.compile(rules["regex"])
                if not pattern.search(cleaned_value):
                    return None, ValidationErrorDetail(
                        field_name=field_name,
                        error_code="PATTERN_MISMATCH",
                        error_message=f"Value does not match required format pattern '{rules['regex']}'.",
                        row_number=row_number,
                    )
            except re.error:
                pass

    elif f_type == "integer":
        try:
            cleaned_value = int(str(raw_value).strip())
        except (ValueError, TypeError):
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_INTEGER",
                error_message=f"'{raw_value}' is not a valid integer.",
                row_number=row_number,
            )
        if "min_value" in rules and cleaned_value < rules["min_value"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="NUMBER_TOO_SMALL",
                error_message=f"Value {cleaned_value} is less than minimum {rules['min_value']}.",
                row_number=row_number,
            )
        if "max_value" in rules and cleaned_value > rules["max_value"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="NUMBER_TOO_LARGE",
                error_message=f"Value {cleaned_value} is greater than maximum {rules['max_value']}.",
                row_number=row_number,
            )

    elif f_type == "decimal":
        try:
            dec = Decimal(str(raw_value).strip())
            cleaned_value = float(dec)
        except (InvalidOperation, ValueError, TypeError):
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_DECIMAL",
                error_message=f"'{raw_value}' is not a valid decimal number.",
                row_number=row_number,
            )
        if "min_value" in rules and cleaned_value < rules["min_value"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="NUMBER_TOO_SMALL",
                error_message=f"Value {cleaned_value} is less than minimum {rules['min_value']}.",
                row_number=row_number,
            )
        if "max_value" in rules and cleaned_value > rules["max_value"]:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="NUMBER_TOO_LARGE",
                error_message=f"Value {cleaned_value} is greater than maximum {rules['max_value']}.",
                row_number=row_number,
            )

    elif f_type == "boolean":
        val_str = str(raw_value).strip().lower()
        if val_str in ("true", "1", "t", "yes", "y"):
            cleaned_value = True
        elif val_str in ("false", "0", "f", "no", "n"):
            cleaned_value = False
        else:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_BOOLEAN",
                error_message=f"'{raw_value}' is not a valid boolean (use true/false, 1/0, yes/no).",
                row_number=row_number,
            )

    elif f_type == "email":
        val_str = str(raw_value).strip().lower()
        if not EMAIL_REGEX.match(val_str):
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_EMAIL",
                error_message=f"'{raw_value}' is not a valid email address.",
                row_number=row_number,
            )
        cleaned_value = val_str

    elif f_type == "date":
        val_str = str(raw_value).strip()
        parsed = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(val_str, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_DATE",
                error_message=f"'{raw_value}' is not a valid date format (expected YYYY-MM-DD).",
                row_number=row_number,
            )
        cleaned_value = parsed.isoformat()

    elif f_type == "datetime":
        val_str = str(raw_value).strip()
        parsed = None
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.strptime(val_str, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return None, ValidationErrorDetail(
                field_name=field_name,
                error_code="INVALID_DATETIME",
                error_message=f"'{raw_value}' is not a valid ISO datetime format.",
                row_number=row_number,
            )
        cleaned_value = parsed.isoformat()

    return cleaned_value, None


def validate_row_against_schema(schema_fields, row_dict, row_number=None):
    """
    Validates a dictionary of row values against a list of DatasetField objects.
    Returns (cleaned_payload, list_of_ValidationErrorDetails).
    """
    cleaned = {}
    errors = []

    for field in schema_fields:
        val = row_dict.get(field.field_name)
        cleaned_val, err = parse_and_validate_value(field, val, row_number=row_number)
        if err:
            errors.append(err)
        else:
            cleaned[field.field_name] = cleaned_val

    return cleaned, errors
