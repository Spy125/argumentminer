"""CLI smoke tests.

These invoke the actual Typer commands so that a drift between the documented
command names and the code (for example a command being renamed, or the app
collapsing to a single command) fails a test instead of only surfacing when a
user runs the README example.
"""

from typer.testing import CliRunner

from argumentminer.cli import app

runner = CliRunner()

SAMPLE = (
    "Social media harms teenagers. Studies show depression rose after 2012. "
    "Either we ban it or society collapses."
)


def test_mine_command_runs():
    result = runner.invoke(app, ["mine", SAMPLE])
    assert result.exit_code == 0
    assert "Argument Structure" in result.stdout


def test_mine_reports_fallacy():
    result = runner.invoke(app, ["mine", SAMPLE])
    assert result.exit_code == 0
    assert "Fallac" in result.stdout  # matches the "Detected Fallacies" table


def test_fallacies_command_runs():
    result = runner.invoke(app, ["fallacies", "Either we ban it or society collapses."])
    assert result.exit_code == 0
    assert "False Dichotomy" in result.stdout


def test_fallacies_clean_text():
    result = runner.invoke(app, ["fallacies", "The meeting is scheduled for Tuesday afternoon."])
    assert result.exit_code == 0
    assert "No obvious fallacies" in result.stdout


def test_missing_text_errors():
    result = runner.invoke(app, ["mine"])
    assert result.exit_code == 1
