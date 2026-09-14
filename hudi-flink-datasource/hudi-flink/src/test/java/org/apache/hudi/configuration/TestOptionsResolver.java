/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.hudi.configuration;

import org.apache.hudi.common.model.HoodieFailedWritesCleaningPolicy;
import org.apache.hudi.common.model.WriteConcurrencyMode;
import org.apache.hudi.config.HoodieCleanConfig;
import org.apache.hudi.config.HoodieWriteConfig;
import org.apache.hudi.index.HoodieIndex;
import org.apache.hudi.common.table.HoodieTableConfig;
import org.apache.hudi.keygen.ComplexAvroKeyGenerator;
import org.apache.hudi.keygen.NonpartitionedAvroKeyGenerator;
import org.apache.hudi.keygen.constant.KeyGeneratorType;

import org.apache.flink.configuration.Configuration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Test for {@link OptionsResolver}
 */
public class TestOptionsResolver {
  @TempDir
  File tempFile;
  
  @Test
  void testGetIndexType() {
    Configuration conf = getConf();
    // set uppercase index
    conf.set(FlinkOptions.INDEX_TYPE, "BLOOM");
    assertEquals(HoodieIndex.IndexType.BLOOM, OptionsResolver.getIndexType(conf));
    // set lowercase index
    conf.set(FlinkOptions.INDEX_TYPE, "bloom");
    assertEquals(HoodieIndex.IndexType.BLOOM, OptionsResolver.getIndexType(conf));
  }

  @Test
  void testIsLazyFailedWritesCleanPolicy() {
    Configuration conf = new Configuration();
    // add any parameter
    conf.set(FlinkOptions.CLEAN_ASYNC_ENABLED, true);
    // add value for FAILED_WRITES_CLEANER_POLICY using default key
    conf.setString(HoodieCleanConfig.FAILED_WRITES_CLEANER_POLICY.key(), HoodieFailedWritesCleaningPolicy.NEVER.name());
    assertFalse(OptionsResolver.isLazyFailedWritesCleanPolicy(conf));

    if (!HoodieCleanConfig.FAILED_WRITES_CLEANER_POLICY.getAlternatives().isEmpty()) {
      conf = new Configuration();
      // add any parameter
      conf.set(FlinkOptions.CLEAN_ASYNC_ENABLED, true);
      // add value for FAILED_WRITES_CLEANER_POLICY using alternative key
      conf.setString(HoodieCleanConfig.FAILED_WRITES_CLEANER_POLICY.getAlternatives().get(0), HoodieFailedWritesCleaningPolicy.LAZY.name());
      assertTrue(OptionsResolver.isLazyFailedWritesCleanPolicy(conf));
    }
  }

  private Configuration getConf() {
    Configuration conf = new Configuration();
    conf.setString(HoodieWriteConfig.WRITE_CONCURRENCY_MODE.key(), WriteConcurrencyMode.OPTIMISTIC_CONCURRENCY_CONTROL.name());
    conf.set(FlinkOptions.PATH, tempFile.getAbsolutePath());
    return conf;
  }

  /** The persisted table encoding is authoritative over the version-derived default. */
  @Test
  void testEncodeSingleKeyFieldNameForComplexKeygen() {
    Configuration conf = new Configuration();
    conf.setString(HoodieWriteConfig.WRITE_TABLE_VERSION.key(), "8");
    conf.setString(HoodieWriteConfig.COMPLEX_KEYGEN_NEW_ENCODING.key(), "true");
    assertFalse(OptionsResolver.encodeSingleKeyFieldNameForComplexKeygen(conf));
    conf.setString(HoodieWriteConfig.COMPLEX_KEYGEN_NEW_ENCODING.key(), "false");
    assertTrue(OptionsResolver.encodeSingleKeyFieldNameForComplexKeygen(conf));
    // version 9+ always prefixes ...
    conf.setString(HoodieWriteConfig.WRITE_TABLE_VERSION.key(), "9");
    conf.setString(HoodieWriteConfig.COMPLEX_KEYGEN_NEW_ENCODING.key(), "true");
    assertTrue(OptionsResolver.encodeSingleKeyFieldNameForComplexKeygen(conf));
    // ... unless the table carries the encoding persisted by the 8 -> 9 upgrade, which wins
    conf.setString(HoodieTableConfig.COMPLEX_KEYGEN_ENCODING.key(), "VALUE_ONLY");
    assertFalse(OptionsResolver.encodeSingleKeyFieldNameForComplexKeygen(conf));
    conf.setString(HoodieTableConfig.COMPLEX_KEYGEN_ENCODING.key(), "FIELD_PREFIXED");
    assertTrue(OptionsResolver.encodeSingleKeyFieldNameForComplexKeygen(conf));
  }

