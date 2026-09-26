"""
command_runner.py  --  Compiler Interface & Python Fallback
===========================================================
Provides the CommandRunner class which bridges the Python GUI
and the Flex/Bison compiler.

Strategy (automatic, no user action needed):
  1. If  compiler/robot_compiler.exe  exists  ->  call it as a
     subprocess (true Flex+Bison pipeline, same as grading demo).
  2. If the binary is missing  ->  use the built-in Python
     lexer+parser that mirrors the Flex/Bison grammar exactly
     so the GUI works even without a C build environment.

Both modes produce the same JSON-shaped command dictionaries.
"""

import subprocess
import json
import os
import re
import sys

# ── Path to the compiled Flex/Bison binary ───────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT  = os.path.dirname(_THIS_DIR)
BINARY_PATH = os.path.join(_PROJ_ROOT, "compiler", "robot_compiler.exe")


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON LEXER  (mirrors robot_lexer.l exactly)
# ═══════════════════════════════════════════════════════════════════════════════

class Token:
    """A single lexical token produced by the Python lexer."""
    __slots__ = ("type", "value", "line")

    def __init__(self, type_: str, value, line: int):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, line={self.line})"


# ── Keyword → token-type map (case-insensitive, same aliases as robot_lexer.l)
KEYWORDS: dict[str, str] = {
    # core keywords
    "move"     : "MOVE",
    "go"       : "MOVE",        # alias
    "forward"  : "FORWARD",
    "backward" : "BACKWARD",
    "back"     : "BACKWARD",    # alias
    "left"     : "LEFT",
    "right"    : "RIGHT",
    "turn"     : "TURN",
    "rotate"   : "TURN",        # alias
    "stop"     : "STOP",
    "halt"     : "STOP",        # alias
    "ability"  : "ABILITY",
    "skill"    : "ABILITY",     # alias
    "speed"    : "SPEED",
    # unit keywords
    "steps"    : "STEPS",
    "step"     : "STEPS",       # singular alias
    "degrees"  : "DEGREES",
    "degree"   : "DEGREES",     # singular alias
    "deg"      : "DEGREES",     # short alias
}


def tokenize(source: str) -> tuple[list[Token], list[str]]:
    """
    Lexical analyser — mirrors robot_lexer.l.
    Scans 'source' left-to-right and returns (tokens, errors).
    """
    tokens : list[Token] = []
    errors : list[str]   = []
    line   = 1
    pos    = 0

    while pos < len(source):

        # ── Skip whitespace (space, tab, carriage-return) ──
        m = re.match(r'[ \t\r]+', source[pos:])
        if m:
            pos += m.end()
            continue

        # ── Skip comment (# to end of line) ──
        m = re.match(r'#[^\n]*', source[pos:])
        if m:
            pos += m.end()
            continue

        # ── Newline: increment line counter ──
        if source[pos] == '\n':
            line += 1
            pos  += 1
            continue

        # ── Float ──
        m = re.match(r'\d+\.\d+', source[pos:])
        if m:
            tokens.append(Token("NUMBER", float(m.group()), line))
            pos += m.end()
            continue

        # ── Integer ──
        m = re.match(r'\d+', source[pos:])
        if m:
            tokens.append(Token("NUMBER", float(m.group()), line))
            pos += m.end()
            continue

        # ── String literal  ("...") ──
        m = re.match(r'"[^"]*"', source[pos:])
        if m:
            content = m.group()[1:-1]   # strip surrounding quotes
            tokens.append(Token("STRING", content, line))
            pos += m.end()
            continue

        # ── Identifier / word ──
        m = re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', source[pos:])
        if m:
            word  = m.group().lower()
            ttype = KEYWORDS.get(word)
            if ttype is None:
                errors.append(
                    f"Syntax Error (Line {line}): Unknown keyword '{word}'. "
                    f"Valid commands: move, turn, speed, stop, ability."
                )
                # Keep token as UNKNOWN for recovery
                tokens.append(Token("UNKNOWN", word, line))
            else:
                tokens.append(Token(ttype, word, line))
            pos += m.end()
            continue

        # ── Unknown character ──
        errors.append(
            f"Lexical Error (Line {line}): Invalid symbol '{source[pos]}'."
        )
        pos += 1

    tokens.append(Token("EOF", None, line))
    return tokens, errors


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON PARSER WITH ENHANCED ERROR REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

