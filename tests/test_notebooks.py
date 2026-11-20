"""The milestone notebooks are valid, ship without outputs, and their code parses."""
from __future__ import annotations

import ast
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS = sorted((Path(__file__).resolve().parents[1] / 'notebooks').glob('*.ipynb'))


def test_there_is_one_notebook_per_milestone():
    assert [p.name[:2] for p in NOTEBOOKS] == ['01', '02', '03', '04']


@pytest.mark.parametrize('path', NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_is_valid_clean_and_parses(path):
    book = nbformat.read(path, as_version=4)
    nbformat.validate(book)
    assert book.cells[0].cell_type == 'markdown'
    assert 'https://livetennisapi.com/teach/capstone' in book.cells[0].source
    for cell in book.cells:
        if cell.cell_type == 'code':
            assert cell.outputs == [] and cell.execution_count is None
            ast.parse(cell.source)
