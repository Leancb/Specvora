import re
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_readme_indexes_every_numbered_module_once_with_a_valid_link():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("### Índice completo dos 44 módulos", 1)[1].split(
        "### Documentos gerais", 1
    )[0]
    entries = re.findall(
        r"(?m)^(\d+)\. \[[^]]+\]\((docs/modules/[^)]+)\)  \n   [^\n]+$", section
    )
    assert [int(number) for number, _path in entries] == list(range(1, 45))
    assert len({path for _number, path in entries}) == 44
    assert all((ROOT / path).is_file() for _number, path in entries)


def test_numbered_module_directory_matches_readme_index():
    module_files = sorted((ROOT / "docs/modules").glob("[0-9][0-9]_*.md"))
    assert [int(path.name[:2]) for path in module_files] == list(range(1, 45))