class Parser:
    """Recursive-descent parser with friendly error messages."""

    def __init__(self, tokens: list[Token]):
        self.tokens   = tokens
        self.pos      = 0
        self.errors   : list[str]  = []
        self.commands : list[dict] = []

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _consume(self, expected_type: str, context: str = "") -> Token | None:
        tok = self._current()
        if tok.type != expected_type:
            val_str = f"'{tok.value}'" if tok.value is not None else "end of input"
            ctx_msg = f" while parsing '{context}'" if context else ""
            
            hints = {
                "NUMBER": "a number (e.g. 5, 90)",
                "STRING": "a double-quoted string (e.g. \"shield\")",
                "STEPS": "'steps'",
                "DEGREES": "'degrees'",
            }
            expected_desc = hints.get(expected_type, expected_type)

            self.errors.append(
                f"Syntax Error (Line {tok.line}): Expected {expected_desc}{ctx_msg}, "
                f"but found {val_str}."
            )
            return None
        self.pos += 1
        return tok

    def parse(self):
        """Parse full stream."""
        while self._current().type != "EOF":
            cmd = self._parse_command()
            if cmd is not None:
                self.commands.append(cmd)

    def _parse_command(self) -> dict | None:
        tok = self._current()
        if   tok.type == "MOVE"   : return self._parse_move()
        elif tok.type == "TURN"   : return self._parse_turn()
        elif tok.type == "SPEED"  : return self._parse_speed()
        elif tok.type == "STOP"   : return self._parse_stop()
        elif tok.type == "ABILITY": return self._parse_ability()
        elif tok.type == "UNKNOWN":
            self.pos += 1  # Skip unknown keyword already reported by lexer
            return None
        else:
            self.errors.append(
                f"Syntax Error (Line {tok.line}): Unexpected token '{tok.value}'. "
                f"Expected a command (move, turn, speed, stop, ability)."
            )
            self.pos += 1  # Skip token
            return None

    def _parse_direction(self, cmd_name: str) -> str | None:
        tok = self._current()
        if tok.type in ("FORWARD", "BACKWARD", "LEFT", "RIGHT"):
            self.pos += 1
            return tok.value
        val = f"'{tok.value}'" if tok.value is not None else "end of line"
        self.errors.append(
            f"Syntax Error (Line {tok.line}): '{cmd_name}' requires a direction "
            f"(forward, backward, left, right), but found {val}."
        )
        return None

    def _parse_move(self) -> dict | None:
        tok = self._consume("MOVE")
        direction = self._parse_direction("move")
        if direction is None:
            self._recover_line()
            return None
        num = self._consume("NUMBER", context=f"move {direction}")
        if num is None:
            self._recover_line()
            return None
        if self._current().type == "STEPS":
            self._consume("STEPS")
        return {
            "type"      : "move",
            "direction" : direction,
            "value"     : num.value,
            "unit"      : "steps",
            "extra"     : ""
        }

    def _parse_turn(self) -> dict | None:
        self._consume("TURN")
        direction = self._parse_direction("turn")
        if direction is None:
            self._recover_line()
            return None
        num = self._consume("NUMBER", context=f"turn {direction}")
        if num is None:
            self._recover_line()
            return None
        if self._current().type == "DEGREES":
            self._consume("DEGREES")
        return {
            "type"      : "turn",
            "direction" : direction,
            "value"     : num.value,
            "unit"      : "degrees",
            "extra"     : ""
        }

    def _parse_speed(self) -> dict | None:
        self._consume("SPEED")
        num = self._consume("NUMBER", context="speed")
        if num is None:
            self._recover_line()
            return None
        val = int(num.value)
        if val < 1 or val > 10:
            self.errors.append(
                f"Semantic Warning (Line {self.tokens[self.pos-1].line}): "
                f"speed value {val} is outside recommended range (1 to 10)."
            )
        return {
            "type"  : "speed",
            "value" : num.value,
            "unit"  : "",
            "extra" : ""
        }

    def _parse_stop(self) -> dict | None:
        self._consume("STOP")
        return {
            "type"  : "stop",
            "value" : -1,
            "unit"  : "",
            "extra" : ""
        }

    def _parse_ability(self) -> dict | None:
        self._consume("ABILITY")
        tok = self._current()
        if tok.type != "STRING":
            val_str = f"'{tok.value}'" if tok.value is not None else "end of input"
            self.errors.append(
                f"Syntax Error (Line {tok.line}): 'ability' expects a double-quoted string. "
                f"Found {val_str}. Example: ability \"shield\""
            )
            self._recover_line()
            return None
        s = self._consume("STRING")
        return {
            "type"  : "ability",
            "value" : -1,
            "unit"  : "",
            "extra" : s.value
        }

    def _recover_line(self):
        """Skip tokens until the next line or command keyword."""
        cur_line = self._current().line
        while (self._current().type != "EOF" and 
               self._current().line == cur_line and 
               self._current().type not in ("MOVE","TURN","SPEED","STOP","ABILITY")):
            self.pos += 1


# ═══════════════════════════════════════════════════════════════════════════════
#  CommandRunner Public API
# ═══════════════════════════════════════════════════════════════════════════════

class CommandRunner:
    """
    Parses Robot Command Language source code and returns
    structured command dictionaries.
    """

    def __init__(self):
        self._binary_ok = os.path.isfile(BINARY_PATH)

    def get_mode(self) -> str:
        if self._binary_ok:
            return "Flex / Bison  (C binary)"
        return "Python Lexer+Parser  (fallback — works without MinGW)"

    def run(self, source_code: str) -> tuple[list[dict], list[str]]:
        """
        Parse source_code.
        Returns (commands, errors).
        """
        if self._binary_ok:
            return self._run_binary(source_code)
        return self._run_python(source_code)

    def _run_binary(self, source_code: str):
        try:
            # Use binary mode + explicit UTF-8 to avoid Windows cp1252
            # UnicodeEncodeError when source contains non-ASCII characters
            result = subprocess.run(
                [BINARY_PATH],
                input=source_code.encode("utf-8"),   # encode input as UTF-8 bytes
                capture_output=True,                  # stdout/stderr returned as bytes
                timeout=10
            )
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            stdout = result.stdout.decode("utf-8", errors="replace").strip()

            errors = [
                line for line in stderr.splitlines()
                if "Error" in line or "error" in line or "FAILED" in line
            ]

            if stdout:
                try:
                    commands = json.loads(stdout)
                    return commands, errors
                except json.JSONDecodeError as exc:
                    errors.append(f"JSON decode error: {exc}")
                    return [], errors

            return [], errors

        except subprocess.TimeoutExpired:
            return [], ["Error: compiler process timed out"]
        except Exception:
            self._binary_ok = False
            return self._run_python(source_code)

    def _run_python(self, source_code: str):
        tokens, lex_errors = tokenize(source_code)
        parser = Parser(tokens)
        parser.parse()
        all_errors = lex_errors + parser.errors
        return parser.commands, all_errors
