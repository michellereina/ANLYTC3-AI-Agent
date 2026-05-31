import csv
import io
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


TEST_DIR = Path("generated_tests")
UPLOAD_DIR = Path("uploaded_projects")

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".json",
}

IGNORED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".pytest_cache",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]"),
]


def classify_testing_need(user_input):
    text = user_input.lower()

    if "api" in text or "endpoint" in text or "http" in text:
        return "api_testing"

    if "function" in text or "code" in text or "python" in text or "def " in text:
        return "unit_testing"

    if "login" in text or "button" in text or "form" in text or "screen" in text:
        return "ui_testing"

    return "manual_test_planning"


def is_testing_related(user_input):
    text = user_input.lower()

    testing_terms = {
        "test",
        "testing",
        "pytest",
        "unit",
        "qa",
        "quality assurance",
        "bug",
        "debug",
        "validate",
        "validation",
        "verify",
        "verification",
        "edge case",
        "negative case",
        "expected result",
        "actual result",
        "feature",
        "api",
        "endpoint",
        "function",
        "code",
        "python",
        "def ",
        "class ",
        "assert",
        "login",
        "form",
        "button",
        "workflow",
    }

    return any(term in text for term in testing_terms)


def create_test_summary(test_type):
    summaries = {
        "api_testing": "Generate API tests for success, validation, authentication, status codes, and error handling.",
        "unit_testing": "Generate Pytest unit tests for normal cases, edge cases, and expected failures.",
        "ui_testing": "Generate UI test cases for flows, validation, error states, and usability.",
        "manual_test_planning": "Generate a structured manual test plan with clear expected results.",
    }
    return summaries.get(test_type, "Generate a general test plan.")


def read_imported_testcases(uploaded_file):
    if uploaded_file is None:
        return ""

    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()
    if not raw_text:
        return ""

    return raw_text[:12000]


def extract_first_markdown_table(markdown_text):
    lines = markdown_text.splitlines()
    table_lines = []
    collecting = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            collecting = True
        elif collecting:
            break

    if len(table_lines) < 2:
        return []

    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return []

    headers = rows[0]
    records = []

    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded[: len(headers)])))

    return records


def records_to_csv(records):
    if not records:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def parse_pytest_statuses(pytest_result):
    statuses = []
    pattern = re.compile(
        r"(?P<nodeid>\S+::(?P<name>[A-Za-z_][\w\[\]\-\.]*))\s+"
        r"(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAILED|XPASSED)"
    )

    for line in (pytest_result.get("stdout") or "").splitlines():
        match = pattern.search(line)
        if match:
            statuses.append(
                {
                    "Test Case": match.group("name"),
                    "Status": match.group("status").title(),
                    "Source": match.group("nodeid"),
                }
            )

    if not statuses and pytest_result.get("return_code") == 124:
        statuses.append(
            {
                "Test Case": "Pytest execution",
                "Status": "Timeout",
                "Source": "Process timed out after 30 seconds",
            }
        )

    return statuses


def records_to_markdown_table(records):
    if not records:
        return "No individual Pytest test-case statuses were found in the output."

    headers = list(records[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for record in records:
        lines.append("| " + " | ".join(str(record.get(header, "")) for header in headers) + " |")

    return "\n".join(lines)


def contains_possible_secret(text):
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def sanitize_project_name(name):
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
    return safe_name.strip("._") or "uploaded_project"


def extract_codebase(uploaded_file, project_name):
    UPLOAD_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    project_path = UPLOAD_DIR / f"{sanitize_project_name(project_name)}_{timestamp}"

    if project_path.exists():
        shutil.rmtree(project_path)

    project_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
        for member in zip_ref.infolist():
            member_parts = Path(member.filename).parts
            if any(part in IGNORED_DIRS for part in member_parts):
                continue
            if Path(member.filename).name.lower() in {".env", ".env.local", ".env.production"}:
                continue

            target_path = (project_path / member.filename).resolve()
            if not str(target_path).startswith(str(project_path.resolve())):
                raise ValueError("Unsafe ZIP path detected.")
            zip_ref.extract(member, project_path)

    return project_path


def is_allowed_file(path):
    path = Path(path)

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False

    if path.name.lower() in {".env", ".env.local", ".env.production"}:
        return False

    return not any(part in IGNORED_DIRS for part in path.parts)


def build_codebase_context(project_path, max_files=25, max_chars_per_file=2500, max_total_chars=30000):
    project_path = Path(project_path)
    context_parts = []
    selected_files = []
    total_chars = 0

    for file_path in project_path.rglob("*"):
        if not file_path.is_file() or not is_allowed_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if contains_possible_secret(content):
            continue

        preview = content[:max_chars_per_file]
        if total_chars + len(preview) > max_total_chars or len(selected_files) >= max_files:
            break

        selected_files.append(str(file_path))
        total_chars += len(preview)
        context_parts.append(
            f"File: {file_path}\n"
            f"Content preview:\n{preview}"
        )

    return "\n\n---\n\n".join(context_parts), selected_files


def save_pytest_file(pytest_code, attempt_label="generated"):
    TEST_DIR.mkdir(exist_ok=True)
    safe_label = re.sub(r"[^A-Za-z0-9_-]+", "_", attempt_label).strip("_") or "generated"
    filename = f"test_{safe_label}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.py"
    filepath = TEST_DIR / filename
    filepath.write_text(pytest_code, encoding="utf-8")
    return filepath


def run_pytest_file(filepath):
    try:
        result = subprocess.run(
            ["pytest", str(filepath), "-v"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "return_code": 124,
            "stdout": error.stdout or "",
            "stderr": "Pytest timed out after 30 seconds.",
        }

    return {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
