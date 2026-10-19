<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Catalog schema and how to query it

## Envelope

```json
{
  "schemaVersion": 4,
  "hudiVersion": "1.3.0-SNAPSHOT",
  "generatedFrom": "<git sha of the tree it was generated from>",
  "configs": [ ... ]
}
```

`schemaVersion` 2 adds `engineDefaults` / `conditionalEngineDefaults`, the `language` field, and
the `readContextResolved` honesty flag for Scala-declared configs. `schemaVersion` 3 adds
`shortCircuits` / `shortCircuitHeuristic`, `gatedBy` and `noExternalConsumer`. `schemaVersion` 4
adds `callSiteDefaults`, `flinkOptions`, `knownImplementations`, `inferredFrom`, `resolvedDefault`, `validations` and `overriddenBy`.

`configs` is sorted by `key`, so regeneration produces a readable diff. Read `hudiVersion` and
`generatedFrom` on every query; they belong in your answer.

## A config entry

### Declared facts — extracted verbatim from the builder chain

| Field | Meaning |
|---|---|
| `key` | The property key, e.g. `hoodie.compact.inline.max.delta.commits`. |
| `keyResolution` | `literal`, `resolvedFromConstants` (key built from a `static final String` prefix), or `derivedFromConfigKey` (key built from another config's key). |
| `keyExpression` | The source expression, when the key was not a plain literal. |
| `type` | The declared type parameter: `String`, `Boolean`, `Integer`, `Long`, … `null` for a Scala `val` with no type ascription. |
| `language` | `java` or `scala`. Scala-declared configs are the `hoodie.datasource.*` keys in `DataSourceReadOptions` / `DataSourceWriteOptions`. |
| `declaredIn` | `{class, constant, file, line}` — where the `ConfigProperty` is declared. |
| `configGroup` | The owning config class, e.g. `HoodieCompactionConfig`. Use this to group related configs. |
| `module` | Top-level Maven module, e.g. `hudi-client`. |
| `hasDefaultValue` | `false` for `noDefaultValue()` configs — these are required or inferred. |
| `defaultValue` | The default, or `null`. |
| `defaultValueIsLiteral` | `false` means `defaultValue` is a **source expression**, not a value — e.g. `String.valueOf(104857600)` or `KEEP_LATEST_COMMITS.name()`. |
| `defaultValueNote` | Present when the default is computed, to say so. |
| `resolvedDefault` | The evaluated value of a computed default — arithmetic (`String.valueOf(120 * 1024 * 1024)` → `125829120`), an enum constant (`HoodieFileFormat.PARQUET` → `PARQUET`), a class literal (`HiveSyncTool.class.getName()` → `org.apache.hudi.hive.HiveSyncTool`), a named constant, an enum's string or int field (`WriteOperationType.UPSERT.value` → `upsert`, `HoodieTableVersion.current().versionCode()` → `10`), or another config's default. Present only when it could be evaluated. This is the value to give a user who will paste it into a config file. |
| `resolvedDefaultHow` | Which of those it was. |
| `documentation` | The `withDocumentation` text. |
| `documentationSource` | `literal`, `resolvedFromConstants`, or `enumClass:<Name>` when the docs live on an enum. |
| `enumDocumentation` | For `enumClass` docs: `{enum, file, description, values: [{value, description}]}`. **This is where valid values and their meanings live** for strategy-style configs. |
| `validValues` | From `withValidValues`, when present. Often empty even for enum-valued configs — check `enumDocumentation` too. |
| `alternatives` | From `withAlternatives`: older key names that still work. |
| `sinceVersion`, `deprecatedAfter`, `supportedVersions` | Version metadata, when declared. |
| `advanced` | `markAdvanced()` was called. A tuning knob, not a routine setting. |
| `hasInferFunction` | Hudi may derive this value from other configs when unset. |
| `builderSteps` | The builder methods seen, in order. Useful for spotting what the parser did and did not see. |
| `parseWarnings` | Non-empty means the generator could not fully read something. Check before answering. |
| `aliasConstants` | Other Java constants that re-export the same config. |
| `alsoDeclaredIn` | Present when the same key is declared in more than one class. |

### Engine-specific effective defaults

`defaultValue` is the **declared** default. For nine configs it is not the one that takes effect: a
builder's `build()` calls `setDefaultValue(PROP, getDefaultXxx(engineType))`, which writes the
engine's value whenever the user has not set the key. For those, the engine's value is the real
default and `defaultValue` is misleading on its own.

| Field | Meaning |
|---|---|
| `engineDefaults` | `{"spark": ..., "flink": ..., "java": ...}` — the effective default per engine, or `null` when the config has no engine override. An engine absent from the object is one the generator could not resolve; do not fall back to `defaultValue` for it. |
| `conditionalEngineDefaults` | Present when an engine's default is not a fixed value. `{<engine>: {condition, whenTrue, whenFalse}}`. Report the condition, not one of the branches. |
| `defaultIsConfigDependent` | `true` when at least one engine's default branches on another config or on the runtime rather than on the engine alone. |
| `engineDefaultsResolvedFrom` | `{helper, class, file, line}` — the `setDefaultValue` call site. Cite it. |
| `engineDefaultNote` | The standing caveat for these configs. |

The nine, as generated against this tree:

| Config | Declared | Spark | Flink | Java |
|---|---|---|---|---|
| `hoodie.metadata.enable` | `true` | `true` | `true` | **`false`** |
| `hoodie.metadata.index.column.stats.enable` | `false` | **`true`** | `false` | `false` |
| `hoodie.metadata.index.secondary.enable` | `true` | `true` | **`false`** | `true` |
| `hoodie.metadata.streaming.write.enabled` | `false` | **`true`** | `false` | `false` |
| `hoodie.index.type` | *(none)* | `SIMPLE` | `INMEMORY` (but see `flinkOptions`: a Flink job gets `FLINK_STATE`) | `SIMPLE` |
| `hoodie.write.markers.type` | `TIMELINE_SERVER_BASED` | *conditional* | `DIRECT` | `DIRECT` |
| `hoodie.parquet.compression.codec` | *(none)* | *conditional* | `zstd` | `gzip` |
| `hoodie.clustering.plan.strategy.class` | Spark size-based | *conditional* | *conditional* | Java size-based |
| `hoodie.clustering.execution.strategy.class` | Spark sort-and-size | *conditional* | Java sort-and-size | Java sort-and-size |

The conditional ones:

- **markers type, Spark** — `TIMELINE_SERVER_BASED` if `writeConfig.isEmbeddedTimelineServerEnabled()`,
  else `DIRECT`.
- **parquet codec, Spark** — `zstd` on Spark 3.5+, else `gzip` (a *runtime* version check, not a
  config).
- **clustering plan and execution strategy** — the consistent-hashing bucket-index variant if
  `isConsistentHashingBucketIndex()`, else the size-based/sort-and-size one.

### Defaults supplied somewhere other than the declaration

Two more places decide what a user gets when the key is unset. Both are extracted from code, not
inferred, but each applies only on the code path it names.

| Field | Meaning |
|---|---|
| `callSiteDefaults` | Reads that pass their own literal fallback — `getOrElse(X.key, "false")`, `props.getString(X.key(), "false")` — **and that literal differs from `defaultValue`**: `{value, at}`. On that path the declared default is wrong. `hoodie.datasource.read.incr.fallback.fulltablescan.enable` declares `true`, but the V1 incremental relations (tables below version 8), `HoodieIncrSource` and `QueryRunner` read it with `false`. Always say which path each value applies to. |
| `callSiteDefaultNote` | The standing caveat, present when `callSiteDefaults` is non-empty. |
| `flinkOptions` | `{flinkOption, flinkDefault, how, at, valueTransformed?}` — a Flink job is driven by a Flink option for this key. `how: "fallbackKey"`: the Flink option declares this key in `withFallbackKeys`, so a Flink job reads the Flink option and looks at this key only when the option is unset. `how: "builder:<method>"`: a Flink write-client builder copies the Flink option into this key. Either way, **with nothing set, a Flink writer gets `flinkDefault`**, not `defaultValue` and not `engineDefaults.flink`. `valueTransformed: true` means the cited line converts it (MB to bytes, an enum `valueOf`). |
| `flinkOptionNote` | The standing caveat, present when `flinkOptions` is non-empty. |
| `inferredFrom` | For `hasInferFunction: true`: `{at, reads, viaHelpers}`. `reads` are the configs the infer function consults, directly or through up to two hops of helper methods (`viaHelpers` cites them). The inferred value replaces the declared default whenever the key is unset, so `hoodie.clean.policy` becomes `KEEP_LATEST_BY_HOURS` when only `hoodie.clean.hours.retained` is set, and `hoodie.datasource.write.keygenerator.class` follows the record-key and partition-path fields. An empty `reads` means the function reads no config (environment, table state). |
| `validations` | Up to 10 checks whose condition, enclosing `if`, or message names this config: `{kind, condition, message, at, when?}`. `kind` is the claim strength — `checkArgument` / `checkState` / `throw <Exception>` are **enforced** (the write fails), `warn` is **recommended** (Hudi logs and carries on, sometimes after overriding the value). `message` is the literal text with format placeholders, so it is what the user sees in their log. Throws inside `catch` blocks are excluded as runtime failures, not checks. Sample and test-harness modules are skipped. |
| `overriddenBy` | Up to 6 places Hudi code writes this key with `setValue`/`setProperty`/`put`, replacing what the user set: `{value, at, when?}`. `setDefaultValue` (fills only an unset key), builder setters storing their own argument, copies of the same key, and upgrade/downgrade internals are excluded. `when` is the enclosing condition. `hoodie.clean.failed.writes.policy` is forced to `LAZY` whenever the concurrency mode supports multiple writers, and an explicit lock provider becomes `InProcessLockProvider` for a single writer with no async table services. Some entries configure an internal client (an indexer, a metadata writer) rather than the user's; open the site before telling a user their value was replaced. |
| `knownImplementations` | For a config that takes a class name: `{baseType, baseTypeFrom, count, classes, baseTypeAmbiguous?}`. `classes` are the fully qualified, concrete implementations of `baseType` found in this tree's `extends`/`implements` clauses (samples in `hudi-examples`, `hudi-integ-test` and `hudi-cli` left out). `baseTypeFrom` says whether the base type came from the documentation or from the default class's ancestry. `baseTypeAmbiguous` lists the packages that share the base type's simple name, so the list may mix two hierarchies. It is what ships, not what is valid: a user's own class on the classpath works too. `null` when not class-valued or not resolved. |

`flinkOptions` overrides `engineDefaults.flink` where both exist. `hoodie.index.type` has
`engineDefaults.flink = INMEMORY` from the write-config builder, but a Flink job reads `index.type`
(default `FLINK_STATE`) and passes that to the builder, so `FLINK_STATE` is what a Flink user gets.
Likewise `hoodie.compact.inline.max.delta.commits` declares `5` and a Flink job gets
`compaction.delta_commits` (also `5`) — setting the `hoodie.*` key in the Flink table options still
wins, because `FlinkWriteClients` applies the raw options after its builder steps.

### Derived context — recovered from code, heuristic

| Field | Meaning |
|---|---|
| `accessors` | Config-class methods that read this config and nothing else, e.g. `HoodieWriteConfig.getInlineCompactDeltaCommitMax`. These are what consumers actually call. |
| `readSites` | Up to 20 `{class, method, file, line, via, gatesResolved, gates}`. `via` is `constant` (the config constant is named at that line), `accessor:<name>` (the line calls a resolved accessor), or `scalaReference`. `gatesResolved: false` means gating was not analysed at that site, not that there is none. |
| `scalaReadSites` | How many of the recorded read sites are in Scala. |
| `readContextResolved` | `true` only when the config has read sites and none of them are Scala. `false` means some or all of the read context (method, co-configs, gating) was not recovered. |
| `readContextNote` | Present when `scalaReadSites > 0`, spelling out how much was not analysed. |
| `coConfigs` | Up to 25 `{key, sharedMethods}` — other configs mentioned in the same method bodies. A **co-occurrence** measure, not a declared dependency. |
| `gatingConditions` | Up to 12 `{condition, at}` — enclosing `if`/`switch` conditions, with the `class.method (file:line)` they came from. |
| `gatingHeuristic` | The standing caveat. Repeat its substance when you quote a gate. |
| `shortCircuits` | Wrapper methods that may answer without reading the key: `{method, class, file, line, viaAccessor, condition, literalReturnedFirst, verified}`. `verified` is always `false` — the shape is matched textually and the attribution is not checked. About half are real; open the `file:line` before citing one. |
| `shortCircuitHeuristic` | The standing caveat, present only when `shortCircuits` is non-empty. |
| `gatedBy` | Configs named inside this config's own gating conditions: `{key, viaAccessor, at}`. Stronger than `coConfigs` — the gate decides whether this config is read at all — and it catches companions compared as typed enums, which the co-config pass cannot see. |
| `noExternalConsumer` | `true` when every read site is in this config's own declaring file, so no consumer was found elsewhere. Either a parser gap or a config that is declared but not wired up — a commented-out call site looks exactly like this. Check before describing behaviour. |

## Reading `readSites` well

Not all read sites are equally interesting:

- `via: "accessor:..."` in a class like `ScheduleCompactionActionExecutor` or `TimelineArchiverV2`
  is a **real consumer** — code that acts on the value. Lead with these.
- `via: "constant"` inside the owning config class (a `withX(...)` builder method, or the accessor
  itself) is **plumbing**. Mention it only to show where the accessor is defined.
- `via: "constant"` in `hudi-cli` is a tool, not the write path.
- `method: null` with `via: "scalaReference"` is a Scala file; the generator resolves the file and
  line but not the enclosing method, so these contribute no co-configs and no gating. They carry
  `gatesResolved: false` for exactly that reason. For a `hoodie.datasource.*` config most sites are
  Scala, so treat an empty `gatingConditions` there as *not analysed*, and check
  `readContextResolved` / `readContextNote` before telling the user anything about gating.

When `readSites` has exactly 20 entries the list was capped — there may be more consumers.

## Query recipes

All of these assume you are in the skill directory.

**One config, everything:**

```bash
python3 - <<'EOF'
import json
catalog = json.load(open('config-catalog.json'))
by_key = {c['key']: c for c in catalog['configs']}
entry = by_key.get('hoodie.compact.inline.max.delta.commits')
print(json.dumps(entry, indent=2) if entry else 'not in catalog')
EOF
```

**Find by substring, in key or documentation:**

```bash
python3 - <<'EOF'
import json
term = 'small file'
for c in json.load(open('config-catalog.json'))['configs']:
    haystack = (c['key'] + ' ' + (c['documentation'] or '')).lower()
    if term in haystack:
        print(c['key'], '|', c['defaultValue'], '| advanced', c['advanced'])
EOF
```

**Is this key an alternative of something else?**

```bash
python3 - <<'EOF'
import json
needle = 'hoodie.cleaner.policy'
for c in json.load(open('config-catalog.json'))['configs']:
    if needle in c['alternatives']:
        print(needle, 'is an old alias of', c['key'])
EOF
```

**The gating story for a config:**

```bash
python3 - <<'EOF'
import json
by_key = {c['key']: c for c in json.load(open('config-catalog.json'))['configs']}
entry = by_key['hoodie.compact.inline.max.delta.commits']
for gate in entry['gatingConditions']:
    print('-', gate['condition'])
    print('   at', gate['at'])
EOF
```

**Everything in one config group:**

```bash
jq -r '.configs[] | select(.configGroup == "HoodieCleanConfig")
       | "\(.key)\t\(.defaultValue)\t advanced=\(.advanced)"' config-catalog.json
```

**Deprecated configs:**

```bash
jq -r '.configs[] | select(.deprecatedAfter != null)
       | "\(.key)\tdeprecated after \(.deprecatedAfter)"' config-catalog.json
```

**Configs with no resolved consumer** (a catalog gap, not proof the config is dead):

```bash
jq -r '.configs[] | select(.readSites | length == 0) | .key' config-catalog.json
```

**Every config whose default depends on the engine:**

```bash
jq -r '.configs[] | select(.engineDefaults != null)
       | "\(.key)\tdeclared=\(.defaultValue)\tspark=\(.engineDefaults.spark)
\tflink=\(.engineDefaults.flink)\tjava=\(.engineDefaults.java)"' config-catalog.json
```

**The default a user on one engine actually gets:**

```bash
python3 - <<'EOF'
import json
engine = 'spark'
key = 'hoodie.metadata.index.column.stats.enable'
catalog = json.load(open('config-catalog.json'))
entry = {c['key']: c for c in catalog['configs']}[key]
conditional = (entry.get('conditionalEngineDefaults') or {}).get(engine)
if conditional:
    print('%s on %s: %s when %s, else %s'
          % (key, engine, conditional['whenTrue'], conditional['condition'],
             conditional['whenFalse']))
elif entry.get('engineDefaults'):
    print('%s on %s: %s (declared %s)'
          % (key, engine, entry['engineDefaults'].get(engine, 'UNRESOLVED'),
             entry['defaultValue']))
else:
    print('%s: %s (no engine override)' % (key, entry['defaultValue']))
EOF
```

**Scala-declared configs** (the `hoodie.datasource.*` keys Spark users set most):

```bash
jq -r '.configs[] | select(.language == "scala") | .key' config-catalog.json
```

## Worked example

`hoodie.compact.inline.max.delta.commits` is the case that motivates the whole catalog.

The published reference gives: key, default `5`, and a description. The catalog adds, from code:

- `accessors`: `HoodieWriteConfig.getInlineCompactDeltaCommitMax` at
  `HoodieWriteConfig.java:2031`.
- A real consumer: `ScheduleCompactionActionExecutor.needCompact` at
  `ScheduleCompactionActionExecutor.java:208`, `via: accessor:getInlineCompactDeltaCommitMax`.
- Its gates at that site: `switch (compactionTriggerStrategy)` under `case NUM_COMMITS`,
  `NUM_COMMITS_AFTER_LAST_REQUEST`, `NUM_OR_TIME` and `NUM_AND_TIME`.
- Top `coConfig`: `hoodie.compact.inline.trigger.strategy`, sharing 4 read-site methods.

So the answer to "I set this to 20 and compaction still triggers every 5 commits" is visible in the
catalog: the value is only consulted under four of the trigger strategies, and the strategy is set
by the co-config. That conclusion is independently confirmed by the config's own documentation —
which is a good sign that the heuristic is working, and a reminder to cross-check it against the
documentation whenever both are present.
