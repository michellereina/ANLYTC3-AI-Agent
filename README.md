# Bugsee: An AI-Powered Software Testing Assistant 🤖

"Turn software requirements and feature descriptions into executable test suites with an autonomous, self-correcting execution loop."

**Bugsee** is a human-in-the-loop AI software testing assistant designed for software engineering students, junior QA analysts, and capstone project teams. Bugsee interprets feature descriptions, Python snippets, imported test cases, or uploaded ZIP codebase context, then generates a structured test plan and executable Pytest checks. It runs generated tests locally through Pytest and, if the generated test fails, observes the real Pytest output and performs one revision attempt.

---

## 🛠️ Tech Stack & Project Dependencies

The application is written natively in Python and leverages the following core ecosystem packages:

### Core Framework & Analytics
* **Streamlit:** Dictates application routing, active view layout states, and session-guided multi-stage container updates.

* **Subprocess Wrapper:** Manages safe system execution calls to trigger local binaries and capture standard outputs.

### Generative AI & Autonomous Tools
* **OpenAI Python SDK:** Sends selected user input, imported test cases, and filtered codebase context to the configured OpenAI model for test planning and test generation.
* **ZIP Archive Processor:** Decodes, filters, and unzips uploaded multi-module source project packages to isolate core logic for context.
* **File I/O System:** Generates, updates, and deletes generated Pytest files under (`generated_tests/`) dynamically during live agent execution loops.

### Storage, Safety, & Execution
* **SQLite3:** Stores local reports of previous output.
* **Pytest Framework:** Functions as the primary automated validation tool, running generated test code files and asserting operational runtime states.
* **python-dotenv:** Loads server-side configuration profiles and critical API credentials silently at initial setup.

---

### 🚀 How It Works
### Bugsee delivers data-driven, privacy-aware software quality assurance through an automated pipeline directly on your dashboard:

### Input Perception & Safety Filtering: You begin by pasting a single code block or uploading a .zip codebase package. The system automatically screens the files, bypassing dependency folders, environmental configurations, and hidden secret directories to protect system keys.

### Intent Classification & Routing: The agent routes the request based on structural objectives—classifying the task as unit testing, API verification, UI validation, or manual test planning. Unrelated queries are immediately filtered out.

### Autonomous Execution & Evaluation Tool: Bugsee generates a structured manual test table and builds a native pytest script. Instead of predicting success, the agent invokes the local system binary wrapper to execute the test suite in real time.

### Self-Correction & Memory Loop: If the console output registers a runtime failure, the agent triggers an observation step, pipes the terminal exception back to the OpenAI engine, and executes a one-time automated fix. The final pass/fail matrix, logs, and metadata are persistently stored in the local SQLite engine.

### ⚠️ Limitations
### To maintain operational structural safety and keep calculations clean, Bugsee operates within strict systemic boundaries:

### The agent's self-correction capability is driven strictly by environment code execution metrics (passing vs. failing). It does not have human intuition to verify if the business logic intent of the test matches your real-world architecture.

### The application runs tests locally inside a local generated test file execution through Pytest. It cannot perform unauthorized network penetrations, run hardware simulation steps, or orchestrate external cloud infrastructure updates.

### The system is a supportive testing utility. It operates independently of production CI/CD servers, meaning it does not deploy code or change live application versions, guaranteeing absolute isolation from your production codebases.

### 📢 Disclaimer
### Bugsee is an advisory tool designed to guide you, not manage your deployment. You always maintain full control over your software quality assurance sign-offs and data. Reports are stored locally, but selected input is sent to OpenAI for processing.