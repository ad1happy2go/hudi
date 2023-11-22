"use strict";(self.webpackChunkhudi=self.webpackChunkhudi||[]).push([[4831],{3905:(e,t,a)=>{a.d(t,{Zo:()=>p,kt:()=>h});var n=a(67294);function i(e,t,a){return t in e?Object.defineProperty(e,t,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[t]=a,e}function r(e,t){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),a.push.apply(a,n)}return a}function o(e){for(var t=1;t<arguments.length;t++){var a=null!=arguments[t]?arguments[t]:{};t%2?r(Object(a),!0).forEach((function(t){i(e,t,a[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):r(Object(a)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))}))}return e}function l(e,t){if(null==e)return{};var a,n,i=function(e,t){if(null==e)return{};var a,n,i={},r=Object.keys(e);for(n=0;n<r.length;n++)a=r[n],t.indexOf(a)>=0||(i[a]=e[a]);return i}(e,t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);for(n=0;n<r.length;n++)a=r[n],t.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(e,a)&&(i[a]=e[a])}return i}var s=n.createContext({}),d=function(e){var t=n.useContext(s),a=t;return e&&(a="function"==typeof e?e(t):o(o({},t),e)),a},p=function(e){var t=d(e.components);return n.createElement(s.Provider,{value:t},e.children)},u="mdxType",c={inlineCode:"code",wrapper:function(e){var t=e.children;return n.createElement(n.Fragment,{},t)}},m=n.forwardRef((function(e,t){var a=e.components,i=e.mdxType,r=e.originalType,s=e.parentName,p=l(e,["components","mdxType","originalType","parentName"]),u=d(a),m=i,h=u["".concat(s,".").concat(m)]||u[m]||c[m]||r;return a?n.createElement(h,o(o({ref:t},p),{},{components:a})):n.createElement(h,o({ref:t},p))}));function h(e,t){var a=arguments,i=t&&t.mdxType;if("string"==typeof e||i){var r=a.length,o=new Array(r);o[0]=m;var l={};for(var s in t)hasOwnProperty.call(t,s)&&(l[s]=t[s]);l.originalType=e,l[u]="string"==typeof e?e:i,o[1]=l;for(var d=2;d<r;d++)o[d]=a[d];return n.createElement.apply(null,o)}return n.createElement.apply(null,a)}m.displayName="MDXCreateElement"},70461:(e,t,a)=>{a.r(t),a.d(t,{contentTitle:()=>o,default:()=>u,frontMatter:()=>r,metadata:()=>l,toc:()=>s});var n=a(87462),i=(a(67294),a(3905));a(26396),a(58215);const r={title:"Release 0.12.0",sidebar_position:8,layout:"releases",toc:!0},o=void 0,l={unversionedId:"release-0.12.0",id:"release-0.12.0",title:"Release 0.12.0",description:"Release 0.12.0 (docs)",source:"@site/releases/release-0.12.0.md",sourceDirName:".",slug:"/release-0.12.0",permalink:"/releases/release-0.12.0",tags:[],version:"current",sidebarPosition:8,frontMatter:{title:"Release 0.12.0",sidebar_position:8,layout:"releases",toc:!0},sidebar:"releases",previous:{title:"Release 0.12.1",permalink:"/releases/release-0.12.1"},next:{title:"Release 0.11.1",permalink:"/releases/release-0.11.1"}},s=[{value:"Release 0.12.0 (docs)",id:"release-0120-docs",children:[],level:2},{value:"Long Term Support",id:"long-term-support",children:[],level:2},{value:"Migration Guide",id:"migration-guide",children:[{value:"Configuration Updates",id:"configuration-updates",children:[],level:3},{value:"API Updates",id:"api-updates",children:[],level:3},{value:"Fallback Partition",id:"fallback-partition",children:[],level:3},{value:"Bundle Updates",id:"bundle-updates",children:[],level:3}],level:2},{value:"Release Highlights",id:"release-highlights",children:[{value:"Presto-Hudi Connector",id:"presto-hudi-connector",children:[],level:3},{value:"Archival Beyond Savepoint",id:"archival-beyond-savepoint",children:[],level:3},{value:"File system based Lock Provider",id:"file-system-based-lock-provider",children:[],level:3},{value:"Deltastreamer Termination Strategy",id:"deltastreamer-termination-strategy",children:[],level:3},{value:"Spark 3.3 Support",id:"spark-33-support",children:[],level:3},{value:"Spark SQL Support Improvements",id:"spark-sql-support-improvements",children:[],level:3},{value:"Flink 1.15 Support",id:"flink-115-support",children:[],level:3},{value:"Flink Integration Improvements",id:"flink-integration-improvements",children:[],level:3},{value:"Performance Improvements",id:"performance-improvements",children:[],level:3}],level:2},{value:"Known Regressions:",id:"known-regressions",children:[],level:2},{value:"Raw Release Notes",id:"raw-release-notes",children:[],level:2}],d={toc:s},p="wrapper";function u(e){let{components:t,...a}=e;return(0,i.kt)(p,(0,n.Z)({},d,a,{components:t,mdxType:"MDXLayout"}),(0,i.kt)("h2",{id:"release-0120-docs"},(0,i.kt)("a",{parentName:"h2",href:"https://github.com/apache/hudi/releases/tag/release-0.12.0"},"Release 0.12.0")," (",(0,i.kt)("a",{parentName:"h2",href:"/docs/0.12.0/quick-start-guide"},"docs"),")"),(0,i.kt)("h2",{id:"long-term-support"},"Long Term Support"),(0,i.kt)("p",null,"We aim to maintain 0.12 for a longer period of time and provide a stable release through the latest 0.12.x release for\nusers to migrate to.  The latest 0.12 release is ",(0,i.kt)("a",{parentName:"p",href:"/releases/release-0.12.3"},"0.12.3"),"."),(0,i.kt)("h2",{id:"migration-guide"},"Migration Guide"),(0,i.kt)("p",null,"In this release, there have been a few API and configuration updates listed below that warranted a new table version.\nHence, the latest ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/blob/bf86efef719b7760ea379bfa08c537431eeee09a/hudi-common/src/main/java/org/apache/hudi/common/table/HoodieTableVersion.java#L41"},"table version"),"\nis ",(0,i.kt)("inlineCode",{parentName:"p"},"5"),". For existing Hudi tables on older version, a one-time upgrade step will be executed automatically. Please take\nnote of the following updates before upgrading to Hudi 0.12.0."),(0,i.kt)("h3",{id:"configuration-updates"},"Configuration Updates"),(0,i.kt)("p",null,"In this release, the default value for a few configurations have been changed. They are as follows:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"hoodie.bulkinsert.sort.mode"),": This config is used to determine mode for sorting records for bulk insert. Its default value has been changed from ",(0,i.kt)("inlineCode",{parentName:"p"},"GLOBAL_SORT")," to ",(0,i.kt)("inlineCode",{parentName:"p"},"NONE"),", which means no sorting is done and it matches ",(0,i.kt)("inlineCode",{parentName:"p"},"spark.write.parquet()")," in terms of overhead.")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"hoodie.datasource.hive_sync.partition_value_extractor"),": This config is used to extract and transform partition value during Hive sync. Its default value has been changed from ",(0,i.kt)("inlineCode",{parentName:"p"},"SlashEncodedDayPartitionValueExtractor")," to ",(0,i.kt)("inlineCode",{parentName:"p"},"MultiPartKeysValueExtractor"),". If you relied on the previous default value (i.e., have not set it explicitly), you are required to set the config to ",(0,i.kt)("inlineCode",{parentName:"p"},"org.apache.hudi.hive.SlashEncodedDayPartitionValueExtractor"),". From this release, if this config is not set and Hive sync is enabled, then partition value extractor class will be ",(0,i.kt)("strong",{parentName:"p"},"automatically inferred")," on the basis of number of partition fields and whether or not hive style partitioning is enabled.")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},"The following configs will be inferred, if not set manually, from other configs' values:"),(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"META_SYNC_BASE_FILE_FORMAT"),": infer from ",(0,i.kt)("inlineCode",{parentName:"p"},"org.apache.hudi.common.table.HoodieTableConfig.BASE_FILE_FORMAT"))),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"META_SYNC_ASSUME_DATE_PARTITION"),": infer from ",(0,i.kt)("inlineCode",{parentName:"p"},"org.apache.hudi.common.config.HoodieMetadataConfig.ASSUME_DATE_PARTITIONING"))),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"META_SYNC_DECODE_PARTITION"),": infer from ",(0,i.kt)("inlineCode",{parentName:"p"},"org.apache.hudi.common.table.HoodieTableConfig.URL_ENCODE_PARTITIONING"))),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},(0,i.kt)("inlineCode",{parentName:"p"},"META_SYNC_USE_FILE_LISTING_FROM_METADATA"),": infer from ",(0,i.kt)("inlineCode",{parentName:"p"},"org.apache.hudi.common.config.HoodieMetadataConfig.ENABLE")))))),(0,i.kt)("h3",{id:"api-updates"},"API Updates"),(0,i.kt)("p",null,"In ",(0,i.kt)("inlineCode",{parentName:"p"},"SparkKeyGeneratorInterface"),", return type of the ",(0,i.kt)("inlineCode",{parentName:"p"},"getRecordKey")," API has been changed from String to UTF8String."),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre",className:"language-java"},"// Before\nString getRecordKey(InternalRow row, StructType schema); \n\n\n// After\nUTF8String getRecordKey(InternalRow row, StructType schema); \n")),(0,i.kt)("h3",{id:"fallback-partition"},"Fallback Partition"),(0,i.kt)("p",null,"If partition field value was null, Hudi has a fallback mechanism instead of failing the write. Until 0.9.0,\n",(0,i.kt)("inlineCode",{parentName:"p"},"__HIVE_DEFAULT_PARTITION__"),"  was used as the fallback partition. After 0.9.0, due to some refactoring, fallback\npartition changed to ",(0,i.kt)("inlineCode",{parentName:"p"},"default"),". This default partition does not sit well with some of the query engines. So, we are\nswitching the fallback partition to ",(0,i.kt)("inlineCode",{parentName:"p"},"__HIVE_DEFAULT_PARTITION__"),"  from 0.12.0. We have added an upgrade step where in,\nwe fail the upgrade if the existing Hudi table has a partition named ",(0,i.kt)("inlineCode",{parentName:"p"},"default"),". Users are expected to rewrite the data\nin this partition to a partition named ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/blob/0d0a4152cfd362185066519ae926ac4513c7a152/hudi-common/src/main/java/org/apache/hudi/common/util/PartitionPathEncodeUtils.java#L29"},"_","_","HIVE_DEFAULT_PARTITION","_","_"),".\nHowever, if you had intentionally named your partition as ",(0,i.kt)("inlineCode",{parentName:"p"},"default"),", you can bypass this using the config ",(0,i.kt)("inlineCode",{parentName:"p"},"hoodie.skip.default.partition.validation"),"."),(0,i.kt)("h3",{id:"bundle-updates"},"Bundle Updates"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"hudi-aws-bundle")," extracts away aws-related dependencies from hudi-utilities-bundle or hudi-spark-bundle. In order to use features such as Glue sync, Cloudwatch metrics reporter or DynamoDB lock provider, users need to provide hudi-aws-bundle jar along with hudi-utilities-bundle or hudi-spark-bundle jars."),(0,i.kt)("li",{parentName:"ul"},"Spark 3.3 support is added; users who are on Spark 3.3 can use ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark3.3-bundle")," or ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark3-bundle")," (legacy bundle name)."),(0,i.kt)("li",{parentName:"ul"},"Spark 3.2 will continue to be supported via ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark3.2-bundle"),"."),(0,i.kt)("li",{parentName:"ul"},"Spark 3.1 will continue to be supported via ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark3.1-bundle"),"."),(0,i.kt)("li",{parentName:"ul"},"Spark 2.4 will continue to be supported via ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark2.4-bundle")," or ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-spark-bundle")," (legacy bundle name)."),(0,i.kt)("li",{parentName:"ul"},"Flink 1.15 support is added; users who are on Flink 1.15 can use ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-flink1.15-bundle"),"."),(0,i.kt)("li",{parentName:"ul"},"Flink 1.14 will continue to be supported via ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-flink1.14-bundle"),"."),(0,i.kt)("li",{parentName:"ul"},"Flink 1.13 will continue to be supported via ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi-flink1.13-bundle"),".")),(0,i.kt)("h2",{id:"release-highlights"},"Release Highlights"),(0,i.kt)("h3",{id:"presto-hudi-connector"},"Presto-Hudi Connector"),(0,i.kt)("p",null,"Since version 0.275 of PrestoDB, users can now leverage native Hudi connector to query Hudi table.\nIt is on par with Hudi support in the Hive connector. To learn more about the usage of the connector,\nplease checkout ",(0,i.kt)("a",{parentName:"p",href:"https://prestodb.io/docs/current/connector/hudi.html"},"prestodb documentation"),"."),(0,i.kt)("h3",{id:"archival-beyond-savepoint"},"Archival Beyond Savepoint"),(0,i.kt)("p",null,"Hudi supports savepoint and restore feature that is useful for backup and disaster recovery scenarios. More info can be\nfound ",(0,i.kt)("a",{parentName:"p",href:"https://hudi.apache.org/docs/disaster_recovery"},"here"),". Until 0.12.0, archival for a given table will not make\nprogress beyond the first savepointed commit. But there has been ask from the community to relax this constraint so that\nsome coarse grained commits can be retained in the active timeline and execute point in time queries. So, with 0.12.0,\nusers can now let archival proceed beyond savepoint commits by enabling ",(0,i.kt)("inlineCode",{parentName:"p"},"hoodie.archive.beyond.savepoint"),' write\nconfiguration. This unlocks new opportunities for Hudi users. For example, one can retain commits for years, by adding\none savepoint per day for older commits (lets say > 30 days). And query hudi table using "as.of.instant" with any older\nsavepointed commit. By this, Hudi does not need to retain every commit in the active timeline for older commits.'),(0,i.kt)("div",{className:"admonition admonition-note alert alert--secondary"},(0,i.kt)("div",{parentName:"div",className:"admonition-heading"},(0,i.kt)("h5",{parentName:"div"},(0,i.kt)("span",{parentName:"h5",className:"admonition-icon"},(0,i.kt)("svg",{parentName:"span",xmlns:"http://www.w3.org/2000/svg",width:"14",height:"16",viewBox:"0 0 14 16"},(0,i.kt)("path",{parentName:"svg",fillRule:"evenodd",d:"M6.3 5.69a.942.942 0 0 1-.28-.7c0-.28.09-.52.28-.7.19-.18.42-.28.7-.28.28 0 .52.09.7.28.18.19.28.42.28.7 0 .28-.09.52-.28.7a1 1 0 0 1-.7.3c-.28 0-.52-.11-.7-.3zM8 7.99c-.02-.25-.11-.48-.31-.69-.2-.19-.42-.3-.69-.31H6c-.27.02-.48.13-.69.31-.2.2-.3.44-.31.69h1v3c.02.27.11.5.31.69.2.2.42.31.69.31h1c.27 0 .48-.11.69-.31.2-.19.3-.42.31-.69H8V7.98v.01zM7 2.3c-3.14 0-5.7 2.54-5.7 5.68 0 3.14 2.56 5.7 5.7 5.7s5.7-2.55 5.7-5.7c0-3.15-2.56-5.69-5.7-5.69v.01zM7 .98c3.86 0 7 3.14 7 7s-3.14 7-7 7-7-3.12-7-7 3.14-7 7-7z"}))),"note")),(0,i.kt)("div",{parentName:"div",className:"admonition-content"},(0,i.kt)("p",{parentName:"div"},"However, if this feature is enabled, restore cannot be supported. This limitation would be relaxed in a future release\nand the development of this feature can be tracked in ",(0,i.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/browse/HUDI-4500"},"HUDI-4500"),"."))),(0,i.kt)("h3",{id:"file-system-based-lock-provider"},"File system based Lock Provider"),(0,i.kt)("p",null,"For multiple writers using optimistic concurrency control, Hudi already supports lock providers based on\nZookeeper, Hive Metastore or Amazon DynamoDB. In this release, there is a new file system based lock provider. Unlike the\nneed for external systems in other lock providers, this implementation acquires/releases a lock based on atomic\ncreate/delete operations of the underlying file system. To use this lock provider, users need to set the following\nminimal configurations (please check the ",(0,i.kt)("a",{parentName:"p",href:"/docs/configurations#Locks-Configurations"},"lock configuration")," for a few\nother optional configs that can be used):"),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre"},"hoodie.write.concurrency.mode=optimistic_concurrency_control\nhoodie.write.lock.provider=org.apache.hudi.client.transaction.lock.FileSystemBasedLockProvider\n")),(0,i.kt)("h3",{id:"deltastreamer-termination-strategy"},"Deltastreamer Termination Strategy"),(0,i.kt)("p",null,"Users can now configure a post-write termination strategy with deltastreamer ",(0,i.kt)("inlineCode",{parentName:"p"},"continuous")," mode if need be. For instance,\nusers can configure graceful shutdown if there is no new data from source for 5 consecutive times. Here is the interface\nfor the termination strategy."),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre",className:"language-java"},"/**\n * Post write termination strategy for deltastreamer in continuous mode.\n */\npublic interface PostWriteTerminationStrategy {\n\n  /**\n   * Returns whether deltastreamer needs to be shutdown.\n   * @param scheduledCompactionInstantAndWriteStatuses optional pair of scheduled compaction instant and write statuses.\n   * @return true if deltastreamer has to be shutdown. false otherwise.\n   */\n  boolean shouldShutdown(Option<Pair<Option<String>, JavaRDD<WriteStatus>>> scheduledCompactionInstantAndWriteStatuses);\n\n}\n")),(0,i.kt)("p",null,"Also, this might help in bootstrapping a new table. Instead of doing one bulk load or bulk_insert leveraging a large\ncluster for a large input of data, one could start deltastreamer on continuous mode and add a shutdown strategy to\nterminate, once all data has been bootstrapped. This way, each batch could be smaller and may not need a large cluster\nto bootstrap data. We have one concrete implementation out of the box, ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/blob/0d0a4152cfd362185066519ae926ac4513c7a152/hudi-utilities/src/main/java/org/apache/hudi/utilities/deltastreamer/NoNewDataTerminationStrategy.java"},"NoNewDataTerminationStrategy"),".\nUsers can feel free to implement their own strategy as they see fit."),(0,i.kt)("h3",{id:"spark-33-support"},"Spark 3.3 Support"),(0,i.kt)("p",null,"Spark 3.3 support is added; users who are on Spark 3.3 can use ",(0,i.kt)("inlineCode",{parentName:"p"},"hudi-spark3.3-bundle")," or ",(0,i.kt)("inlineCode",{parentName:"p"},"hudi-spark3-bundle"),". Spark 3.2,\nSpark 3.1 and Spark 2.4 will continue to be supported. Please check the migration guide for ",(0,i.kt)("a",{parentName:"p",href:"#bundle-updates"},"bundle updates"),"."),(0,i.kt)("h3",{id:"spark-sql-support-improvements"},"Spark SQL Support Improvements"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Support for upgrade, downgrade, bootstrap, clean, rollback and repair through ",(0,i.kt)("inlineCode",{parentName:"li"},"Call Procedure")," command."),(0,i.kt)("li",{parentName:"ul"},"Support for ",(0,i.kt)("inlineCode",{parentName:"li"},"analyze table"),"."),(0,i.kt)("li",{parentName:"ul"},"Support for ",(0,i.kt)("inlineCode",{parentName:"li"},"Create/Drop/Show/Refresh Index")," syntax through Spark SQL.")),(0,i.kt)("h3",{id:"flink-115-support"},"Flink 1.15 Support"),(0,i.kt)("p",null,"Flink 1.15.x is integrated with Hudi, use profile param ",(0,i.kt)("inlineCode",{parentName:"p"},"-Pflink1.15")," when compiling the codes to adapt the version.\nAlternatively, use ",(0,i.kt)("inlineCode",{parentName:"p"},"hudi-flink1.15-bundle"),". Flink 1.14 and Flink 1.13 will continue to be supported. Please check the\nmigration guide for ",(0,i.kt)("a",{parentName:"p",href:"#bundle-updates"},"bundle updates"),"."),(0,i.kt)("h3",{id:"flink-integration-improvements"},"Flink Integration Improvements"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("strong",{parentName:"li"},"Data skipping")," is supported for batch mode read, set up SQL option ",(0,i.kt)("inlineCode",{parentName:"li"},"metadata.enabled"),", ",(0,i.kt)("inlineCode",{parentName:"li"},"hoodie.metadata.index.column.stats.enable"),"  and ",(0,i.kt)("inlineCode",{parentName:"li"},"read.data.skipping.enabled")," as true to enable it."),(0,i.kt)("li",{parentName:"ul"},"A ",(0,i.kt)("strong",{parentName:"li"},"HMS-based Flink catalog")," is added with catalog identifier as ",(0,i.kt)("inlineCode",{parentName:"li"},"hudi"),". You can instantiate the catalog through API directly or use the ",(0,i.kt)("inlineCode",{parentName:"li"},"CREATE CATALOG"),"  syntax to create it. Specifies catalog option ",(0,i.kt)("inlineCode",{parentName:"li"},"'mode' = 'hms'"),"  to switch to the HMS catalog. By default, the catalog is in ",(0,i.kt)("inlineCode",{parentName:"li"},"dfs")," mode."),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("strong",{parentName:"li"},"Async clustering")," is supported for Flink ",(0,i.kt)("inlineCode",{parentName:"li"},"INSERT")," operation, set up SQL option ",(0,i.kt)("inlineCode",{parentName:"li"},"clustering.schedule.enabled")," and ",(0,i.kt)("inlineCode",{parentName:"li"},"clustering.async.enabled")," as true to enable it. When enabling this feature, a clustering sub-pipeline is scheduled asynchronously continuously to merge the small files continuously into larger ones.")),(0,i.kt)("h3",{id:"performance-improvements"},"Performance Improvements"),(0,i.kt)("p",null,"This version brings more improvements to make Hudi the most performant lake storage format. Some notable improvements are:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Closed the performance gap in writing through Spark datasource vs sql. Previously, datasource writes were faster."),(0,i.kt)("li",{parentName:"ul"},"All built-in key generators implement more performant Spark-specific APIs."),(0,i.kt)("li",{parentName:"ul"},"Replaced UDF in bulk insert operation with RDD transformation to cut down serde cost."),(0,i.kt)("li",{parentName:"ul"},"Optimized column stats index performance in data skipping.")),(0,i.kt)("p",null,"We recently benchmarked Hudi against TPC-DS workload.\nPlease check out ",(0,i.kt)("a",{parentName:"p",href:"/blog/2022/06/29/Apache-Hudi-vs-Delta-Lake-transparent-tpc-ds-lakehouse-performance-benchmarks"},"our blog")," for more details."),(0,i.kt)("h2",{id:"known-regressions"},"Known Regressions:"),(0,i.kt)("p",null,"We discovered a regression in Hudi 0.12 release related to Bloom\nIndex metadata persisted w/in Parquet footers ",(0,i.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/browse/HUDI-4992"},"HUDI-4992"),"."),(0,i.kt)("p",null,"Crux of the problem was that min/max statistics for the record keys were\ncomputed incorrectly during (Spark-specific) ",(0,i.kt)("a",{parentName:"p",href:"https://hudi.apache.org/docs/next/configurations#hoodiedatasourcewriterowwriterenable"},"row-writing"),"\nBulk Insert operation affecting ",(0,i.kt)("a",{parentName:"p",href:"https://hudi.apache.org/docs/next/basic_configurations/#hoodiebloomindexprunebyranges"},"Key Range Pruning flow"),"\nw/in ",(0,i.kt)("a",{parentName:"p",href:"https://hudi.apache.org/docs/next/faq/#how-do-i-configure-bloom-filter-when-bloomglobal_bloom-index-is-used"},"Hoodie Bloom Index"),'\ntagging sequence, resulting into updated records being incorrectly tagged\nas "inserts" and not as "updates", leading to duplicated records in the\ntable.'),(0,i.kt)("p",null,(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/pull/6883"},"PR#6883")," addressing the problem is incorporated into\nHudi 0.12.1 release.*"),(0,i.kt)("p",null,"If all of the following is applicable to you:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Using Spark as an execution engine"),(0,i.kt)("li",{parentName:"ol"},"Using Bulk Insert (using ",(0,i.kt)("a",{parentName:"li",href:"https://hudi.apache.org/docs/next/configurations#hoodiedatasourcewriterowwriterenable"},"row-writing"),",\nenabled ",(0,i.kt)("em",{parentName:"li"},"by default"),")"),(0,i.kt)("li",{parentName:"ol"},"Using Bloom Index (with ",(0,i.kt)("a",{parentName:"li",href:"https://hudi.apache.org/docs/next/basic_configurations/#hoodiebloomindexprunebyranges"},"range-pruning"),"\nenabled, enabled ",(0,i.kt)("em",{parentName:"li"},"by default"),') for "UPSERT" operations')),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Note: Default index type is SIMPLE. So, unless you have over-ridden the index type, you may not hit this issue.")),(0,i.kt)("p",null,"Please consider one of the following potential remediations to avoid\ngetting duplicate records in your pipeline:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("a",{parentName:"li",href:"https://hudi.apache.org/docs/next/basic_configurations/#hoodiebloomindexprunebyranges"},"Disabling Bloom Index range-pruning"),"\nflow (might\naffect performance of upsert operations)"),(0,i.kt)("li",{parentName:"ul"},"Upgrading to 0.12.1."),(0,i.kt)("li",{parentName:"ul"},"Making sure that the ",(0,i.kt)("a",{parentName:"li",href:"https://github.com/apache/hudi/pull/6883"},"fix")," is\nincluded in your custom artifacts (if you're building and using ones)")),(0,i.kt)("p",null,"We also found another regression related to metadata table and timeline server interplay with streaming ingestion pipelines."),(0,i.kt)("p",null,"The FileSystemView that Hudi maintains internally could go out of sync due to a occasional race conditions when table services are involved\n(compaction, clustering) and could result in updates and deletes routed to older file versions and hence resulting in missed updates and deletes."),(0,i.kt)("p",null,"Here are the user-flows that could potentially be impacted with this."),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"This impacts pipelines using Deltastreamer in ",(0,i.kt)("strong",{parentName:"li"},"continuous mode")," (sync once is not impacted), Spark streaming, or if you have been directly\nusing write client across batches/commits instead of the standard ways to write to Hudi. In other words, batch writes should not be impacted."),(0,i.kt)("li",{parentName:"ul"},"Among these write models, this could have an impact only when table services are enabled.",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"COW: clustering enabled (inline or async)"),(0,i.kt)("li",{parentName:"ul"},"MOR: compaction enabled (by default, inline or async)"))),(0,i.kt)("li",{parentName:"ul"},"Also, the impact is applicable only when metadata table is enabled, and timeline server is enabled (which are defaults as of 0.12.0)")),(0,i.kt)("p",null,"Based on some production data, we expect this issue might impact roughly < 1% of updates to be missed, since its a race condition\nand table services are generally scheduled once every N commits. The percentage of update misses could be even less if the\nfrequency of table services is less."),(0,i.kt)("p",null,(0,i.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/browse/HUDI-5863"},"Here")," is the jira for the issue of interest and the fix has already been landed in master.\n0.12.3 should have the ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/pull/8079"},"fix"),". Until we have a 0.12.3 release, we recommend you to disable metadata table\n(",(0,i.kt)("inlineCode",{parentName:"p"},"hoodie.metadata.enable=false"),") to mitigate the issue."),(0,i.kt)("p",null,"We also discovered a regression for Flink streaming writer with the hive meta sync which is introduced by HUDI-3730, the refactoring to ",(0,i.kt)("inlineCode",{parentName:"p"},"HiveSyncConfig"),"\ncauses the Hive ",(0,i.kt)("inlineCode",{parentName:"p"},"Resources")," config objects leaking, which finally leads to an OOM exception for the JobManager if the streaming job runs continuously for weeks.\n0.12.3 should have the ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/apache/hudi/pull/8050"},"fix"),". Until we have a 0.12.3 release, we recommend you to cherry-pick the fix to local\nif hive meta sync is required."),(0,i.kt)("p",null,"Sorry about the inconvenience caused."),(0,i.kt)("h2",{id:"raw-release-notes"},"Raw Release Notes"),(0,i.kt)("p",null,"The raw release notes are available ",(0,i.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12322822&version=12351209"},"here"),"."))}u.isMDXComponent=!0},58215:(e,t,a)=>{a.d(t,{Z:()=>i});var n=a(67294);const i=function(e){let{children:t,hidden:a,className:i}=e;return n.createElement("div",{role:"tabpanel",hidden:a,className:i},t)}},26396:(e,t,a)=>{a.d(t,{Z:()=>c});var n=a(87462),i=a(67294),r=a(72389),o=a(79443);const l=function(){const e=(0,i.useContext)(o.Z);if(null==e)throw new Error('"useUserPreferencesContext" is used outside of "Layout" component.');return e};var s=a(53810),d=a(86010);const p={tabItem:"tabItem_vU9c"};function u(e){const{lazy:t,block:a,defaultValue:r,values:o,groupId:u,className:c}=e,m=i.Children.map(e.children,(e=>{if((0,i.isValidElement)(e)&&void 0!==e.props.value)return e;throw new Error(`Docusaurus error: Bad <Tabs> child <${"string"==typeof e.type?e.type:e.type.name}>: all children of the <Tabs> component should be <TabItem>, and every <TabItem> should have a unique "value" prop.`)})),h=o??m.map((e=>{let{props:{value:t,label:a,attributes:n}}=e;return{value:t,label:a,attributes:n}})),f=(0,s.lx)(h,((e,t)=>e.value===t.value));if(f.length>0)throw new Error(`Docusaurus error: Duplicate values "${f.map((e=>e.value)).join(", ")}" found in <Tabs>. Every value needs to be unique.`);const k=null===r?r:r??m.find((e=>e.props.default))?.props.value??m[0]?.props.value;if(null!==k&&!h.some((e=>e.value===k)))throw new Error(`Docusaurus error: The <Tabs> has a defaultValue "${k}" but none of its children has the corresponding value. Available values are: ${h.map((e=>e.value)).join(", ")}. If you intend to show no default tab, use defaultValue={null} instead.`);const{tabGroupChoices:g,setTabGroupChoices:b}=l(),[v,y]=(0,i.useState)(k),N=[],{blockElementScrollPositionUntilNextRender:w}=(0,s.o5)();if(null!=u){const e=g[u];null!=e&&e!==v&&h.some((t=>t.value===e))&&y(e)}const C=e=>{const t=e.currentTarget,a=N.indexOf(t),n=h[a].value;n!==v&&(w(t),y(n),null!=u&&b(u,n))},S=e=>{let t=null;switch(e.key){case"ArrowRight":{const a=N.indexOf(e.currentTarget)+1;t=N[a]||N[0];break}case"ArrowLeft":{const a=N.indexOf(e.currentTarget)-1;t=N[a]||N[N.length-1];break}}t?.focus()};return i.createElement("div",{className:"tabs-container"},i.createElement("ul",{role:"tablist","aria-orientation":"horizontal",className:(0,d.Z)("tabs",{"tabs--block":a},c)},h.map((e=>{let{value:t,label:a,attributes:r}=e;return i.createElement("li",(0,n.Z)({role:"tab",tabIndex:v===t?0:-1,"aria-selected":v===t,key:t,ref:e=>N.push(e),onKeyDown:S,onFocus:C,onClick:C},r,{className:(0,d.Z)("tabs__item",p.tabItem,r?.className,{"tabs__item--active":v===t})}),a??t)}))),t?(0,i.cloneElement)(m.filter((e=>e.props.value===v))[0],{className:"margin-vert--md"}):i.createElement("div",{className:"margin-vert--md"},m.map(((e,t)=>(0,i.cloneElement)(e,{key:t,hidden:e.props.value!==v})))))}function c(e){const t=(0,r.Z)();return i.createElement(u,(0,n.Z)({key:String(t)},e))}}}]);