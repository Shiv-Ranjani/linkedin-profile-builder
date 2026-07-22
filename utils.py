"""Utility helpers for the AI LinkedIn Profile Builder.

Responsibilities:
    * Load configuration (GCP project / location) from the environment.
    * Provide a thin, well-documented wrapper around Vertex AI Gemini.
    * Parse the model's Markdown response back into individual sections.

Authentication uses Application Default Credentials (ADC) - there is NO API
key. Locally you run ``gcloud auth application-default login``; on Cloud Run the
service account identity is used automatically. All network/error handling lives
here so that ``app.py`` stays focused on the Streamlit user interface.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from prompts import SECTION_TITLES, SYSTEM_PROMPT, build_profile_prompt

# Load variables from a local .env file when present (no-op in production where
# the environment already provides them, e.g. Cloud Run).
load_dotenv()

# GCP configuration. On Cloud Run these are provided as environment variables.
DEFAULT_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
# Default Gemini model. Can be overridden via the GEMINI_MODEL env variable.
DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class ProfileGenerationError(Exception):
    """Raised when the profile could not be generated.

    Carries a user-friendly message that ``app.py`` can display directly.
    """


def get_project_id() -> str:
    """Read the Google Cloud project id from the environment.

    Returns:
        The GCP project id string.

    Raises:
        ProfileGenerationError: If no project id can be found.
    """

    project = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        or ""
    ).strip()
    if not project:
        raise ProfileGenerationError(
            "GOOGLE_CLOUD_PROJECT is not set. Add it to your .env file locally "
            "or configure it as an environment variable on Cloud Run."
        )
    return project


def _get_client():
    """Create a Vertex AI Gemini client using Application Default Credentials.

    Returns:
        An initialized ``google.genai.Client`` bound to Vertex AI.

    Raises:
        ProfileGenerationError: If the SDK is missing or credentials are absent.
    """

    try:
        # Imported lazily so that missing dependencies produce a clear message.
        from google import genai
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise ProfileGenerationError(
            "The 'google-genai' package is not installed. Run "
            "'pip install -r requirements.txt'."
        ) from exc

    try:
        # vertexai=True routes requests through Vertex AI using ADC (no key).
        return genai.Client(
            vertexai=True,
            project=get_project_id(),
            location=DEFAULT_LOCATION,
        )
    except Exception as exc:
        raise ProfileGenerationError(
            "Could not initialize the Vertex AI client. Run "
            "'gcloud auth application-default login' locally, or ensure the "
            "Cloud Run service account has the 'roles/aiplatform.user' role. "
            f"Details: {exc}"
        ) from exc


def generate_profile(data: Dict[str, str], model: str = DEFAULT_MODEL) -> str:
    """Call Vertex AI Gemini and return the raw Markdown profile.

    Args:
        data: Dictionary of raw student inputs collected from the UI.
        model: The Gemini model id to use.

    Returns:
        The full Markdown string returned by the model.

    Raises:
        ProfileGenerationError: For any API, network or configuration failure.
    """

    from google.genai import types

    client = _get_client()
    user_prompt = build_profile_prompt(data)

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.6,
                max_output_tokens=2048,
            ),
        )
    except Exception as exc:  # Broad catch: surface a clean message to the UI.
        raise ProfileGenerationError(
            f"Vertex AI request failed: {exc}. Please verify your GCP project, "
            "that the Vertex AI API is enabled, your credentials/permissions "
            "and internet connection, then try again."
        ) from exc

    content = (response.text or "").strip()
    if not content:
        raise ProfileGenerationError(
            "The model returned an empty response. Please try again."
        )
    return content


def split_sections(markdown_text: str) -> List[Tuple[str, str]]:
    """Parse the model output into ``(title, body)`` pairs.

    The prompt instructs the model to delimit sections with ``### <Title>``
    headers. This function splits on those headers and returns the sections in
    the canonical order defined in ``prompts.SECTION_TITLES``. Any content that
    does not match a known header is ignored, which keeps rendering robust.

    Args:
        markdown_text: The raw Markdown returned by :func:`generate_profile`.

    Returns:
        A list of ``(title, body)`` tuples in display order. If no known
        headers are found, returns a single ``("LinkedIn Profile", text)``
        pair so the user still sees the output.
    """

    # Split while keeping the header text. Matches lines like "### Skills".
    pattern = re.compile(r"^#{1,6}\s*(.+?)\s*$", re.MULTILINE)

    matches = list(pattern.finditer(markdown_text))
    if not matches:
        return [("LinkedIn Profile", markdown_text.strip())]

    found: Dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(
            markdown_text
        )
        body = markdown_text[start:end].strip()
        # Normalize the title so minor formatting differences still match.
        found[title.lower()] = body if body else "_No content provided._"

    ordered: List[Tuple[str, str]] = []
    for title in SECTION_TITLES:
        body = found.get(title.lower())
        if body is not None:
            ordered.append((title, body))

    # Fall back to whatever was parsed if none of the canonical titles matched.
    if not ordered:
        return [
            (match.group(1).strip(), _body_for(markdown_text, matches, i))
            for i, match in enumerate(matches)
        ]

    return ordered


def _body_for(text: str, matches: List[re.Match], index: int) -> str:
    """Return the body text that follows the header at ``index``.

    Helper used only by the fallback branch in :func:`split_sections`.
    """

    start = matches[index].end()
    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
    return text[start:end].strip()


def validate_inputs(data: Dict[str, str]) -> List[str]:
    """Validate the minimum required inputs before calling the API.

    Args:
        data: Dictionary of raw student inputs collected from the UI.

    Returns:
        A list of human-readable error messages. Empty list means valid.
    """

    errors: List[str] = []
    if not str(data.get("full_name", "")).strip():
        errors.append("Full Name is required.")
    if not str(data.get("career_goal", "")).strip():
        errors.append("Career Goal is required.")
    if not str(data.get("skills", "")).strip():
        errors.append("At least one Skill is required.")
    return errors
