import re
import json
from typing import List, Dict, Any, Tuple, Optional

from app.rag.format.types import OutputFormat

class ValidationError:
    def __init__(self, code: str, message: str, severity: str):
        self.code = code
        self.message = message
        self.severity = severity

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity
        }

class ValidationResult:
    def __init__(self, is_valid: bool, format: OutputFormat, errors: List[ValidationError], suggestions: List[str]):
        self.isValid = is_valid
        self.format = format
        self.errors = errors
        self.suggestions = suggestions

    def to_dict(self) -> dict:
        return {
            "isValid": self.isValid,
            "format": self.format.value if isinstance(self.format, OutputFormat) else self.format,
            "errors": [e.to_dict() for e in self.errors],
            "suggestions": self.suggestions
        }

class OutputValidator:
    def validate(self, output: str, format: OutputFormat) -> ValidationResult:
        trimmed = output.strip()
        fmt_val = format.value if isinstance(format, OutputFormat) else format

        if fmt_val == OutputFormat.TABLE.value:
            return self.validate_table(trimmed)
        elif fmt_val == OutputFormat.LIST.value:
            return self.validate_list(trimmed)
        elif fmt_val == OutputFormat.JSON.value:
            return self.validate_json(trimmed)
        elif fmt_val == OutputFormat.STEPS.value:
            return self.validate_steps(trimmed)
        elif fmt_val == OutputFormat.COMPARISON.value:
            return self.validate_comparison(trimmed)
        elif fmt_val == OutputFormat.SUMMARY.value:
            return self.validate_summary(trimmed)
        else:
            return self.validate_paragraph(trimmed)

    def validate_table(self, output: str) -> ValidationResult:
        errors = []
        suggestions = []

        if '|' not in output:
            errors.append(ValidationError('TABLE_NO_PIPES', 'Output does not contain table pipes (|)', 'error'))
            suggestions.append('Use Markdown table format with | separators')

        has_header_sep = bool(re.search(r"\|[\s-]+\|", output)) or "---" in output
        if '|' in output and not has_header_sep:
            errors.append(ValidationError('TABLE_NO_HEADER_SEP', 'Table missing header separator (---)', 'warning'))
            suggestions.append('Add a header separator row with dashes')

        lines = [line for line in output.split('\n') if '|' in line]
        if len(lines) < 2:
            errors.append(ValidationError('TABLE_TOO_FEW_ROWS', 'Table has fewer than 2 rows', 'warning'))

        if len(lines) >= 2:
            col_counts = [line.count('|') for line in lines]
            if any(c != col_counts[0] for c in col_counts):
                errors.append(ValidationError('TABLE_INCONSISTENT_COLS', 'Table rows have inconsistent column counts', 'warning'))

        is_valid = not any(e.severity == 'error' for e in errors)
        return ValidationResult(is_valid, OutputFormat.TABLE, errors, suggestions)

    def validate_list(self, output: str) -> ValidationResult:
        errors = []
        suggestions = []

        has_bullets = bool(re.search(r"^[\s]*[-•*]\s", output, re.MULTILINE))
        has_numbers = bool(re.search(r"^[\s]*\d+[.)]\s", output, re.MULTILINE))

        if not has_bullets and not has_numbers:
            errors.append(ValidationError('LIST_NO_MARKERS', 'Output does not contain list markers (-, •, *, or 1.)', 'error'))
            suggestions.append('Format as bullet points with - or numbered items with 1. 2. 3.')

        matches = re.findall(r"^[\s]*[-•*]\s|^[\s]*\d+[.)]\s", output, re.MULTILINE)
        if len(matches) < 2:
            errors.append(ValidationError('LIST_TOO_FEW_ITEMS', 'List has fewer than 2 items', 'warning'))
            suggestions.append('Add more list items for a complete answer')

        is_valid = not any(e.severity == 'error' for e in errors)
        return ValidationResult(is_valid, OutputFormat.LIST, errors, suggestions)

    def validate_json(self, output: str) -> ValidationResult:
        errors = []
        suggestions = []

        json_content = output
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if code_match:
            json_content = code_match.group(1).strip()

        if not (json_content.startswith('{') or json_content.startswith('[')):
            errors.append(ValidationError('JSON_INVALID_START', 'Output does not start with { or [', 'error'))
            suggestions.append('Return only valid JSON without any surrounding text')

        try:
            json.loads(json_content)
        except Exception as e:
            errors.append(ValidationError('JSON_PARSE_ERROR', f'Invalid JSON: {str(e)}', 'error'))
            suggestions.append('Ensure proper JSON syntax with double quotes and valid structure')

        is_valid = not any(e.severity == 'error' for e in errors)
        return ValidationResult(is_valid, OutputFormat.JSON, errors, suggestions)

    def validate_steps(self, output: str) -> ValidationResult:
        errors = []
        suggestions = []

        matches = re.findall(r"^\s*(\d+)[.)]\s", output, re.MULTILINE)
        if len(matches) < 2:
            errors.append(ValidationError('STEPS_TOO_FEW', 'Output has fewer than 2 numbered steps', 'error'))
            suggestions.append('Use numbered format: 1. First step, 2. Second step, etc.')
        else:
            step_nums = [int(n) for n in matches]
            is_seq = all(step_nums[i] == step_nums[i - 1] + 1 for i in range(1, len(step_nums)))
            if not is_seq:
                errors.append(ValidationError('STEPS_NOT_SEQUENTIAL', 'Step numbers are not sequential', 'warning'))
            if step_nums[0] != 1:
                errors.append(ValidationError('STEPS_NOT_FROM_ONE', 'Steps should start from 1', 'warning'))

        is_valid = not any(e.severity == 'error' for e in errors)
        return ValidationResult(is_valid, OutputFormat.STEPS, errors, suggestions)

    def validate_comparison(self, output: str) -> ValidationResult:
        table_val = self.validate_table(output)
        if table_val.isValid:
            return ValidationResult(True, OutputFormat.COMPARISON, table_val.errors, table_val.suggestions)

        errors = []
        suggestions = []
        has_keywords = bool(re.search(r"\b(vs\.?|versus|compared to|difference|similar)\b", output, re.IGNORECASE))
        has_struct = ':' in output or '-' in output

        if not has_keywords and not has_struct:
            errors.append(ValidationError('COMPARISON_NO_STRUCTURE', 'Output lacks comparison structure', 'warning'))
            suggestions.append('Use a comparison table or clearly label each item being compared')

        return ValidationResult(True, OutputFormat.COMPARISON, errors, suggestions)

    def validate_summary(self, output: str) -> ValidationResult:
        errors = []
        suggestions = []
        words = len(output.split())

        if words > 300:
            errors.append(ValidationError('SUMMARY_TOO_LONG', f'Summary is {words} words - consider making it more concise', 'warning'))
            suggestions.append('Keep summaries under 200 words for clarity')
        elif words < 20:
            errors.append(ValidationError('SUMMARY_TOO_SHORT', 'Summary may be too brief to be informative', 'warning'))

        return ValidationResult(True, OutputFormat.SUMMARY, errors, suggestions)

    def validate_paragraph(self, output: str) -> ValidationResult:
        errors = []
        if len(output) < 20:
            errors.append(ValidationError('PARAGRAPH_TOO_SHORT', 'Response is very short', 'warning'))

        return ValidationResult(True, OutputFormat.PARAGRAPH, errors, [])

    def generate_retry_prompt(self, original_prompt: str, format: OutputFormat, validation: ValidationResult) -> str:
        errs = '\n'.join([f"- {e.message}" for e in validation.errors])
        suggs = '\n'.join([f"- {s}" for s in validation.suggestions])
        fmt_name = format.value.upper() if isinstance(format, OutputFormat) else str(format).upper()

        return f"""{original_prompt}

⚠️ PREVIOUS ATTEMPT FAILED FORMAT VALIDATION

Errors found:
{errs}

Required corrections:
{suggs}

You MUST fix these issues and respond in the correct {fmt_name} format."""
