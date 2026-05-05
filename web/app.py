import json
import sys
import tempfile
from pathlib import Path
import subprocess

import streamlit as st

from web.config_writer import update_location
from web.results import parse_contacts, parse_jobs

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "output.json"
APP_ROOT = Path(__file__).parent.parent


def _run_pipeline(cv_path: str, location: str, keywords: list[str]) -> int:
    update_location(location)
    cmd = [sys.executable, "cli.py", "full", "--cv", cv_path, "--no-ui"]
    if keywords:
        cmd += ["--keywords"] + keywords
    result = subprocess.run(cmd, cwd=APP_ROOT, capture_output=True)
    if result.returncode != 0:
        import sys as _sys
        print(result.stderr.decode(errors="replace"), file=_sys.stderr)
    return result.returncode


def _render_jobs(jobs: list[dict]) -> None:
    if not jobs:
        st.info("No jobs found.")
        return
    rows = [
        {"Title": j.get("role", ""), "Company": j.get("company", ""), "Score": j.get("score", ""), "Apply": j.get("apply", "")}
        for j in jobs
    ]
    st.dataframe(
        rows,
        column_config={"Apply": st.column_config.LinkColumn("Apply")},
        use_container_width=True,
    )


def _render_contacts(contacts: list[dict]) -> None:
    if not contacts:
        st.info("No contacts found.")
        return
    for c in contacts:
        linkedin = c.get("linkedin_url", "").strip()
        link = f"[Profile]({linkedin})" if linkedin else "—"
        st.markdown(
            f"**{c.get('name', '')}** · {c.get('title', '')} · {c.get('category', '')} "
            f"· Score: {c.get('relevance_score', '')} · {link}"
        )


def _render_messages(contacts: list[dict]) -> None:
    has_messages = any(c.get("message") for c in contacts)
    if not has_messages:
        st.info("No outreach messages generated.")
        return
    for i, c in enumerate(contacts):
        msg = c.get("message", "")
        if msg:
            st.markdown(f"**{c.get('name', '')}**")
            st.text_area(
                label="",
                value=msg,
                height=100,
                disabled=True,
                key=f"msg_{i}_{c.get('name', '')}",
            )


def main() -> None:
    st.title("Job Search Agent")
    st.markdown(
        "Upload your resume, tell us what you're looking for, "
        "and we'll find matching jobs and contacts for you."
    )

    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.session_state["resume_bytes"] = uploaded_file.getbuffer().tobytes()

    location = st.text_input("Where are you looking?", value="Denver, CO")
    keywords_raw = st.text_input(
        "What kind of jobs? (comma-separated)",
        value="",
        placeholder="e.g. Python, Data Engineering",
    )

    has_resume = "resume_bytes" in st.session_state
    if st.button("Find My Jobs", disabled=not has_resume):
        if "resume_bytes" not in st.session_state:
            st.warning("Please upload your resume again.")
            st.stop()

        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(st.session_state["resume_bytes"])
            cv_path = tmp.name

        try:
            with st.spinner("Searching for jobs… this takes 2–3 minutes"):
                returncode = _run_pipeline(cv_path, location, keywords)
        finally:
            Path(cv_path).unlink(missing_ok=True)

        if returncode != 0:
            st.error("Something went wrong. Check that your API keys are valid and try again.")
            return

        if not OUTPUT_PATH.exists():
            st.warning("No results found. Try different keywords or a broader location.")
            return

        try:
            data = json.loads(OUTPUT_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            st.warning("No results found. Try different keywords or a broader location.")
            return

        jobs = parse_jobs(data)
        contacts = parse_contacts(data)
        message_count = sum(1 for c in contacts if c.get("message"))

        with st.expander(f"Top Jobs ({len(jobs)})", expanded=True):
            _render_jobs(jobs)

        with st.expander(f"Contacts ({len(contacts)})", expanded=True):
            _render_contacts(contacts)

        with st.expander(f"Outreach Messages ({message_count})", expanded=True):
            _render_messages(contacts)


if __name__ == "__main__":
    main()
