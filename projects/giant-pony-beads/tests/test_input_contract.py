"""Input-contract gates for giant-beads main.py (no renders).

Regression tests for the Sol FIX round: an explicitly requested letter
job must run or fail (never silently vanish), --word-gap must be finite
>= 0, and --spec field types are validated with named-field messages
(no silent truncation/coercion, no AttributeError).
"""
import json
import math

import pytest

from conftest import load_main

gbmain = load_main()


# --- BLOCK-1: explicit letters that normalise to empty must fail ---------

def test_explicit_letters_helper_flags_no_renderable_letters():
    explicit, letters = gbmain.explicit_letters("123")
    assert explicit is True
    assert letters == []


def test_explicit_letters_helper_passes_blanks_through():
    # absent / empty letters stay "not explicitly requested"
    assert gbmain.explicit_letters(None) == (False, [])
    assert gbmain.explicit_letters("") == (False, [])
    assert gbmain.explicit_letters("  ") == (False, [])


def test_main_invalid_letters_with_parts_exits_2_without_rendering(
        tmp_path, capsys):
    """--letters 123 --parts heart: exit 2 before any render happens."""
    res = gbmain.main([
        "--width", "60", "--letters", "123", "--parts", "heart",
        "--save-to", str(tmp_path),
    ])
    assert res == 2
    err = capsys.readouterr().err
    assert "--letters" in err and "123" in err
    assert "no renderable A-Z letters" in err
    # nothing was rendered: the gate fires before any job
    assert not list(tmp_path.glob("*.stl"))


def test_main_invalid_spec_letters_list_exits_2(tmp_path, capsys):
    res = gbmain.main([
        "--spec", json.dumps({"letters": ["1", "2"], "parts": "heart"}),
        "--save-to", str(tmp_path),
    ])
    assert res == 2
    assert "no renderable A-Z letters" in capsys.readouterr().err


# --- BLOCK-2: --word-gap must be a finite number >= 0 --------------------

def test_word_gap_error_rejects_negative_and_nonfinite():
    assert "-10" in gbmain.word_gap_error(-10.0)
    assert gbmain.word_gap_error(0) is None          # zero = touching beads
    assert gbmain.word_gap_error(10.0) is None
    assert "inf" in gbmain.word_gap_error(math.inf)
    assert gbmain.word_gap_error(math.nan) is not None


def test_main_negative_word_gap_exits_2(tmp_path, capsys):
    res = gbmain.main([
        "--width", "60", "--letters", "A", "--word-gap", "-10",
        "--save-to", str(tmp_path),
    ])
    assert res == 2
    err = capsys.readouterr().err
    assert "--word-gap" in err and "-10" in err
    assert not list(tmp_path.glob("*.stl"))


# --- BLOCK-2: --spec field types are validated with named messages -------

def _spec(**fields):
    return gbmain.parse_args(["--spec", json.dumps(fields)])


def test_spec_fractional_width_rejected_not_truncated():
    with pytest.raises(ValueError) as exc:
        gbmain.config_from_args(_spec(parts="heart", width=120.9))
    assert "width" in str(exc.value) and "120.9" in str(exc.value)


def test_spec_boolean_width_rejected_named_field():
    with pytest.raises(ValueError) as exc:
        gbmain.config_from_args(_spec(parts="heart", width=True))
    assert "width" in str(exc.value) and "boolean" in str(exc.value)


def test_spec_non_numeric_width_rejected():
    with pytest.raises(ValueError) as exc:
        gbmain.config_from_args(_spec(parts="heart", width="120"))
    assert "width" in str(exc.value)


def test_spec_nonpositive_width_rejected():
    for bad in (0, -60, float("inf"), float("nan")):
        with pytest.raises(ValueError) as exc:
            gbmain.config_from_args(_spec(parts="heart", width=bad))
        assert "width" in str(exc.value)


def test_spec_numeric_letters_rejected_no_attributeerror():
    with pytest.raises(ValueError) as exc:
        gbmain.config_from_args(_spec(parts="heart", letters=123))
    assert "letters" in str(exc.value)


def test_spec_non_string_parts_save_to_preset_rejected():
    for key, bad in (("parts", ["heart"]), ("save_to", 7),
                     ("preset", True)):
        with pytest.raises(ValueError) as exc:
            gbmain.config_from_args(_spec(**{key: bad}))
        assert key in str(exc.value)


def test_spec_letters_list_accepted_and_space_joined():
    ns = _spec(letters=["c", "a"], parts="heart")
    cfg = gbmain.config_from_args(ns)
    assert cfg.letters == "c a"


def test_spec_letters_list_rejects_empty_or_nonstring_entries():
    for bad in (["c", ""], ["c", 3], [None]):
        with pytest.raises(ValueError) as exc:
            gbmain.config_from_args(_spec(letters=bad))
        assert "letters" in str(exc.value)


# --- CLI flag consistency --------------------------------------------------

def test_cli_fractional_width_still_rejected_by_argparse():
    # argparse type=int already exits 2 for non-integers; keep it that way
    with pytest.raises(SystemExit) as exc:
        gbmain.parse_args(["--width", "120.9"])
    assert exc.value.code == 2
