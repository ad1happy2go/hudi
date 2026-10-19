#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Extract every Hudi configuration property from the source tree, with code context.

The published configuration reference tells a user a config's key, default and
description. It cannot tell them where the value is actually read, what else is
read beside it, or under what condition the read happens at all. That last part
is what makes a config silently do nothing. This script recovers it from source.

Three passes:

  1. Declarations. Parse ``ConfigProperty`` builder chains (and Flink's
     ``ConfigOptions`` chains whose key is a literal ``hoodie.*``) out of the
     main source trees. Chains span many lines and end at the statement
     semicolon, so the parser works on brace/paren-balanced statement text
     rather than on single lines.

  2. Accessors. Find config-class methods whose body is a single
     ``getInt(SOME_CONFIG)`` style read, so that call sites of
     ``getInlineCompactDeltaCommitMax()`` can be attributed back to
     ``hoodie.compact.inline.max.delta.commits``.

  3. Read sites. Walk every source file again, attributing each mention of a
     config constant or of a resolved accessor to the enclosing method, and
     recording the other configs mentioned in that same method (co-configs) and
     the enclosing ``if``/``switch``/``case`` conditions (gating). The gating
     pass is a textual heuristic; every condition it emits is marked as such.

Standard library only. Written to degrade: anything it cannot fully parse still
appears in the catalog, carrying a ``parseWarnings`` list.

Usage:
    python3 scripts/generate_config_catalog.py [--repo-root DIR] [--out-dir DIR]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, OrderedDict

# --------------------------------------------------------------------------
# Tree walking
# --------------------------------------------------------------------------

# Modules that declare configs. Anything under the repo root that is not one of
# these is still scanned for *read sites*; declarations are only looked for in
# main source trees, which SOURCE_DIR_MARKER enforces.
SOURCE_DIR_MARKER = os.path.join("src", "main")

EXCLUDED_PATH_PARTS = (
    os.sep + "target" + os.sep,
    os.sep + "test" + os.sep,
    os.sep + "src" + os.sep + "test" + os.sep,
    os.sep + "node_modules" + os.sep,
    os.sep + ".git" + os.sep,
    os.sep + ".claude" + os.sep,
)

# Directories we never descend into at all. ".claude" matters: a nested git
# worktree under .claude/worktrees/ is a second full copy of the tree, and
# scanning it yields duplicate declarations with unusable paths.
PRUNED_DIR_NAMES = {"target", "node_modules", ".git", ".claude", ".idea", "docker", "rfc"}

READ_SITE_EXTENSIONS = (".java", ".scala")

MAX_READ_SITES = 20

# Collect well past the reported cap so that ranking, not file-walk order, picks
# which sites survive. Without this the twenty slots fill alphabetically and the
# CLI's MOR-to-COW helper crowds out the archiver and the compaction scheduler
# for hoodie.compact.inline.max.delta.commits.
COLLECT_READ_SITES = 200

# How much a read site is worth to someone trying to understand runtime
# behaviour. Core engine code first; CLI, examples and test harnesses last --
# they are real reads, so they are kept, just not at the expense of the code
# that actually runs during a write.
READ_SITE_MODULE_RANK = (
    ("hudi-client", 0),
    ("hudi-common", 0),
    ("hudi-spark-datasource", 1),
    ("hudi-flink-datasource", 1),
    ("hudi-utilities", 1),
    ("hudi-sync", 2),
    ("hudi-aws", 2),
    ("hudi-gcp", 2),
    ("hudi-cli", 3),
    ("hudi-examples", 4),
    ("hudi-integ-test", 4),
)


def read_site_rank(site):
    """Lower sorts first. Config-class plumbing ranks below real consumers."""
    path = site.get("file") or ""
    module_rank = 2
    for prefix, rank in READ_SITE_MODULE_RANK:
        if path.startswith(prefix):
            module_rank = rank
            break
    # A read inside the config class that declares it is plumbing, not a
    # consumer -- builders and getters, which tell you nothing about behaviour.
    owner = site.get("class") or ""
    plumbing = 1 if (owner.startswith("Hoodie") and owner.endswith("Config")) else 0
    # An accessor call site names a real caller; a bare constant reference is
    # often the declaration's neighbourhood.
    via = site.get("via") or ""
    via_rank = 0 if via.startswith("accessor:") else 1
    return (plumbing, module_rank, via_rank, path, site.get("line") or 0)
MAX_CO_CONFIGS = 25
MAX_GATES_PER_SITE = 3


def is_excluded(path):
    normalized = os.sep + path.strip(os.sep) + os.sep
    return any(part in normalized for part in EXCLUDED_PATH_PARTS)


def walk_source_files(repo_root, extensions):
    """Yield absolute paths of non-test, non-generated source files."""
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in PRUNED_DIR_NAMES]
        if is_excluded(dirpath):
            continue
        for filename in filenames:
            if filename.endswith(extensions):
                full = os.path.join(dirpath, filename)
                if not is_excluded(full):
                    yield full


# --------------------------------------------------------------------------
# Lightweight Java/Scala lexing helpers
# --------------------------------------------------------------------------

def strip_comments_and_strings(text, keep_string_bodies=False, scala=False):
    """Blank out comments and (optionally) string bodies, preserving offsets.

    Offsets are preserved so that any index computed on the stripped text maps
    straight back onto the original. Newlines survive so line numbers hold.

    ``scala`` switches on the two lexical rules that differ enough to corrupt
    offsets if Java's are applied: triple-quoted strings, and the fact that a
    single quote opens a character literal in Java but far more often opens a
    symbol or a type parameter in Scala (``Option['a]``, ``case 'x'``). Treating
    a lone Scala quote as a string opener would blank out the rest of the file.
    """
    out = list(text)
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if scala and ch == '"' and text.startswith('"""', i):
            # Triple-quoted: ends at the next `"""`, and may span lines.
            out[i] = out[i + 1] = out[i + 2] = " "
            i += 3
            while i < n and not text.startswith('"""', i):
                if not keep_string_bodies and text[i] != "\n":
                    out[i] = " "
                i += 1
            for offset in range(3):
                if i + offset < n:
                    out[i + offset] = " "
            i += 3
            continue
        if scala and ch == "'":
            # Only a genuine `'c'` char literal; anything else is a symbol or a
            # type parameter and must be left alone.
            if i + 2 < n and text[i + 2] == "'" and text[i + 1] != "\\":
                if not keep_string_bodies:
                    out[i + 1] = " "
                i += 3
            elif i + 3 < n and text[i + 1] == "\\" and text[i + 3] == "'":
                if not keep_string_bodies:
                    out[i + 1] = out[i + 2] = " "
                i += 4
            else:
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            out[i] = out[i + 1] = " "
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            if i < n:
                out[i] = " "
                if i + 1 < n:
                    out[i + 1] = " "
                i += 2
        elif ch in ('"', "'"):
            quote = ch
            i += 1
            while i < n:
                if text[i] == "\\":
                    if not keep_string_bodies:
                        out[i] = " "
                        if i + 1 < n:
                            out[i + 1] = " "
                    i += 2
                    continue
                if text[i] == quote:
                    break
                # A single-quoted string never spans a line. Stopping here keeps
                # one unterminated quote from blanking the rest of the file.
                if text[i] == "\n":
                    break
                if not keep_string_bodies:
                    out[i] = " "
                i += 1
            i += 1
        else:
            i += 1
    return "".join(out)


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def find_statement_end(text, start):
    """Index just past the ``;`` ending the statement that starts at ``start``.

    Respects nesting and ignores semicolons inside strings, chars and comments.
    """
    masked = strip_comments_and_strings(text[start:])
    depth_paren = depth_brace = depth_bracket = 0
    for offset, ch in enumerate(masked):
        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
        elif ch == ";" and depth_paren <= 0 and depth_brace <= 0 and depth_bracket <= 0:
            return start + offset + 1
    return -1


def find_scala_statement_end(text, start):
    """Index just past the end of a Scala builder chain starting at ``start``.

    Scala has no statement terminator, so the chain ends at the first newline
    that leaves every bracket balanced and is not followed by a continuation --
    another ``.step(...)``, or a binary operator left dangling from the previous
    line. Builder chains here do carry multi-line lambdas (``withInferFunction``
    takes one), which is why balance has to be tracked rather than stopping at
    the first line break.
    """
    masked = strip_comments_and_strings(text[start:], scala=True)
    depth_paren = depth_brace = depth_bracket = 0
    limit = min(len(masked), 20000)
    # A match may begin on the newline that ends the previous statement; that
    # newline must not be read as this chain's terminator.
    i = 0
    while i < limit and masked[i].isspace():
        i += 1
    while i < limit:
        ch = masked[i]
        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
        elif ch == "\n" and depth_paren <= 0 and depth_brace <= 0 and depth_bracket <= 0:
            before = masked[:i].rstrip()
            # A line ending in `+`, `=` or `.` is continued on the next one.
            if before.endswith(("+", "=", ".", ",", "(", "{")):
                i += 1
                continue
            rest = masked[i + 1:]
            stripped = rest.lstrip()
            if stripped.startswith(".") and not stripped.startswith(".."):
                i += 1
                continue
            return start + i
        i += 1
    return start + limit


def split_top_level_args(arg_text):
    """Split a call's argument text on top-level commas."""
    masked = strip_comments_and_strings(arg_text)
    args = []
    depth = 0
    current_start = 0
    for i, ch in enumerate(masked):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            args.append(arg_text[current_start:i].strip())
            current_start = i + 1
    tail = arg_text[current_start:].strip()
    if tail:
        args.append(tail)
    return args


def extract_call_args(text, call_start):
    """Given an index at the ``(`` of a call, return (args_text, index_past_close)."""
    if call_start >= len(text) or text[call_start] != "(":
        return None, call_start
    # Mask only from the call forward: masking the whole file on every call
    # was most of the generator's run time. Offsets are relative to call_start.
    for window in (8000, len(text) - call_start):
        masked = strip_comments_and_strings(text[call_start:call_start + window])
        depth = 0
        for i, ch in enumerate(masked):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return text[call_start + 1:call_start + i], call_start + i + 1
        if call_start + window >= len(text):
            break
    return None, call_start


# --------------------------------------------------------------------------
# Java string-literal evaluation
# --------------------------------------------------------------------------

_JAVA_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f",
    '"': '"', "'": "'", "\\": "\\", "0": "\0",
}

STRING_LITERAL_RE = re.compile(r'"((?:[^"\\]|\\.)*)"', re.DOTALL)


