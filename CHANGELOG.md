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

# Changelog

## [0.15.0.3]

### Fixed

- **Optimize `MERGE INTO` performance in Spark**  
  *(commit: `8b16794b34c881675e39a97d3e56f3656f7d8b31`)*  
  - Eliminates unnecessary scanning of the target table during `MERGE INTO`.  
  - When the target table has a record key, only the source table is used as input.  
  - Previously, a left join between source and target caused all target partitions to be scanned, even when updates affected only a few partitions.  
  - Improves efficiency for partitioned tables with selective updates.  
  - Behavior for primary-keyless tables remains unchanged (still performs left join to fetch meta columns for prepped upserts).

- **Fix file group bug with uncommitted file slices**  
  *(commit: `3a4f58685a56131dca55ac209757cab3bfcb2850`)*  
  - Applies consistent filtering in `getAllFileSlicesBeforeOn`, matching `getAllFileSlices`.  
  - Prevents uncommitted file slices from being returned.  
  - Fixes errors in the small file handling flow caused by inclusion of uncommitted slices.

- **Avoid unnecessary schema evolution when no effective change**  
  *(commit: `0218898dd2a2950f553cd3b5a92507e02e28bf6f`)*  
  - Prevents schema evolution if the reconciled schema remains unchanged except for version ID differences.  
  - Reduces redundant schema updates and improves efficiency.  
  - Based on [HUDI-9597].  
  - Co-authored-by: Lokesh Jain, Shuo Cheng.

- **Fix incremental query with full scan mode on MOR tables (Databricks Runtime)**  
  *(commit: `ea59d79d7467e5a13d2605ee05c4f39ea5288f26`)*  
  - Resolves issues with incremental queries when running in full scan mode on Merge-On-Read (MOR) tables.  
  - Ensures correct query behavior on Databricks Runtime.

- **Automatic detection and caching of ComplexKeyGenerator encoding format**  
  *(commit: `04e2f6503e4e4b0c726003c65481de9a5c8f3cd0`)*  
  - Introduces automatic encoding detection for tables using ComplexKeyGenerator with a single record key field.  
  - Deduction logic reads existing base files to determine if the old format (`fieldName:fieldValue`) or new format (`fieldValue`) is used.  
  - Caches deduced encoding in `.hoodie/.aux/complex_key_encoding` to avoid repeated computation.  
  - Adds new config `hoodie.write.complex.keygen.auto.deduce.encoding` (default: `true`) for seamless upgrades.  
  - Improves user experience by removing the need for manual configuration or validation toggling during upgrades.  

### Added

- **Add billing project ID config for BigQuery sync**  
  *(commit: `0fb3e940a89d83352a41a7ad42b57f687cb4f4a2`, HUDI-8212)*  
  - Introduces an additional configuration to specify a billing project ID for BigQuery sync.  
  - Enables submitting jobs under a different billing project when the dataset project ID and billing project ID differ.  
  - Improves flexibility for cross-project BigQuery usage scenarios.

- **Support Databricks Spark runtime**  
  *(commit: `d840259ff19b122cd779d6397067098acc6fd9b4`)*  
  - Adds compatibility and support for running on Databricks Spark runtime.

- **Partition predicate fix for Databricks runtime support**  
  *(commit: `284b95420c692615e933ba49cc2c0f68e175e747`)*  
  - Fixes partition predicate handling to ensure correct behavior on Databricks runtime.
