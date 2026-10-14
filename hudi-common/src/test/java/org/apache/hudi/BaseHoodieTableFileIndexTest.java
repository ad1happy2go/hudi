/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.hudi;

import org.apache.hudi.common.config.HoodieMetadataConfig;
import org.apache.hudi.common.table.timeline.HoodieInstant;
import org.apache.hudi.common.table.timeline.HoodieTimeline;
import org.apache.hudi.common.testutils.MockHoodieTimeline;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.lang.reflect.Field;
import java.util.Arrays;

import static org.apache.hudi.common.testutils.HoodieTestUtils.INSTANT_GENERATOR;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

public class BaseHoodieTableFileIndexTest {

  @Test
  public void testGetMetadataConfigReturnsFieldValue() throws Exception {
    // Create a mock of BaseHoodieTableFileIndex
    BaseHoodieTableFileIndex fileIndex = mock(BaseHoodieTableFileIndex.class, 
        org.mockito.Mockito.CALLS_REAL_METHODS);
    
    // Create a test metadata config
    HoodieMetadataConfig testConfig = HoodieMetadataConfig.newBuilder()
        .enable(true)
        .withMetadataIndexBloomFilter(true)
        .withMetadataIndexColumnStats(true)
        .build();
    
    // Use reflection to set the private metadataConfig field
    Field metadataConfigField = BaseHoodieTableFileIndex.class.getDeclaredField("metadataConfig");
    metadataConfigField.setAccessible(true);
    metadataConfigField.set(fileIndex, testConfig);
    
    // Test the getMetadataConfig method
    HoodieMetadataConfig result = fileIndex.getMetadataConfig();
    
    assertNotNull(result, "Metadata config should not be null");
    assertSame(testConfig, result, "Should return the same metadata config instance");
    assertEquals(true, result.isEnabled(), "Metadata should be enabled");
    assertEquals(true, result.isBloomFilterIndexEnabled(), "Bloom filter index should be enabled");
    assertEquals(true, result.isColumnStatsIndexEnabled(), "Column stats index should be enabled");
  }

  /**
   * The incremental partition listing reads written partitions from the write timeline, so the
   * "has the start been archived" guard must be evaluated against that same timeline. A completed
   * rollback (or clean) older than every active commit must not make an archived start look active,
   * otherwise only the partitions of the active commits in the range are listed.
   *
   * <p>Timeline: rollback 001 (completed 002), commit 005 (completed 006), commit 007 (completed 008).
   */
  @ParameterizedTest
  @ValueSource(booleans = {false, true})
  public void testIncrementalStartBeforeFirstWriteIsArchivedDespiteOlderNonWriteInstant(boolean completionTimeBased) throws Exception {
    HoodieTimeline activeTimeline = new MockHoodieTimeline(Arrays.asList(
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.ROLLBACK_ACTION, "001", "002"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.COMMIT_ACTION, "005", "006"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.COMMIT_ACTION, "007", "008")));

    // start after the rollback but before the first commit: archived
    assertTrue(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, "003"));
    // start at or after the first commit: covered by the active write timeline
    assertFalse(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, completionTimeBased ? "006" : "005"));
    assertFalse(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, "007"));
  }

  /**
   * With archival beyond savepoint, a savepointed commit stays on the active timeline while the commits after it are
   * archived. A start in that hole is archived, so the savepointed commit must not count as the start of the timeline.
   *
   * <p>Timeline: commit 001 (completed 002) with savepoint 001, commit 010 (completed 011), commit 012 (completed 013).
   */
  @ParameterizedTest
  @ValueSource(booleans = {false, true})
  public void testIncrementalStartInArchivalHoleAfterSavepointIsArchived(boolean completionTimeBased) throws Exception {
    HoodieTimeline activeTimeline = new MockHoodieTimeline(Arrays.asList(
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.COMMIT_ACTION, "001", "002"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.SAVEPOINT_ACTION, "001", "003"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.COMMIT_ACTION, "010", "011"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.COMMIT_ACTION, "012", "013")));

    // start between the savepointed commit and the first active commit after it: archived
    assertTrue(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, "005"));
    assertFalse(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, completionTimeBased ? "011" : "010"));
  }

  /**
   * Without a completed write instant on the active timeline the written partitions are unknown, so every start is
   * treated as archived and all partitions are listed.
   */
  @ParameterizedTest
  @ValueSource(booleans = {false, true})
  public void testIncrementalStartIsArchivedWithoutActiveWriteInstant(boolean completionTimeBased) throws Exception {
    HoodieTimeline activeTimeline = new MockHoodieTimeline(Arrays.asList(
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.ROLLBACK_ACTION, "001", "002"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.CLEAN_ACTION, "003", "004")));

    assertTrue(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, "000"));
    assertTrue(BaseHoodieTableFileIndex.isBeforeTimelineStarts(activeTimeline, completionTimeBased, "005"));

    // a pending write instant alone does not tell which partitions were written either
    HoodieTimeline pendingOnlyTimeline = new MockHoodieTimeline(Arrays.asList(
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.COMPLETED, HoodieTimeline.ROLLBACK_ACTION, "001", "002"),
        INSTANT_GENERATOR.createNewInstant(HoodieInstant.State.REQUESTED, HoodieTimeline.COMPACTION_ACTION, "003")));
    assertTrue(BaseHoodieTableFileIndex.isBeforeTimelineStarts(pendingOnlyTimeline, completionTimeBased, "005"));
  }
}
