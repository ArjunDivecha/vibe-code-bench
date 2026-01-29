"""
=============================================================================
SCRIPT NAME: fast_suite.py
=============================================================================

INPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/eval_cases/*/tests.py:
  Existing functional tests. This file only references test names.

OUTPUT FILES:
- None (configuration module used by runner)

VERSION: 1.0
LAST UPDATED: 2026-01-27
AUTHOR: Arjun (automated by assistant)

DESCRIPTION:
Defines the fast evaluation suite: a smaller, high-signal subset of cases and
test functions designed to improve differentiation while reducing runtime.

DEPENDENCIES:
- Python standard library only

USAGE:
Imported by EvalRunner when --suite fast is enabled.

NOTES:
- Keep test names in sync with eval_cases/*/tests.py.
=============================================================================
"""

from __future__ import annotations

from typing import Optional


FAST_SUITE_CASES = [
    "case_03_calculator",
    "case_04_notes",
    "case_07_stopwatch",
    "case_08_typing",
    "case_11_palette",
    "case_15_markdown",
    "case_21_spreadsheet",
    "case_22_flowchart",
    "case_23_richtext",
    "case_25_dataviz",
    "case_31_api_integration",
    "case_33_refactor",
]


FAST_SUITE_TESTS = {
    "case_03_calculator": [
        "test_addition_7_plus_3",
        "test_multiplication_6_times_7",
        "test_division_100_by_4",
        "test_decimal_calculation",
        "test_chained_operations",
        "test_no_console_errors",
    ],
    "case_04_notes": [
        "test_can_create_note",
        "test_notes_persist_after_reload",
        "test_can_delete_note",
        "test_search_filters_notes",
        "test_has_title_and_content_inputs",
        "test_no_console_errors",
    ],
    "case_07_stopwatch": [
        "test_stopwatch_starts_counting",
        "test_has_timer_mode",
        "test_dual_mode_interface",
        "test_reset_clears_time",
        "test_has_lap_functionality",
        "test_no_console_errors",
    ],
    "case_08_typing": [
        "test_shows_text_to_type",
        "test_has_input_area",
        "test_typing_updates_stats",
        "test_shows_wpm",
        "test_shows_accuracy",
        "test_no_console_errors",
    ],
    "case_11_palette": [
        "test_generate_changes_colors",
        "test_has_lock_functionality",
        "test_shows_color_codes",
        "test_has_copy_functionality",
        "test_spacebar_generates",
        "test_no_console_errors",
    ],
    "case_15_markdown": [
        "test_has_editor_area",
        "test_has_preview_area",
        "test_bold_renders",
        "test_list_renders",
        "test_live_preview",
        "test_no_console_errors",
    ],
    "case_21_spreadsheet": [
        "test_formula_addition",
        "test_cell_reference_formula",
        "test_sum_function",
        "test_keyboard_navigation",
        "test_formula_bar_exists",
        "test_no_console_errors",
    ],
    "case_22_flowchart": [
        "test_has_svg_canvas",
        "test_can_add_shape_to_canvas",
        "test_can_connect_shapes",
        "test_connections_have_arrows",
        "test_has_delete_capability",
        "test_no_console_errors",
    ],
    "case_23_richtext": [
        "test_has_contenteditable",
        "test_can_type_text",
        "test_bold_button_works",
        "test_italic_button_works",
        "test_toolbar_has_formatting_buttons",
        "test_no_console_errors",
    ],
    "case_25_dataviz": [
        "test_uses_svg_not_libraries",
        "test_has_bar_chart",
        "test_has_line_chart",
        "test_has_pie_chart",
        "test_has_legend",
        "test_no_console_errors",
    ],
    "case_31_api_integration": [
        "test_script_exists",
        "test_has_help_option",
        "test_uses_open_meteo_api",
        "test_uses_geocoding",
        "test_uses_urllib_not_requests",
        "test_no_syntax_errors",
    ],
    "case_33_refactor": [
        "test_package_structure_exists",
        "test_has_models_module",
        "test_has_storage_module",
        "test_has_manager_module",
        "test_no_import_errors",
        "test_cli_runs",
    ],
}


def get_fast_suite_cases() -> list[str]:
    """Return the list of fast suite case names."""
    return list(FAST_SUITE_CASES)


def get_fast_suite_allowlist(case_name: str) -> Optional[set[str]]:
    """Return allowed test names for a case, or None for full tests."""
    tests = FAST_SUITE_TESTS.get(case_name)
    return set(tests) if tests else None
