"""Paletas y aplicación del tema visual de la interfaz."""
import tkinter as tk
from tkinter import ttk


LIGHT_THEME = {
    "background": "#f0f2f5",
    "surface": "#ffffff",
    "text": "#202124",
    "muted": "#5f6368",
    "control": "#ffffff",
    "select": "#b7d4f5",
    "button": "#e8eaed",
    "accent": "#1769aa",
}

DARK_THEME = {
    "background": "#202124",
    "surface": "#303134",
    "text": "#f1f3f4",
    "muted": "#bdc1c6",
    "control": "#3c4043",
    "select": "#4285f4",
    "button": "#5f6368",
    "accent": "#4285f4",
}

_current_theme = LIGHT_THEME
THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def _theme_background(widget, colors):
    if isinstance(widget, tk.Button) and widget.cget("background") in ("#1769aa", "#4285f4"):
        return colors["accent"]
    if isinstance(widget, (tk.Entry, tk.Checkbutton, tk.Scale)):
        return colors["control"]
    return colors["surface"]


def get_theme():
    return _current_theme


def set_theme(theme_name):
    global _current_theme
    _current_theme = THEMES.get(str(theme_name).lower(), LIGHT_THEME)
    return _current_theme


def apply_theme(root):
    """Aplica la paleta a widgets Tkinter existentes."""
    colors = get_theme()

    def update(widget):
        try:
            options = widget.keys()
            if "background" in options:
                widget.configure(background=_theme_background(widget, colors))
            if "foreground" in options:
                widget.configure(foreground=colors["text"])
            if "insertbackground" in options:
                widget.configure(insertbackground=colors["text"])
            if "activebackground" in options:
                widget.configure(activebackground=colors["button"])
            if "activeforeground" in options:
                widget.configure(activeforeground=colors["text"])
            if "selectcolor" in options:
                widget.configure(selectcolor=colors["select"])
            if "highlightbackground" in options:
                widget.configure(highlightbackground=colors["surface"])
            if isinstance(widget, tk.Canvas):
                widget.configure(background=colors["surface"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            update(child)

    style = ttk.Style(root)
    style.configure("TFrame", background=colors["surface"])
    style.configure("TLabel", background=colors["surface"], foreground=colors["text"])
    style.configure("App.TFrame", background=colors["surface"])
    style.configure("App.TLabel", background=colors["surface"], foreground=colors["text"])
    update(root)
