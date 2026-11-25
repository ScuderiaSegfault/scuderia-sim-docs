# Sphinx configuration for the Scuderia simulator documentation.
# Documentation only: nothing here imports the simulator.

project = "Scuderia Sim"
author = "Scuderia Segfault"
copyright = "2026, Scuderia Segfault"
release = "docs"

extensions = [
    "myst_parser",
    "sphinx.ext.mathjax",
]

myst_enable_extensions = [
    "dollarmath",
    "amsmath",
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "Scuderia Sim"
html_static_path = []
html_theme_options = {
    "navigation_with_keys": True,
}
