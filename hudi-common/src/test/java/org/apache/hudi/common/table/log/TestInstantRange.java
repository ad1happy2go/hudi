/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package org.apache.hudi.common.table.log;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Tests {@link InstantRange} built with nullable boundaries.
 */
public class TestInstantRange {

  private static final String T1 = "20240101000000001";
  private static final String T2 = "20240101000000002";
  private static final String T3 = "20240101000000003";
  private static final String T4 = "20240101000000004";

  private static InstantRange nullableRange(InstantRange.RangeType rangeType, String start, String end) {
    return InstantRange.builder()
        .rangeType(rangeType)
        .startInstant(start)
        .endInstant(end)
        .nullableBoundary(true)
        .build();
  }

  @ParameterizedTest
  @EnumSource(value = InstantRange.RangeType.class, names = {"OPEN_CLOSED", "CLOSED_CLOSED"})
  public void testOnlyEndInstant(InstantRange.RangeType rangeType) {
    InstantRange range = nullableRange(rangeType, null, T3);
    assertFalse(range.getStartInstant().isPresent());
    assertEquals(T3, range.getEndInstant().get());
    assertTrue(range.isInRange(T1));
    assertTrue(range.isInRange(T3));
    assertFalse(range.isInRange(T4));
  }

  @ParameterizedTest
  @EnumSource(value = InstantRange.RangeType.class, names = {"OPEN_CLOSED", "CLOSED_CLOSED"})
  public void testOnlyStartInstant(InstantRange.RangeType rangeType) {
    InstantRange range = nullableRange(rangeType, T2, null);
    assertEquals(T2, range.getStartInstant().get());
    assertFalse(range.getEndInstant().isPresent());
    assertFalse(range.isInRange(T1));
    assertEquals(rangeType == InstantRange.RangeType.CLOSED_CLOSED, range.isInRange(T2));
    assertTrue(range.isInRange(T4));
  }

  @ParameterizedTest
  @EnumSource(value = InstantRange.RangeType.class, names = {"OPEN_CLOSED", "CLOSED_CLOSED"})
  public void testBothInstants(InstantRange.RangeType rangeType) {
    InstantRange range = nullableRange(rangeType, T2, T3);
    assertFalse(range.isInRange(T1));
    assertEquals(rangeType == InstantRange.RangeType.CLOSED_CLOSED, range.isInRange(T2));
    assertTrue(range.isInRange(T3));
    assertFalse(range.isInRange(T4));
  }

  @ParameterizedTest
  @EnumSource(value = InstantRange.RangeType.class, names = {"OPEN_CLOSED", "CLOSED_CLOSED"})
  public void testNoInstants(InstantRange.RangeType rangeType) {
    assertThrows(IllegalArgumentException.class, () -> nullableRange(rangeType, null, null));
  }

  @Test
  public void testNonNullableRangeRequiresStartInstant() {
    assertThrows(NullPointerException.class, () -> InstantRange.builder()
        .rangeType(InstantRange.RangeType.CLOSED_CLOSED)
        .endInstant(T3)
        .build());
  }
}