  @Test
  void testIsComplexKeyGenerator() {
    Configuration conf = new Configuration();
    conf.set(FlinkOptions.RECORD_KEY_FIELD, "uuid");
    // not configured: inferred from the field counts, as StreamerUtil#checkKeygenGenerator would select it
    assertFalse(OptionsResolver.isComplexKeyGenerator(conf));
    conf.set(FlinkOptions.PARTITION_PATH_FIELD, "partition,ts");
    assertTrue(OptionsResolver.isComplexKeyGenerator(conf));
    conf.set(FlinkOptions.PARTITION_PATH_FIELD, "partition");
    conf.set(FlinkOptions.RECORD_KEY_FIELD, "uuid,name");
    assertTrue(OptionsResolver.isComplexKeyGenerator(conf));
    // configured explicitly: the class decides, whatever the field counts
    conf.set(FlinkOptions.RECORD_KEY_FIELD, "uuid");
    conf.set(FlinkOptions.KEYGEN_CLASS_NAME, ComplexAvroKeyGenerator.class.getName());
    assertTrue(OptionsResolver.isComplexKeyGenerator(conf));
    conf.set(FlinkOptions.KEYGEN_CLASS_NAME, "org.apache.hudi.keygen.ComplexKeyGenerator");
    assertTrue(OptionsResolver.isComplexKeyGenerator(conf));
    conf.set(FlinkOptions.PARTITION_PATH_FIELD, "partition,ts");
    conf.set(FlinkOptions.KEYGEN_CLASS_NAME, "org.apache.hudi.keygen.SimpleAvroKeyGenerator");
    assertFalse(OptionsResolver.isComplexKeyGenerator(conf));
  }

  /**
   * The row writer decides the prefix from the job configuration, the reader side from the table config. They
   * must not disagree: when they do, the RLI probes keys that were never written and prunes every file, so the
   * query returns nothing rather than failing. The table's encoding therefore wins over the job configuration.
   */
  @Test
  void testPrefixSingleRecordKeyFollowsTableEncoding() {
    Configuration conf = new Configuration();
    conf.set(FlinkOptions.RECORD_KEY_FIELD, "uuid");
    conf.setString(HoodieWriteConfig.WRITE_TABLE_VERSION.key(), "9");

    // A non-partitioned table: HoodieTableFactory#setupHoodieKeyOptions resets the key generator option, so the
    // job conf no longer says "complex" even though the table does. The persisted encoding must still decide.
    conf.set(FlinkOptions.KEYGEN_CLASS_NAME, NonpartitionedAvroKeyGenerator.class.getName());
    assertFalse(OptionsResolver.isComplexKeyGenerator(conf));
    conf.setString(HoodieTableConfig.COMPLEX_KEYGEN_ENCODING.key(), "FIELD_PREFIXED");
    assertTrue(OptionsResolver.prefixSingleRecordKey(conf),
        "A FIELD_PREFIXED table must be written with the prefix even when the job conf's keygen was rewritten");
    conf.setString(HoodieTableConfig.COMPLEX_KEYGEN_ENCODING.key(), "VALUE_ONLY");
    assertFalse(OptionsResolver.prefixSingleRecordKey(conf), "A VALUE_ONLY table must be written bare");

    // Without an encoding from the table, the job configuration decides as before.
    Configuration noEncoding = new Configuration();
    noEncoding.set(FlinkOptions.RECORD_KEY_FIELD, "uuid");
    noEncoding.setString(HoodieWriteConfig.WRITE_TABLE_VERSION.key(), "9");
    noEncoding.set(FlinkOptions.KEYGEN_CLASS_NAME, NonpartitionedAvroKeyGenerator.class.getName());
    assertFalse(OptionsResolver.prefixSingleRecordKey(noEncoding));
    noEncoding.set(FlinkOptions.KEYGEN_CLASS_NAME, ComplexAvroKeyGenerator.class.getName());
    assertTrue(OptionsResolver.prefixSingleRecordKey(noEncoding));
  }

  /** The key generator can be selected by type alone; the complex-keygen check has to honour that too. */
  @Test
  void testIsComplexKeyGeneratorFromType() {
    Configuration conf = new Configuration();
    conf.set(FlinkOptions.RECORD_KEY_FIELD, "uuid");
    conf.set(FlinkOptions.PARTITION_PATH_FIELD, "partition");
    assertFalse(OptionsResolver.isComplexKeyGenerator(conf));
    conf.set(FlinkOptions.KEYGEN_TYPE, KeyGeneratorType.COMPLEX.name());
    assertTrue(OptionsResolver.isComplexKeyGenerator(conf), "keygen type COMPLEX must be recognised");
    // an explicit class still wins over the type
    conf.set(FlinkOptions.KEYGEN_CLASS_NAME, NonpartitionedAvroKeyGenerator.class.getName());
    assertFalse(OptionsResolver.isComplexKeyGenerator(conf));
  }
}
