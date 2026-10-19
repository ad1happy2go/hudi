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

"""Facts the config catalog must keep getting right.

Each assertion is a fact checked by hand against the source, chosen because
the generator once got it wrong or because a skill answer depends on it. When
the code it describes changes, update the assertion; when the generator
changes, these should still pass.

    python3 scripts/test_generate_config_catalog.py

Stdlib only. Builds the catalog once from this checkout (about a minute).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_config_catalog as generator  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = None


def setUpModule():
    global CATALOG
    configs, _ = generator.build_catalog(REPO_ROOT)
    CATALOG = {entry["key"]: entry for entry in configs if entry.get("key")}


def entry(key):
    assert key in CATALOG, "%s missing from the catalog" % key
    return CATALOG[key]


def gates(key):
    return [g["condition"] for g in entry(key)["gatingConditions"]]


class DeclaredFacts(unittest.TestCase):

    def test_scala_declarations_are_included(self):
        self.assertEqual(entry("hoodie.datasource.query.type")["language"], "scala")

    def test_alternatives_fold_onto_the_current_key(self):
        self.assertIn("hoodie.metadata.record.index.enable",
                      entry("hoodie.metadata.global.record.level.index.enable")["alternatives"])


class EffectiveDefaults(unittest.TestCase):

    def test_engine_default_overrides_declared(self):
        e = entry("hoodie.metadata.index.column.stats.enable")
        self.assertEqual(e["defaultValue"], "false")
        self.assertEqual(e["engineDefaults"]["spark"], "true")

    def test_call_site_default_disagrees_with_declaration(self):
        # The V1 incremental relations (table version < 8) read it with "false".
        e = entry("hoodie.datasource.read.incr.fallback.fulltablescan.enable")
        self.assertEqual(e["defaultValue"], "true")
        sites = " ".join(s["at"] for s in e["callSiteDefaults"] if s["value"] == "false")
        self.assertIn("IncrementalRelationV1", sites)
        self.assertIn("HoodieIncrSource", sites)

    def test_flink_index_default_is_flink_state(self):
        options = entry("hoodie.index.type")["flinkOptions"]
        self.assertIn(("index.type", "FLINK_STATE"),
                      [(o["flinkOption"], o["flinkDefault"]) for o in options])

    def test_flink_builder_copies_compaction_delta_commits(self):
        options = entry("hoodie.compact.inline.max.delta.commits")["flinkOptions"]
        self.assertIn("compaction.delta_commits", [o["flinkOption"] for o in options])
        # The metadata-table builder has a method of the same name; it must not leak here.
        self.assertNotIn("metadata.compaction.delta_commits", [o["flinkOption"] for o in options])

    def test_flink_cleaner_retains_thirty(self):
        options = entry("hoodie.clean.commits.retained")["flinkOptions"]
        self.assertIn(("clean.retain_commits", "30"),
                      [(o["flinkOption"], o["flinkDefault"]) for o in options])

    def test_computed_defaults_are_evaluated(self):
        self.assertEqual(entry("hoodie.parquet.max.file.size")["resolvedDefault"], "125829120")
        self.assertEqual(entry("hoodie.datasource.write.operation")["resolvedDefault"], "upsert")
        self.assertEqual(entry("hoodie.write.lock.storage.validity.timeout.secs")["resolvedDefault"], "300")
        self.assertEqual(entry("hoodie.meta.sync.client.tool.class")["resolvedDefault"],
                         "org.apache.hudi.hive.HiveSyncTool")


class ReadContext(unittest.TestCase):

    def test_scala_conjunction_gate(self):
        # Async clustering on the Spark datasource path only when inline is off.
        self.assertTrue(any("inlineClusteringEnabled" in g and "isAsyncClusteringEnabled" in g
                            for g in gates("hoodie.clustering.async.enabled")))

    def test_scala_match_arm_gate(self):
        self.assertTrue(any(g.startswith("match (queryType) case")
                            for g in gates("hoodie.datasource.query.type")))

    def test_guard_clause_gate(self):
        # Inert once the table records its key encoding.
        self.assertIn("unless (!StringUtils.isNullOrEmpty(tableEncoding))",
                      gates("hoodie.write.complex.keygen.new.encoding"))

    def test_commented_out_consumer_is_flagged(self):
        self.assertTrue(entry("hoodie.datasource.read.incr.skip_cluster")["noExternalConsumer"])

    def test_literal_key_read_is_a_read_site(self):
        # ConfigUtils reads it as props.getBoolean("hoodie.write.track.event.time.watermark", false).
        self.assertTrue(entry("hoodie.write.track.event.time.watermark")["readSites"])

    def test_statically_imported_constant_is_a_read_site(self):
        # StreamSync: import static ...HoodieErrorTableConfig.ERROR_TABLE_ENABLED.
        files = [s["file"] for s in entry("hoodie.errortable.enable")["readSites"]]
        self.assertTrue(any(f.endswith("StreamSync.java") for f in files))

    def test_ambiguous_bare_constant_is_not_misattributed(self):
        sites = [o["at"] for o in entry("hoodie.bootstrap.base.path")["flinkOptions"]]
        self.assertFalse(any("StreamerUtil" in at for at in sites))


class Relationships(unittest.TestCase):

    def test_known_lock_providers(self):
        classes = entry("hoodie.write.lock.provider")["knownImplementations"]["classes"]
        self.assertIn("org.apache.hudi.client.transaction.lock.StorageBasedLockProvider", classes)
        self.assertIn("org.apache.hudi.aws.transaction.lock.DynamoDBBasedLockProvider", classes)

    def test_infer_function_inputs(self):
        reads = entry("hoodie.clean.policy")["inferredFrom"]["reads"]
        self.assertIn("hoodie.clean.hours.retained", reads)
        reads = entry("hoodie.datasource.write.keygenerator.class")["inferredFrom"]["reads"]
        self.assertIn("hoodie.datasource.write.recordkey.field", reads)

    def test_enforced_validation_with_message(self):
        messages = [v["message"] for v in entry("hoodie.clean.failed.writes.policy")["validations"]
                    if v["kind"] == "checkArgument"]
        self.assertTrue(any("hoodie.clean.failed.writes.policy=LAZY" in m for m in messages))

    def test_warn_validation_for_archival_retention(self):
        kinds = {v["kind"] for v in entry("hoodie.keep.min.commits")["validations"]}
        self.assertIn("checkArgument", kinds)
        self.assertIn("warn", kinds)

    def test_same_named_accessor_defaults_to_write_config(self):
        # HoodieMetadataConfig also declares getWriteConcurrencyMode(); the
        # HoodieWriteConfig mapping must still attribute NBCC's requirements.
        messages = " ".join(v["message"] for v in entry("hoodie.write.concurrency.mode")["validations"])
        self.assertIn("MOR table with simple bucket index", messages)

    def test_silent_override_is_recorded(self):
        overrides = entry("hoodie.write.lock.provider")["overriddenBy"]
        self.assertTrue(any("InProcessLockProvider" in o["value"] for o in overrides))
        overrides = entry("hoodie.clean.failed.writes.policy")["overriddenBy"]
        self.assertTrue(any("LAZY" in o["value"] for o in overrides))


if __name__ == "__main__":
    unittest.main()
