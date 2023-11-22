"use strict";(self.webpackChunkhudi=self.webpackChunkhudi||[]).push([[57657],{3905:(e,t,a)=>{a.d(t,{Zo:()=>d,kt:()=>h});var r=a(67294);function n(e,t,a){return t in e?Object.defineProperty(e,t,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[t]=a,e}function i(e,t){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),a.push.apply(a,r)}return a}function o(e){for(var t=1;t<arguments.length;t++){var a=null!=arguments[t]?arguments[t]:{};t%2?i(Object(a),!0).forEach((function(t){n(e,t,a[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):i(Object(a)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))}))}return e}function l(e,t){if(null==e)return{};var a,r,n=function(e,t){if(null==e)return{};var a,r,n={},i=Object.keys(e);for(r=0;r<i.length;r++)a=i[r],t.indexOf(a)>=0||(n[a]=e[a]);return n}(e,t);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);for(r=0;r<i.length;r++)a=i[r],t.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(e,a)&&(n[a]=e[a])}return n}var s=r.createContext({}),u=function(e){var t=r.useContext(s),a=t;return e&&(a="function"==typeof e?e(t):o(o({},t),e)),a},d=function(e){var t=u(e.components);return r.createElement(s.Provider,{value:t},e.children)},p="mdxType",c={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},m=r.forwardRef((function(e,t){var a=e.components,n=e.mdxType,i=e.originalType,s=e.parentName,d=l(e,["components","mdxType","originalType","parentName"]),p=u(a),m=n,h=p["".concat(s,".").concat(m)]||p[m]||c[m]||i;return a?r.createElement(h,o(o({ref:t},d),{},{components:a})):r.createElement(h,o({ref:t},d))}));function h(e,t){var a=arguments,n=t&&t.mdxType;if("string"==typeof e||n){var i=a.length,o=new Array(i);o[0]=m;var l={};for(var s in t)hasOwnProperty.call(t,s)&&(l[s]=t[s]);l.originalType=e,l[p]="string"==typeof e?e:n,o[1]=l;for(var u=2;u<i;u++)o[u]=a[u];return r.createElement.apply(null,o)}return r.createElement.apply(null,a)}m.displayName="MDXCreateElement"},59127:(e,t,a)=>{a.r(t),a.d(t,{contentTitle:()=>o,default:()=>p,frontMatter:()=>i,metadata:()=>l,toc:()=>s});var r=a(87462),n=(a(67294),a(3905));a(26396),a(58215);const i={title:"Release 0.6.0",sidebar_position:16,layout:"releases",toc:!0},o=void 0,l={unversionedId:"release-0.6.0",id:"release-0.6.0",title:"Release 0.6.0",description:"Release 0.6.0 (docs)",source:"@site/releases/release-0.6.0.md",sourceDirName:".",slug:"/release-0.6.0",permalink:"/releases/release-0.6.0",tags:[],version:"current",sidebarPosition:16,frontMatter:{title:"Release 0.6.0",sidebar_position:16,layout:"releases",toc:!0},sidebar:"releases",previous:{title:"Release 0.7.0",permalink:"/releases/release-0.7.0"},next:{title:"Older Releases",permalink:"/releases/older-releases"}},s=[{value:"Release 0.6.0 (docs)",id:"release-060-docs",children:[],level:2},{value:"Migration Guide for this release",id:"migration-guide-for-this-release",children:[],level:2},{value:"Release Highlights",id:"release-highlights",children:[{value:"Writer side improvements:",id:"writer-side-improvements",children:[],level:3},{value:"Query side improvements:",id:"query-side-improvements",children:[],level:3},{value:"Usability:",id:"usability",children:[],level:3}],level:2},{value:"Raw Release Notes",id:"raw-release-notes",children:[],level:2}],u={toc:s},d="wrapper";function p(e){let{components:t,...a}=e;return(0,n.kt)(d,(0,r.Z)({},u,a,{components:t,mdxType:"MDXLayout"}),(0,n.kt)("h2",{id:"release-060-docs"},(0,n.kt)("a",{parentName:"h2",href:"https://github.com/apache/hudi/releases/tag/release-0.6.0"},"Release 0.6.0")," (",(0,n.kt)("a",{parentName:"h2",href:"/docs/0.6.0/quick-start-guide"},"docs"),")"),(0,n.kt)("h2",{id:"migration-guide-for-this-release"},"Migration Guide for this release"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"If migrating from release older than 0.5.3, please also check the upgrade instructions for each subsequent release below."),(0,n.kt)("li",{parentName:"ul"},"With 0.6.0 Hudi is moving from list based rollback to marker based rollbacks. To smoothly aid this transition a\nnew property called ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.table.version")," is added to ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.properties")," file. Whenever Hudi is launched with\nnewer table version i.e 1 (or moving from pre 0.6.0 to 0.6.0), an upgrade step will be executed automatically.\nThis automatic upgrade step will happen just once per Hudi table as the ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.table.version")," will be updated in property file after upgrade is completed."),(0,n.kt)("li",{parentName:"ul"},"Similarly, a command line tool for Downgrading (command - ",(0,n.kt)("inlineCode",{parentName:"li"},"downgrade"),") is added if in case some users want to downgrade Hudi from table version 1 to 0 or move from Hudi 0.6.0 to pre 0.6.0"),(0,n.kt)("li",{parentName:"ul"},"If you were using a user defined partitioner with bulkInsert() RDD API, the base interface has changed to ",(0,n.kt)("inlineCode",{parentName:"li"},"BulkInsertPartitioner")," and will need minor adjustments to your existing implementations.")),(0,n.kt)("h2",{id:"release-highlights"},"Release Highlights"),(0,n.kt)("h3",{id:"writer-side-improvements"},"Writer side improvements:"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"Bootstrapping existing parquet datasets :  Adds support for bootstrapping existing datasets into Hudi, via both Spark datasource writer and\ndeltastreamer tool, with support for reading from Hive, SparkSQL, AWS Athena (prestoDB support coming soon). See ",(0,n.kt)("a",{parentName:"li",href:"https://cwiki.apache.org/confluence/display/HUDI/RFC+-+15%3A+HUDI+File+Listing+and+Query+Planning+Improvements"},"RFC-15")," for technical details.\nNote that this is an experimental feature, which will be improved upon further in the 0.6.x versions."),(0,n.kt)("li",{parentName:"ul"},"Native row writing for bulk_insert : Avoids any dataframe-rdd conversion for bulk_insert path, which can improve performance of initial bulk loads.\nAlthough, this is typically not the bottleneck for upsert/deletes, subsequent releases in 0.6.x versions will expand this to other write operations\nto make reasoning about schema management easier, avoiding the spark-avro conversion totally."),(0,n.kt)("li",{parentName:"ul"},"Bulk insert sort modes : Hudi bulk_insert sorts the input globally to optimize file sizes and avoid out-of-memory issues encountered when writing parallely to multiple DFS partitions.\nFor users who want to prepare the dataframe for writing outside of Hudi, we have made this configurable using ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.bulkinsert.sort.mode"),"."),(0,n.kt)("li",{parentName:"ul"},"Cleaning can now be run concurrently with writing, using ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.clean.async=true"),"which can speed up time taken to finish committing."),(0,n.kt)("li",{parentName:"ul"},"Async compaction for spark streaming writes to hudi table, is now self managed by default, controlling ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.datasource.compaction.async.enable"),"."),(0,n.kt)("li",{parentName:"ul"},"Rollbacks no longer perform full table listings, by leveraging marker files. To enable, set ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.rollback.using.markers=true"),"."),(0,n.kt)("li",{parentName:"ul"},"Added a new index ",(0,n.kt)("inlineCode",{parentName:"li"},"hoodie.index.type=SIMPLE")," which can be faster than ",(0,n.kt)("inlineCode",{parentName:"li"},"BLOOM_INDEX")," for cases where updates/deletes spread across a large portion of the table."),(0,n.kt)("li",{parentName:"ul"},"Hudi now supports ",(0,n.kt)("inlineCode",{parentName:"li"},"Azure Data Lake Storage V2")," , ",(0,n.kt)("inlineCode",{parentName:"li"},"Alluxio")," and ",(0,n.kt)("inlineCode",{parentName:"li"},"Tencent Cloud Object Storage")," storages."),(0,n.kt)("li",{parentName:"ul"},(0,n.kt)("a",{parentName:"li",href:"https://hudi.apache.org/docs/writing_data#multitabledeltastreamer"},"HoodieMultiDeltaStreamer")," adds support for ingesting multiple kafka streams in a single DeltaStreamer deployment, effectively reducing operational burden for using delta streamer\nas your data lake ingestion tool (Experimental feature)"),(0,n.kt)("li",{parentName:"ul"},"Added a new tool - InitialCheckPointProvider, to set checkpoints when migrating to DeltaStreamer after an initial load of the table is complete."),(0,n.kt)("li",{parentName:"ul"},"Delta Streamer tool now supports ingesting CSV data sources, chaining of multiple transformers to build more advanced ETL jobs."),(0,n.kt)("li",{parentName:"ul"},"Introducing a new ",(0,n.kt)("inlineCode",{parentName:"li"},"CustomKeyGenerator")," key generator class, that provides flexible configurations to provide enable different types of key, partition path generation in  single class.\nWe also added support for more time units and date/time formats in ",(0,n.kt)("inlineCode",{parentName:"li"},"TimestampBasedKeyGenerator"),". See ",(0,n.kt)("a",{parentName:"li",href:"https://hudi.apache.org/docs/writing_data#key-generation"},"docs")," for more.")),(0,n.kt)("h3",{id:"query-side-improvements"},"Query side improvements:"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"Starting 0.6.0, snapshot queries are feasible on MOR tables using spark datasource. (experimental feature)"),(0,n.kt)("li",{parentName:"ul"},"In prior versions we only supported ",(0,n.kt)("inlineCode",{parentName:"li"},"HoodieCombineHiveInputFormat")," for CopyOnWrite tables to ensure that there is a limit on the number of mappers spawned for\nany query. Hudi now supports Merge on Read tables also using ",(0,n.kt)("inlineCode",{parentName:"li"},"HoodieCombineInputFormat"),"."),(0,n.kt)("li",{parentName:"ul"},"Speedup spark read queries by caching metaclient in HoodieROPathFilter. This helps reduce listing related overheads in S3 when filtering files for read-optimized queries.")),(0,n.kt)("h3",{id:"usability"},"Usability:"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"Spark DAGs are named to aid better debuggability."),(0,n.kt)("li",{parentName:"ul"},"Support pluggable metrics reporting by introducing proper abstraction for user defined metrics. Console, JMX, Prometheus and DataDog metric reporters have been added."),(0,n.kt)("li",{parentName:"ul"},"A new utility called Data snapshot exporter has been added. Latest table snapshot as of a certain point in time can be exported as plain parquet files with this tool."),(0,n.kt)("li",{parentName:"ul"},"Introduce write committed callback hooks for incremental pipelines to be notified and act on new commits in the timeline. For e.g, Apache Airflow jobs can be triggered\nas new commits arrive."),(0,n.kt)("li",{parentName:"ul"},"Added support for deleting savepoints via CLI"),(0,n.kt)("li",{parentName:"ul"},"Added a new command - ",(0,n.kt)("inlineCode",{parentName:"li"},"export instants"),", to export metadata of instants")),(0,n.kt)("h2",{id:"raw-release-notes"},"Raw Release Notes"),(0,n.kt)("p",null,"The raw release notes are available ",(0,n.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12322822&version=12346663"},"here")))}p.isMDXComponent=!0},58215:(e,t,a)=>{a.d(t,{Z:()=>n});var r=a(67294);const n=function(e){let{children:t,hidden:a,className:n}=e;return r.createElement("div",{role:"tabpanel",hidden:a,className:n},t)}},26396:(e,t,a)=>{a.d(t,{Z:()=>c});var r=a(87462),n=a(67294),i=a(72389),o=a(79443);const l=function(){const e=(0,n.useContext)(o.Z);if(null==e)throw new Error('"useUserPreferencesContext" is used outside of "Layout" component.');return e};var s=a(53810),u=a(86010);const d={tabItem:"tabItem_vU9c"};function p(e){const{lazy:t,block:a,defaultValue:i,values:o,groupId:p,className:c}=e,m=n.Children.map(e.children,(e=>{if((0,n.isValidElement)(e)&&void 0!==e.props.value)return e;throw new Error(`Docusaurus error: Bad <Tabs> child <${"string"==typeof e.type?e.type:e.type.name}>: all children of the <Tabs> component should be <TabItem>, and every <TabItem> should have a unique "value" prop.`)})),h=o??m.map((e=>{let{props:{value:t,label:a,attributes:r}}=e;return{value:t,label:a,attributes:r}})),f=(0,s.lx)(h,((e,t)=>e.value===t.value));if(f.length>0)throw new Error(`Docusaurus error: Duplicate values "${f.map((e=>e.value)).join(", ")}" found in <Tabs>. Every value needs to be unique.`);const b=null===i?i:i??m.find((e=>e.props.default))?.props.value??m[0]?.props.value;if(null!==b&&!h.some((e=>e.value===b)))throw new Error(`Docusaurus error: The <Tabs> has a defaultValue "${b}" but none of its children has the corresponding value. Available values are: ${h.map((e=>e.value)).join(", ")}. If you intend to show no default tab, use defaultValue={null} instead.`);const{tabGroupChoices:g,setTabGroupChoices:k}=l(),[v,y]=(0,n.useState)(b),w=[],{blockElementScrollPositionUntilNextRender:N}=(0,s.o5)();if(null!=p){const e=g[p];null!=e&&e!==v&&h.some((t=>t.value===e))&&y(e)}const C=e=>{const t=e.currentTarget,a=w.indexOf(t),r=h[a].value;r!==v&&(N(t),y(r),null!=p&&k(p,r))},O=e=>{let t=null;switch(e.key){case"ArrowRight":{const a=w.indexOf(e.currentTarget)+1;t=w[a]||w[0];break}case"ArrowLeft":{const a=w.indexOf(e.currentTarget)-1;t=w[a]||w[w.length-1];break}}t?.focus()};return n.createElement("div",{className:"tabs-container"},n.createElement("ul",{role:"tablist","aria-orientation":"horizontal",className:(0,u.Z)("tabs",{"tabs--block":a},c)},h.map((e=>{let{value:t,label:a,attributes:i}=e;return n.createElement("li",(0,r.Z)({role:"tab",tabIndex:v===t?0:-1,"aria-selected":v===t,key:t,ref:e=>w.push(e),onKeyDown:O,onFocus:C,onClick:C},i,{className:(0,u.Z)("tabs__item",d.tabItem,i?.className,{"tabs__item--active":v===t})}),a??t)}))),t?(0,n.cloneElement)(m.filter((e=>e.props.value===v))[0],{className:"margin-vert--md"}):n.createElement("div",{className:"margin-vert--md"},m.map(((e,t)=>(0,n.cloneElement)(e,{key:t,hidden:e.props.value!==v})))))}function c(e){const t=(0,i.Z)();return n.createElement(p,(0,r.Z)({key:String(t)},e))}}}]);