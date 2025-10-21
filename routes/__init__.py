"""
Routes API pour FormForge
"""

from .forms import forms_bp
from .questions import questions_bp
from .responses import responses_bp

__all__ = ["forms_bp", "questions_bp", "responses_bp"]
