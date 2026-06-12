"""Парсеры Graff: язык → (nodes, edges).

python_ast — Python через встроенный ast (полная точность).
treesitter  — остальные языки через tree-sitter (структурные определения + вызовы).
"""
from .python_ast import parse_python
from .treesitter import parse_treesitter, TS_LANGS, ext_to_lang

__all__ = ["parse_python", "parse_treesitter", "TS_LANGS", "ext_to_lang"]
