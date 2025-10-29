/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


package org.apache.hudi

import org.apache.hudi.config.HoodieWriteConfig
import org.apache.hudi.keygen.SimpleKeyGenerator
import org.apache.spark.sql._

import org.apache.spark.sql.streaming.{Trigger}
import org.junit.jupiter.api.Test

class TestHoodieSparkStreamingReader extends HoodieSparkWriterTestBase {

  @Test
  def testStructuredStreamingIncremental(): Unit = {
    val _spark = spark
    import _spark.implicits._
    val tempBasePath = System.getProperty("java.io.tmpdir") + "/hudi_test_" + System.currentTimeMillis()
    val hudiInputPath = s"$tempBasePath/hudi_input"
    val parquetOutputPath = s"$tempBasePath/output"
    val checkpointPath = s"$tempBasePath/checkpoint"

    // Step 1: Write 3 Hudi commits
    for (i <- 0 to 2) {
      val saveMode = if (i == 0) SaveMode.Overwrite else SaveMode.Append
      val df = Seq((i, s"a$i", 10, 1000 + i, "2021-10-16"))
        .toDF("id", "name", "value", "ts", "dt")

      val options = Map(
        DataSourceWriteOptions.RECORDKEY_FIELD.key -> "id",
        DataSourceWriteOptions.PRECOMBINE_FIELD.key -> "ts",
        DataSourceWriteOptions.PARTITIONPATH_FIELD.key -> "dt",
        HoodieWriteConfig.TBL_NAME.key -> "testStructuredStreaming",
        HoodieWriteConfig.KEYGENERATOR_CLASS_NAME.key -> classOf[SimpleKeyGenerator].getName
      )

      df.write.format("hudi")
        .options(options)
        .mode(saveMode)
        .save(hudiInputPath)
    }

    // Function to read Hudi stream
    def readHudiStream = spark.readStream
      .format("hudi")
      .load(hudiInputPath)

    def writeParquet(streamingDF: DataFrame) =
      streamingDF.writeStream
        .format("parquet")
        .option("path", parquetOutputPath)
        .option("checkpointLocation", checkpointPath)
        .outputMode("append")

    val query1 = writeParquet(readHudiStream)
      .trigger(Trigger.ProcessingTime("0 seconds"))
      .start()

    query1.processAllAvailable()
    query1.stop()

    val df = spark.read.parquet(parquetOutputPath).withColumn("file_name", functions.input_file_name())
    val filesAndCounts = df.groupBy("file_name").count().collect()
    assert(filesAndCounts.length == 1, s"Expected 1 parquet files, found ${filesAndCounts.length}")
    val recordCounts = filesAndCounts.map(_.getLong(1)).sorted
    assert(recordCounts.sameElements(Array(3L)), s"Expected record counts [1,2], found ${recordCounts.mkString(",")}")
  }

  @Test
  def testStructuredStreamingIncrementalWithLimit(): Unit = {
    val _spark = spark
    import _spark.implicits._
    val tempBasePath = System.getProperty("java.io.tmpdir") + "/hudi_test_" + System.currentTimeMillis()
    val hudiInputPath = s"$tempBasePath/hudi_input"
    val parquetOutputPath = s"$tempBasePath/output"
    val checkpointPath = s"$tempBasePath/checkpoint"

    // Step 1: Write 3 Hudi commits
    for (i <- 0 to 2) {
      val saveMode = if (i == 0) SaveMode.Overwrite else SaveMode.Append
      val df = Seq((i, s"a$i", 10, 1000 + i, "2021-10-16"))
        .toDF("id", "name", "value", "ts", "dt")

      val options = Map(
        DataSourceWriteOptions.RECORDKEY_FIELD.key -> "id",
        DataSourceWriteOptions.PRECOMBINE_FIELD.key -> "ts",
        DataSourceWriteOptions.PARTITIONPATH_FIELD.key -> "dt",
        HoodieWriteConfig.TBL_NAME.key -> "testStructuredStreaming",
        HoodieWriteConfig.KEYGENERATOR_CLASS_NAME.key -> classOf[SimpleKeyGenerator].getName
      )

      df.write.format("hudi")
        .options(options)
        .mode(saveMode)
        .save(hudiInputPath)
    }

    def readHudiStream = spark.readStream
      .format("hudi")
      .option("hoodie.spark.streaming.read.incr.limit.num.instants", "2")
      .load(hudiInputPath)

    def writeParquet(streamingDF: DataFrame) =
      streamingDF.writeStream
        .format("parquet")
        .option("path", parquetOutputPath)
        .option("checkpointLocation", checkpointPath)
        .outputMode("append")

    // --- First microbatch: should pick 2 commits (id=0,1)
    val query1 = writeParquet(readHudiStream)
      .trigger(Trigger.ProcessingTime("0 seconds"))
      .start()

    query1.processAllAvailable()
    query1.stop()

    val df = spark.read.parquet(parquetOutputPath).withColumn("file_name", functions.input_file_name())
    val filesAndCounts = df.groupBy("file_name").count().collect()
    assert(filesAndCounts.length == 2, s"Expected 2 parquet files, found ${filesAndCounts.length}")
    val recordCounts = filesAndCounts.map(_.getLong(1)).sorted
    assert(recordCounts.sameElements(Array(1L, 2L)), s"Expected record counts [1,2], found ${recordCounts.mkString(",")}")
  }
}
