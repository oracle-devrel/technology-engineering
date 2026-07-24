"""Logan QL canonicalizer (D-01, D-02, D-04).

Phase 6 normalizes **whitespace + quoting only**. Commutative reorder,
AND-chain sort, and keyword case-folding are deferred (D-01).

Strategy: hand-rolled mini-tokenizer (~150 LoC) over Logan QL output.
Tokens are re-emitted with collapsed whitespace and uniform single-quote
strings (matching the current promoted corpus). Malformed input raises
``CanonicalizationError`` (D-04) — no best-effort passthrough.
"""

from __future__ import annotations

from typing import List, Tuple


class CanonicalizationError(Exception):
    """Raised when ``canonical()`` encounters malformed KQL/Logan QL input.

    Includes unterminated quoted strings and unrecognized characters
    outside the whitespace/identifier/operator/punctuation/quote classes.
    """


# Multi-character operator tokens, longest first so the tokenizer prefers
# ``==`` over ``=`` and so on.
_MULTI_OPS = ("==", "!=", "<=", ">=", "=~", "!~", "&&", "||")
_SINGLE_OPS = set("=<>+-*/")
_PUNCTUATION = set(",()[]{};:")


def _tokenize(text: str) -> List[Tuple[str, str]]:
    """Return a list of (kind, value) token tuples.

    Kinds: WS, QSTRING, IDENT, NUMBER, OP, PUNCT, PIPE, COMMA.
    Whitespace runs collapse to a single WS token with value " ".
    """

    tokens: List[Tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        # Whitespace run
        if ch.isspace():
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            tokens.append(("WS", " "))
            i = j
            continue

        # Quoted string (single or double). Logan QL doubles a single quote
        # to escape it: 'foo''bar' is the literal foo'bar.
        if ch in ("'", '"'):
            quote = ch
            j = i + 1
            buf: List[str] = []
            while j < n:
                cj = text[j]
                if cj == quote:
                    # Check for doubled-quote escape: only valid inside a
                    # single-quoted string per Logan QL convention.
                    if quote == "'" and j + 1 < n and text[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(cj)
                j += 1
            else:
                raise CanonicalizationError(
                    f"Unterminated quoted string starting at offset {i}"
                )
            tokens.append(("QSTRING", "".join(buf)))
            i = j + 1
            continue

        # Pipe — stage separator. Distinguish from ``=~``/``!~`` operators
        # (handled above as multi-char ops) and from ``||`` (booleans).
        if ch == "|":
            # ``||`` is a boolean OR in some KQL dialects; treat as an
            # operator token so we don't fragment it.
            if i + 1 < n and text[i + 1] == "|":
                tokens.append(("OP", "||"))
                i += 2
                continue
            tokens.append(("PIPE", "|"))
            i += 1
            continue

        # Comma — separate token so emit logic can space-pad it.
        if ch == ",":
            tokens.append(("COMMA", ","))
            i += 1
            continue

        # Multi-char operator
        matched = False
        for op in _MULTI_OPS:
            if text.startswith(op, i):
                tokens.append(("OP", op))
                i += len(op)
                matched = True
                break
        if matched:
            continue

        # Single-char operator
        if ch in _SINGLE_OPS:
            tokens.append(("OP", ch))
            i += 1
            continue

        # Punctuation
        if ch in _PUNCTUATION:
            tokens.append(("PUNCT", ch))
            i += 1
            continue

        # Number
        if ch.isdigit() or (ch == "-" and i + 1 < n and text[i + 1].isdigit()):
            j = i + 1
            seen_dot = False
            while j < n and (text[j].isdigit() or (text[j] == "." and not seen_dot)):
                if text[j] == ".":
                    seen_dot = True
                j += 1
            tokens.append(("NUMBER", text[i:j]))
            i = j
            continue

        # Identifier (letter / underscore / dollar / dot for qualified names,
        # plus digits after the first char). Permissive — Logan QL identifiers
        # cover a range of shapes.
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in "_."):
                j += 1
            tokens.append(("IDENT", text[i:j]))
            i = j
            continue

        raise CanonicalizationError(
            f"Unrecognized character {ch!r} at offset {i}"
        )

    return tokens


def _emit_qstring(value: str) -> str:
    """Re-emit a string literal in single-quote form, escaping interior quotes."""

    return "'" + value.replace("'", "''") + "'"


def _emit(tokens: List[Tuple[str, str]]) -> str:
    """Re-emit normalized whitespace + quoting from a token stream."""

    out: List[str] = []
    n = len(tokens)
    for idx, (kind, value) in enumerate(tokens):
        if kind == "WS":
            # Only emit a single space, and only when surrounded by
            # non-whitespace tokens. Skip leading/trailing.
            if not out or out[-1].endswith(" "):
                continue
            if idx == n - 1:
                continue
            out.append(" ")
        elif kind == "QSTRING":
            out.append(_emit_qstring(value))
        elif kind == "PIPE":
            # Ensure exactly one space on each side of the stage separator.
            if out and not out[-1].endswith(" "):
                out.append(" ")
            out.append("|")
            out.append(" ")
        elif kind == "COMMA":
            # Strip preceding whitespace, follow with a single space.
            while out and out[-1] == " ":
                out.pop()
            out.append(",")
            out.append(" ")
        else:
            out.append(value)

    result = "".join(out).strip()
    # Collapse any accidental double spaces that survived the merge.
    while "  " in result:
        result = result.replace("  ", " ")
    return result


def canonical(query: str) -> str:
    """Return the canonical Logan QL form of ``query``.

    Normalizes only whitespace and quoting per D-01. Idempotent:
    ``canonical(canonical(x)) == canonical(x)``.

    Raises ``CanonicalizationError`` on malformed input (D-04).
    """

    if not isinstance(query, str):
        raise CanonicalizationError(f"canonical() requires str, got {type(query).__name__}")
    tokens = _tokenize(query)
    return _emit(tokens)


__all__ = ["canonical", "CanonicalizationError"]
