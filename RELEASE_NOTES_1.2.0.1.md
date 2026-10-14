
<!--
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Apache Hudi 1.2.0.1 Release Notes

1.2.0.1 is a patch release on top of 1.2.0. It backports two correctness fixes from master. Neither fix
changes the table version or the storage format.

## Fixes

### Single-field ComplexKeyGenerator record keys across upgrades ([HUDI-9666](https://issues.apache.org/jira/browse/HUDI-9666))

Backports [#19304](https://github.com/apache/hudi/pull/19304) and its follow-up [#20063](https://github.com/apache/hudi/pull/20063).

**Problem.** Tables written by 0.14.1, 0.15.0 or 1.0.0 - 1.0.2 that use `ComplexKeyGenerator` with a single
record key field store `_hoodie_record_key` as the bare value (`<value>`). All other versions store `<field>:<value>`.
From table version 9 the encoding was derived from the table version alone. A table that crossed the 8 to 9
upgrade then keyed new writes as `<field>:<value>`, the upsert index missed the existing records, and every
update was written as a duplicate insert.

**Fix.**
- New table property `hoodie.table.complex.keygenerator.encoding`, with values `FIELD_PREFIXED` or `VALUE_ONLY`.
  It records the encoding the table's data actually uses, and every writer key generator and reader-side
  record-level index / bloom filter lookup follows it, on every table version.
- New tables record `FIELD_PREFIXED`.
- An existing table without the property gets it on its next write or upgrade. The value is deduced from the
  record keys of its most recently written data file.
- Covered for the Spark datasource and Spark SQL, Hudi Streamer, the Java write client and Flink.
- Follow-up (#20063):
  - `upgrade_table`, the hudi-cli upgrade and `rollback_to_instant` read the table's own timeline layout.
  - The encoding is no longer deduced from an empty timeline left by an upgrade that did not finish.

**Notes.**
- The property is written to `hoodie.properties` and kept across upgrades and downgrades. Readers on 1.2.0 and
  older ignore it.
- The deduction inspects only the most recently written data file. A table that already contains both
  encodings is not repaired by it.

### Incremental fallback reads with a stale non-write instant ([#20286](https://github.com/apache/hudi/issues/20286))

Backports [#20273](https://github.com/apache/hudi/pull/20273).

**Problem.** An incremental query with `hoodie.datasource.read.incr.fallback.fulltablescan.enable=true` whose
start instant is archived returned no rows, or only the rows of some partitions, with no error. This happened
when a completed rollback or clean older than every active commit was still on the active timeline. That is
common on tables written by 0.14.x, whose archiver keeps a lone rollback long after the commits around it are
archived.

**Fix.**
- The file index decides whether the start instant is archived from the completed write timeline, the same
  timeline it reads written partitions from, instead of the whole active timeline.
- `CompletionTimeQueryViewV2` (table version 8 and above) treats an instant as archived when it is older than
  the first active write instant that is not savepointed. It now loads the archived commits that sit behind a
  stale rollback or clean, and behind a savepointed commit when archival beyond savepoint is enabled.
- `IncrementalQueryAnalyzer` splits archived and active instants one by one and orders the result by instant
  time, since they can interleave around a savepointed commit.

## Known issues

- **Archived-timeline migration during an upgrade to table version 8.** Upgrading a table at version 6 or 7
  to version 8 or above rewrites its archived timeline into new history files. Each file is named after the
  first and last instant of its batch rather than the smallest and largest. When a batch spans several old
  archive files, the name can understate the instants the file holds, and archived-timeline range lookups can
  skip it. Incremental reads whose window starts in the archived history of such an upgraded table can then
  miss commits. Tables that stay at version 6 and tables created on 1.x are not affected. This is not fixed in
  1.2.0.1, and master has the same behavior.

## Upgrading

No table version change and no configuration change is required. Replace the 1.2.0 bundles with 1.2.0.1.
