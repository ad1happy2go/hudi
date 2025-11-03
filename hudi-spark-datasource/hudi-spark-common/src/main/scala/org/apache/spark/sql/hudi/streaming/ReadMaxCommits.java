package org.apache.spark.sql.hudi.streaming;

import org.apache.spark.sql.connector.read.streaming.ReadLimit;

public class ReadMaxCommits implements ReadLimit {
  private long commits;

  ReadMaxCommits(long commits) {
    this.commits = commits;
  }

  public long maxCommits() {
    return this.commits;
  }

  public String toString() {
    return "MaxCommits: " + this.maxCommits();
  }

  public boolean equals(Object o) {
    if (this == o) {
      return true;
    } else if (o != null && this.getClass() == o.getClass()) {
      ReadMaxCommits other = (ReadMaxCommits) o;
      return other.maxCommits() == this.maxCommits();
    } else {
      return false;
    }
  }

  public int hashCode() {
    return Long.hashCode(this.commits);
  }
}
