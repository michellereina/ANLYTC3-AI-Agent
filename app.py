import base64
from pathlib import Path

import streamlit as st
from PIL import Image

from agent import (
    generate_pytest_code,
    revise_pytest_code,
    run_testpilot_agent,
    summarize_test_run_revise,
)
from database import get_reports, init_db, reset_generated_artifacts, save_report
from tools import (
    build_codebase_context,
    extract_codebase,
    extract_first_markdown_table,
    is_testing_related,
    parse_pytest_statuses,
    read_imported_testcases,
    records_to_csv,
    records_to_markdown_table,
    run_pytest_file,
    save_pytest_file,
)


init_db()
reset_generated_artifacts()

APP_NAME = "Bugsee"
LOGO_PATH = Path(__file__).parent / "assets" / "bugsee-logo.png"


def logo_data_uri() -> str:
    encoded_logo = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded_logo}"


st.set_page_config(
    page_title=f"{APP_NAME} AI Testing Agent",
    page_icon=Image.open(LOGO_PATH),
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 9%, rgba(183, 255, 105, 0.28), transparent 22rem),
            radial-gradient(circle at 82% 12%, rgba(156, 209, 236, 0.28), transparent 20rem),
            linear-gradient(180deg, #fbfff4 0%, #f3fbff 55%, #fff9ee 100%);
        color: #263325;
    }
    .stApp, .stApp p, .stApp label, .stApp span, .stApp div {
        color: #263325;
    }
    .stApp [data-testid="stHeader"] {
        background: rgba(251, 255, 244, 0.88);
        backdrop-filter: blur(10px);
    }
    .block-container {
        padding-top: 4.75rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }
    h1, h2, h3 {
        color: #243322 !important;
        letter-spacing: 0;
    }
    p, li, label {
        color: #263325 !important;
    }
    div[data-testid="stTabs"] button {
        color: #34432f !important;
        font-weight: 600;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #087f4d !important;
    }
    div[data-testid="stButton"] > button {
        border-radius: 6px;
        font-weight: 700;
        min-height: 2.8rem;
        background: linear-gradient(135deg, #12c76f 0%, #87df50 100%);
        color: #102314;
        border: 1px solid #0dab62;
        box-shadow: 0 8px 18px rgba(18, 129, 78, 0.15);
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #087f4d;
        color: #102314;
        transform: translateY(-1px);
    }
    div[data-testid="stFileUploader"] section {
        border-radius: 8px;
        border-color: #cce9b0;
        background: #ffffff;
    }
    div[data-testid="stFileUploader"] section * {
        color: #263325 !important;
    }
    div[data-testid="stFileUploader"] button {
        background: #ffffff !important;
        color: #263325 !important;
        border: 1px solid #bddf9f !important;
        border-radius: 6px !important;
    }
    div[data-testid="stFileUploader"] button * {
        color: #263325 !important;
        fill: #263325 !important;
    }
    div[data-testid="stFileUploader"] small {
        color: #68795d !important;
    }
    div[data-testid="stTextArea"] textarea {
        border-radius: 8px;
        border-color: #bde3a6;
        background: #ffffff;
        color: #263325;
        font-family: "Consolas", "Courier New", monospace;
    }
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #75836e;
        opacity: 1;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.88);
        border-color: #d6ecbd;
        border-radius: 8px;
        box-shadow: 0 10px 28px rgba(35, 86, 46, 0.08);
    }
    div[data-testid="stToggle"] * {
        color: #263325 !important;
    }
    div[data-testid="stMarkdownContainer"] {
        color: #263325;
    }
    div[data-testid="stExpander"] {
        background: #ffffff;
        border-color: #d6ecbd;
        border-radius: 8px;
    }
    div[data-testid="stMarkdownContainer"] table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
    }
    div[data-testid="stMarkdownContainer"] th,
    div[data-testid="stMarkdownContainer"] td {
        white-space: normal !important;
        overflow-wrap: anywhere;
        word-break: break-word;
        vertical-align: top;
        padding: 0.55rem 0.65rem;
    }
    div[data-testid="stTable"] {
        width: 100%;
        overflow-x: auto;
    }
    div[data-testid="stTable"] table {
        width: 100%;
        table-layout: fixed;
    }
    div[data-testid="stTable"] th,
    div[data-testid="stTable"] td {
        white-space: normal !important;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    pre, code {
        color: #e5e7eb !important;
    }
    .tp-header {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 1rem;
        align-items: center;
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid #d6ecbd;
        border-radius: 8px;
        box-shadow: 0 18px 44px rgba(34, 94, 51, 0.1);
        padding: 1rem 1.1rem;
        margin-top: 0.25rem;
        margin-bottom: 1rem;
    }
    .tp-logo {
        width: clamp(74px, 10vw, 118px);
        aspect-ratio: 1;
        object-fit: contain;
        border-radius: 8px;
        background: #101510;
        padding: 0.35rem;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08), 0 10px 24px rgba(36, 60, 31, 0.12);
    }
    .tp-kicker {
        color: #087f4d;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .tp-title {
        color: #243322;
        font-size: clamp(2.1rem, 5vw, 3.2rem);
        font-weight: 750;
        margin: 0;
    }
    .tp-subtitle {
        color: #586b4f;
        font-size: 1rem;
        max-width: 780px;
        margin-top: 0.35rem;
    }
    .tp-note {
        background: #fff8db;
        border: 1px solid #f2cf71;
        border-radius: 8px;
        color: #5d4610;
        padding: 0.8rem 1rem;
        margin: 0.75rem 0 1rem 0;
    }
    @media (max-width: 640px) {
        .tp-header {
            grid-template-columns: 1fr;
        }
        .tp-logo {
            width: 86px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="tp-header">
      <img class="tp-logo" src="{logo_data_uri()}" alt="Bugsee logo" />
      <div>
        <div class="tp-kicker">Human-in-the-loop QA agent</div>
        <h1 class="tp-title">Bugsee</h1>
        <div class="tp-subtitle">
          Spot issues, generate a structured test plan, run Pytest checks,
          and save a reviewable report.
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tp-note">
      Do not upload or paste passwords, API keys, private user data, .env files, or confidential source code.
      AI-generated tests should be reviewed before use.
    </div>
    """,
    unsafe_allow_html=True,
)

if "codebase_context" not in st.session_state:
    st.session_state["codebase_context"] = ""
if "selected_files" not in st.session_state:
    st.session_state["selected_files"] = ""
if "imported_testcases" not in st.session_state:
    st.session_state["imported_testcases"] = ""

tab_test, tab_history, tab_about = st.tabs(["Generate Tests", "Saved Reports", "Architecture"])

with tab_test:
    setup_col, input_col = st.columns([0.9, 1.35], gap="large")

    with setup_col:
        with st.container(border=True):
            st.subheader("Codebase Context")
            st.caption("Optional. Upload a ZIP when you want Bugsee to use project files as reference.")
            uploaded_zip = st.file_uploader(
                "Upload project ZIP",
                type=["zip"],
                help="Skip this if you only want to test a pasted code snippet or feature description.",
            )

            if st.session_state["selected_files"]:
                st.success("Codebase context is active.")
                with st.expander("Files included as context"):
                    st.code(st.session_state["selected_files"])

            if st.button("Clear Context", use_container_width=True):
                st.session_state["codebase_context"] = ""
                st.session_state["selected_files"] = ""
                st.success("Codebase context cleared.")

        with st.container(border=True):
            st.subheader("Test Case Import")
            imported_file = st.file_uploader(
                "Import test cases",
                type=["csv", "md", "txt"],
                help="Optional. Imported test cases are used as extra testing requirements.",
            )

            if imported_file:
                st.session_state["imported_testcases"] = read_imported_testcases(imported_file)
                st.success("Imported test cases loaded.")

            if st.session_state["imported_testcases"]:
                with st.expander("Preview imported test cases"):
                    st.text(st.session_state["imported_testcases"][:3000])

            if st.button("Clear Imported Test Cases", use_container_width=True):
                st.session_state["imported_testcases"] = ""
                st.success("Imported test cases cleared.")

        with st.container(border=True):
            st.subheader("Agent Settings")
            beginner_mode = st.toggle(
                "Beginner-Friendly QA Mode",
                value=True,
                help="Explains QA terms, failures, and test results in simpler language.",
            )
            st.caption("When enabled, Bugsee explains QA concepts while keeping the report suitable for review.")

    with input_col:
        with st.container(border=True):
            st.subheader("Describe what you want to test")
            user_input = st.text_area(
                "Feature, API, Python code, or testing goal",
                height=260,
                placeholder="Example: Test a login feature where users enter an email and password...",
            )

            if st.session_state["codebase_context"]:
                st.info("Selected codebase context will be used as reference. Generated tests avoid importing extracted ZIP paths directly.")

            run_agent = st.button("Generate Test Plan and Run Agent", use_container_width=True)

    if run_agent:
        active_context = st.session_state["codebase_context"]
        selected_files = st.session_state["selected_files"]
        imported_testcases = st.session_state["imported_testcases"]

        if uploaded_zip:
            with st.spinner("Reading uploaded codebase as filtered reference context..."):
                try:
                    project_name = uploaded_zip.name.removesuffix(".zip")
                    project_path = extract_codebase(uploaded_zip, project_name)
                    active_context, selected_file_list = build_codebase_context(project_path)
                    selected_files = "\n".join(selected_file_list)
                    st.session_state["codebase_context"] = active_context
                    st.session_state["selected_files"] = selected_files
                except Exception as error:
                    st.error(f"Could not process ZIP file: {error}")
                    active_context = ""
                    selected_files = ""

            if selected_files:
                st.success("Codebase context loaded.")
                with st.expander("Files included as context"):
                    st.code(selected_files)

        agent_request = user_input.strip()
        if imported_testcases:
            agent_request = f"{agent_request}\n\nImported test cases to include:\n{imported_testcases}".strip()

        if not agent_request and not active_context:
            st.warning("Please enter something to test.")
        elif user_input.strip() and not is_testing_related(user_input):
            st.warning(
                "Bugsee only handles software testing requests. "
                "Please enter a feature, API, Python code, or testing goal."
            )
        else:
            with st.spinner("Bugsee is generating a structured test plan..."):
                test_plan = run_testpilot_agent(agent_request, active_context, beginner_mode)

            st.divider()
            report_col, execution_col = st.columns([1, 1], gap="large")

            with report_col:
                st.subheader("Generated Test Report")
                st.markdown(test_plan)
                exported_records = extract_first_markdown_table(test_plan)
                exported_csv = records_to_csv(exported_records)
                if exported_csv:
                    st.download_button(
                        "Export Generated Test Cases",
                        data=exported_csv,
                        file_name="bugsee_generated_test_cases.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            attempts = []

            with st.spinner("Attempt 1: generating and running Pytest code..."):
                pytest_code = generate_pytest_code(
                    agent_request,
                    active_context,
                    test_plan,
                    beginner_mode,
                )
                filepath = save_pytest_file(pytest_code, "attempt_1")
                test_result = run_pytest_file(filepath)
                attempts.append(
                    {
                        "attempt": 1,
                        "code": pytest_code,
                        "filepath": str(filepath),
                        "result": test_result,
                        "statuses": parse_pytest_statuses(test_result),
                    }
                )

            if test_result["return_code"] != 0:
                with st.spinner("Attempt 2: revising the Pytest code using the failure output..."):
                    revised_code = revise_pytest_code(
                        agent_request,
                        active_context,
                        pytest_code,
                        test_result,
                        beginner_mode,
                    )
                    revised_filepath = save_pytest_file(revised_code, "attempt_2_revised")
                    revised_result = run_pytest_file(revised_filepath)
                    attempts.append(
                        {
                            "attempt": 2,
                            "code": revised_code,
                            "filepath": str(revised_filepath),
                            "result": revised_result,
                            "statuses": parse_pytest_statuses(revised_result),
                        }
                    )

            with st.spinner("Summarizing the test-run-revise loop..."):
                for attempt in attempts:
                    attempt["status_table"] = records_to_markdown_table(attempt["statuses"])
                revise_summary = summarize_test_run_revise(attempts, beginner_mode)

            with execution_col:
                st.subheader("Agent Execution Result")
            final_result = attempts[-1]["result"]

            with execution_col:
                if final_result["return_code"] == 0:
                    st.success("Final attempt passed.")
                else:
                    st.error("Final attempt still has failures or execution errors.")

                st.markdown(revise_summary)

            for attempt in attempts:
                with st.expander(f"Attempt {attempt['attempt']} | {attempt['filepath']}"):
                    st.code(attempt["code"], language="python")
                    st.markdown(f"**Return code:** `{attempt['result']['return_code']}`")
                    st.text_area(
                        f"stdout attempt {attempt['attempt']}",
                        attempt["result"]["stdout"],
                        height=180,
                    )
                    st.text_area(
                        f"stderr attempt {attempt['attempt']}",
                        attempt["result"]["stderr"],
                        height=120,
                    )

            combined_report = f"""
# Bugsee Test Report

## Report Metadata

Beginner-Friendly QA Mode: `{beginner_mode}`

Selected files:

```text
{selected_files or "None"}
```

## Generated Test Plan

{test_plan}

## Agent Execution Result

{revise_summary}
"""
            for attempt in attempts:
                combined_report += f"""

## Executed Code: Attempt {attempt['attempt']}

File: `{attempt['filepath']}`

```python
{attempt['code']}
```

Return code: `{attempt['result']['return_code']}`

Parsed test case status:

{records_to_markdown_table(attempt['statuses'])}

stdout:

```text
{attempt['result']['stdout']}
```

stderr:

```text
{attempt['result']['stderr']}
```
"""
            save_report(user_input, combined_report, selected_files)

with tab_history:
    st.subheader("Saved Reports")
    reports = get_reports()

    if not reports:
        st.info("No reports saved yet.")
    else:
        st.caption(f"{len(reports)} report(s) saved locally in SQLite.")
        for report_id, saved_input, saved_output, selected_files, created_at in reports:
            with st.expander(f"Report #{report_id} - {created_at}"):
                meta_col, output_col = st.columns([0.8, 1.2], gap="large")

                with meta_col:
                    st.markdown("**User Input**")
                    st.write(saved_input)

                    if selected_files:
                        st.markdown("**Selected Files**")
                        st.code(selected_files)

                with output_col:
                    st.markdown("**Agent Output**")
                    st.markdown(saved_output)

with tab_about:
    arch_col, safety_col = st.columns([1, 1], gap="large")

    with arch_col:
        st.subheader("Agent Architecture")
        st.code(
            """
User
  -> Streamlit Frontend
  -> Python Backend Controller
  -> Input Classifier / Decision Logic
  -> Optional Codebase Upload Context
  -> OpenAI Reasoning Engine
  -> Agent Actions
       - Generate test plan
       - Execute generated tests and revise once if needed
       - Save report to SQLite
  -> Final response and saved history
        """.strip()
        )

    with safety_col:
        st.subheader("Responsible AI Safeguards")
        st.markdown(
            """
- The agent separates suggested tests from real Pytest execution results.
- Uploaded files are filtered to avoid dependency folders, `.env` files, and common secret patterns.
- Codebase uploads are optional and used as one combined reference context.
- Generated tests avoid importing extracted ZIP paths directly.
- Users should review generated tests before using them in production.
            """.strip()
        )