def unescape_java(raw):
    out = []
    i = 0
    while i < len(raw):
        if raw[i] == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt == "u":
                try:
                    out.append(chr(int(raw[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            out.append(_JAVA_ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return "".join(out)


IDENT_PATH_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*)*")


CONFIG_KEY_CALL_RE = re.compile(
    r"([A-Za-z_$][A-Za-z0-9_$]*(?:\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*)*)\s*\.\s*key\s*\(\s*\)")


def concatenated_string_literal(expr, string_constants=None, owner_class=None, _depth=0,
                                key_resolver=None):
    """Evaluate a Java expression that is a concatenation of string literals.

    With ``string_constants`` supplied, identifiers that name a ``static final
    String`` constant are substituted too, which is how the many
    ``SOME_PREFIX + "suffix"`` config keys get resolved. Returns None when the
    expression contains anything else, so that callers can distinguish "a
    literal we read exactly" from "something computed".

    ``key_resolver`` additionally substitutes ``OTHER_CONFIG.key()``. Several
    configs name another config inside their own documentation ("Required when
    `" + QUERY_TYPE.key() + "` is set to ..."), and without this the whole
    documentation string is discarded as computed.
    """
    expr = expr.strip()
    if not expr or _depth > 8:
        return None
    pieces = []
    pos = 0
    saw_literal = False
    while pos < len(expr):
        if key_resolver is not None:
            key_call = CONFIG_KEY_CALL_RE.match(expr, pos)
            if key_call:
                resolved_key = key_resolver(key_call.group(1).replace(" ", ""))
                if resolved_key is not None:
                    pieces.append(resolved_key)
                    saw_literal = True
                    pos = key_call.end()
                    continue
                return None
        match = STRING_LITERAL_RE.match(expr, pos)
        if match:
            pieces.append(unescape_java(match.group(1)))
            saw_literal = True
            pos = match.end()
            continue
        ch = expr[pos]
        if ch.isspace() or ch == "+":
            pos += 1
            continue
        if string_constants is not None:
            ident = IDENT_PATH_RE.match(expr, pos)
            if ident:
                resolved = lookup_string_constant(
                    ident.group(0), string_constants, owner_class, _depth)
                if resolved is not None:
                    pieces.append(resolved)
                    saw_literal = True
                    pos = ident.end()
                    continue
        return None
    return "".join(pieces) if saw_literal else None


def lookup_string_constant(path, string_constants, owner_class, depth):
    """Resolve ``PREFIX`` / ``Holder.PREFIX`` to its literal value, recursively."""
    parts = [p.strip() for p in path.split(".")]
    const = parts[-1]
    qualifier = parts[-2] if len(parts) >= 2 else None
    for candidate in ((qualifier, const), (owner_class, const), (None, const)):
        expression = string_constants.get(candidate)
        if expression is None:
            continue
        resolved = concatenated_string_literal(
            expression, string_constants, candidate[0] or owner_class, depth + 1)
        if resolved is not None:
            return resolved
    return None


ENUM_DESCRIPTION_RE = re.compile(r"@EnumDescription\s*\(")
ENUM_FIELD_DESCRIPTION_RE = re.compile(r"@EnumFieldDescription\s*\(")
ENUM_DECL_RE = re.compile(r"\benum\s+([A-Za-z_$][A-Za-z0-9_$]*)")
# The last constant in an enum body is followed by `}` rather than `,` or `;`.
ENUM_CONSTANT_RE = re.compile(r"\A\s*([A-Z][A-Z0-9_]*)\s*[,;(){}]")


def collect_enum_documentation(repo_root):
    """Pass 0b. Enum name -> its ``@EnumDescription`` and per-constant descriptions.

    ``withDocumentation(SomeEnum.class)`` means the user-facing text for that
    config lives on the enum, not at the declaration. Without this the catalog
    would report "no documentation" for exactly the configs whose valid values
    matter most.
    """
    documented = {}
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "@EnumDescription" not in original:
            continue
        masked = strip_comments_and_strings(original, keep_string_bodies=True)
        for match in ENUM_DESCRIPTION_RE.finditer(masked):
            args, after = extract_call_args(masked, match.end() - 1)
            if args is None:
                continue
            enum_match = ENUM_DECL_RE.search(masked, after)
            if not enum_match:
                continue
            name = enum_match.group(1)
            body_start = masked.find("{", enum_match.end())
            if body_start < 0:
                continue
            depth = 0
            body_end = len(masked)
            for i in range(body_start, len(masked)):
                if masked[i] == "{":
                    depth += 1
                elif masked[i] == "}":
                    depth -= 1
                    if depth == 0:
                        body_end = i
                        break
            values = []
            for field in ENUM_FIELD_DESCRIPTION_RE.finditer(masked, body_start, body_end):
                field_args, field_after = extract_call_args(masked, field.end() - 1)
                if field_args is None:
                    continue
                tail = masked[field_after:field_after + 160]
                constant = ENUM_CONSTANT_RE.match(tail)
                if not constant:
                    continue
                values.append(OrderedDict([
                    ("value", constant.group(1)),
                    ("description", concatenated_string_literal(field_args) or ""),
                ]))
            documented[name] = OrderedDict([
                ("enum", name),
                ("file", os.path.relpath(file_path, repo_root)),
                ("description", concatenated_string_literal(args) or ""),
                ("values", values),
            ])
    return documented


STRING_CONSTANT_RE = re.compile(
    r"\bstatic\s+final\s+String\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?P<value>[^;]*);")

# `val QUERY_TYPE_SNAPSHOT_OPT_VAL = "snapshot"`, with the type ascription
# optional. Scala values spelled across several lines are left alone: the value
# stops at the newline, and an unresolved name is reported rather than guessed.
SCALA_STRING_CONSTANT_RE = re.compile(
    r"\b(?:lazy\s+)?val\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*"
    r"(?::\s*String\s*)?=\s*(?P<value>[^\n]*?)\s*(?:\n|$)")


def collect_string_constants(repo_root):
    """Pass 0. (class, constant) -> its initializer expression, for key prefixes.

    Keyed both by owning class and by bare name. A bare name claimed by two
    different expressions is dropped, so an ambiguous prefix never silently
    resolves to the wrong value.
    """
    by_qualified = {}
    bare = {}
    bare_conflicts = set()
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "static final String" not in original:
            continue
        masked = strip_comments_and_strings(original, keep_string_bodies=True)
        for match in STRING_CONSTANT_RE.finditer(masked):
            name = match.group("name")
            value = match.group("value").strip()
            if not value or len(value) > 400:
                continue
            owner = find_enclosing_class(masked, match.start())
            by_qualified[(owner, name)] = value
            if name in bare and bare[name] != value:
                bare_conflicts.add(name)
            bare[name] = value

    # Scala `val` string constants. Spark's datasource configs take their
    # defaults and valid values from these, so without them a Spark user is told
    # the default of hoodie.datasource.query.type is the literal text
    # "QUERY_TYPE_SNAPSHOT_OPT_VAL" rather than "snapshot".
    for file_path in walk_source_files(repo_root, (".scala",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "val " not in original:
            continue
        masked = strip_comments_and_strings(original, keep_string_bodies=True, scala=True)
        for match in SCALA_STRING_CONSTANT_RE.finditer(masked):
            name = match.group("name")
            value = match.group("value").strip()
            # Only plain string expressions; a chain or a call is not a constant.
            if not value or len(value) > 400 or '"' not in value:
                continue
            if value.endswith(("+", "(", "{", ",", "=")):
                continue
            owner = find_enclosing_scala_object(masked, match.start())
            by_qualified[(owner, name)] = value
            if name in bare and bare[name] != value:
                bare_conflicts.add(name)
            bare[name] = value

    for name in bare_conflicts:
        bare.pop(name, None)
    constants = {(None, name): value for name, value in bare.items()}
    constants.update(by_qualified)
    return constants


ENUM_CONSTANT_CALL_RE = re.compile(
    r"\A(?:[A-Za-z_$][A-Za-z0-9_$]*\s*\.\s*)*?([A-Z][A-Z0-9_]*)\s*\.\s*"
    r"(?:name|toString)\s*\(\s*\)\Z")


def enum_constant_name(expr):
    """`IndexType.SIMPLE.name()` -> `SIMPLE`, else None.

    The value such an expression produces is the constant's own name, so this
    is a resolution rather than a guess. Valid-value lists are written this way
    throughout, and leaving them unresolved would answer "what can I set this
    to?" with `SIMPLE.name()`.
    """
    match = ENUM_CONSTANT_CALL_RE.match(" ".join(expr.split()))
    return match.group(1) if match else None


def literal_or_expression(expr, string_constants=None, owner_class=None):
    """Return (value, is_literal) for a default-value expression.

    With ``string_constants``, a default written as a named constant resolves to
    the string it holds. That is the difference between telling a user the
    default is "snapshot" and telling them it is QUERY_TYPE_SNAPSHOT_OPT_VAL.
    """
    literal = concatenated_string_literal(expr)
    if literal is not None:
        return literal, True
    if string_constants is not None:
        resolved = concatenated_string_literal(expr, string_constants, owner_class)
        if resolved is not None:
            return resolved, True
    enum_member = enum_constant_name(expr)
    if enum_member is not None:
        return enum_member, True
    collapsed = " ".join(expr.split())
    if re.fullmatch(r"(true|false)", collapsed):
        return collapsed, True
    if re.fullmatch(r"-?\d+[LlFfDd]?", collapsed):
        return collapsed.rstrip("LlFfDd"), True
    if re.fullmatch(r"-?\d*\.\d+[FfDd]?", collapsed):
        return collapsed.rstrip("FfDd"), True
    return collapsed, False


# --------------------------------------------------------------------------
# Pass 1 -- config declarations
# --------------------------------------------------------------------------

# Matches both `ConfigProperty<String> FOO = ConfigProperty` and the Flink
# `ConfigOption<String> FOO = ConfigOptions` forms, plus the rarer single-line
# `= ConfigProperty.key(...)`.
DECLARATION_RE = re.compile(
    r"(?P<decl>(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?"
    r"(?P<holder>ConfigProperty|ConfigOption)\s*<\s*(?P<type>[^>]*(?:<[^>]*>)?[^>]*)\s*>\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*)"
    r"(?P<builder>ConfigProperty|ConfigOptions)\b"
)

# `public static final ConfigProperty<String> EXPRESSION_INDEX_TYPE =
#  HoodieIndexingConfig.INDEX_TYPE;` -- a re-export that is a plain reference,
# not a builder chain, so DECLARATION_RE never sees it. Without this the
# re-exporting class's own getter (getExpressionIndexType) cannot be resolved.
DIRECT_ALIAS_RE = re.compile(
    r"(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?"
    r"(?:ConfigProperty|ConfigOption)\s*<[^>]*>\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
    r"(?P<target>[A-Za-z_$][A-Za-z0-9_$]*\.[A-Za-z_$][A-Za-z0-9_$]*)\s*;"
)


CLASS_DECL_RE = re.compile(
    r"\b(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?"
    r"(?:class|interface|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
)

# Scala: `val QUERY_TYPE: ConfigProperty[String] = ConfigProperty`. The type
# ascription is optional, and `lazy val`/`var`/`private` may precede it.
SCALA_DECLARATION_RE = re.compile(
    r"(?P<decl>\b(?:private|protected)?\s*(?:\[[A-Za-z0-9_$]*\]\s*)?(?:lazy\s+)?(?:val|var)\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*"
    r"(?::\s*(?P<holder>ConfigProperty|ConfigOption)\s*\[\s*(?P<type>[^\]]*(?:\[[^\]]*\])?[^\]]*)\s*\]\s*)?"
    r"=\s*)"
    r"(?P<builder>ConfigProperty|ConfigOptions)\s*\n?\s*\.\s*key\s*\("
)

# Scala objects, classes and traits all hold configs.
SCALA_CLASS_DECL_RE = re.compile(
    r"\b(?:case\s+)?(?:object|class|trait)\s+([A-Za-z_$][A-Za-z0-9_$]*)")

# `val REALTIME_MERGE: ConfigProperty[String] = HoodieReaderConfig.MERGE_TYPE`
# re-exports a Java-declared config under a Scala name. It declares no new key,
# but a read site naming the Scala constant must still resolve to the real key.
SCALA_ALIAS_RE = re.compile(
    r"\b(?:private|protected)?\s*(?:lazy\s+)?(?:val|var)\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*"
    r":\s*(?:ConfigProperty|ConfigOption)\s*\[[^\]]*\]\s*=\s*"
    r"(?P<target>[A-Za-z_$][A-Za-z0-9_$]*(?:\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*)+)\s*(?:\n|$)")


def find_enclosing_scala_object(text, index):
    """Innermost-looking object/class/trait name declared before ``index``."""
    best = None
    for match in SCALA_CLASS_DECL_RE.finditer(text, 0, index):
        best = match.group(1)
    return best

# Builder steps we care about, applied to the chain text after the key.
CHAIN_STEP_RE = re.compile(r"\.\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")


def find_enclosing_class(text, index):
    """Innermost-looking class name declared before ``index``."""
    best = None
    for match in CLASS_DECL_RE.finditer(text, 0, index):
        best = match.group(1)
    return best


def parse_chain_steps(chain_text, scala=False):
    """Return an ordered list of (method_name, args_text) from a builder chain.

    Comments are blanked first -- authors do put explanatory comments between a
    builder call's arguments, and those must not end up inside an extracted
    value. String bodies are kept so literals survive.
    """
    chain_text = strip_comments_and_strings(
        chain_text, keep_string_bodies=True, scala=scala)
    steps = []
    pos = 0
    while True:
        match = CHAIN_STEP_RE.search(chain_text, pos)
        if not match:
            break
        args, after = extract_call_args(chain_text, match.end() - 1)
        if args is None:
            pos = match.end()
            continue
        steps.append((match.group(1), args))
        pos = after
    return steps


DERIVED_KEY_RE = re.compile(
    r"([A-Za-z_$][A-Za-z0-9_$.]*)\s*\.\s*key\(\s*\)\s*(?:\+\s*(.+))?")


def derived_from_config_key(expr, string_constants, owner_class, base_key_resolver):
    """Resolve `OTHER_CONFIG.key()` and `OTHER_CONFIG.key() + ".suffix"`.

    Several configs name their own key, and several name an alternative key,
    relative to another config's. Returns None when the base config is unknown.
    """
    match = DERIVED_KEY_RE.fullmatch(" ".join(expr.split()))
    if not match:
        return None
    base = base_key_resolver(match.group(1))
    if base is None:
        return None
    if match.group(2) is None:
        return base
    suffix = concatenated_string_literal(match.group(2), string_constants, owner_class)
    return None if suffix is None else base + suffix


def parse_declaration(masked_for_scan, original, match, file_path, repo_root,
                      string_constants, base_key_resolver=lambda path: None,
                      enum_docs=None, scala=False):
    """Build one catalog entry from a declaration match. Never raises."""
    warnings = []
    start = match.start()
    end = (find_scala_statement_end(original, start) if scala
           else find_statement_end(original, start))
    if end < 0:
        end = min(len(original), start + 4000)
        warnings.append("statement terminator not found; chain truncated at 4000 chars")
    chain_text = original[start:end]

    steps = parse_chain_steps(chain_text, scala=scala)
    step_names = [name for name, _ in steps]

    enclosing_class = (find_enclosing_scala_object(masked_for_scan, start) if scala
                       else find_enclosing_class(masked_for_scan, start))

    key = None
    key_expr = None
    key_resolution = None
    for name, args in steps:
        if name == "key":
            key_expr = args.strip()
            key = concatenated_string_literal(args)
            if key is not None:
                key_resolution = "literal"
            else:
                key = concatenated_string_literal(
                    args, string_constants, enclosing_class)
                if key is not None:
                    key_resolution = "resolvedFromConstants"
            break

    if key is None and key_expr:
        # Flink re-exports read the key off another ConfigProperty, and some
        # Java configs build the key from a shared prefix constant.
        reference = re.fullmatch(
            r"([A-Za-z_$][A-Za-z0-9_$.]*)\s*\.\s*key\(\s*\)", key_expr.strip())
        if reference:
            return None, "alias:" + reference.group(1)
        # `OTHER_CONFIG.key() + ".suffix"` -- a key derived from another config's.
        key = derived_from_config_key(
            key_expr, string_constants, enclosing_class, base_key_resolver)
        if key is not None:
            key_resolution = "derivedFromConfigKey"
        else:
            warnings.append(
                "key is a computed expression: " + " ".join(key_expr.split())[:160])

    entry = OrderedDict()
    entry["key"] = key
    entry["keyResolution"] = key_resolution
    entry["keyExpression"] = (" ".join(key_expr.split())
                              if key_expr and key_resolution != "literal" else None)
    # Scala makes the type ascription optional, so there may be no type to read.
    declared_type = match.groupdict().get("type")
    entry["type"] = " ".join(declared_type.split()) if declared_type else None
    entry["language"] = "scala" if scala else "java"
    entry["declaredIn"] = OrderedDict([
        ("class", enclosing_class),
        ("constant", match.group("name")),
        ("file", os.path.relpath(file_path, repo_root)),
        ("line", line_of(original, start)),
    ])
    entry["configGroup"] = entry["declaredIn"]["class"]
    entry["builderStyle"] = "ConfigProperty" if match.group("builder") == "ConfigProperty" else "FlinkConfigOptions"

    # Default value.
    default_value = None
    default_is_literal = False
    has_default = None
    for name, args in steps:
        if name == "defaultValue":
            parts = split_top_level_args(args)
            if parts:
                default_value, default_is_literal = literal_or_expression(
                    parts[0], string_constants, enclosing_class)
                has_default = True
                if len(parts) > 1:
                    doc_on_default = concatenated_string_literal(parts[1])
                    if doc_on_default:
                        entry["docOnDefaultValue"] = doc_on_default
            break
        if name == "noDefaultValue":
            has_default = False
            break
    if has_default is None:
        has_default = False
        if entry["builderStyle"] == "ConfigProperty":
            warnings.append("neither defaultValue() nor noDefaultValue() found in chain")
    entry["hasDefaultValue"] = has_default
    entry["defaultValue"] = default_value
    entry["defaultValueIsLiteral"] = default_is_literal
    if has_default and not default_is_literal:
        entry["defaultValueNote"] = "computed at class-init time; shown as the source expression"

    # Documentation: a string, or a class reference whose text lives elsewhere.
    documentation = None
    documentation_source = None
    enum_documentation = None
    for name, args in steps:
        if name not in ("withDocumentation", "withDescription"):
            continue
        parts = split_top_level_args(args)
        if not parts:
            continue
        class_ref = re.fullmatch(r"([A-Za-z_$][A-Za-z0-9_$.]*)\s*\.\s*class", parts[0].strip())
        if class_ref:
            enum_name = class_ref.group(1).split(".")[-1]
            documentation_source = "enumClass:" + enum_name
            extra = concatenated_string_literal(parts[1]) if len(parts) > 1 else None
            described = (enum_docs or {}).get(enum_name)
            if described:
                entry_enum = described
                pieces = [p for p in (extra, described["description"]) if p]
                documentation = "\n".join(pieces)
                enum_documentation = entry_enum
            else:
                documentation = extra
                warnings.append(
                    "documentation points at enum %s, whose @EnumDescription was not found"
                    % enum_name)
        else:
            documentation = concatenated_string_literal(parts[0])
            documentation_source = "literal"
            if documentation is None:
                documentation = concatenated_string_literal(
                    parts[0], string_constants, enclosing_class)
                documentation_source = "resolvedFromConstants"
            if documentation is None:
                # Documentation that cites another config by `OTHER.key()`.
                documentation = concatenated_string_literal(
                    parts[0], string_constants, enclosing_class,
                    key_resolver=base_key_resolver)
                documentation_source = "resolvedFromConfigKeys"
            if documentation is None:
                documentation_source = None
                warnings.append("documentation is a computed expression")
        break
    entry["documentation"] = documentation
    entry["documentationSource"] = documentation_source
    entry["enumDocumentation"] = enum_documentation

    def collect_string_args(step_name):
        for name, args in steps:
            if name == step_name:
                values = []
                for part in split_top_level_args(args):
                    literal = concatenated_string_literal(part)
                    if literal is None:
                        literal = concatenated_string_literal(
                            part, string_constants, enclosing_class)
                    if literal is None:
                        literal = derived_from_config_key(
                            part, string_constants, enclosing_class, base_key_resolver)
                    if literal is None:
                        literal = enum_constant_name(part)
                    values.append(literal if literal is not None
                                  else " ".join(part.split()))
                return values
        return []

    entry["validValues"] = collect_string_args("withValidValues")
    # A config whose documentation is an enum class declares its permitted values on the enum
    # rather than via withValidValues(...). Fall back to the enum's constants so that
    # "what can I set this to?" is answerable for strategy/policy configs, which are exactly
    # the ones where it matters most.
    if not entry["validValues"] and enum_documentation:
        entry["validValues"] = [v["value"] for v in enum_documentation.get("values", []) if v.get("value")]
    entry["alternatives"] = collect_string_args("withAlternatives")
    since = collect_string_args("sinceVersion")
    entry["sinceVersion"] = since[0] if since else None
    deprecated = collect_string_args("deprecatedAfter")
    entry["deprecatedAfter"] = deprecated[0] if deprecated else None
    entry["supportedVersions"] = collect_string_args("supportedVersions")
    entry["advanced"] = "markAdvanced" in step_names
    entry["hasInferFunction"] = "withInferFunction" in step_names
    entry["builderSteps"] = step_names

    if key is None:
        warnings.append("key could not be resolved to a string literal")
    if documentation is None and documentation_source != "enumClass":
        warnings.append("no documentation text resolved")

    entry["parseWarnings"] = warnings
    return entry, None


def collect_declarations(repo_root, verbose=False):
    """Pass 1. Returns (entries, constant_index, stats)."""
    entries = []
    # (file-local class, constant name) -> config key, so later passes can map a
    # constant reference back to the config it names.
    constant_index = {}
    alias_pending = []
    alias_pending_scala = []
    stats = defaultdict(int)

    string_constants = collect_string_constants(repo_root)
    stats["stringConstants"] = len(string_constants)
    enum_docs = collect_enum_documentation(repo_root)
    stats["documentedEnums"] = len(enum_docs)
    if verbose:
        print("  string constants indexed: %d" % len(string_constants), file=sys.stderr)
        print("  documented enums indexed: %d" % len(enum_docs), file=sys.stderr)

    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            stats["unreadableFiles"] += 1
            continue
        if "ConfigProperty" not in original and "ConfigOptions" not in original:
            continue

        masked = strip_comments_and_strings(original)

        def resolve_base_key(path, _index=constant_index):
            parts = path.split(".")
            const = parts[-1]
            qualifier = parts[-2] if len(parts) >= 2 else None
            return _index.get((qualifier, const)) or _index.get((None, const))

        for match in DECLARATION_RE.finditer(masked):
            stats["declarationsSeen"] += 1
            entry, alias_target = parse_declaration(
                masked, original, match, file_path, repo_root, string_constants,
                resolve_base_key, enum_docs)
            if alias_target is not None:
                alias_pending.append((
                    find_enclosing_class(masked, match.start()),
                    match.group("name"),
                    alias_target.split(":", 1)[1],
                    os.path.relpath(file_path, repo_root),
                    line_of(original, match.start()),
                ))
                continue
            if entry is None:
                stats["unparseable"] += 1
                continue
            # Flink ConfigOptions that do not name a hoodie.* key belong to the
            # Flink option namespace, not the Hudi config namespace.
            if entry["builderStyle"] == "FlinkConfigOptions" and not (
                    entry["key"] or "").startswith("hoodie."):
                stats["flinkOptionsSkipped"] += 1
                continue
            entries.append(entry)
            owner = entry["declaredIn"]["class"]
            if entry["key"]:
                constant_index[(owner, entry["declaredIn"]["constant"])] = entry["key"]
                constant_index[(None, entry["declaredIn"]["constant"])] = entry["key"]

    # Scala declarations come second so that a Scala config deriving its key
    # from a Java config's (`OTHER.key() + ".suffix"`) finds it already indexed.
    for file_path in walk_source_files(repo_root, (".scala",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            stats["unreadableFiles"] += 1
            continue
        if "ConfigProperty" not in original and "ConfigOptions" not in original:
            continue

        masked = strip_comments_and_strings(original, scala=True)

        def resolve_base_key(path, _index=constant_index):
            parts = path.split(".")
            const = parts[-1]
            qualifier = parts[-2] if len(parts) >= 2 else None
            return _index.get((qualifier, const)) or _index.get((None, const))

        for match in SCALA_DECLARATION_RE.finditer(masked):
            stats["scalaDeclarationsSeen"] += 1
            stats["declarationsSeen"] += 1
            entry, alias_target = parse_declaration(
                masked, original, match, file_path, repo_root, string_constants,
                resolve_base_key, enum_docs, scala=True)
            if entry is None:
                stats["unparseable"] += 1
                continue
            # A Scala config whose key resolves outside the hoodie namespace is
            # not a Hudi table config: `ConfigProperty.key(prop.key())` inside a
            # generic type-converting wrapper declares no key of its own.
            if not (entry["key"] or "").startswith("hoodie."):
                stats["scalaNonHoodieSkipped"] += 1
                continue
            entries.append(entry)
            owner = entry["declaredIn"]["class"]
            constant_index[(owner, entry["declaredIn"]["constant"])] = entry["key"]
            constant_index[(None, entry["declaredIn"]["constant"])] = entry["key"]
            stats["scalaDeclarationsParsed"] += 1

        # Scala re-exports of Java configs: index the Scala name against the
        # Java key so read sites naming the Scala constant still attribute.
        for match in SCALA_ALIAS_RE.finditer(masked):
            target = match.group("target")
            target_parts = [p.strip() for p in target.split(".")]
            key = (constant_index.get((target_parts[-2] if len(target_parts) >= 2 else None,
                                       target_parts[-1]))
                   or constant_index.get((None, target_parts[-1])))
            if not key:
                stats["scalaAliasesUnresolved"] += 1
                continue
            owner = find_enclosing_scala_object(masked, match.start())
            constant_index[(owner, match.group("name"))] = key
            alias_pending_scala.append(OrderedDict([
                ("key", key), ("aliasClass", owner), ("aliasConstant", match.group("name")),
                ("file", os.path.relpath(file_path, repo_root)),
                ("line", line_of(original, match.start()))]))
            stats["scalaAliasesResolved"] += 1

    # Direct re-exports (`FOO = OtherHolder.FOO`), which are a plain reference
    # rather than a builder chain and so are invisible to DECLARATION_RE.
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "ConfigProperty" not in original and "ConfigOption" not in original:
            continue
        masked = strip_comments_and_strings(original)
        class_match = CLASS_DECL_RE.search(masked)
        owner = class_match.group(1) if class_match else None
        if owner is None:
            continue
        rel = os.path.relpath(file_path, repo_root)
        for m in DIRECT_ALIAS_RE.finditer(masked):
            alias_pending.append((
                owner, m.group("name"), m.group("target"), rel,
                masked[:m.start()].count("\n") + 1))

    # Resolve re-export aliases (`FOO = OtherHolder.FOO`) to the real key so a
    # read site that uses the alias still lands on the right config.
    aliases = []
    for owner, name, target, rel_file, line in alias_pending:
        target_parts = target.split(".")
        target_const = target_parts[-1]
        target_class = target_parts[-2] if len(target_parts) >= 2 else None
        key = constant_index.get((target_class, target_const)) or \
            constant_index.get((None, target_const))
        if key:
            constant_index[(owner, name)] = key
            aliases.append(OrderedDict([
                ("key", key), ("aliasClass", owner), ("aliasConstant", name),
                ("file", rel_file), ("line", line)]))
            stats["aliasesResolved"] += 1
        else:
            stats["aliasesUnresolved"] += 1

    aliases.extend(alias_pending_scala)

    return entries, constant_index, aliases, stats


# --------------------------------------------------------------------------
# Pass 2 -- accessor methods
# --------------------------------------------------------------------------

# Methods and constructors, including package-private ones. The modifier is
# optional, so NON_METHOD_KEYWORDS below keeps `if (...) {` and friends out.
METHOD_SIGNATURE_RE = re.compile(
    r"(?:(?:public|protected|private)\s+)?(?:static\s+|final\s+|synchronized\s+|abstract\s+)*"
    r"(?:(?P<ret>[A-Za-z_$][A-Za-z0-9_$<>,.\[\]\s?]*?)\s+)?"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*\((?P<params>[^;{()]*(?:\([^()]*\)[^;{()]*)*)\)\s*"
    r"(?:throws\s+[A-Za-z0-9_$.,\s]+)?\{"
)

NON_METHOD_KEYWORDS = frozenset((
    "if", "else", "for", "while", "switch", "catch", "try", "do", "synchronized",
    "return", "new", "case", "assert", "super", "this",
))

GETTER_CALL_RE = re.compile(
    r"\bget(?:String|Int|Integer|Long|Boolean|Double|Float|StringOrDefault|"
    r"IntOrDefault|BooleanOrDefault|LongOrDefault|Enum|Class)?\s*\(\s*"
    r"(?P<arg>[A-Za-z_$][A-Za-z0-9_$.]*?)(?:\.key\(\))?\s*[,)]"
)

ALT_KEYS_CALL_RE = re.compile(
    r"\b(?:get|contains)(?:String|Int|Integer|Long|Boolean|Double|Raw)?WithAltKeys\s*\([^)]*?"
    r"\b(?P<arg>[A-Za-z_$][A-Za-z0-9_$.]*?)(?:\.key\(\))?\s*[,)]"
)


def find_method_bodies(masked, original):
    """Yield (name, body_start, body_end, signature_line) for each method.

    ``body_start`` indexes the ``{``; ``body_end`` the matching ``}``.
    """
    for match in METHOD_SIGNATURE_RE.finditer(masked):
        if match.group("name") in NON_METHOD_KEYWORDS:
            continue
        if (match.group("ret") or "").split()[-1:] and \
                (match.group("ret") or "").split()[-1] in NON_METHOD_KEYWORDS:
            continue
        brace_index = masked.find("{", match.end() - 1)
        if brace_index < 0:
            continue
        depth = 0
        end = -1
        for i in range(brace_index, len(masked)):
            if masked[i] == "{":
                depth += 1
            elif masked[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end < 0:
            continue
        yield match.group("name"), brace_index, end, line_of(original, match.start())


STATIC_IMPORT_RE = re.compile(
    r"^\s*import\s+static\s+[\w.]*?\.(?P<cls>[A-Z][\w$]*)\.(?P<member>[A-Z][A-Z0-9_]*|\*)\s*;", re.M)


def static_imports(original):
    """``import static ...HoodieCommonConfig.BASE_PATH;`` -> {"BASE_PATH": "HoodieCommonConfig"}.

    Wildcard imports are returned under "*" as a list of classes.
    """
    result = {"*": []}
    for match in STATIC_IMPORT_RE.finditer(original):
        if match.group("member") == "*":
            result["*"].append(match.group("cls"))
        else:
            result[match.group("member")] = match.group("cls")
    return result


_BARE_COUNTS = {}


def _bare_is_ambiguous(const, constant_index):
    counts = _BARE_COUNTS.get(id(constant_index))
    if counts is None or counts[0] != len(constant_index):
        tally = defaultdict(set)
        for (qualifier, name), key in constant_index.items():
            if qualifier is not None:
                tally[name].add(key)
        counts = (len(constant_index), tally)
        _BARE_COUNTS[id(constant_index)] = counts
    return len(counts[1].get(const, ())) > 1


def resolve_constant(expr, owner_class, constant_index, imports=None):
    """Map a (possibly qualified) constant reference to a config key.

    ``imports`` (from :func:`static_imports`) qualifies a bare name the file
    imports statically. Without it, a bare name declared by several classes is
    refused rather than resolved to whichever class registered it last:
    HoodieTimeGeneratorConfig's statically imported BASE_PATH is
    hoodie.base.path, not hoodie.bootstrap.base.path.
    """
    # `props.getBoolean(ERROR_TABLE_ENABLED.key(), ...)` -- a very common shape,
    # especially in hudi-utilities where configs are read straight off a
    # TypedProperties rather than through a HoodieWriteConfig getter. Without
    # this the trailing member swallows the constant name and the read site is
    # lost, which made a dozen configs look like they had no consumer at all.
    if expr.endswith(".key"):
        expr = expr[:-len(".key")]
    parts = expr.split(".")
    const = parts[-1]
    qualifier = parts[-2] if len(parts) >= 2 else None
    # Order matters. A bare `INDEX_TYPE` has no qualifier, and the (None, const)
    # bucket holds whichever class won the race -- INDEX_TYPE is declared both in
    # HoodieIndexConfig (hoodie.index.type) and HoodieIndexingConfig
    # (hoodie.expression.index.type). The file we are reading is the better
    # evidence, so try the owning class before the ambiguous bare name.
    if qualifier is not None:
        resolved = constant_index.get((qualifier, const))
        if resolved:
            return resolved
    else:
        resolved = constant_index.get((owner_class, const))
        if resolved:
            return resolved
        if imports:
            if const in imports:
                resolved = constant_index.get((imports[const], const))
                if resolved:
                    return resolved
            for cls in imports.get("*", ()):
                resolved = constant_index.get((cls, const))
                if resolved:
                    return resolved
        if imports is not None and _bare_is_ambiguous(const, constant_index):
            return None
    return constant_index.get((None, const))


# Method names too common to attribute a config to. HoodieIndexConfig.Builder
# has a build() that mentions exactly one config constant, which made every
# .build() call in the tree -- AvroParquetReader.builder().build(), HoodiePath
# .newBuilder().build(), every writer constructor -- resolve to that config.
# A name like this cannot identify a consumer at a call site, whatever its body
# looks like.
ACCESSOR_CALL_IN_GATE_RE = re.compile(r"\b([a-z][A-Za-z0-9_]*)\s*\(")
# Scala calls a no-arg accessor without parentheses: `getConfig.inlineClusteringEnabled`.
ACCESSOR_REF_IN_GATE_RE = re.compile(r"\b([a-z][A-Za-z0-9_]*)\b(?!\s*=)")


GENERIC_METHOD_NAMES = frozenset((
    "build", "builder", "newBuilder", "get", "getInstance", "newInstance",
    "create", "of", "from", "apply", "value", "valueOf", "parse", "toString",
))


# Hudi names a getter after the config it reads: hoodie.table.service.manager.enabled
# -> isTableServiceManagerEnabled, hoodie.archive.beyond.savepoint ->
# shouldArchiveBeyondSavepoint. Booleans take is/should/do/can/has, values take
# get, and some take no prefix at all. That convention is strong enough to use
# as a cross-check on a constant that resolved by bare name: INDEX_TYPE is
# declared in both HoodieIndexConfig (hoodie.index.type) and
# HoodieIndexingConfig (hoodie.expression.index.type), and without the name
# check HoodieIndexingConfig.getIndexType is filed under the wrong key.
ACCESSOR_PREFIXES = ("get", "is", "should", "do", "does", "use", "can", "has")


def accessor_name_matches_key(method_name, key):
    """True when a getter's name is the camelCase of the config key."""
    parts = [p for p in key.split(".") if p]
    if parts and parts[0] in ("hoodie", "_hoodie", "_"):
        parts = parts[1:]
    if not parts:
        return False
    core = method_name
    lowered = method_name.lower()
    for prefix in ACCESSOR_PREFIXES:
        if lowered.startswith(prefix) and len(method_name) > len(prefix):
            core = method_name[len(prefix):]
            break
    core = core.lower()
    # the full key, and every suffix of it, in camelCase
    for start in range(len(parts)):
        tail = parts[start:]
        candidate = (tail[0] + "".join(w[:1].upper() + w[1:] for w in tail[1:])).lower()
        if core == candidate:
            return True
    return False


PRIMARY_ACCESSOR_CLASS = "HoodieWriteConfig"
# accessor name -> {declaring class: key}, for names declared by several classes.
AMBIGUOUS_ACCESSORS = {}


def accessor_key_for_receiver(name, preceding, default):
    """Pick among same-named accessors by the receiver written before the call.

    `metaClient.getTableConfig().getTableType()` and `tableConfig.getTableType()`
    name HoodieTableConfig; `getMetadataConfig().getBloomFilterType()` names
    HoodieMetadataConfig. Anything else keeps the HoodieWriteConfig default.
    """
    options = AMBIGUOUS_ACCESSORS.get(name)
    if not options:
        return default
    receiver = re.split(r"[\s;,(=!&|{}]", preceding.rstrip(". \n\t"))[-1].lower()
    for cls, key in options.items():
        if not cls or cls == PRIMARY_ACCESSOR_CLASS:
            continue
        hint = cls[len("Hoodie"):] if cls.startswith("Hoodie") else cls
        if hint.lower() in receiver:
            return key
    return default


def collect_accessors(repo_root, constant_index):
    """Pass 2. accessor method name -> set of config keys it reads.

    Deliberately narrow: only methods whose body is short and mentions exactly
    one config constant, so that a call site of the method is unambiguous.
    """
    accessors = defaultdict(set)
    by_class = defaultdict(dict)
    accessor_sites = {}
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "get" not in original or "Config" not in original:
            continue
        masked = strip_comments_and_strings(original)
        owner_class = None
        class_match = CLASS_DECL_RE.search(masked)
        if class_match:
            owner_class = class_match.group(1)

        file_imports = static_imports(original)
        for name, body_start, body_end, sig_line in find_method_bodies(masked, original):
            body = masked[body_start:body_end]
            if len(body) > 600:
                continue
            keys = set()
            for pattern in (GETTER_CALL_RE, ALT_KEYS_CALL_RE):
                for call in pattern.finditer(body):
                    key = resolve_constant(call.group("arg"), owner_class, constant_index, file_imports)
                    if key:
                        keys.add(key)
            if len(keys) == 1 and name not in GENERIC_METHOD_NAMES:
                only = next(iter(keys))
                # If the method name follows the naming convention but names a
                # *different* config than the body resolved to, the body's bare
                # name hit the wrong class's constant. Trust the name.
                better = None
                if not accessor_name_matches_key(name, only):
                    for candidate_key in sorted(set(constant_index.values())):
                        if accessor_name_matches_key(name, candidate_key):
                            if better is not None:
                                better = None
                                break
                            better = candidate_key
                accessors[name].add(better or only)
                by_class[name][owner_class] = better or only
                accessor_sites.setdefault(name, (owner_class, os.path.relpath(file_path, repo_root), sig_line))
    # An accessor name that maps to more than one key across classes is
    # ambiguous at a call site. Dropping it lost getWriteConcurrencyMode,
    # getIndexType, getTableType and getRecordMergeMode -- HoodieMetadataConfig
    # or HoodieTableConfig defines a same-named method for its own key -- and
    # with them every gate written against those. HoodieWriteConfig is the
    # receiver at nearly every call site, so its mapping is the default, and
    # AMBIGUOUS_ACCESSORS lets a call site whose receiver names another config
    # class (`tableConfig.getTableType()`) pick that one instead.
    resolved = {}
    AMBIGUOUS_ACCESSORS.clear()
    for name, keys in accessors.items():
        if len(keys) == 1:
            resolved[name] = next(iter(keys))
        elif PRIMARY_ACCESSOR_CLASS in by_class[name]:
            resolved[name] = by_class[name][PRIMARY_ACCESSOR_CLASS]
            AMBIGUOUS_ACCESSORS[name] = dict(by_class[name])
            sites = accessor_sites.get(name)
            if sites and sites[0] != PRIMARY_ACCESSOR_CLASS:
                accessor_sites[name] = (PRIMARY_ACCESSOR_CLASS,) + sites[1:]
    return resolved, accessor_sites


SHORT_CIRCUIT_HEURISTIC = (
    "Candidate wrappers found textually: a method that returns an accessor's value on one "
    "branch and a literal on another, so the literal path never reads the key. The shape is "
    "matched, the attribution is not verified -- roughly half of these are real gates and the "
    "rest call the accessor incidentally. Open the cited file:line and confirm the literal "
    "return really bypasses this config before telling a user it does."
)

LITERAL_RETURN_RE = re.compile(r"return\s+(true|false)\s*;")
IF_RE = re.compile(r"\bif\s*\(")


def collect_short_circuits(repo_root, accessors):
    """Pass 2a. Wrapper methods that can answer without reading the config.

    A config is normally found by its constant or by a resolved accessor. But a
    second-level wrapper -- one that calls an accessor rather than reading the
    key itself -- can return a fixed value on some branch and never reach the
    read at all. The canonical case is

        public boolean isMetadataStreamingWritesEnabled(HoodieTableVersion v) {
          if (v.greaterThanOrEquals(HoodieTableVersion.EIGHT)) {
            return metadataConfig.isStreamingWriteEnabled();
          } else {
            return false;
          }
        }

    On a table below version eight the key is never consulted, so setting it
    does nothing and Hudi reports no error. That is invisible in both
    readSites and gatingConditions: the read site is real and unconditional,
    and the condition lives one frame up in the caller.

    Returns {config key: [ {method, class, file, line, condition, ...} ]}.
    """
    result = defaultdict(list)
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        masked = strip_comments_and_strings(original)
        owner_class = None
        class_match = CLASS_DECL_RE.search(masked)
        if class_match:
            owner_class = class_match.group(1)

        for name, body_start, body_end, sig_line in find_method_bodies(masked, original):
            if name in accessors:
                continue
            body = masked[body_start:body_end]
            if len(body) > 1200:
                continue
            if not LITERAL_RETURN_RE.search(body) or not IF_RE.search(body):
                continue
            called = sorted({a for a in accessors
                             if re.search(r"\b" + re.escape(a) + r"\s*\(", body)})
            if not called:
                continue
            # Require the shape that actually matters: the method returns the
            # accessor's value on one branch and a literal on the other, so the
            # literal path never reads the key. Anything looser matches every
            # helper that happens to call a getter and return a boolean.
            for accessor_name in called:
                call_re = re.compile(r"return\s+[^;]*\b" + re.escape(accessor_name) + r"\s*\(")
                call_match = call_re.search(body)
                if not call_match:
                    continue
                literal_match = LITERAL_RETURN_RE.search(body)
                if not literal_match:
                    continue
                # The two returns must be distinct statements, and an `if` must
                # sit above the earlier of them.
                first = min(call_match.start(), literal_match.start())
                if call_match.start() == literal_match.start():
                    continue
                guard = re.search(r"\bif\s*\(([^{;]{3,200})\)", body[:first + 1])
                if not guard:
                    continue
                condition = " ".join(guard.group(1).split())
                returns_literal_first = literal_match.start() < call_match.start()
                result[accessors[accessor_name]].append(OrderedDict([
                    ("method", name),
                    ("class", owner_class),
                    ("file", os.path.relpath(file_path, repo_root)),
                    ("line", sig_line),
                    ("viaAccessor", accessor_name),
                    ("condition", condition),
                    ("literalReturnedFirst", returns_literal_first),
                    ("verified", False),
                ]))
    for key in result:
        result[key].sort(key=lambda s: (s["class"] or "", s["method"]))
    return result


# --------------------------------------------------------------------------
# Pass 2b -- engine-specific effective defaults
# --------------------------------------------------------------------------
#
# `ConfigProperty.defaultValue()` is the *declared* default, and for a handful of
# configs it is not the one that takes effect. A builder's `build()` calls
#
#     config.setDefaultValue(PROP, getDefaultXxx(engineType))
#
# and `HoodieConfig.setDefaultValue(prop, value)` writes that value whenever the
# user has not set the key -- so for those configs the engine's value *is* the
# effective default. Reporting the declared one tells a Spark user that
# hoodie.metadata.index.column.stats.enable defaults to false when on Spark it is
# true, which is the kind of confidently wrong answer this catalog exists to
# prevent.
#
# This pass finds the two-argument setDefaultValue calls, follows the named
# helper to its `switch (engineType)`, and reads one value per engine. Some of
# those helpers do not return a fixed value per engine: they branch further on
# another config (`isConsistentHashingBucketIndex()`) or on the runtime
# (`getSparkRuntimeVersion()`). Those are recorded as conditional rather than
# flattened into a value that would be wrong half the time.

ENGINE_NAMES = ("SPARK", "FLINK", "JAVA")

SET_DEFAULT_VALUE_RE = re.compile(
    r"\.\s*setDefaultValue\s*\(")

# `getDefaultColStatsEnable(engineType)` -- a bare call passing the engine.
ENGINE_HELPER_CALL_RE = re.compile(
    r"\A(?P<helper>[A-Za-z_$][A-Za-z0-9_$]*)\s*\(\s*engineType\s*\)\Z")

CASE_LABEL_RE = re.compile(
    r"\b(?:case\s+([A-Za-z_$][A-Za-z0-9_$]*)|(default))\s*:")
RETURN_RE = re.compile(r"\breturn\b")
TERNARY_RE = re.compile(r"\A(?P<cond>.+?)\?(?P<yes>.+):(?P<no>.+)\Z", re.DOTALL)


def _if_else_returns_as_ternary(region):
    """Rewrite ``if (c) { return a; } else { return b; }`` as ``c ? a : b``.

    Only the shape where both arms return is handled; anything else returns None
    so the caller falls back to reading the first return it finds.
    """
    match = IF_RE.search(region)
    if not match:
        return None
    condition, after = extract_call_args(region, match.end() - 1)
    if condition is None:
        return None

    then_value, after_then = _first_returned_expression(region, after)
    if then_value is None:
        return None

    else_index = region.find("else", after_then)
    if else_index < 0:
        return None
    else_value, _ = _first_returned_expression(region, else_index + 4)
    if else_value is None:
        return None

    return "%s ? %s : %s" % (" ".join(condition.split()), then_value, else_value)


def _first_returned_expression(region, start):
    """The expression of the first ``return`` at or after ``start``."""
    match = RETURN_RE.search(region, start)
    if not match:
        return None, start
    semicolon = region.find(";", match.end())
    if semicolon < 0:
        return None, start
    return " ".join(region[match.end():semicolon].split()), semicolon + 1


def _switch_case_returns(body):
    """Map each ``case LABEL:`` in a switch body to the expression it returns.

    Labels that fall through to a later ``return`` share that return, which is
    how SPARK and JAVA come to share one value in several of these helpers.
    """
    labels = [(m.group(1) or "default", m.start(), m.end())
              for m in CASE_LABEL_RE.finditer(body)]
    if not labels:
        return {}
    returns = {}
    for index, (label, _, label_end) in enumerate(labels):
        # The region running to the next case label (or the end of the body).
        region_end = labels[index + 1][1] if index + 1 < len(labels) else len(body)
        region = body[label_end:region_end]

        # An engine arm may itself branch -- Spark's marker type depends on
        # whether the embedded timeline server is on. Rewriting that if/else as
        # the equivalent ternary lets the caller record it as a condition rather
        # than silently reporting only the first branch's value.
        branched = _if_else_returns_as_ternary(region)
        if branched:
            returns[label] = branched
            continue

        match = RETURN_RE.search(region)
        if match:
            expression = region[match.end():]
            semicolon = expression.find(";")
            returns[label] = expression[:semicolon if semicolon >= 0 else len(expression)].strip()
        else:
            # Fall-through: this label shares whatever the next one returns.
            returns[label] = None

    # Resolve fall-through by walking forward to the next label that returns.
    ordered = [label for label, _, _ in labels]
    for position, label in enumerate(ordered):
        if returns.get(label) is not None:
            continue
        for later in ordered[position + 1:]:
            if returns.get(later) is not None:
                returns[label] = returns[later]
                break
    return returns


def _resolve_engine_expression(expression, string_constants, owner_class):
    """Turn one engine's return expression into (value, conditional_or_None).

    Returns ``(value, None)`` for a fixed value, or ``(None, description)`` when
    the helper branches on something other than the engine, so the caller can
    record the condition instead of inventing a value.
    """
    collapsed = " ".join(expression.split())
    if not collapsed:
        return None, None

    ternary = TERNARY_RE.match(collapsed)
    if ternary:
        condition = " ".join(ternary.group("cond").split())
        yes, _ = _resolve_engine_expression(
            ternary.group("yes"), string_constants, owner_class)
        no, _ = _resolve_engine_expression(
            ternary.group("no"), string_constants, owner_class)
        return None, OrderedDict([
            ("condition", condition),
            ("whenTrue", yes),
            ("whenFalse", no),
        ])

    literal, is_literal = literal_or_expression(
        collapsed, string_constants, owner_class)
    if is_literal:
        return literal, None

    # `MarkerType.DIRECT.toString()` -- an enum constant, whose own name is the
    # value the config receives.
    enum_member = enum_constant_name(collapsed)
    if enum_member:
        return enum_member, None

    # `ENABLE.defaultValue()` -- explicitly the declared default.
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$.]*\s*\.\s*defaultValue\s*\(\s*\)", collapsed):
        return "(declared default)", None

    return None, OrderedDict([("expression", collapsed), ("resolved", False)])


def _resolve_config_constant_strictly(expr, owner_class, constant_index):
    """Resolve a config constant without the ambiguous bare-name fallback.

    Getting this wrong here is worse than returning nothing: an engine default
    attached to the wrong config is a confident lie about a config nobody
    overrode. A qualified name must match its qualifier, and an unqualified one
    must belong to the file's own config class.
    """
    parts = [part.strip() for part in expr.split(".")]
    const = parts[-1]
    if len(parts) >= 2:
        return constant_index.get((parts[-2], const))
    return constant_index.get((owner_class, const))


def collect_engine_defaults(repo_root, constant_index):
    """Pass 2b. config key -> per-engine effective default, with provenance."""
    string_constants = collect_string_constants(repo_root)
    by_key = {}
    stats = defaultdict(int)

    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "setDefaultValue" not in original or "engineType" not in original:
            continue

        masked = strip_comments_and_strings(original, keep_string_bodies=True)
        relative = os.path.relpath(file_path, repo_root)
        # These calls sit inside a nested Builder, but the constants they name
        # belong to the enclosing config class. Resolving against the innermost
        # class would miss and fall back to a bare-name lookup, which happily
        # matches a same-named constant in an unrelated config class --
        # HoodieMetadataConfig.ENABLE would come back as ConsistencyGuardConfig's.
        top_level_match = CLASS_DECL_RE.search(masked)
        owner_class = top_level_match.group(1) if top_level_match else None

        # Index every method body in the file once, so a helper can be found
        # wherever it is declared: some sit on the Builder, others (the Parquet
        # codec one) are static on the config class itself.
        bodies = {}
        for name, body_start, body_end, _ in find_method_bodies(masked, original):
            bodies.setdefault(name, masked[body_start:body_end])

        for call in SET_DEFAULT_VALUE_RE.finditer(masked):
            args, _ = extract_call_args(masked, call.end() - 1)
            if args is None:
                continue
            parts = split_top_level_args(args)
            if len(parts) != 2:
                continue
            key = _resolve_config_constant_strictly(
                parts[0].strip(), owner_class, constant_index)
            if not key:
                stats["constantUnresolved"] += 1
                continue
            helper_call = ENGINE_HELPER_CALL_RE.match(" ".join(parts[1].split()))
            if not helper_call:
                continue
            helper = helper_call.group("helper")
            body = bodies.get(helper)
            if body is None:
                stats["helperBodyNotFound"] += 1
                continue

            returns = _switch_case_returns(body)
            if not returns:
                stats["helperWithoutSwitch"] += 1
                continue

            # Most helpers end `default: throw new HoodieNotSupportedException`,
            # which returns nothing and must not become any engine's value. Where
            # `default:` does return (the Parquet codec helper puts Java there),
            # it is the value for every engine without its own case.
            fallback = returns.get("default")

            engine_defaults = OrderedDict()
            conditional = OrderedDict()
            for engine in ENGINE_NAMES:
                expression = returns.get(engine)
                if expression is None:
                    expression = fallback
                if expression is None:
                    continue
                value, condition = _resolve_engine_expression(
                    expression, string_constants, owner_class)
                if condition is not None:
                    conditional[engine.lower()] = condition
                    stats["conditionalEngineDefaults"] += 1
                else:
                    engine_defaults[engine.lower()] = value

            if not engine_defaults and not conditional:
                continue

            record = OrderedDict()
            record["engineDefaults"] = engine_defaults
            if conditional:
                record["conditionalEngineDefaults"] = conditional
                record["defaultIsConfigDependent"] = True
            else:
                record["defaultIsConfigDependent"] = False
            record["resolvedFrom"] = OrderedDict([
                ("helper", helper),
                ("class", owner_class),
                ("file", relative),
                ("line", line_of(original, call.start())),
            ])
            by_key[key] = record
            stats["configsWithEngineDefaults"] += 1

    return by_key, stats


# --------------------------------------------------------------------------
# Pass 3 -- read sites, co-configs, gating
# --------------------------------------------------------------------------

IDENTIFIER_RE = re.compile(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:\.\s*([A-Za-z_$][A-Za-z0-9_$]*))?")

IF_RE = re.compile(r"\bif\s*\(")
SWITCH_RE = re.compile(r"\bswitch\s*\(")
CASE_RE = re.compile(r"\bcase\s+([A-Za-z_$][A-Za-z0-9_$.]*)\s*:")

# Strings that mean "this read only happens under a condition", used to decide
# whether a gate is worth recording at all.
CONDITION_NOISE_RE = re.compile(r"^\s*(true|false|1|0)\s*$")


def summarize_condition(condition):
    collapsed = " ".join(condition.split())
    if len(collapsed) > 160:
        collapsed = collapsed[:157] + "..."
    return collapsed


def enclosing_gates(masked, body_start, site_index):
    """Best-effort: conditions of the if/switch/case blocks containing ``site_index``.

    Textual, not an AST walk. It finds each ``if (...)`` / ``switch (...)``
    before the site, locates the block it opens, and keeps the condition when
    the site falls inside that block. ``case`` labels are matched by scanning
    backwards to the nearest label within the enclosing switch.
    """
    gates = []

    for pattern, kind in ((IF_RE, "if"), (SWITCH_RE, "switch")):
        for match in pattern.finditer(masked, body_start, site_index):
            condition, after = extract_call_args(masked, match.end() - 1)
            if condition is None:
                continue
            brace = masked.find("{", after)
            if kind == "if" and (brace < 0 or masked[after:brace].strip()):
                # Brace-less: `if (cond) return x;` in Java, `if (cond) a else b`
                # in Scala. The statement runs to the end of its line, or the
                # next line when the condition ends one.
                line_end = masked.find("\n", after)
                line_end = len(masked) if line_end < 0 else line_end
                if not masked[after:line_end].strip():
                    next_end = masked.find("\n", line_end + 1)
                    line_end = len(masked) if next_end < 0 else next_end
                if after <= site_index < line_end:
                    text = summarize_condition(condition)
                    if not CONDITION_NOISE_RE.match(text):
                        gates.append("if (%s)" % text)
                continue
            if brace < 0 or brace > site_index:
                continue
            # Nothing but whitespace may sit between ")" and "{" for the brace
            # to be this construct's own block.
            if masked[after:brace].strip():
                continue
            depth = 0
            block_end = -1
            for i in range(brace, len(masked)):
                if masked[i] == "{":
                    depth += 1
                elif masked[i] == "}":
                    depth -= 1
                    if depth == 0:
                        block_end = i
                        break
            if block_end < 0 or not (brace < site_index < block_end):
                continue
            text = summarize_condition(condition)
            if CONDITION_NOISE_RE.match(text):
                continue
            if kind == "switch":
                label = None
                for case_match in CASE_RE.finditer(masked, brace, site_index):
                    label = case_match.group(1)
                if label:
                    gates.append("switch (%s) case %s" % (text, label))
                else:
                    gates.append("switch (%s)" % text)
            else:
                gates.append("if (%s)" % text)

    # Innermost conditions are the informative ones.
    return gates[-MAX_GATES_PER_SITE:]


_GUARD_CACHE = {}


def _method_guards(masked, lo, hi):
    """Per method, once: [(if_start, depth, after_index, guard_text)] for every
    `if` whose block (or brace-less statement) only exits, plus the depth array."""
    cache_key = (id(masked), lo, hi)
    cached = _GUARD_CACHE.get(cache_key)
    if cached is not None:
        return cached
    depth_at = []
    depth = 0
    for i in range(lo, hi):
        depth_at.append(depth)
        ch = masked[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
    guards = []
    for match in IF_RE.finditer(masked, lo, hi):
        condition, after = extract_call_args(masked, match.end() - 1)
        if condition is None:
            continue
        brace = masked.find("{", after, hi)
        if brace >= 0 and not masked[after:brace].strip():
            d, end = 0, -1
            for i in range(brace, hi):
                if masked[i] == "{":
                    d += 1
                elif masked[i] == "}":
                    d -= 1
                    if d == 0:
                        end = i
                        break
            if end < 0:
                continue
            block = masked[brace + 1:end]
            if not re.search(r"\b(?:return|throw)\b[^;]*;\s*$", block.strip() + "\n"):
                continue
            if re.match(r"\s*else\b", masked[end + 1:end + 12]):
                continue
            exit_end = end
        else:
            stmt_end = masked.find(";", after, hi)
            if stmt_end < 0 or not re.match(r"\s*(?:return|throw)\b", masked[after:stmt_end]):
                continue
            exit_end = stmt_end
        text = summarize_condition(condition)
        if CONDITION_NOISE_RE.match(text):
            continue
        guards.append((match.start(), depth_at[match.start() - lo], exit_end, "unless (%s)" % text))
    if len(_GUARD_CACHE) > 4096:
        _GUARD_CACHE.clear()
    _GUARD_CACHE[cache_key] = (depth_at, guards)
    return depth_at, guards


def guard_clauses(masked, lo, hi, site_index, limit=2):
    """Early exits before a read at the same block depth: ``if (c) { return x; }``.

    The read only happens when ``c`` is false, so it is recorded as
    ``unless (c)``. KeyGenUtils.encodeSingleKeyFieldNameForComplexKeyGen returns
    early whenever the table records its key encoding, which is what makes
    hoodie.write.complex.keygen.new.encoding inert on any table that has it.
    """
    depth_at, guards = _method_guards(masked, lo, hi)
    if site_index - lo >= len(depth_at):
        return []
    site_depth = depth_at[site_index - lo]
    found = [text for start, depth, exit_end, text in guards
             if start < site_index and exit_end < site_index and depth == site_depth
             and min(depth_at[exit_end - lo:site_index - lo] or [site_depth]) >= site_depth]
    return found[-limit:]


def conjunction_gate(masked, lo, hi, site_index):
    """The boolean expression a read is combined into, when it has `&&` / `||`.

    ``asyncClusteringTriggerFnDefined && !client.getConfig.inlineClusteringEnabled
    && client.getConfig.isAsyncClusteringEnabled`` is a gate on async clustering
    -- inline wins -- with no `if` anywhere. The expression is the run of lines
    joined by a trailing or leading boolean operator around the site.
    """
    start = masked.rfind("\n", lo, site_index) + 1 or lo
    end = masked.find("\n", site_index, hi)
    end = hi if end < 0 else end
    for _ in range(6):
        prev_end = start - 1
        if prev_end <= lo:
            break
        prev_start = masked.rfind("\n", lo, prev_end) + 1 or lo
        if masked[prev_start:prev_end].rstrip().endswith(("&&", "||")) or \
                masked[start:end].lstrip().startswith(("&&", "||")):
            start = prev_start
        else:
            break
    for _ in range(6):
        if end >= hi:
            break
        next_end = masked.find("\n", end + 1, hi)
        next_end = hi if next_end < 0 else next_end
        if masked[start:end].rstrip().endswith(("&&", "||")) or \
                masked[end + 1:next_end].lstrip().startswith(("&&", "||")):
            end = next_end
        else:
            break
    text = masked[start:end]
    if "&&" not in text and "||" not in text:
        return None
    # Trim to the expression: drop a leading `return`, assignment or `if (`.
    text = re.sub(r"^\s*(?:return\b|(?:val|var|final)?\s*[\w<>\[\], ]*\b\w+\s*=(?!=)|if\s*\()", "", text)
    return "when (%s)" % summarize_condition(text.strip().rstrip("{;").strip())


SCALA_MATCH_RE = re.compile(r"\bmatch\s*\{")
SCALA_CASE_RE = re.compile(r"\bcase\b([^\n]*?)=>")


def scala_match_gates(masked, lo, site_index, limit=2):
    """`x match { case Some(v) => <read> }` -> "match (x) case Some(v)".

    The scrutinee is the expression on the line before `match`; the arm is the
    last `case ... =>` at the block's top level before the site.
    """
    gates = []
    for match in SCALA_MATCH_RE.finditer(masked, lo, site_index):
        brace = match.end() - 1
        depth, end = 0, -1
        for i in range(brace, min(len(masked), brace + 20000)):
            if masked[i] == "{":
                depth += 1
            elif masked[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end < 0 or not (brace < site_index < end):
            continue
        line_start = masked.rfind("\n", lo, match.start()) + 1
        scrutinee = masked[line_start:match.start()].strip()
        scrutinee = re.sub(r"^(?:val|var|lazy val)\s+\w+\s*(?::[^=]+)?=\s*", "", scrutinee)
        label = None
        depth = 0
        i = brace
        while i < site_index:
            ch = masked[i]
            if ch in "{(":
                depth += 1
            elif ch in "})":
                depth -= 1
            elif depth == 1 and masked.startswith("case", i) and \
                    (i == 0 or not (masked[i - 1].isalnum() or masked[i - 1] == "_")):
                arrow = masked.find("=>", i)
                if 0 < arrow < site_index:
                    label = " ".join(masked[i + 4:arrow].split())
                    i = arrow + 1
            i += 1
        # `case _` is the fallthrough arm: no condition worth recording.
        if label and scrutinee and label != "_":
            gates.append("match (%s) case %s" % (summarize_condition(scrutinee), summarize_condition(label)))
    return gates[-limit:]


SCALA_DEF_RE = re.compile(r"^(?P<indent>[ \t]*)(?:(?:private|protected|override|final|implicit|lazy)(?:\[[^\]]*\])?\s+)*def\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)", re.M)


def find_scala_method_spans(masked, original):
    """Yield (name, start, end, line) for each Scala ``def``.

    No Scala parser here: a def runs until the next def at the same or a
    shallower indent, or the end of the file. Nested defs fall inside their
    parent's span and also get their own, and the innermost wins at lookup.
    """
    defs = [(m.start(), len(m.group("indent").expandtabs(2)), m.group("name"))
            for m in SCALA_DEF_RE.finditer(masked)]
    for i, (start, indent, name) in enumerate(defs):
        end = len(masked)
        for later_start, later_indent, _ in defs[i + 1:]:
            if later_indent <= indent:
                end = later_start
                break
        yield name, start, end, line_of(original, start)


def collect_read_sites(repo_root, constant_index, accessors, config_keys, verbose=False):
    """Pass 3. Returns key -> {"readSites": [...], "coConfigs": {key: count}}."""
    result = defaultdict(lambda: {"readSites": [], "coConfigs": defaultdict(int)})
    # Constant names that are unambiguous enough to attribute without a
    # qualifier: a bare name used by exactly one config.
    bare_constants = defaultdict(set)
    for (qualifier, const), key in constant_index.items():
        bare_constants[const].add(key)
    unambiguous_bare = {const: next(iter(keys))
                        for const, keys in bare_constants.items() if len(keys) == 1}

    stats = defaultdict(int)

    for file_path in walk_source_files(repo_root, READ_SITE_EXTENSIONS):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        is_scala = file_path.endswith(".scala")
        masked = strip_comments_and_strings(original, scala=is_scala)
        relative = os.path.relpath(file_path, repo_root)
        owner_class = None
        class_match = (SCALA_CLASS_DECL_RE if is_scala else CLASS_DECL_RE).search(masked)
        if class_match:
            owner_class = class_match.group(1)

        if is_scala:
            # A Scala mention gets its enclosing def from an indentation-based
            # span finder, and its gates from the same textual `if` matcher the
            # Java pass uses plus boolean conjunctions. That is shallower than
            # the Java pass -- `match` arms are recovered, for-comprehension guards are not
            # -- so the site stays marked `via: scalaReference` and
            # `gatesResolved` says whether a method was found at all.
            spans = list(find_scala_method_spans(masked, original))
            per_method = defaultdict(list)
            for match in IDENTIFIER_RE.finditer(masked):
                key, via = _identifier_to_key(match, owner_class, constant_index,
                                              unambiguous_bare, accessors)
                if not key or key not in config_keys:
                    continue
                # `def isAsyncClusteringEnabled(...)` names the accessor it shadows;
                # the definition is not a read.
                if re.search(r"\bdef\s+$", masked[max(0, match.start() - 12):match.start()]):
                    continue
                enclosing = None
                for span in spans:
                    if span[1] <= match.start() < span[2] and \
                            (enclosing is None or span[1] >= enclosing[1]):
                        enclosing = span
                per_method[enclosing].append((key, match.start()))
            for enclosing, hits in per_method.items():
                lo, hi = (enclosing[1], enclosing[2]) if enclosing else (0, len(masked))
                touched = OrderedDict((k, True) for k, _ in hits)
                seen = set()
                for key, index in hits:
                    bucket = result[key]
                    bucket["scalaReferences"] = bucket.get("scalaReferences", 0) + 1
                    if key in seen:
                        # A later mention in the same def can carry the gate the
                        # first one lacked; fold it into the recorded site.
                        if enclosing and bucket["readSites"]:
                            site = bucket["readSites"][-1]
                            if site["file"] == relative and site["method"] == enclosing[0]:
                                extra = list(enclosing_gates(masked, lo, index))
                                conj = conjunction_gate(masked, lo, hi, index)
                                if conj:
                                    extra.append(conj)
                                extra += scala_match_gates(masked, lo, index)
                                for gate in extra:
                                    if gate not in site["gates"] and \
                                            len(site["gates"]) < MAX_GATES_PER_SITE * 2:
                                        site["gates"].append(gate)
                        continue
                    seen.add(key)
                    if enclosing:
                        for other in touched:
                            if other != key:
                                bucket["coConfigs"][other] += 1
                    if len(bucket["readSites"]) >= COLLECT_READ_SITES:
                        stats["readSitesCapped"] += 1
                        continue
                    gates = list(enclosing_gates(masked, lo, index)) if enclosing else []
                    conj = conjunction_gate(masked, lo, hi, index) if enclosing else None
                    if conj and conj not in gates:
                        gates.append(conj)
                    if enclosing:
                        for arm in scala_match_gates(masked, lo, index):
                            if arm not in gates:
                                gates.append(arm)
                    bucket["readSites"].append(OrderedDict([
                        ("class", owner_class),
                        ("method", enclosing[0] if enclosing else None),
                        ("file", relative),
                        ("line", line_of(original, index)),
                        ("via", "scalaReference"),
                        ("gatesResolved", enclosing is not None),
                        ("gates", gates[:MAX_GATES_PER_SITE * 2]),
                    ]))
                    stats["readSites"] += 1
                    stats["scalaReadSites"] += 1
            continue

        declaring_file = relative
        file_imports = static_imports(original)
        with_strings = strip_comments_and_strings(original, keep_string_bodies=True) \
            if '"hoodie.' in original else None

        for method_name, body_start, body_end, sig_line in find_method_bodies(masked, original):
            body = masked[body_start:body_end]
            # Which configs does this method touch at all? Needed for co-configs.
            hits = []
            for match in IDENTIFIER_RE.finditer(body):
                key, via = _identifier_to_key(match, owner_class, constant_index,
                                              unambiguous_bare, accessors, file_imports)
                if key and key in config_keys:
                    hits.append((key, body_start + match.start(), via))
            # `props.getBoolean("hoodie.write.track.event.time.watermark", false)`:
            # a key spelled as a literal is a read the identifier scan cannot see.
            if with_strings is not None:
                for match in re.finditer(r'"(hoodie\.[A-Za-z0-9_.\-]+)"', with_strings[body_start:body_end]):
                    if match.group(1) in config_keys:
                        hits.append((match.group(1), body_start + match.start(), "literalKey"))
                hits.sort(key=lambda hit: hit[1])
            if not hits:
                continue

            touched = OrderedDict()
            for key, _, _ in hits:
                touched[key] = True

            # A value read into a local is almost always *used* further down,
            # often inside the branch that decides whether it matters at all.
            # Following the local is what surfaces the real gate.
            local_uses = local_alias_uses(body, body_start, hits)

            seen_in_method = set()
            for key, absolute_index, via in hits:
                bucket = result[key]
                # One read site per (method, key); the first mention wins.
                if key in seen_in_method:
                    continue
                seen_in_method.add(key)

                for other in touched:
                    if other != key:
                        bucket["coConfigs"][other] += 1

                if len(bucket["readSites"]) >= COLLECT_READ_SITES:
                    stats["readSitesCapped"] += 1
                    continue
                # Reading the declaration itself is not a read site.
                if declaring_file.endswith(".java") and via == "constant" \
                        and _is_declaration_site(masked, absolute_index):
                    continue
                if via == "literalKey" and re.search(r"\.\s*key\s*\(\s*$",
                                                     masked[max(0, absolute_index - 20):absolute_index]):
                    continue

                gates = list(enclosing_gates(masked, body_start, absolute_index))
                for use_index in local_uses.get(absolute_index, ()):
                    for gate in enclosing_gates(masked, body_start, use_index):
                        if gate not in gates:
                            gates.append(gate)
                conj = conjunction_gate(masked, body_start, body_end, absolute_index)
                if conj and conj not in gates:
                    gates.append(conj)
                for guard in guard_clauses(masked, body_start, body_end, absolute_index):
                    if guard not in gates:
                        gates.append(guard)

                bucket["readSites"].append(OrderedDict([
                    ("class", owner_class),
                    ("method", method_name),
                    ("file", declaring_file),
                    ("line", line_of(original, absolute_index)),
                    ("via", via),
                    ("gatesResolved", True),
                    ("gates", gates[:MAX_GATES_PER_SITE * 2]),
                ]))
                stats["readSites"] += 1

    return result, stats


LOCAL_ASSIGNMENT_RE = re.compile(
    r"(?:\b(?:final\s+)?[A-Za-z_$][A-Za-z0-9_$<>,.\[\]\s?]*?\s+)?"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*$")


def local_alias_uses(body, body_start, hits):
    """Map a read site to later uses of the local variable it is assigned to.

    ``int inlineCompactDeltaCommitMax = config.getInlineCompactDeltaCommitMax();``
    puts the value in a local, and the branch that decides whether the config
    matters tests that local, not the accessor. Without this the gate for such a
    config would always come back empty.
    """
    uses = defaultdict(list)
    for _, absolute_index, _ in hits:
        relative = absolute_index - body_start
        line_start = body.rfind("\n", 0, relative) + 1
        prefix = body[line_start:relative]
        match = LOCAL_ASSIGNMENT_RE.search(prefix)
        if not match:
            continue
        name = match.group("name")
        if len(name) < 3:
            continue
        for occurrence in re.finditer(r"\b%s\b" % re.escape(name), body):
            if occurrence.start() <= relative:
                continue
            uses[absolute_index].append(body_start + occurrence.start())
            if len(uses[absolute_index]) >= 12:
                break
    return uses


def _is_declaration_site(masked, index):
    line_start = masked.rfind("\n", 0, index) + 1
    line_end = masked.find("\n", index)
    line = masked[line_start:line_end if line_end > 0 else len(masked)]
    return "ConfigProperty" in line and "=" in line


def _identifier_to_key(match, owner_class, constant_index, unambiguous_bare, accessors,
                       imports=None):
    """Map one identifier occurrence to a config key, or None.

    Returns (key, via). ``via`` records how the attribution was made so a reader
    can tell a direct constant reference from a call through an accessor.
    """
    first, second = match.group(1), match.group(2)
    if second == "key" and _looks_like_constant(first):
        # `ERROR_TABLE_ENABLED.key()` on a bare (often statically imported) constant.
        second = None
    if second:
        # `HoodieCompactionConfig.INLINE_COMPACT_NUM_DELTA_COMMITS`
        key = constant_index.get((first, second))
        if key:
            return key, "constant"
        # `config.getInlineCompactDeltaCommitMax()` -- the receiver is a value,
        # so only the method name carries the attribution.
        if second in accessors:
            key = accessor_key_for_receiver(
                second, match.string[max(0, match.start() - 60):match.end(1)], accessors[second])
            return key, "accessor:" + second
        if _looks_like_constant(second):
            key = unambiguous_bare.get(second)
            if key:
                return key, "constant"
        return None, None
    if first in accessors:
        key = accessor_key_for_receiver(
            first, match.string[max(0, match.start() - 60):match.start()], accessors[first])
        return key, "accessor:" + first
    if _looks_like_constant(first):
        # `import static ...HoodieErrorTableConfig.ERROR_TABLE_ENABLED;` qualifies a
        # bare name that is ambiguous across config classes.
        if imports and first in imports:
            key = constant_index.get((imports[first], first))
            if key:
                return key, "constant"
        if owner_class:
            key = constant_index.get((owner_class, first))
            if key:
                return key, "constant"
        key = unambiguous_bare.get(first)
        if key:
            return key, "constant"
    return None, None


def _looks_like_constant(name):
    return name.upper() == name and any(ch.isalpha() for ch in name)


# --------------------------------------------------------------------------
# Pass 4: defaults supplied at the call site
# --------------------------------------------------------------------------

# `optParams.getOrElse(INCREMENTAL_FALLBACK_TO_FULL_TABLE_SCAN.key, "false")`,
# `props.getBoolean(SOME_CONFIG.key(), false)`. The literal is what the reader
# gets when the key is unset, whatever the declaration says. When it disagrees
# with the declared default the declaration is the wrong answer on that code
# path: hoodie.datasource.read.incr.fallback.fulltablescan.enable declares
# "true", and the V1 incremental relations that serve tables below version 8
# read it with "false".
LITERAL_KEY_DEFAULT_RE = re.compile(
    r"\.\s*(?:getOrElse|getOrDefault|getProperty|getBoolean|getInteger|getInt|getLong|getString|"
    r"getDouble|getFloat)\s*\(\s*\"(?P<key>hoodie\.[A-Za-z0-9_.\-]+)\"\s*,\s*"
    r"(?P<arg>\"(?:[^\"\\]|\\.)*\"|true|false|-?\d+(?:\.\d+)?[LlDdFf]?)\s*\)")
CALL_SITE_DEFAULT_RE = re.compile(
    r"\.\s*(?P<call>getOrElse|getOrDefault|getProperty|getBoolean|getInteger|getInt|getLong|"
    r"getString|getDouble|getFloat|getBooleanOrDefault|getIntOrDefault|getLongOrDefault|"
    r"getStringOrDefault)\s*\(\s*"
    r"(?P<const>(?:[A-Za-z_$][A-Za-z0-9_$]*\s*\.\s*)*[A-Z][A-Z0-9_]*)\s*(?:\(\s*\))?"
    r"(?:\s*\.\s*key\s*(?:\(\s*\))?)?\s*,\s*"
    r"(?P<arg>\"(?:[^\"\\]|\\.)*\"|true|false|-?\d+(?:\.\d+)?[LlDdFf]?)\s*\)")


def normalize_default(value):
    """Compare defaults as written in different places: "true" vs true, 10L vs "10"."""
    if value is None:
        return None
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        text = text[1:-1]
    # "", null and a cast null all mean "no default": an empty-string fallback
    # against a noDefaultValue() declaration is not a disagreement.
    if re.fullmatch(r"(?:\([A-Za-z_$][\w$.<>]*\)\s*)?(?:null|none)?", text.strip(), re.I):
        return None
    if re.match(r"^-?\d+(?:\.\d+)?[LlDdFf]$", text):
        text = text[:-1]
    return text.lower()


def collect_call_site_defaults(repo_root, constant_index):
    """key -> [{value, at, differsFromDeclared}] for explicit fallbacks at a read."""
    found = defaultdict(list)
    for file_path in walk_source_files(repo_root, READ_SITE_EXTENSIONS):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if ".key" not in original:
            continue
        is_scala = file_path.endswith(".scala")
        # Comments blanked, string bodies kept: the fallback literal is the point.
        text = strip_comments_and_strings(original, keep_string_bodies=True, scala=is_scala)
        class_match = (SCALA_CLASS_DECL_RE if is_scala else CLASS_DECL_RE).search(text)
        owner_class = class_match.group(1) if class_match else None
        relative = os.path.relpath(file_path, repo_root)
        file_imports = static_imports(original)
        for match in LITERAL_KEY_DEFAULT_RE.finditer(text):
            found[match.group("key")].append(OrderedDict([
                ("value", match.group("arg").strip('"')),
                ("at", "%s (%s:%d)" % (owner_class or "?", relative,
                                       line_of(original, match.start()))),
            ]))
        for match in CALL_SITE_DEFAULT_RE.finditer(text):
            const = re.sub(r"\s+", "", match.group("const"))
            key = resolve_constant(const, owner_class, constant_index, file_imports)
            if not key:
                continue
            found[key].append(OrderedDict([
                ("value", match.group("arg").strip('"')),
                ("at", "%s (%s:%d)" % (owner_class or "?", relative,
                                       line_of(original, match.start()))),
            ]))
    return found


# --------------------------------------------------------------------------
# Pass 5: Flink options that stand in for hoodie.* keys
# --------------------------------------------------------------------------

FLINK_OPTIONS_FILE = os.path.join(
    "hudi-flink-datasource", "hudi-flink", "src", "main", "java", "org", "apache", "hudi",
    "configuration", "FlinkOptions.java")
FLINK_OPTION_DECL_RE = re.compile(
    r"ConfigOption\s*<[^;=]*?>\s+(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*ConfigOptions\s*\.\s*key\s*\(",
    re.S)
BUILDER_SETTER_RE = re.compile(
    r"(?:setValue|setDefaultValue)\s*\(\s*(?P<const>(?:[A-Za-z_$][A-Za-z0-9_$]*\s*\.\s*)*[A-Z][A-Z0-9_]*)\s*,"
    r"|setProperty\s*\(\s*(?P<const2>(?:[A-Za-z_$][A-Za-z0-9_$]*\s*\.\s*)*[A-Z][A-Z0-9_]*)\s*\.\s*key\s*\(\s*\)\s*,")
FLINK_OPTION_REF_RE = re.compile(r"\bFlinkOptions\s*\.\s*([A-Z][A-Z0-9_]*)\b")


def collect_flink_options(repo_root, constant_index):
    """FlinkOptions constant -> {key, default, fallbackKeys, line}.

    These live in Flink's own key namespace and are not catalog entries, but a
    Flink job reads them in place of the hoodie.* key they stand in for.
    """
    path = os.path.join(repo_root, FLINK_OPTIONS_FILE)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            original = handle.read()
    except OSError:
        return {}
    text = strip_comments_and_strings(original, keep_string_bodies=True)
    options = {}
    for match in FLINK_OPTION_DECL_RE.finditer(text):
        end = find_statement_end(text, match.end())
        chain = text[match.end() - 1:end]
        key_text, _ = extract_call_args(chain, 0)
        key_args = split_top_level_args(key_text) if key_text else []
        key = key_args[0].strip().strip('"') if key_args else None
        default = None
        dm = re.search(r"\.\s*defaultValue\s*\(", chain)
        if dm:
            args_text, _ = extract_call_args(chain, dm.end() - 1)
            if args_text:
                default, _ = literal_or_expression(args_text.strip())
                default = " ".join(str(default).split()).strip('"') if default is not None else None
                enum_name = re.match(r"^(?:[A-Za-z_$][\w$]*\.)*([A-Z][A-Z0-9_]*)\.name\(\)$", default or "")
                if enum_name:
                    default = enum_name.group(1)
        fallbacks = []
        fm = re.search(r"\.\s*withFallbackKeys\s*\(", chain)
        if fm:
            fallback_text, _ = extract_call_args(chain, fm.end() - 1)
            for arg in split_top_level_args(fallback_text or ""):
                arg = arg.strip()
                if arg.startswith('"'):
                    fallbacks.append(arg.strip('"'))
                else:
                    resolved = resolve_constant(re.sub(r"\.key\(\)$", "", arg), None, constant_index)
                    if resolved:
                        fallbacks.append(resolved)
        if key and not key.startswith('"') and "(" in key:
            key = resolve_constant(re.sub(r"\.\s*key\s*\(\s*\)$", "", key), None, constant_index) or key
        options[match.group("name")] = OrderedDict([
            ("key", key), ("default", default), ("fallbackKeys", fallbacks),
            ("line", line_of(original, match.start()))])
    return options


def collect_builder_setters(repo_root, constant_index):
    """Builder method name -> list of (param index, config key) it sets.

    `withMaxNumDeltaCommitsBeforeCompaction(int n)` sets
    hoodie.compact.inline.max.delta.commits from its first argument. A method
    whose name is shared by builders that set different configs is dropped
    rather than guessed at.
    """
    setters = {}
    conflicts = set()
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path or not os.path.basename(file_path).endswith("Config.java"):
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "Builder" not in original:
            continue
        masked = strip_comments_and_strings(original)
        class_match = CLASS_DECL_RE.search(masked)
        owner_class = class_match.group(1) if class_match else None
        file_imports = static_imports(original)
        for name, body_start, body_end, _ in find_method_bodies(masked, original):
            if name in GENERIC_METHOD_NAMES or name.startswith(("get", "is", "should")):
                continue
            # Builder setters return the builder; a plain method that happens to
            # call setValue (build(), setDefaults()) is not one.
            sig_line_start = masked.rfind("\n", 0, masked.rfind(name, 0, body_start)) + 1
            if "Builder" not in masked[sig_line_start:body_start]:
                continue
            sig_open = masked.rfind("(", 0, body_start)
            sig_close = masked.rfind(")", 0, body_start)
            params = [p.strip().split()[-1] for p in
                      split_top_level_args(masked[sig_open + 1:sig_close]) if p.strip()]
            body = masked[body_start:body_end]
            mapping = []
            for setter in BUILDER_SETTER_RE.finditer(body):
                const = re.sub(r"\s+", "", setter.group("const") or setter.group("const2"))
                key = resolve_constant(const, owner_class, constant_index, file_imports)
                if not key:
                    continue
                rest = body[setter.end():body.find(";", setter.end())]
                used = [i for i, p in enumerate(params) if re.search(r"\b%s\b" % re.escape(p), rest)]
                if len(used) == 1:
                    mapping.append((used[0], key))
            if not mapping:
                continue
            mapping = tuple(sorted(set(mapping)))
            setters[(owner_class, name)] = mapping
            if name in setters and setters[name] != mapping:
                conflicts.add(name)
            setters[name] = mapping
    for name in conflicts:
        setters.pop(name, None)
    return setters


NEW_BUILDER_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*Config)\s*\.\s*newBuilder\s*\(")


def builder_receiver(masked, index):
    """The *Config class whose builder chain a call at ``index`` belongs to.

    ``.withCompactionConfig(HoodieCompactionConfig.newBuilder().withX(..).build())``:
    the nearest ``Foo.newBuilder(`` before the call whose chain has not been
    closed by a ``.build()`` yet. Good enough to tell HoodieCompactionConfig's
    withMaxNumDeltaCommitsBeforeCompaction from HoodieMetadataConfig's.
    """
    window = masked[max(0, index - 6000):index]
    for match in reversed(list(NEW_BUILDER_RE.finditer(window))):
        # Same chain means the text from `newBuilder(` to the call is balanced
        # and never closes more than it opened: a builder nested in an earlier
        # argument closes that argument before the call is reached.
        depth = 0
        ok = True
        for ch in window[match.end() - 1:]:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    ok = False
                    break
        if ok and depth == 0:
            return match.group(1)
    return None


def collect_flink_mappings(repo_root, constant_index):
    """hoodie.* key -> [{flinkOption, flinkDefault, how, at}].

    Two shapes put a Flink option in charge of a hoodie.* key:

    - ``withFallbackKeys(HoodieIndexConfig.INDEX_TYPE.key())`` on the Flink
      option: the job reads ``index.type`` (default FLINK_STATE) and only looks
      at hoodie.index.type when the Flink option is unset.
    - the Flink write-client builders copy an option into the write config,
      ``.withMaxNumDeltaCommitsBeforeCompaction(conf.get(FlinkOptions.COMPACTION_DELTA_COMMITS))``,
      so an unset hoodie.compact.inline.max.delta.commits gets the Flink
      option's default (5), not the declared one.
    """
    options = collect_flink_options(repo_root, constant_index)
    if not options:
        return {}, {}
    mappings = defaultdict(list)
    for name, option in options.items():
        for fallback in option["fallbackKeys"]:
            if fallback.startswith("hoodie."):
                mappings[fallback].append(OrderedDict([
                    ("flinkOption", option["key"]), ("flinkDefault", option["default"]),
                    ("how", "fallbackKey"),
                    ("at", "FlinkOptions.%s (%s:%d)" % (name, FLINK_OPTIONS_FILE, option["line"]))]))

    setters = collect_builder_setters(repo_root, constant_index)
    flink_root = os.path.join(repo_root, "hudi-flink-datasource")
    for file_path in walk_source_files(flink_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "FlinkOptions." not in original:
            continue
        masked = strip_comments_and_strings(original)
        relative = os.path.relpath(file_path, repo_root)
        class_match = CLASS_DECL_RE.search(masked)
        owner_class = class_match.group(1) if class_match else "?"
        for call in re.finditer(r"\.\s*([a-z][A-Za-z0-9]*)\s*\(", masked):
            receiver = builder_receiver(masked, call.start())
            # A known receiver is authoritative: falling back to the bare name
            # would file HoodieTimeGeneratorConfig.withPath under
            # HoodieBootstrapConfig's withPath.
            mapping = setters.get((receiver, call.group(1))) if receiver \
                else setters.get(call.group(1))
            if not mapping:
                continue
            args_text, _ = extract_call_args(masked, call.end() - 1)
            args = split_top_level_args(args_text or "")
            for index, key in mapping:
                if index >= len(args):
                    continue
                refs = FLINK_OPTION_REF_RE.findall(args[index])
                if len(refs) != 1 or refs[0] not in options:
                    continue
                option = options[refs[0]]
                direct = re.fullmatch(r"\s*conf\s*\.\s*get(?:String|Integer|Boolean|Long|Double)?\s*\(\s*FlinkOptions\s*\.\s*[A-Z][A-Z0-9_]*\s*\)\s*",
                                      args[index])
                record = OrderedDict([
                    ("flinkOption", option["key"]), ("flinkDefault", option["default"]),
                    ("valueTransformed", not direct),
                    ("how", "builder:" + call.group(1)),
                    ("at", "%s (%s:%d)" % (owner_class, relative, line_of(original, call.start())))])
                if all(r["flinkOption"] != record["flinkOption"] for r in mappings[key]):
                    mappings[key].append(record)
    return mappings, options


# --------------------------------------------------------------------------
# Pass 10: places Hudi overwrites a value the user may have set
# --------------------------------------------------------------------------

OVERRIDE_CALL_RE = re.compile(
    r"\b(?:setValue|setProperty|put|putIfAbsent)\s*\(\s*"
    r"(?P<const>(?:[A-Za-z_$][\w$]*\s*\.\s*)*[A-Z][A-Z0-9_]*)(?:\s*\.\s*key\s*\(\s*\))?\s*,")
MAX_OVERRIDES = 6


def collect_overrides(repo_root, constant_index, accessors):
    """key -> [{at, value, when}] for writes that replace a configured value.

    ``setDefaultValue`` only fills an unset key and is excluded; a builder
    setter that stores its own parameter is the user setting the value and is
    excluded too. What is left is Hudi deciding for the user:
    ``writeConfig.setValue(FAILED_WRITES_CLEANER_POLICY.key(), LAZY.name())``
    under ``if (writeConcurrencyMode.supportsMultiWriter())``.
    """
    result = defaultdict(list)
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        if module_of(os.path.relpath(file_path, repo_root)) in SAMPLE_MODULES:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "setValue" not in original and "setProperty" not in original and ".put(" not in original:
            continue
        masked = strip_comments_and_strings(original)
        with_strings = strip_comments_and_strings(original, keep_string_bodies=True)
        class_match = CLASS_DECL_RE.search(masked)
        owner = class_match.group(1) if class_match else None
        # Upgrade/downgrade handlers configure their own internal write clients;
        # that is not Hudi overriding a user's setting.
        if owner and re.search(r"Upgrade|Downgrade", owner):
            continue
        imports = static_imports(original)
        relative = os.path.relpath(file_path, repo_root)
        for name, body_start, body_end, line in find_method_bodies(masked, original):
            sig_open = masked.rfind("(", 0, body_start)
            sig_close = masked.rfind(")", 0, body_start)
            params = [p.strip().split()[-1] for p in
                      split_top_level_args(masked[sig_open + 1:sig_close]) if p.strip()]
            for call in OVERRIDE_CALL_RE.finditer(masked, body_start, body_end):
                const_expr = re.sub(r"\s+", "", call.group("const"))
                # `json.put(TYPE, RECORD)` is a map write, not a config: a bare name
                # counts only when this file declares or statically imports it.
                if "." not in const_expr and (owner, const_expr) not in constant_index \
                        and const_expr not in imports and not imports.get("*"):
                    continue
                key = resolve_constant(const_expr, owner, constant_index, imports)
                if not key:
                    continue
                args_text, _ = extract_call_args(with_strings, with_strings.find("(", call.start()))
                args = split_top_level_args(args_text or "")
                value = " ".join(args[1].split()) if len(args) > 1 else ""
                # The user's own value flowing through (a setter's parameter, or a
                # copy of the same key from another config) is not an override.
                if any(re.search(r"\b%s\b" % re.escape(p), value) for p in params):
                    continue
                if re.search(r"\bget\w*\(\s*%s\b" % re.escape(call.group("const").split(".")[-1]), value):
                    continue
                if any(accessors.get(m) == key for m in re.findall(r"\b([a-z]\w*)\s*\(", value)):
                    continue
                if not value or value in ('""', "null"):
                    continue
                # Only a value Hudi decides -- a literal, a constant, an enum, a class
                # literal -- is an override. A local or field (`databaseName`,
                # `tableType.name()`) is the user's input being propagated.
                if not re.search(r'"[^"]*"|\b\d+\b|\btrue\b|\bfalse\b|\b[A-Z][A-Z0-9_]{2,}\b|\.class\b', value):
                    continue
                gates = enclosing_gates(masked, body_start, call.start())
                for guard in guard_clauses(masked, body_start, body_end, call.start()):
                    gates.append(guard)
                if not gates and name in ("build", "setDefaults"):
                    # An unconditional write in build() is a fixed setting, still
                    # an override, but say so without inventing a condition.
                    pass
                record = OrderedDict([
                    ("value", summarize_condition(value)),
                    ("at", "%s.%s (%s:%d)" % (owner or "?", name, relative,
                                              line_of(original, call.start()))),
                ])
                if gates:
                    record["when"] = gates[-3:]
                if len(result[key]) < MAX_OVERRIDES and record not in result[key]:
                    result[key].append(record)
    return result


# --------------------------------------------------------------------------
# Pass 9: validations that reject a configuration
# --------------------------------------------------------------------------

CHECK_CALL_RE = re.compile(r"\b(?:ValidationUtils\s*\.\s*|Preconditions\s*\.\s*)?(checkArgument|checkState)\s*\(")
THROW_RE = re.compile(r"\bthrow\s+new\s+([A-Z]\w*(?:Exception|Error))\s*\(")
WARN_RE = re.compile(r"\b(?:log|LOG|logger|LOGGER)\s*\.\s*warn\s*\(")
CONFIG_KEY_IN_TEXT_RE = re.compile(r"\bhoodie\.[a-z0-9_.\-]+[a-z0-9_]")
MAX_VALIDATIONS = 10


def _message_text(arg, text_with_strings):
    """The string literals of a message argument, joined: the readable part."""
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', arg)
    return " ".join(p for p in parts)[:300]


def _inside_catch(masked, lo, index):
    """True when ``index`` sits inside a ``catch (...) { ... }`` block: a rethrow
    of a runtime failure, not a check on configuration."""
    for match in re.finditer(r"\bcatch\s*\(", masked[lo:index]):
        _, after = extract_call_args(masked, lo + match.end() - 1)
        brace = masked.find("{", after)
        if brace < 0 or brace > index:
            continue
        depth = 0
        for i in range(brace, index):
            if masked[i] == "{":
                depth += 1
            elif masked[i] == "}":
                depth -= 1
        if depth > 0:
            return True
    return False


def collect_validations(repo_root, constant_index, accessors, config_keys):
    """key -> [{kind, condition, message, at, when}] for checks that reject a config.

    A config is attached to a check when the check's condition names it
    (constant or accessor), when the enclosing `if` names it, or when the
    message spells out its key -- "To enable NON_BLOCKING_CONCURRENCY_CONTROL,
    set hoodie.clean.failed.writes.policy=LAZY" names the companion outright.
    """
    result = defaultdict(list)
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        if module_of(os.path.relpath(file_path, repo_root)) in SAMPLE_MODULES:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if "checkArgument" not in original and "checkState" not in original \
                and "throw new" not in original and ".warn(" not in original:
            continue
        masked = strip_comments_and_strings(original)
        with_strings = strip_comments_and_strings(original, keep_string_bodies=True)
        class_match = CLASS_DECL_RE.search(masked)
        owner = class_match.group(1) if class_match else None
        imports = static_imports(original)
        relative = os.path.relpath(file_path, repo_root)
        for name, body_start, body_end, _ in find_method_bodies(masked, original):
            body = masked[body_start:body_end]
            if "check" not in body and "throw" not in body and "warn" not in body:
                continue
            found = []
            for call in CHECK_CALL_RE.finditer(masked, body_start, body_end):
                args_text, _ = extract_call_args(with_strings, call.end() - 1)
                if not args_text:
                    continue
                args = split_top_level_args(args_text)
                condition = strip_comments_and_strings(args[0]) if args else ""
                message = _message_text(" ".join(args[1:]), with_strings) if len(args) > 1 else ""
                found.append((call.group(1), call.start(), condition, message))
            # A throw or a warning under an `if` is a check only when that `if`
            # itself names a config; otherwise it is a runtime failure ("Async
            # clustering failed") that merely sits inside a feature branch.
            for pattern, label in ((THROW_RE, "throw"), (WARN_RE, "warn")):
                for hit in pattern.finditer(masked, body_start, body_end):
                    if label == "throw" and _inside_catch(masked, body_start, hit.start()):
                        continue
                    gates = enclosing_gates(masked, body_start, hit.start())
                    if not gates:
                        continue
                    condition = gates[-1]
                    local_scope = condition
                    for local in set(re.findall(r"\b([a-z][A-Za-z0-9_]{2,})\b", condition)):
                        assignment = re.search(r"\b%s\s*=(?!=)\s*([^;]+);" % re.escape(local),
                                               masked[body_start:hit.start()])
                        if assignment:
                            local_scope += " " + assignment.group(1)
                    if not _config_refs(local_scope, owner, constant_index, imports, accessors):
                        continue
                    args_text, _ = extract_call_args(with_strings, hit.end() - 1)
                    kind = "throw " + hit.group(1) if label == "throw" else "warn"
                    found.append((kind, hit.start(), condition,
                                  _message_text(args_text or "", with_strings)))
            for kind, index, condition, message in found:
                when = [g for g in enclosing_gates(masked, body_start, index)
                        if g != condition][-2:]
                scope = " ".join([condition] + when)
                # `checkArgument(maxInstantsToKeep > minInstantsToKeep, ...)` tests
                # locals; the config is in their assignments earlier in the method.
                for local in set(re.findall(r"\b([a-z][A-Za-z0-9_]{2,})\b", scope)):
                    assignment = re.search(r"\b%s\s*=(?!=)\s*([^;]+);" % re.escape(local),
                                           masked[body_start:index])
                    if assignment:
                        scope += " " + assignment.group(1)
                # Format arguments name configs too: "%s should be set to %s", X.key().
                scope += " " + " ".join(re.findall(r"[A-Z][\w$.]*\s*\.\s*key\s*\(\s*\)",
                                                   masked[index:masked.find(";", index)]))
                keys = []
                for k in _config_refs(scope, owner, constant_index, imports, accessors):
                    if k not in keys:
                        keys.append(k)
                for k in CONFIG_KEY_IN_TEXT_RE.findall(message):
                    if k in config_keys and k not in keys:
                        keys.append(k)
                if not keys:
                    continue
                record = OrderedDict([
                    ("kind", kind),
                    ("condition", summarize_condition(condition)),
                    ("message", message),
                    ("at", "%s.%s (%s:%d)" % (owner or "?", name, relative, line_of(original, index))),
                ])
                if when:
                    record["when"] = when
                for k in keys[:6]:
                    if len(result[k]) < MAX_VALIDATIONS and record not in result[k]:
                        result[k].append(record)
    return result


# --------------------------------------------------------------------------
# Pass 8: evaluate computed defaults
# --------------------------------------------------------------------------

VALUE_CONSTANT_RE = re.compile(
    r"\b(?:static\s+)?final\s+(?:static\s+)?(?:int|long|double|float|boolean|Integer|Long|Double|Boolean)\s+"
    r"(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*(?P<value>[^;]+);")
SCALA_VALUE_CONSTANT_RE = re.compile(
    r"^[ \t]*(?:final\s+)?val\s+(?P<name>[A-Z][A-Z0-9_]*)\s*(?::\s*[\w\[\]]+)?\s*=\s*(?P<value>[^\n]+?)\s*$", re.M)
ENUM_VALUE_RE = re.compile(r"\b(?P<const>[A-Z][A-Z0-9_]*)\s*\(\s*\"(?P<value>[^\"]*)\"")
ARITH_RE = re.compile(r"^[\d\s*+\-/().LlDdFf]+$")
TIME_UNIT_SECONDS = {"NANOSECONDS": 1e-9, "MICROSECONDS": 1e-6, "MILLISECONDS": 1e-3, "SECONDS": 1,
                     "MINUTES": 60, "HOURS": 3600, "DAYS": 86400}
TIME_UNIT_TARGET = {"toNanos": 1e-9, "toMicros": 1e-6, "toMillis": 1e-3, "toSeconds": 1,
                    "toMinutes": 60, "toHours": 3600, "toDays": 86400}
JAVA_LIMITS = {
    "Long.MAX_VALUE": str(2 ** 63 - 1), "Integer.MAX_VALUE": str(2 ** 31 - 1),
    "Long.MIN_VALUE": str(-2 ** 63), "Integer.MIN_VALUE": str(-2 ** 31),
}


def collect_value_constants(repo_root):
    """(owner, NAME) and (None, NAME) -> expression, for numeric/boolean static finals
    and single-line Scala vals. Ambiguous bare names are dropped."""
    found, bare, conflicts = {}, {}, set()
    for file_path in walk_source_files(repo_root, (".java", ".scala")):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        is_scala = file_path.endswith(".scala")
        masked = strip_comments_and_strings(original, scala=is_scala)
        pattern = SCALA_VALUE_CONSTANT_RE if is_scala else VALUE_CONSTANT_RE
        for match in pattern.finditer(masked):
            name, value = match.group("name"), " ".join(match.group("value").split())
            if "ConfigProperty" in value or value.endswith(("(", "{", "+", ".")):
                continue
            owner = (find_enclosing_scala_object(masked, match.start()) if is_scala
                     else find_enclosing_class(masked, match.start()))
            found[(owner, name)] = value
            if name in bare and bare[name] != value:
                conflicts.add(name)
            bare[name] = value
    for name, value in bare.items():
        if name not in conflicts:
            found[(None, name)] = value
    return found


def collect_enum_string_values(repo_root):
    """(Enum, CONST) -> first string constructor arg, e.g. (WriteOperationType, UPSERT) -> upsert.

    Also records, under ("#int", Enum, CONST), a leading int constructor arg
    (HoodieTableVersion.TEN -> 10), and under ("#returns", Enum, method), a
    static no-arg method that only returns one of its constants
    (HoodieTableVersion.current() -> TEN).
    """
    values = {}
    for file_path in walk_source_files(repo_root, (".java",)):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        if " enum " not in original:
            continue
        text = strip_comments_and_strings(original, keep_string_bodies=True)
        for enum_match in re.finditer(r"\benum\s+([A-Z]\w*)[^{]*\{", text):
            body_start = enum_match.end()
            body_end = text.find(";", body_start)
            if body_end < 0:
                continue
            for value_match in ENUM_VALUE_RE.finditer(text[body_start:body_end]):
                values[(enum_match.group(1), value_match.group("const"))] = value_match.group("value")
            for int_match in re.finditer(r"\b([A-Z][A-Z0-9_]*)\s*\(\s*(-?\d+)\s*[,)]",
                                         text[body_start:body_end]):
                values[("#int", enum_match.group(1), int_match.group(1))] = int_match.group(2)
            for ret in re.finditer(r"\bstatic\s+%s\s+(\w+)\s*\(\s*\)\s*\{\s*return\s+([A-Z][A-Z0-9_]*)\s*;\s*\}"
                                   % re.escape(enum_match.group(1)), text):
                values[("#returns", enum_match.group(1), ret.group(1))] = ret.group(2)
    return values


def _eval_arith(expr):
    cleaned = re.sub(r"(?<=\d)_(?=\d)", "", expr)
    cleaned = re.sub(r"(?<=\d)[LlDdFf]\b", "", cleaned)
    if not ARITH_RE.match(cleaned) or not re.search(r"\d", cleaned):
        return None
    try:
        value = eval(cleaned, {"__builtins__": {}}, {})  # digits and operators only, checked above
    except Exception:
        return None
    if isinstance(value, float) and value.is_integer() and "." not in cleaned and "/" not in cleaned:
        value = int(value)
    return str(value)


def evaluate_default(expr, ctx, depth=0):
    """Best-effort value of a default expression, or None. Returns (value, how)."""
    if expr is None or depth > 4:
        return None, None
    expr = " ".join(str(expr).split())
    inner = re.fullmatch(r"(?:String\s*\.\s*valueOf|Long\s*\.\s*valueOf|Integer\s*\.\s*valueOf|"
                         r"Boolean\s*\.\s*toString|Integer\s*\.\s*toString|Long\s*\.\s*toString)\s*\((.*)\)", expr)
    if inner:
        expr = inner.group(1).strip()
    if expr in JAVA_LIMITS:
        return JAVA_LIMITS[expr], "javaConstant"
    unit = re.fullmatch(r"TimeUnit\s*\.\s*([A-Z]+)\s*\.\s*(to[A-Z][a-z]+)\s*\((.*)\)", expr)
    if unit and unit.group(1) in TIME_UNIT_SECONDS and unit.group(2) in TIME_UNIT_TARGET:
        amount = _eval_arith(unit.group(3))
        if amount is not None:
            value = float(amount) * TIME_UNIT_SECONDS[unit.group(1)] / TIME_UNIT_TARGET[unit.group(2)]
            return str(int(value)), "timeUnit"
    value = _eval_arith(expr)
    if value is not None:
        return value, "arithmetic"
    if expr in ("true", "false"):
        return expr, "literal"
    # X.class.getName(), classOf[X].getName -> FQN
    cls = re.fullmatch(r"(?:classOf\[\s*)?([A-Z][\w$]*)(?:\s*\])?(?:\s*\.\s*class)?\s*\.\s*"
                       r"(?:getName|getCanonicalName|getSimpleName)\s*(?:\(\s*\))?", expr)
    if cls:
        info = ctx["types"].get(cls.group(1))
        if info and not info.get("ambiguous"):
            return info["fqn"], "className"
        return None, None
    # OTHER_CONFIG.defaultValue()
    other = re.fullmatch(r"((?:[A-Z][\w$]*\s*\.\s*)?[A-Z][A-Z0-9_]*)\s*\.\s*defaultValue\s*\(\s*\)", expr)
    if other:
        key = resolve_constant(other.group(1).replace(" ", ""), None, ctx["constant_index"])
        entry = ctx["by_key"].get(key)
        if entry:
            if entry.get("defaultValueIsLiteral"):
                return entry.get("defaultValue"), "otherConfigDefault:" + key
            value, _ = evaluate_default(entry.get("defaultValue"), ctx, depth + 1)
            if value is not None:
                return value, "otherConfigDefault:" + key
        return None, None
    # Enum.current() / Enum.current().versionCode()
    returns = re.fullmatch(r"([A-Z][\w$]*)\s*\.\s*([a-z]\w*)\s*\(\s*\)(?:\s*\.\s*(\w+)\s*\(\s*\))?", expr)
    if returns:
        const = ctx["enum_values"].get(("#returns", returns.group(1), returns.group(2)))
        if const:
            if not returns.group(3):
                return const, "enumMethod"
            number = ctx["enum_values"].get(("#int", returns.group(1), const))
            if number is not None:
                return number, "enumMethod"
    # Enum.CONST.value / .value() / .getValue() / .name()
    enum_value = re.fullmatch(r"(?:[\w$]+\s*\.\s*)*?([A-Z][\w$]*)\s*\.\s*([A-Z][A-Z0-9_]*)\s*\.\s*"
                              r"(value|getValue|configValue|getConfigValue|name|toString)\s*(?:\(\s*\))?", expr)
    if enum_value:
        if enum_value.group(3) in ("name", "toString"):
            return enum_value.group(2), "enumName"
        found = ctx["enum_values"].get((enum_value.group(1), enum_value.group(2)))
        if found is not None:
            return found, "enumValue"
        return None, None
    # Enum.CONST (a typed default; the stored string is the constant's name)
    enum_const = re.fullmatch(r"(?:[\w$]+\s*\.\s*)*([A-Z][\w$]*[a-z][\w$]*)\s*\.\s*([A-Z][A-Z0-9_]*)", expr)
    if enum_const and (enum_const.group(1), enum_const.group(2)) not in ctx["string_constants"] \
            and (enum_const.group(1), enum_const.group(2)) not in ctx["value_constants"]:
        return enum_const.group(2), "enumConstant"
    # A bare or qualified constant: string, then numeric.
    const = re.fullmatch(r"(?:([A-Z][\w$]*)\s*\.\s*)?([A-Z][A-Z0-9_]*)", expr)
    if const:
        raw = ctx["string_constants"].get((const.group(1), const.group(2))) \
            or ctx["string_constants"].get((None, const.group(2)))
        if raw is not None:
            literal = concatenated_string_literal(raw)
            if literal is not None:
                return literal, "stringConstant"
            value, _ = evaluate_default(raw, ctx, depth + 1)
            if value is not None:
                return value, "stringConstant"
        raw = ctx["value_constants"].get((const.group(1) or ctx.get("owner"), const.group(2))) \
            or ctx["value_constants"].get((None, const.group(2)))
        if raw is not None:
            value, _ = evaluate_default(raw, ctx, depth + 1)
            if value is not None:
                return value, "constant"
    return None, None


# --------------------------------------------------------------------------
# Pass 7: what an infer function reads
# --------------------------------------------------------------------------

INFER_HELPER_SKIP = frozenset((
    "of", "ofNullable", "empty", "isPresent", "get", "getOrElse", "orElse", "map", "flatMap",
    "filter", "contains", "equals", "equalsIgnoreCase", "toString", "valueOf", "name", "key",
    "getProps", "getString", "getStringOrDefault", "getBoolean", "getBooleanOrDefault",
    "getInt", "getIntOrDefault", "getLong", "getLongOrDefault", "getDouble", "isNullOrEmpty",
    "nonEmpty", "isEmpty", "split", "trim", "toJavaFunction", "apply", "getName", "length",
    "size", "stream", "collect", "toUpperCase", "toLowerCase", "format", "startsWith",
    "endsWith", "getProperty", "containsKey", "defaultValue", "ofNullable", "orNull",
))
CONSTANT_REF_RE = re.compile(r"\b(?:([A-Z][A-Za-z0-9_$]*)\s*\.\s*)?([A-Z][A-Z0-9_]{2,})\b")


def _config_refs(text, owner_class, constant_index, imports, accessors, string_keys=None):
    keys = []
    for match in CONSTANT_REF_RE.finditer(text):
        expr = "%s.%s" % (match.group(1), match.group(2)) if match.group(1) else match.group(2)
        key = resolve_constant(expr, owner_class, constant_index, imports)
        if not key and string_keys:
            # `cfg.contains(CLEANER_COMMITS_RETAINED_KEY)`: a plain String
            # constant holding a config key, not the ConfigProperty.
            key = string_keys.get((match.group(1) or owner_class, match.group(2))) \
                or string_keys.get((None, match.group(2)))
        if key and key not in keys:
            keys.append(key)
    for match in re.finditer(r"\b([a-z][A-Za-z0-9_]*)\s*\(", text):
        key = accessors.get(match.group(1))
        if key and key not in keys:
            keys.append(key)
    return keys


def collect_infer_sources(repo_root, entries, constant_index, accessors, string_constants=None):
    """key -> {at, reads, viaHelpers} for configs declared withInferFunction(...).

    The function either names the configs it reads inline -- `cfg ->
    cfg.getStringOrDefault(FileSystemViewStorageConfig.SPILLABLE_DIR)` -- or
    hands off to a helper (`HoodieTableConfigUtils::inferPartitionValueExtractorClass`,
    `DataSourceOptionsHelper.inferKeyGenClazz`). Helpers are followed one hop.
    """
    pending = []
    helper_names = set()
    file_cache = {}
    config_keys = {e["key"] for e in entries if e.get("key")}
    string_keys = {}
    for ref, value in (string_constants or {}).items():
        literal = value.strip()
        if len(literal) >= 2 and literal[0] == literal[-1] == '"' and literal[1:-1] in config_keys:
            string_keys[ref] = literal[1:-1]

    def load(rel):
        if rel not in file_cache:
            path = os.path.join(repo_root, rel)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    original = handle.read()
            except OSError:
                original = ""
            is_scala = rel.endswith(".scala")
            file_cache[rel] = (original, strip_comments_and_strings(original, scala=is_scala),
                               static_imports(original))
        return file_cache[rel]

    for entry in entries:
        if not entry.get("hasInferFunction") or not entry.get("key"):
            continue
        declared = entry["declaredIn"]
        original, masked, imports = load(declared["file"])
        if not masked:
            continue
        start = sum(len(line) + 1 for line in masked.split("\n")[:declared["line"] - 1])
        call = re.compile(r"\.\s*withInferFunction\s*\(").search(masked, start)
        if not call or call.start() - start > 4000:
            continue
        arg_text, _ = extract_call_args(masked, call.end() - 1)
        arg_text = (arg_text or "").strip()
        at = "%s (%s:%d)" % (declared.get("class") or "?", declared["file"],
                             line_of(original, call.start()))
        # `withInferFunction(keyGeneratorInferFunc)`: follow the val to its body.
        if re.fullmatch(r"[A-Za-z_$][\w$]*", arg_text):
            definition = re.search(r"\b(?:val|var|def)\s+%s\b[^=]*=" % re.escape(arg_text), masked) \
                or re.search(r"\b%s\s*=" % re.escape(arg_text), masked)
            if definition:
                if declared["file"].endswith(".scala"):
                    end = find_scala_statement_end(masked, definition.end())
                else:
                    end = find_statement_end(masked, definition.end())
                if end < 0 or end - definition.end() > 3000:
                    end = min(len(masked), definition.end() + 600)
                arg_text = masked[definition.end():end]
        helpers = set()
        for match in re.finditer(r"(?:::|\.)\s*([a-z][A-Za-z0-9_]*)\b", arg_text):
            if match.group(1) not in INFER_HELPER_SKIP and match.group(1) not in accessors:
                helpers.add(match.group(1))
        helper_names |= helpers
        pending.append((entry, arg_text, helpers, at, declared.get("class"), imports))

    # One hop into the helpers: find each by name across the tree.
    helper_bodies = defaultdict(list)
    if helper_names:
        name_re = re.compile(r"\b(?:%s)\b" % "|".join(sorted(map(re.escape, helper_names))))
        for file_path in walk_source_files(repo_root, (".java", ".scala")):
            if SOURCE_DIR_MARKER not in file_path:
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                    original = handle.read()
            except OSError:
                continue
            if not name_re.search(original):
                continue
            is_scala = file_path.endswith(".scala")
            masked = strip_comments_and_strings(original, scala=is_scala)
            class_match = (SCALA_CLASS_DECL_RE if is_scala else CLASS_DECL_RE).search(masked)
            owner = class_match.group(1) if class_match else None
            imports = static_imports(original)
            relative = os.path.relpath(file_path, repo_root)
            spans = (find_scala_method_spans(masked, original) if is_scala else
                     ((n, s, e, l) for n, s, e, l in find_method_bodies(masked, original)))
            for name, body_start, body_end, line in spans:
                if name in helper_names:
                    helper_bodies[name].append((masked[body_start:body_end], owner, imports,
                                                "%s.%s (%s:%d)" % (owner or "?", name, relative, line)))

    def helpers_in(text):
        return {m.group(1) for m in re.finditer(r"(?:::|\.|\b)([a-z][A-Za-z0-9_]*)\s*\(", text)
                if m.group(1) not in INFER_HELPER_SKIP and m.group(1) not in accessors}

    # Second hop: a helper that only dispatches to another helper
    # (inferKeyGenClazz -> inferKeyGeneratorTypeFromWriteConfig).
    second = set()
    for name in list(helper_bodies):
        for body, _, _, _ in helper_bodies[name]:
            second |= helpers_in(body) - set(helper_bodies)
    if second:
        name_re = re.compile(r"\b(?:%s)\b" % "|".join(sorted(map(re.escape, second))))
        for file_path in walk_source_files(repo_root, (".java", ".scala")):
            if SOURCE_DIR_MARKER not in file_path:
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                    original = handle.read()
            except OSError:
                continue
            if not name_re.search(original):
                continue
            is_scala = file_path.endswith(".scala")
            masked = strip_comments_and_strings(original, scala=is_scala)
            class_match = (SCALA_CLASS_DECL_RE if is_scala else CLASS_DECL_RE).search(masked)
            owner = class_match.group(1) if class_match else None
            imports = static_imports(original)
            relative = os.path.relpath(file_path, repo_root)
            spans = (find_scala_method_spans(masked, original) if is_scala else
                     find_method_bodies(masked, original))
            for name, body_start, body_end, line in spans:
                if name in second:
                    helper_bodies[name].append((masked[body_start:body_end], owner, imports,
                                                "%s.%s (%s:%d)" % (owner or "?", name, relative, line)))

    result = {}
    for entry, arg_text, helpers, at, owner, imports in pending:
        key = entry["key"]
        reads = [k for k in _config_refs(arg_text, owner, constant_index, imports, accessors)
                 if k != key]
        via = []
        reads = [k for k in _config_refs(arg_text, owner, constant_index, imports, accessors, string_keys)
                 if k != key]
        frontier, visited = sorted(helpers), set()
        for _hop in range(2):
            following = []
            for helper in frontier:
                if helper in visited:
                    continue
                visited.add(helper)
                bodies = helper_bodies.get(helper, [])
                if not bodies or len(bodies) > 3:
                    continue
                for body, body_owner, body_imports, where in bodies:
                    found = [k for k in _config_refs(body, body_owner, constant_index, body_imports,
                                                     accessors, string_keys) if k != key]
                    if found:
                        via.append(where)
                        for k in found:
                            if k not in reads:
                                reads.append(k)
                    following += sorted(helpers_in(body))
            frontier = following
        result[key] = OrderedDict([("at", at), ("reads", reads[:15]), ("viaHelpers", via[:5])])
    return result


# --------------------------------------------------------------------------
# Pass 6: implementations that ship for class-valued configs
# --------------------------------------------------------------------------

CLASS_VALUED_KEY_RE = re.compile(r"\.(?:class|classes|provider|impl|impls)$|\.class\.name$")
JAVA_TYPE_DECL_RE = re.compile(
    r"\b(?P<mods>(?:(?:public|protected|private|static|final|abstract|sealed|non-sealed)\s+)*)"
    r"(?P<kind>class|interface|enum|record)\s+(?P<name>[A-Z][A-Za-z0-9_$]*)(?P<rest>[^{;]*)\{")
SCALA_TYPE_DECL_RE = re.compile(
    r"\b(?P<mods>(?:(?:abstract|final|sealed|case|private|protected)\s+)*)"
    r"(?P<kind>class|trait|object)\s+(?P<name>[A-Z][A-Za-z0-9_$]*)(?P<rest>[^{\n]*)")
PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
GENERIC_SUPERTYPES = frozenset((
    "Serializable", "Closeable", "AutoCloseable", "Object", "Comparable", "Cloneable",
    "Iterable", "Iterator", "Function", "Supplier", "Runnable", "Callable", "HoodieConfig",
    "Configurable", "Product", "Logging", "SparkAdapterSupport", "Enum",
))
CLASS_DOC_RE = re.compile(
    r"(?:subclass(?:es)? of|implementations? of|implement(?:s|ing)?|extend(?:s|ing)?|instances? of|"
    r"type of|class of)\s+`?(?:the\s+)?(?P<pkg>(?:[a-z][\w]*\.)*)(?P<name>[A-Z][A-Za-z0-9_$]*)")
# Implementations in these modules are samples and test harnesses, not something
# to recommend to an operator.
SAMPLE_MODULES = frozenset(("hudi-examples", "hudi-integ-test", "hudi-cli"))


def _strip_generics(text):
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"<[^<>]*>", "", text)
        text = re.sub(r"\[[^\[\]]*\]", "", text)
    return text


def collect_type_hierarchy(repo_root):
    """name -> {fqn, parents, concrete} for every top-level and nested type."""
    types = {}
    for file_path in walk_source_files(repo_root, (".java", ".scala")):
        if SOURCE_DIR_MARKER not in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                original = handle.read()
        except OSError:
            continue
        is_scala = file_path.endswith(".scala")
        masked = strip_comments_and_strings(original, scala=is_scala)
        package = PACKAGE_RE.search(masked)
        package = package.group(1) if package else ""
        pattern = SCALA_TYPE_DECL_RE if is_scala else JAVA_TYPE_DECL_RE
        for match in pattern.finditer(masked):
            name, kind, mods = match.group("name"), match.group("kind"), match.group("mods")
            rest = _strip_generics(match.group("rest"))
            rest = re.sub(r"\([^()]*\)", "", rest)
            parents = []
            if is_scala:
                ext = re.search(r"\bextends\s+(.*)", rest)
                if ext:
                    parents = [p.strip().split(".")[-1] for p in
                               re.split(r"\bwith\b", ext.group(1)) if p.strip()]
            else:
                for clause in ("extends", "implements"):
                    found = re.search(r"\b%s\s+([\w.$,\s]+?)(?:\bimplements\b|\bpermits\b|$)" % clause, rest)
                    if found:
                        parents += [p.strip().split(".")[-1] for p in found.group(1).split(",") if p.strip()]
            parents = [re.sub(r"\W.*$", "", p) for p in parents if p]
            concrete = kind in ("class", "record") and "abstract" not in mods
            if name in types:
                # Same simple name in two packages: keep both parents, mark ambiguous.
                types[name]["parents"] = sorted(set(types[name]["parents"]) | set(parents))
                types[name]["ambiguous"] = True
                types[name]["fqns"].append("%s.%s" % (package, name) if package else name)
                continue
            types[name] = {
                "fqn": "%s.%s" % (package, name) if package else name,
                "parents": parents,
                "concrete": concrete,
                "kind": kind,
                "module": module_of(os.path.relpath(file_path, repo_root)),
                "fqns": ["%s.%s" % (package, name) if package else name],
            }
    return types


def _descendants(base, children):
    seen, stack = set(), [base]
    while stack:
        for child in children.get(stack.pop(), ()):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def collect_known_implementations(entries, types):
    """key -> {baseType, baseTypeFrom, classes} for class-valued configs."""
    children = defaultdict(set)
    for name, info in types.items():
        for parent in info["parents"]:
            children[parent].add(name)
    result = {}
    for entry in entries:
        key = entry.get("key") or ""
        default = str(entry.get("defaultValue") or "")
        default_class = None
        m = re.search(r"(?:classOf\[)?([A-Z][A-Za-z0-9_$]*)(?:\])?(?:\.class)?\s*\.\s*getName", default) \
            or re.fullmatch(r"(?:[a-z][\w]*\.)+([A-Z][A-Za-z0-9_$]*)", default.strip())
        if m:
            default_class = m.group(1)
        if not (CLASS_VALUED_KEY_RE.search(key) or default_class):
            continue
        if entry.get("enumDocumentation") or entry.get("validValues"):
            continue
        candidates = []
        doc = entry.get("documentation") or ""
        doc_fqn = {}
        for doc_match in CLASS_DOC_RE.finditer(doc):
            candidates.append((doc_match.group("name"), "documentation"))
            if doc_match.group("pkg"):
                doc_fqn[doc_match.group("name")] = doc_match.group("pkg") + doc_match.group("name")
        if default_class and default_class in types:
            # Walk up from the default; the first ancestor with several concrete
            # descendants is the extension point.
            frontier = list(types[default_class]["parents"])
            seen = set()
            while frontier:
                parent = frontier.pop(0)
                if parent in seen:
                    continue
                seen.add(parent)
                candidates.append((parent, "defaultValue ancestry"))
                if parent in types:
                    frontier += types[parent]["parents"]
        for base, source in candidates:
            if base in GENERIC_SUPERTYPES or base not in types:
                continue
            concrete = sorted(types[c]["fqn"] for c in _descendants(base, children)
                              if types[c]["concrete"] and types[c]["module"] not in SAMPLE_MODULES)
            if len(concrete) < 2 and not (source == "documentation" and concrete):
                continue
            base_fqn = doc_fqn.get(base) or types[base]["fqn"]
            record = OrderedDict([
                ("baseType", base_fqn),
                ("baseTypeFrom", source),
                ("count", len(concrete)),
                ("classes", concrete[:30]),
            ])
            if types[base].get("ambiguous"):
                # Hierarchy is by simple name; two types share this one, so the
                # list may mix implementations of both.
                record["baseTypeAmbiguous"] = sorted(types[base]["fqns"])
            result[key] = record
            break
    return result


# --------------------------------------------------------------------------
# Assembly and output
# --------------------------------------------------------------------------

def read_project_version(repo_root):
    pom = os.path.join(repo_root, "pom.xml")
    try:
        with open(pom, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return None
    # The project's own version is the first <version> after the hudi artifactId.
    anchor = text.find("<artifactId>hudi</artifactId>")
    if anchor < 0:
        anchor = 0
    match = re.search(r"<version>([^<]+)</version>", text[anchor:])
    return match.group(1).strip() if match else None


def read_git_sha(repo_root):
    try:
        output = subprocess.run(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=False)
        return output.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def module_of(relative_path):
    return relative_path.split(os.sep, 1)[0] if os.sep in relative_path else relative_path


def build_catalog(repo_root, verbose=False):
    entries, constant_index, aliases, decl_stats = collect_declarations(repo_root, verbose)
    if verbose:
        print("  declarations parsed: %d" % len(entries), file=sys.stderr)

    accessors, accessor_sites = collect_accessors(repo_root, constant_index)
    if verbose:
        print("  accessor methods resolved: %d" % len(accessors), file=sys.stderr)

    short_circuits = collect_short_circuits(repo_root, accessors)
    if verbose:
        print("  configs with a short-circuiting wrapper: %d" % len(short_circuits),
              file=sys.stderr)

    engine_defaults, engine_stats = collect_engine_defaults(repo_root, constant_index)
    if verbose:
        print("  configs with engine-specific defaults: %d" % len(engine_defaults),
              file=sys.stderr)

    known_implementations = collect_known_implementations(
        entries, collect_type_hierarchy(repo_root))
    overrides = collect_overrides(repo_root, constant_index, accessors)
    validations = collect_validations(repo_root, constant_index, accessors,
                                      {e["key"] for e in entries if e.get("key")})
    string_constants = collect_string_constants(repo_root)
    infer_sources = collect_infer_sources(repo_root, entries, constant_index, accessors,
                                          string_constants)
    default_ctx = {
        "types": collect_type_hierarchy(repo_root),
        "constant_index": constant_index,
        "by_key": {e["key"]: e for e in entries if e.get("key")},
        "enum_values": collect_enum_string_values(repo_root),
        "string_constants": string_constants,
        "value_constants": collect_value_constants(repo_root),
    }
    call_site_defaults = collect_call_site_defaults(repo_root, constant_index)
    flink_mappings, _ = collect_flink_mappings(repo_root, constant_index)
    if verbose:
        print("  configs with a call-site default: %d" % len(call_site_defaults),
              file=sys.stderr)
        print("  configs a Flink option stands in for: %d" % len(flink_mappings),
              file=sys.stderr)

    # Merge duplicate keys (same key declared in several classes -- re-exports
    # that the alias pass could not fold, or genuinely duplicated declarations).
    by_key = OrderedDict()
    keyless = []
    for entry in entries:
        key = entry["key"]
        if not key:
            keyless.append(entry)
            continue
        if key in by_key:
            existing = by_key[key]
            # A key can be declared twice for real: Flink declares a handful of
            # shared keys as ConfigOptions while Spark declares them as a
            # ConfigProperty. The ConfigProperty form is the engine-agnostic one
            # and carries alternatives and valid values, so let it own the entry
            # and demote the other to alsoDeclaredIn.
            if (existing["builderStyle"] == "FlinkConfigOptions"
                    and entry["builderStyle"] == "ConfigProperty"):
                entry.setdefault("alsoDeclaredIn", []).extend(
                    existing.get("alsoDeclaredIn", []))
                entry["alsoDeclaredIn"].append(existing["declaredIn"])
                if not entry.get("documentation") and existing.get("documentation"):
                    entry["documentation"] = existing["documentation"]
                    entry["documentationSource"] = existing["documentationSource"]
                by_key[key] = entry
                continue
            existing.setdefault("alsoDeclaredIn", []).append(entry["declaredIn"])
            # Prefer whichever declaration carries documentation.
            if not existing.get("documentation") and entry.get("documentation"):
                existing["documentation"] = entry["documentation"]
                existing["documentationSource"] = entry["documentationSource"]
            continue
        by_key[key] = entry

    config_keys = set(by_key)
    read_data, read_stats = collect_read_sites(
        repo_root, constant_index, accessors, config_keys, verbose)

    alias_by_key = defaultdict(list)
    for alias in aliases:
        alias_by_key[alias["key"]].append(alias)

    accessor_by_key = defaultdict(list)
    for name, key in accessors.items():
        owner, rel_file, line = accessor_sites.get(name, (None, None, None))
        accessor_by_key[key].append(OrderedDict([
            ("method", name), ("class", owner), ("file", rel_file), ("line", line)]))

    configs = []
    for key in sorted(by_key):
        entry = by_key[key]
        entry["module"] = module_of(entry["declaredIn"]["file"])
        entry["accessors"] = sorted(accessor_by_key.get(key, []),
                                    key=lambda a: (a["class"] or "", a["method"]))
        entry["aliasConstants"] = alias_by_key.get(key, [])
        entry["shortCircuits"] = short_circuits.get(key, [])
        if entry["shortCircuits"]:
            entry["shortCircuitHeuristic"] = SHORT_CIRCUIT_HEURISTIC

        # Engine-specific effective defaults, alongside the declared one rather
        # than replacing it: both are facts a user may need, and which applies
        # depends on the engine they are writing with.
        override = engine_defaults.get(key)
        if override:
            resolved = OrderedDict()
            for engine, value in override["engineDefaults"].items():
                resolved[engine] = (entry["defaultValue"]
                                    if value == "(declared default)" else value)
            entry["engineDefaults"] = resolved
            if override.get("conditionalEngineDefaults"):
                entry["conditionalEngineDefaults"] = override["conditionalEngineDefaults"]
            entry["defaultIsConfigDependent"] = override["defaultIsConfigDependent"]
            entry["engineDefaultsResolvedFrom"] = override["resolvedFrom"]
            entry["engineDefaultNote"] = (
                "The builder overrides this config's declared default per engine via "
                "setDefaultValue(), which applies whenever the key is not set explicitly. "
                "For a user on a given engine the engineDefaults value is the effective "
                "default; declaredValue is not.")
        else:
            entry["engineDefaults"] = None

        # The classes a class-valued config can name, as shipped. Recovered from
        # extends/implements clauses, so a class loaded by reflection from
        # outside this tree is never listed.
        entry["knownImplementations"] = known_implementations.get(key)
        # Checks that reject a configuration naming this key. These are the
        # enforced constraints -- a write fails -- as opposed to co-occurrence.
        entry["validations"] = validations.get(key, [])
        # Places Hudi writes this key itself, replacing what the user set.
        entry["overriddenBy"] = overrides.get(key, [])
        # A computed default is a source expression nobody can paste into a config
        # file. Evaluate the shapes that can be evaluated without running Java.
        if entry.get("hasDefaultValue") and not entry.get("defaultValueIsLiteral"):
            default_ctx["owner"] = entry["declaredIn"].get("class")
            value, how = evaluate_default(entry.get("defaultValue"), default_ctx)
            if value is not None:
                entry["resolvedDefault"] = value
                entry["resolvedDefaultHow"] = how
        # What an unset value is inferred from. `reads` names the configs the
        # infer function (and up to two hops of helpers) consults.
        # The same key may be declared twice (Java and Scala) and only one of the
        # declarations carry the infer function; the merge above can keep the
        # other, so key the lookup by config, not by surviving declaration.
        entry["inferredFrom"] = infer_sources.get(key)
        if entry["inferredFrom"]:
            entry["hasInferFunction"] = True

        # A literal fallback at the read beats the declaration on that code path.
        # Only the disagreeing ones are worth a reader's attention.
        declared = normalize_default(entry.get("defaultValue"))
        differing = [site for site in call_site_defaults.get(key, [])
                     if normalize_default(site["value"]) != declared]
        entry["callSiteDefaults"] = differing[:10]
        if differing:
            entry["callSiteDefaultNote"] = (
                "These reads supply their own fallback when the key is unset, and it differs "
                "from the declared default. On the cited code path the declared default is "
                "not what the user gets. Open the site to see which path (table version, "
                "relation class, source) it serves.")

        # A Flink job reads a Flink option in place of this key, or copies one into
        # it, so the declared default is not what a Flink writer gets.
        flink = [m for m in flink_mappings.get(key, [])
                 if not (m["flinkOption"] == key and m["flinkDefault"] is None)]
        entry["flinkOptions"] = flink
        if flink:
            entry["flinkOptionNote"] = (
                "On Flink this key is driven by a Flink option. 'fallbackKey': the job reads "
                "the Flink option and consults this key only when the Flink option is unset, so "
                "flinkDefault is the effective default. 'builder:<method>': the Flink write "
                "client copies the Flink option into this key, so with this key unset a Flink "
                "writer gets flinkDefault (valueTransformed: true means a unit conversion or "
                "other expression is applied at the cited line). An explicit hoodie.* key passed "
                "through the Flink table options is applied after the builder in FlinkWriteClients "
                "and wins; check the cited line for other builders.")

        data = read_data.get(key)
        if data:
            entry["readSites"] = sorted(
                data["readSites"], key=read_site_rank)[:MAX_READ_SITES]
            co_configs = sorted(data["coConfigs"].items(), key=lambda kv: (-kv[1], kv[0]))
            entry["coConfigs"] = [OrderedDict([("key", k), ("sharedMethods", c)])
                                  for k, c in co_configs[:MAX_CO_CONFIGS]]
            # Roll the per-site gates up, keeping provenance. A gate on its own
            # is close to useless -- "if (compactable)" means nothing without
            # the method it came from.
            gates = OrderedDict()
            # Same ranking as the read sites: a gate from the CLI's table-type
            # helper should not outrank the archiver's own condition.
            for site in sorted(data["readSites"], key=read_site_rank):
                for gate in site["gates"]:
                    where = "%s.%s (%s:%d)" % (
                        site["class"] or "?", site["method"] or "?",
                        site["file"], site["line"])
                    gates.setdefault(gate, where)
            entry["gatingConditions"] = [
                OrderedDict([("condition", gate), ("at", where)])
                for gate, where in list(gates.items())[:12]]

            # A config named inside a gate on this config is a stronger signal
            # than co-occurrence: the gate decides whether this config's read
            # happens at all. These are often invisible to the co-config pass,
            # which keys on config constants -- `getWriteConcurrencyMode() ==
            # SINGLE_WRITER` names no key, yet it is what silently replaces an
            # explicit lock provider with the in-process one. Recorded
            # separately so they are not flattened into a co-occurrence count.
            gating_refs = OrderedDict()
            for gate, where in gates.items():
                for call in ACCESSOR_REF_IN_GATE_RE.finditer(gate):
                    other = accessors.get(call.group(1))
                    if other and other != key:
                        gating_refs.setdefault(other, (call.group(1), where))
            entry["gatedBy"] = [
                OrderedDict([("key", k), ("viaAccessor", meth), ("at", where)])
                for k, (meth, where) in list(gating_refs.items())[:12]]
        else:
            entry["readSites"] = []
            entry["coConfigs"] = []
            entry["gatingConditions"] = []
            entry["gatedBy"] = []
            entry["parseWarnings"].append("no read site resolved for this config")

        # Every recorded read site sitting in the config's own declaring file
        # means no consumer was found anywhere else -- the only mentions are the
        # declaration and its own accessors. Sometimes that is a parser gap, but
        # it is also exactly what a config whose call site has been commented
        # out looks like: hoodie.datasource.read.incr.skip_cluster is fully
        # declared, documented and versioned, and its one Spark call site is
        # commented out at MergeOnReadIncrementalRelationV2.scala:231 with a
        # reference to HUDI-9672. Comments are stripped before scanning, so the
        # catalog correctly records no read -- but nothing said so out loud.
        sites = entry.get("readSites") or []
        entry["noExternalConsumer"] = bool(sites) and all(
            site["file"] == entry["declaredIn"]["file"] for site in sites)
        if entry["noExternalConsumer"]:
            entry["parseWarnings"].append(
                "every read site is in this config's own declaring file; no "
                "external consumer was found. Check whether the call site is "
                "commented out or the feature is not wired up, before "
                "describing behaviour this config may not have")

        # Say plainly how much of this config's read context was actually
        # recovered. A Scala-only config has locations but no method, no
        # co-configs and no gates -- which must not read as "nothing gates it".
        scala_sites = sum(1 for site in entry["readSites"]
                          if site.get("via") == "scalaReference")
        unresolved = sum(1 for site in entry["readSites"] if not site.get("gatesResolved"))
        entry["scalaReadSites"] = scala_sites
        entry["readContextResolved"] = bool(entry["readSites"]) and unresolved == 0
        if scala_sites:
            entry["readContextNote"] = (
                "%d of %d recorded read sites are in Scala (%d with no enclosing def found). "
                "Scala gating is shallower than Java's: `if` blocks and `&&`/`||` "
                "conjunctions and `match` arms are recovered, for-comprehension guards are not. Absence of a "
                "gate at a Scala site is weak evidence; check the cited line."
                % (scala_sites, len(entry["readSites"]), unresolved))
        entry["gatingHeuristic"] = (
            "Conditions are recovered by text matching on enclosing if/switch blocks. "
            "They indicate where a read is conditional; they are not a complete or "
            "verified account of when the config takes effect. Confirm at the cited line.")
        configs.append(entry)

    for entry in keyless:
        entry["module"] = module_of(entry["declaredIn"]["file"])
        entry["readSites"] = []
        entry["coConfigs"] = []
        entry["gatingConditions"] = []
        entry["gatedBy"] = []
        entry["scalaReadSites"] = 0
        entry["readContextResolved"] = False
        entry["accessors"] = []
        entry["aliasConstants"] = []
        entry["shortCircuits"] = []
        entry["callSiteDefaults"] = []
        entry["flinkOptions"] = []
        entry["knownImplementations"] = None
        entry["inferredFrom"] = None
        entry["validations"] = []
        entry["overriddenBy"] = []
        configs.append(entry)

    stats = {
        "declarationsSeen": decl_stats["declarationsSeen"],
        "distinctKeys": len(by_key),
        "keylessDeclarations": len(keyless),
        "aliasesResolved": decl_stats["aliasesResolved"],
        "aliasesUnresolved": decl_stats["aliasesUnresolved"],
        "flinkOptionsSkipped": decl_stats["flinkOptionsSkipped"],
        "accessorsResolved": len(accessors),
        "readSites": read_stats["readSites"],
        "readSitesCapped": read_stats["readSitesCapped"],
        "scalaDeclarations": decl_stats["scalaDeclarationsParsed"],
        "scalaReadSites": read_stats["scalaReadSites"],
        "configsWithEngineDefaults": len(engine_defaults),
        "configsWithCallSiteDefaults": sum(1 for c in configs if c.get("callSiteDefaults")),
        "configsWithFlinkOptions": sum(1 for c in configs if c.get("flinkOptions")),
        "configsWithKnownImplementations": sum(1 for c in configs if c.get("knownImplementations")),
        "configsWithValidations": sum(1 for c in configs if c.get("validations")),
        "configsWithOverrides": sum(1 for c in configs if c.get("overriddenBy")),
        "configsWithConfigDependentDefaults": sum(
            1 for record in engine_defaults.values()
            if record.get("defaultIsConfigDependent")),
    }
    return configs, stats


def write_summary(configs, stats, catalog, out_path):
    by_group = defaultdict(int)
    by_module = defaultdict(int)
    advanced = 0
    deprecated = 0
    documented = 0
    with_reads = 0
    with_gates = 0
    scala_declared = 0
    with_engine_defaults = 0
    config_dependent = 0
    for entry in configs:
        by_group[entry.get("configGroup") or "(unknown)"] += 1
        by_module[entry.get("module") or "(unknown)"] += 1
        advanced += 1 if entry.get("advanced") else 0
        deprecated += 1 if entry.get("deprecatedAfter") else 0
        documented += 1 if entry.get("documentation") else 0
        with_reads += 1 if entry.get("readSites") else 0
        with_gates += 1 if entry.get("gatingConditions") else 0
        scala_declared += 1 if entry.get("language") == "scala" else 0
        with_engine_defaults += 1 if entry.get("engineDefaults") else 0
        config_dependent += 1 if entry.get("defaultIsConfigDependent") else 0

    lines = []
    lines.append("<!--")
    lines.append("Licensed to the Apache Software Foundation (ASF) under one")
    lines.append("or more contributor license agreements.  See the NOTICE file")
    lines.append("distributed with this work for additional information")
    lines.append("regarding copyright ownership.  The ASF licenses this file")
    lines.append("to you under the Apache License, Version 2.0 (the")
    lines.append('"License"); you may not use this file except in compliance')
    lines.append("with the License.  You may obtain a copy of the License at")
    lines.append("")
    lines.append("   http://www.apache.org/licenses/LICENSE-2.0")
    lines.append("")
    lines.append("Unless required by applicable law or agreed to in writing, software")
    lines.append('distributed under the License is distributed on an "AS IS" BASIS,')
    lines.append("WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.")
    lines.append("See the License for the specific language governing permissions and")
    lines.append("limitations under the License.")
    lines.append("-->")
    lines.append("")
    lines.append("# Config catalog summary")
    lines.append("")
    lines.append("Generated by `scripts/generate_config_catalog.py`. Do not edit by hand.")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| Hudi version | `%s` |" % catalog["hudiVersion"])
    lines.append("| Source commit | `%s` |" % catalog["generatedFrom"])
    lines.append("| Distinct config keys | %d |" % len(configs))
    lines.append("| Declared in Scala | %d |" % scala_declared)
    lines.append("| With engine-specific defaults | %d |" % with_engine_defaults)
    lines.append("| Whose default is also config-dependent | %d |" % config_dependent)
    lines.append("| Advanced | %d |" % advanced)
    lines.append("| Deprecated | %d |" % deprecated)
    lines.append("| With documentation text | %d |" % documented)
    lines.append("| With at least one read site | %d |" % with_reads)
    lines.append("| With at least one gating condition | %d |" % with_gates)
    lines.append("| Read sites recorded | %d |" % stats["readSites"])
    lines.append("| Accessor methods resolved | %d |" % stats["accessorsResolved"])
    lines.append("")
    engine_rows = [entry for entry in configs if entry.get("engineDefaults")]
    if engine_rows:
        lines.append("## Engine-specific effective defaults")
        lines.append("")
        lines.append("For these configs the builder overrides the declared default per engine, so "
                     "`defaultValue` alone is not what a user gets. `(conditional)` means that "
                     "engine's default branches on another config or on the runtime; see "
                     "`conditionalEngineDefaults` in the catalog.")
        lines.append("")
        lines.append("| Config | Declared | Spark | Flink | Java |")
        lines.append("|---|---|---|---|---|")
        for entry in engine_rows:
            conditional = entry.get("conditionalEngineDefaults") or {}
            cells = []
            for engine in ("spark", "flink", "java"):
                if engine in conditional:
                    cells.append("_(conditional)_")
                else:
                    value = entry["engineDefaults"].get(engine)
                    cells.append("`%s`" % value if value is not None else "_(unresolved)_")
            declared = entry.get("defaultValue")
            lines.append("| `%s` | %s | %s | %s | %s |" % (
                entry["key"],
                "`%s`" % declared if declared is not None else "_(none)_",
                cells[0], cells[1], cells[2]))
        lines.append("")

    lines.append("## By module")
    lines.append("")
    lines.append("| Module | Configs |")
    lines.append("|---|---|")
    for module, count in sorted(by_module.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append("| `%s` | %d |" % (module, count))
    lines.append("")
    lines.append("## By config group")
    lines.append("")
    lines.append("| Group | Configs |")
    lines.append("|---|---|")
    for group, count in sorted(by_group.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append("| `%s` | %d |" % (group, count))
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo-root",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="Hudi checkout to scan (default: the repo this script lives in)")
    parser.add_argument(
        "--out-dir", default=None,
        help="Where to write config-catalog.json and config-catalog-summary.md "
             "(default: hudi-ai-operator/skills/hudi-config-consultant)")
    parser.add_argument("--verbose", action="store_true", help="Per-pass progress on stderr")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    out_dir = args.out_dir or os.path.join(
        repo_root, "hudi-ai-operator", "skills", "hudi-config-consultant")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.verbose:
        print("Scanning %s" % repo_root, file=sys.stderr)
    configs, stats = build_catalog(repo_root, args.verbose)

    catalog = OrderedDict([
        # 2: adds engineDefaults / conditionalEngineDefaults, and Scala-declared
        # configs with their readContextResolved honesty flag.
        ("schemaVersion", 4),
        ("hudiVersion", read_project_version(repo_root)),
        ("generatedFrom", read_git_sha(repo_root)),
        ("configs", configs),
    ])

    json_path = os.path.join(out_dir, "config-catalog.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, sort_keys=False, ensure_ascii=False)
        handle.write("\n")

    summary_path = os.path.join(out_dir, "config-catalog-summary.md")
    write_summary(configs, stats, catalog, summary_path)

    fully = sum(1 for c in configs if not c["parseWarnings"])
    partially = len(configs) - fully
    with_reads = sum(1 for c in configs if c["readSites"])
    with_co = sum(1 for c in configs if c["coConfigs"])
    with_gates = sum(1 for c in configs if c["gatingConditions"])

    print("Hudi version      : %s" % catalog["hudiVersion"])
    print("Source commit     : %s" % catalog["generatedFrom"])
    print("Declarations seen : %d" % stats["declarationsSeen"])
    print("Distinct configs  : %d" % len(configs))
    print("  fully parsed    : %d" % fully)
    print("  with warnings   : %d" % partially)
    print("  declared in Scala: %d" % stats["scalaDeclarations"])
    print("Engine defaults   : %d configs (%d also config-dependent)"
          % (stats["configsWithEngineDefaults"],
             stats["configsWithConfigDependentDefaults"]))
    print("Call-site defaults: %d configs read with a fallback that differs from the declared default"
          % stats["configsWithCallSiteDefaults"])
    print("Flink options     : %d configs driven by a Flink option on Flink" % stats["configsWithFlinkOptions"])
    print("Implementations   : %d class-valued configs with shipped implementations listed"
          % stats["configsWithKnownImplementations"])
    print("Validations       : %d configs named by a check that rejects a configuration"
          % stats["configsWithValidations"])
    print("Overrides         : %d configs Hudi itself overwrites somewhere"
          % stats["configsWithOverrides"])
    print("Aliases resolved  : %d (unresolved %d)"
          % (stats["aliasesResolved"], stats["aliasesUnresolved"]))
    print("Accessors         : %d" % stats["accessorsResolved"])
    print("Read sites        : %d across %d configs (%d configs capped at %d)"
          % (stats["readSites"], with_reads, stats["readSitesCapped"], MAX_READ_SITES))
    print("Co-configs        : %d configs have at least one" % with_co)
    print("Gating conditions : %d configs have at least one" % with_gates)
    print("Wrote %s" % json_path)
    print("Wrote %s" % summary_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
