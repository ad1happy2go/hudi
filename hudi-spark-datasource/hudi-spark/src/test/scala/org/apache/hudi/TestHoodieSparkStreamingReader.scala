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

import org.apache.hudi.common.table.HoodieTableMetaClient
import org.apache.hudi.config.HoodieWriteConfig
import org.apache.hudi.keygen.SimpleKeyGenerator
import org.apache.hudi.storage.hadoop.HadoopStorageConfiguration
import org.apache.spark.sql._
import org.apache.spark.sql.streaming.{OutputMode, Trigger}
import org.junit.jupiter.api.Test

class TestHoodieSparkStreamingReader extends HoodieSparkWriterTestBase {

  @Test
  def testStructuredStreamingIncremental(): Unit = {
    val _spark = spark
    import _spark.implicits._
    val collectedRows = scala.collection.mutable.ArrayBuffer.empty[Row]

    // Step 1: Write initial Hudi commits
      for (i <- 30 to 33) {
        val saveMode = if (i == 0) SaveMode.Overwrite else SaveMode.Append
        val df = Seq((i, s"a$i", 10, 1000 + i, "2021-10-16")).toDF("id", "name", "value", "ts", "dt")

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
          .save(tempBasePath)
      }

    // Step 3: Read Hudi as streaming DataFrame
    val streamingDF = spark.readStream
      .format("hudi")
      .load(tempBasePath)

    // Step 4: Define streaming query using foreachBatch
    val query = streamingDF.writeStream
      .foreachBatch { (batchDF: DataFrame, _: Long) =>
        batchDF.collect().foreach(collectedRows += _)
      }
      .outputMode(OutputMode.Append)
      .trigger(Trigger.Once())
      .start()


    query.awaitTermination()

    // Step 5: Verify results from first batch
    println(s"Collected rows after first batch: ${collectedRows.size}")
    assert(collectedRows.size == 3, s"Expected 3 records from all commits, got ${collectedRows.size}")
  }

  @Test
  def testStructuredStreamingIncrementalWithLimit(): Unit = {
    val _spark = spark
    import _spark.implicits._
    val collectedRows = scala.collection.mutable.ArrayBuffer.empty[Row]

    // Step 1: Write initial Hudi commits
    for (i <- 0 to 2) {
      val saveMode = if (i == 0) SaveMode.Overwrite else SaveMode.Append
      val df = Seq((i, s"a$i", 10, 1000 + i, "2021-10-16")).toDF("id", "name", "value", "ts", "dt")

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
        .save(tempBasePath)
    }

    // Step 2: Show commits for debugging
    val metaClient = HoodieTableMetaClient.builder()
      .setConf(new HadoopStorageConfiguration(spark.sparkContext.hadoopConfiguration))
      .setBasePath(tempBasePath)
      .build()

    println("=== Hudi Commit List ===")
    metaClient.getCommitsTimeline.getInstants.iterator().forEachRemaining { instant =>
      println(s"Commit: ${instant.getTimestamp}, Action: ${instant.getAction}")
    }

    // Step 3: Read Hudi as streaming DataFrame
    val streamingDF = spark.readStream
      .format("hudi")
      .option("hoodie.datasource.read.incr.limit.num.instants", "2")
      .load(tempBasePath)

    // Step 4: Define streaming query using foreachBatch
    val query = streamingDF.writeStream
      .foreachBatch { (batchDF: DataFrame, _: Long) =>
        batchDF.collect().foreach(collectedRows += _)
      }
      .outputMode(OutputMode.Append)
      .trigger(Trigger.Once())
      .start()


    query.awaitTermination()

    // Step 5: Verify results from first batch
    println(s"Collected rows after first batch: ${collectedRows.size}")
    assert(collectedRows.size == 2, s"Expected 2 records from first 2 commits, got ${collectedRows.size}")
  }
  @Test
  def manual(): Unit = {
    val _spark = spark
    import _spark.implicits._
    val hudibasePath = "/tmp/test_ss/hudi_path"

    // Step 1: Write initial Hudi commits
    for (i <- 0 to 2) {
      val saveMode = if (i == 0) SaveMode.Overwrite else SaveMode.Append
      val df = Seq((i, s"a$i", 10, 1000 + i, "2021-10-16")).toDF("id", "name", "value", "ts", "dt")

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
        .save(hudibasePath)
    }

    // Step 2: Show commits for debugging
    val metaClient = HoodieTableMetaClient.builder()
      .setConf(new HadoopStorageConfiguration(spark.sparkContext.hadoopConfiguration))
      .setBasePath(hudibasePath)
      .build()

    println("=== Hudi Commit List ===")
    metaClient.getCommitsTimeline.getInstants.iterator().forEachRemaining { instant =>
      println(s"Commit: ${instant.getTimestamp}, Action: ${instant.getAction}")
    }

    // Step 3: Read Hudi as streaming DataFrame
    val streamingDF = spark.readStream
      .format("hudi")
      .option("hoodie.datasource.read.incr.limit.num.instants", "2")
      .load(hudibasePath)


    val query = streamingDF.writeStream
      .format("parquet").option("path", "/tmp/test_ss/parquet_Code")
      .option("checkpointLocation", "/tmp/test_ss/parquet_Check")
      .outputMode("append")
      .start()


    query.awaitTermination()
  }
}
