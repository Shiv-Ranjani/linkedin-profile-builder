"""AI LinkedIn Profile Builder - Streamlit application.

A modern, student-friendly web app that turns raw academic and project
information into a polished LinkedIn profile using the OpenAI API.

Run locally:
    streamlit run app.py

The app reads OPENAI_API_KEY from the environment (or a local .env file).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st

from utils import (
    ProfileGenerationError,
    generate_profile,
    split_sections,
    validate_inputs,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI LinkedIn Profile Builder",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
def inject_styles() -> None:
    """Inject custom CSS for the hero banner, cards and footer."""

    st.markdown(
        """
        <style>
        .hero {
            background: linear-gradient(135deg, #0a66c2 0%, #004182 100%);
            padding: 2.2rem 2rem;
            border-radius: 16px;
            color: #ffffff;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 24px rgba(10, 102, 194, 0.25);
        }
        .hero h1 { margin: 0; font-size: 2.1rem; font-weight: 800; }
        .hero p { margin: 0.4rem 0 0; font-size: 1.05rem; opacity: 0.95; }
        .card {
            background: #ffffff;
            border: 1px solid #e6e9ef;
            border-radius: 12px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }
        .footer {
            text-align: center;
            color: #6b7280;
            padding: 1.5rem 0 0.5rem;
            font-size: 0.9rem;
        }
        .stButton > button {
            background: #0a66c2;
            color: #ffffff;
            border: none;
            border-radius: 24px;
            padding: 0.6rem 1.6rem;
            font-weight: 700;
            width: 100%;
        }
        .stButton > button:hover { background: #004182; color: #ffffff; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Render the professional hero banner."""

    st.markdown(
        """
        <div class="hero">
            <h1>💼 AI LinkedIn Profile Builder</h1>
            <p>Turn your college journey into a recruiter-ready LinkedIn profile
            &mdash; powered by AI, built with Python &amp; Streamlit.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    """Render the sidebar with instructions and settings.

    Returns:
        The OpenAI model id chosen by the user.
    """

    with st.sidebar:
        st.header("⚙️ How it works")
        st.markdown(
            "1. Fill in your real details in the form.\n"
            "2. Click **Generate LinkedIn Profile**.\n"
            "3. Review, copy and paste each section into LinkedIn."
        )
        st.divider()
        st.subheader("Model")
        model = st.selectbox(
            "OpenAI model",
            options=["gpt-4o-mini", "gpt-4o"],
            index=0,
            help="gpt-4o-mini is fast and low-cost; gpt-4o is more detailed.",
        )
        st.divider()
        st.info(
            "Honesty first: the AI only rewrites what you enter. It never "
            "invents fake companies, internships or certifications.",
            icon="🛡️",
        )
        return model


def render_form() -> Tuple[Dict[str, str], bool]:
    """Render the input form and return the collected data plus submit state.

    Returns:
        A tuple ``(data, submitted)`` where ``data`` holds every field value
        and ``submitted`` indicates whether the button was pressed.
    """

    with st.form("profile_form"):
        st.subheader("👤 Basic Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Jane Doe")
            college = st.text_input(
                "College", placeholder="ABC Institute of Technology"
            )
            degree = st.text_input("Degree", placeholder="B.Tech")
        with col2:
            branch = st.text_input(
                "Branch / Specialization",
                placeholder="Computer Science & Engineering",
            )
            graduation_year = st.text_input(
                "Graduation Year", placeholder="2026"
            )
            languages = st.text_input(
                "Languages", placeholder="English, Hindi, Tamil"
            )

        st.subheader("🎯 Career & Skills")
        career_goal = st.text_area(
            "Career Goal *",
            placeholder="Become a backend engineer working on scalable systems.",
            height=80,
        )
        skills = st.text_area(
            "Skills *",
            placeholder="Python, SQL, Docker, REST APIs, Git",
            height=80,
        )

        st.subheader("🚀 Experience & Projects")
        projects = st.text_area(
            "Projects",
            placeholder=(
                "Expense Tracker - a Flask app with JWT auth and PostgreSQL.\n"
                "Weather Bot - a Python CLI using the OpenWeather API."
            ),
            height=110,
        )
        internships = st.text_area(
            "Internships",
            placeholder="Summer intern at XYZ Labs - built internal dashboards.",
            height=80,
        )
        certifications = st.text_area(
            "Certifications",
            placeholder="Google Cloud Digital Leader, freeCodeCamp Python",
            height=70,
        )
        achievements = st.text_area(
            "Achievements",
            placeholder="Winner - College Hackathon 2025; Dean's list 2024",
            height=70,
        )

        st.subheader("🔗 Links")
        lcol1, lcol2, lcol3 = st.columns(3)
        with lcol1:
            github_url = st.text_input(
                "GitHub URL", placeholder="https://github.com/janedoe"
            )
        with lcol2:
            portfolio_url = st.text_input(
                "Portfolio URL", placeholder="https://janedoe.dev"
            )
        with lcol3:
            linkedin_url = st.text_input(
                "LinkedIn URL", placeholder="https://linkedin.com/in/janedoe"
            )

        submitted = st.form_submit_button("✨ Generate LinkedIn Profile")

    data: Dict[str, str] = {
        "full_name": full_name,
        "college": college,
        "degree": degree,
        "branch": branch,
        "graduation_year": graduation_year,
        "career_goal": career_goal,
        "skills": skills,
        "projects": projects,
        "internships": internships,
        "certifications": certifications,
        "achievements": achievements,
        "languages": languages,
        "github_url": github_url,
        "portfolio_url": portfolio_url,
        "linkedin_url": linkedin_url,
    }
    return data, submitted


def render_results(sections: List[Tuple[str, str]]) -> None:
    """Render each generated section in an expandable card with a copy box.

    Args:
        sections: List of ``(title, body)`` pairs from ``split_sections``.
    """

    st.success("✅ Your LinkedIn profile is ready! Expand each section below.")

    # The first section (headline) is expanded by default for quick preview.
    for index, (title, body) in enumerate(sections):
        with st.expander(f"📄 {title}", expanded=index == 0):
            st.markdown(body)
            # st.code doubles as a one-click "copy" widget in Streamlit.
            st.caption("Copy-ready text:")
            st.code(body, language="markdown")


def render_footer() -> None:
    """Render the page footer."""

    st.markdown(
        """
        <div class="footer">
            Made with ❤️ using Python, Streamlit and Google Cloud
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""

    inject_styles()
    render_hero()
    model = render_sidebar()

    data, submitted = render_form()

    if submitted:
        errors = validate_inputs(data)
        if errors:
            for message in errors:
                st.warning(message, icon="⚠️")
            render_footer()
            return

        progress = st.progress(0, text="Preparing your information...")
        try:
            progress.progress(35, text="Contacting the AI model...")
            with st.spinner("Crafting your professional profile..."):
                raw_markdown = generate_profile(data, model=model)
            progress.progress(80, text="Formatting sections...")
            sections = split_sections(raw_markdown)
            progress.progress(100, text="Done!")
            progress.empty()
            render_results(sections)
        except ProfileGenerationError as exc:
            progress.empty()
            st.error(str(exc), icon="🚫")
        except Exception as exc:  # Last-resort guard for unexpected errors.
            progress.empty()
            st.error(f"Unexpected error: {exc}", icon="🚫")

    render_footer()


if __name__ == "__main__":
    main()
