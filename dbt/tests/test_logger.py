from logger import Checks, target_line


def test_checks_counts_only_failures(capsys):
    c = Checks()
    c.line(True, "a")
    c.line(None, "b", "skip")
    c.line(False, "c", "boom")
    out = capsys.readouterr().out
    assert c.bad == 1
    assert "[OK  ] a" in out and "[skip] b" in out and "[FAIL] c" in out and "boom" in out


def test_target_line_formats_unknown_type():
    r = {"target": "pg", "type": None, "ok": False, "ms": 7, "message": "нет"}
    s = target_line(r)
    assert s.startswith("[FAIL] pg") and " ? " in s and s.endswith("нет")
