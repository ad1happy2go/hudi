#!/usr/bin/env python3
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Unit tests for the catalog generator's text heuristics, on small snippets.

Fast (no tree walk). Each case is a shape the generator once got wrong.

    python3 scripts/test_generate_config_catalog_units.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_config_catalog as g  # noqa: E402


def mask(text, scala=False):
    return g.strip_comments_and_strings(text, scala=scala)


class ReceiverHint(unittest.TestCase):

    def setUp(self):
        g.AMBIGUOUS_ACCESSORS.clear()
        g.AMBIGUOUS_ACCESSORS["getTableType"] = {
            "HoodieWriteConfig": "hoodie.table.type",
            "DeltaConfig": "hoodie.datasource.write.table.type",
        }
        g.AMBIGUOUS_ACCESSORS["getBloomFilterType"] = {
            "HoodieWriteConfig": "hoodie.bloom.index.filter.type",
            "HoodieMetadataConfig": "hoodie.metadata.bloom.filter.type",
        }

    def tearDown(self):
        g.AMBIGUOUS_ACCESSORS.clear()

    def test_receiver_ending_in_a_call(self):
        key = g.accessor_key_for_receiver(
            "getBloomFilterType", "    x = writeConfig.getMetadataConfig().", "default")
        self.assertEqual(key, "hoodie.metadata.bloom.filter.type")

    def test_plain_receiver_keeps_default(self):
        key = g.accessor_key_for_receiver("getBloomFilterType", "    x = config.", "default")
        self.assertEqual(key, "default")


class Gates(unittest.TestCase):

    def test_braceless_if_does_not_gate_the_else_branch(self):
        text = "def f() = { val p = if (useA) conf.a else config.getFoo }"
        masked = mask(text, scala=True)
        site = masked.index("getFoo")
        self.assertEqual(g.enclosing_gates(masked, 0, site), [])
        site_then = masked.index("conf.a")
        self.assertEqual(g.enclosing_gates(masked, 0, site_then), ["if (useA)"])

    def test_else_if_arm_is_not_a_guard(self):
        text = ("int f() {\n  if (a) {\n    x();\n  } else if (b) {\n    return 1;\n  }\n"
                "  return cfg.getFoo();\n}")
        masked = mask(text)
        lo, hi = masked.index("{"), len(masked) - 1
        site = masked.index("getFoo")
        self.assertNotIn("unless (b)", g.guard_clauses(masked, lo, hi, site))

    def test_plain_guard_is_recorded(self):
        text = "int f() {\n  if (done) {\n    return 0;\n  }\n  return cfg.getFoo();\n}"
        masked = mask(text)
        lo, hi = masked.index("{"), len(masked) - 1
        self.assertEqual(g.guard_clauses(masked, lo, hi, masked.index("getFoo")), ["unless (done)"])

    def test_guard_cache_is_per_text(self):
        a = mask("int f() {\n  if (x) {\n    return 0;\n  }\n  return cfg.getFoo();\n}")
        b = mask("int f() {\n  if (y) {\n    return 0;\n  }\n  return cfg.getFoo();\n}")
        lo_a, lo_b = a.index("{"), b.index("{")
        self.assertEqual(g.guard_clauses(a, lo_a, len(a) - 1, a.index("getFoo")), ["unless (x)"])
        self.assertEqual(g.guard_clauses(b, lo_b, len(b) - 1, b.index("getFoo")), ["unless (y)"])

    def test_java_if_conjunction_is_balanced(self):
        text = "void f() {\n  if (a &&\n      cfg.isFoo()) {\n    go();\n  }\n}"
        masked = mask(text)
        gate = g.conjunction_gate(masked, 0, len(masked), masked.index("isFoo"))
        self.assertIsNotNone(gate)
        self.assertEqual(gate.count("("), gate.count(")"), gate)

    def test_scala_equality_names_the_accessor(self):
        refs = [m.group(1) for m in
                g.ACCESSOR_REF_IN_GATE_RE.finditer("if (writeConfig.getTableType == MERGE_ON_READ)")]
        self.assertIn("getTableType", refs)
        refs = [m.group(1) for m in g.ACCESSOR_REF_IN_GATE_RE.finditer("tableType = x")]
        self.assertNotIn("tableType", refs)


class ScalaSpans(unittest.TestCase):

    def test_last_def_stops_at_its_class(self):
        text = ("class A {\n  def f(): Int = {\n    1\n  }\n}\n\n"
                "object B {\n  val x = conf.getOrElse(SOME.key, \"a\")\n}\n")
        masked = mask(text, scala=True)
        spans = list(g.find_scala_method_spans(masked, text))
        f = [s for s in spans if s[0] == "f"][0]
        self.assertLess(f[2], masked.index("object B"))


class Defaults(unittest.TestCase):

    def ctx(self):
        return {"types": {"HoodieFileFormat": {"kind": "enum", "fqn": "x.HoodieFileFormat"},
                          "SomeConfig": {"kind": "class", "fqn": "x.SomeConfig"}},
                "constant_index": {}, "by_key": {}, "enum_values": {},
                "string_constants": {}, "value_constants": {}}

    def test_enum_constant_resolves(self):
        self.assertEqual(g.evaluate_default("HoodieFileFormat.PARQUET", self.ctx())[0], "PARQUET")

    def test_unknown_class_constant_is_not_returned_as_its_name(self):
        self.assertEqual(g.evaluate_default("SomeConfig.DEFAULT_MAX_SIZE", self.ctx()), (None, None))

    def test_null_like_defaults_compare_equal(self):
        self.assertIsNone(g.normalize_default("(RecordMergeMode) null"))
        self.assertEqual(g.normalize_default('"10"'), g.normalize_default("10L"))


class Constants(unittest.TestCase):

    def test_unknown_qualifier_does_not_take_an_ambiguous_bare_name(self):
        index = {("HoodieTableConfig", "TYPE"): "hoodie.table.type",
                 ("OtherConfig", "TYPE"): "hoodie.other.type",
                 (None, "TYPE"): "hoodie.other.type"}
        self.assertIsNone(g.resolve_constant("json.TYPE", None, index))
        self.assertEqual(g.resolve_constant("HoodieTableConfig.TYPE", None, index), "hoodie.table.type")


class Shadowing(unittest.TestCase):

    def test_local_constant_shadows_config_name(self):
        masked = mask('class J {\n  private static final String TYPE = "type";\n}')
        self.assertIn("TYPE", g.local_constants(masked))

    def test_config_property_is_not_a_local_constant(self):
        masked = mask('class C {\n  public static final ConfigProperty<String> TYPE = ConfigProperty.key("x");\n}')
        self.assertNotIn("TYPE", g.local_constants(masked))


if __name__ == "__main__":
    unittest.main()
