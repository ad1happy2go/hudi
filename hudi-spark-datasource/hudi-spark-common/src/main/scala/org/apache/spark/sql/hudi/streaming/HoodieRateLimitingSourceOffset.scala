package org.apache.spark.sql.hudi.streaming

import com.fasterxml.jackson.annotation.JsonInclude.Include
import com.fasterxml.jackson.databind.{DeserializationFeature, ObjectMapper}
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import org.apache.hudi.common.table.timeline.HoodieTimeline
import org.apache.spark.sql.connector.read.streaming.Offset
import org.apache.spark.sql.execution.streaming.{Offset, SerializedOffset}

case class HoodieRateLimitingSourceOffset(commitTime: String) extends Offset {

  override val json: String = {
    HoodieRateLimitingSourceOffset.toJson(this)
  }

  override def equals(obj: Any): Boolean = {
    obj match {
      case HoodieRateLimitingSourceOffset(otherCommitTime) =>
        otherCommitTime == commitTime
      case _=> false
    }
  }

  override def hashCode(): Int = {
    commitTime.hashCode
  }
}


object HoodieRateLimitingSourceOffset {

  lazy val mapper: ObjectMapper = {
    val _mapper = new ObjectMapper
    _mapper.setSerializationInclusion(Include.NON_ABSENT)
    _mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
    _mapper.registerModule(DefaultScalaModule)
    _mapper
  }

  def toJson(offset: HoodieRateLimitingSourceOffset): String = {
    mapper.writeValueAsString(offset)
  }

  def fromJson(json: String): HoodieRateLimitingSourceOffset = {
    mapper.readValue(json, classOf[HoodieRateLimitingSourceOffset])
  }

  def apply(offset: Offset): HoodieRateLimitingSourceOffset = {
    offset match {
      case SerializedOffset(json) => fromJson(json)
      case o: HoodieRateLimitingSourceOffset => o
    }
  }

  val INIT_OFFSET = HoodieRateLimitingSourceOffset(HoodieTimeline.INIT_INSTANT_TS)
}
