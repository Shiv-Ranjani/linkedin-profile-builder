"""Prompt templates for the AI LinkedIn Profile Builder.

This module centralizes every prompt sent to the OpenAI API. Keeping the
prompts in a dedicated file makes them easy to review, test and tune without
touching the application or utility logic.

Golden rule enforced by every prompt:
    NEVER invent fake companies, internships, certifications, achievements or
    experience. The model may only rewrite and enhance the information that the
    student actually provided.
"""

from __future__ import annotations

from typing import Dict

# ---------------------------------------------------------------------------
# System prompt: sets the assistant persona and the non-negotiable rules.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = (
    "You are an expert LinkedIn profile writer and career coach who helps "
    "college students present themselves professionally to recruiters.\n\n"
    "STRICT RULES (never break these):\n"
    "1. NEVER fabricate companies, internships, certifications, achievements, "
    "dates, metrics or experience that the user did not provide.\n"
    "2. Only rewrite, polish and professionally rephrase the information given.\n"
    "3. If a field is empty, do not invent content for it - simply skip it.\n"
    "4. Keep the tone professional, confident and honest.\n"
    "5. Write in clear, modern, recruiter-friendly English.\n"
    "6. Output clean Markdown only, with no extra commentary before or after."
)


def _format_user_block(data: Dict[str, str]) -> str:
    """Build the shared, human-readable block of student data.

    Args:
        data: Dictionary of raw student inputs collected from the UI.

    Returns:
        A formatted string listing every provided field. Empty fields are
        rendered as ``(not provided)`` so the model knows to skip them.
    """

    def value(key: str) -> str:
        raw = str(data.get(key, "") or "").strip()
        return raw if raw else "(not provided)"

    return (
        f"Full Name: {value('full_name')}\n"
        f"College: {value('college')}\n"
        f"Degree: {value('degree')}\n"
        f"Branch / Specialization: {value('branch')}\n"
        f"Graduation Year: {value('graduation_year')}\n"
        f"Career Goal: {value('career_goal')}\n"
        f"Skills: {value('skills')}\n"
        f"Projects: {value('projects')}\n"
        f"Internships: {value('internships')}\n"
        f"Certifications: {value('certifications')}\n"
        f"Achievements: {value('achievements')}\n"
        f"Languages: {value('languages')}\n"
        f"GitHub URL: {value('github_url')}\n"
        f"Portfolio URL: {value('portfolio_url')}\n"
        f"LinkedIn URL: {value('linkedin_url')}\n"
    )


def build_profile_prompt(data: Dict[str, str]) -> str:
    """Create the main prompt that generates the full LinkedIn profile.

    The model is asked to return a single Markdown document with clearly
    delimited section markers. ``utils.split_sections`` later parses those
    markers back into individual, displayable sections.

    Args:
        data: Dictionary of raw student inputs collected from the UI.

    Returns:
        The complete user prompt string.
    """

    student_block = _format_user_block(data)

    return (
        "Using ONLY the student information below, generate a complete, "
        "professional LinkedIn profile.\n\n"
        "Do not invent anything that is not present in the data. If a section "
        "has no supporting input, write a short, honest line based only on the "
        "provided goal/skills instead of fabricating experience.\n\n"
        "=== STUDENT INFORMATION ===\n"
        f"{student_block}\n"
        "=== OUTPUT FORMAT ===\n"
        "Return Markdown using EXACTLY these section headers (keep the '###' "
        "markers and the exact titles so the app can parse them):\n\n"
        "### Professional Headline\n"
        "One punchy LinkedIn headline (max 220 characters).\n\n"
        "### About Section\n"
        "A first-person 'About' summary of 3-4 short paragraphs.\n\n"
        "### Skills\n"
        "A clean, comma-separated or bulleted list of relevant skills.\n\n"
        "### Professional Project Descriptions\n"
        "For each provided project, a professional 2-3 line description with "
        "impact-oriented language. Skip if no projects were provided.\n\n"
        "### Internship Description\n"
        "A polished description of the provided internship(s). If none were "
        "provided, write exactly: 'No internship information provided.'\n\n"
        "### Certifications\n"
        "A formatted list of the provided certifications. Skip if none.\n\n"
        "### Career Objective\n"
        "A concise, forward-looking career objective (2-3 sentences).\n\n"
        "### Resume Bullet Points\n"
        "5-7 strong, action-verb resume bullets derived only from the inputs.\n\n"
        "### Career Recommendations\n"
        "3-5 practical, honest recommendations to strengthen this profile "
        "(courses to take, skills to add, communities to join).\n\n"
        "### LinkedIn Banner Tagline\n"
        "One short, memorable tagline suitable for a LinkedIn banner image.\n"
    )


# Ordered list of the section titles the model is instructed to emit. The app
# uses this ordering to render sections consistently.
SECTION_TITLES: list[str] = [
    "Professional Headline",
    "About Section",
    "Skills",
    "Professional Project Descriptions",
    "Internship Description",
    "Certifications",
    "Career Objective",
    "Resume Bullet Points",
    "Career Recommendations",
    "LinkedIn Banner Tagline",
]
