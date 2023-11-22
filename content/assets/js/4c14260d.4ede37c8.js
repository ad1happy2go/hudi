"use strict";(self.webpackChunkhudi=self.webpackChunkhudi||[]).push([[83777],{3905:(e,t,r)=>{r.d(t,{Zo:()=>c,kt:()=>h});var a=r(67294);function n(e,t,r){return t in e?Object.defineProperty(e,t,{value:r,enumerable:!0,configurable:!0,writable:!0}):e[t]=r,e}function i(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(e);t&&(a=a.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),r.push.apply(r,a)}return r}function l(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{};t%2?i(Object(r),!0).forEach((function(t){n(e,t,r[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(r)):i(Object(r)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(r,t))}))}return e}function o(e,t){if(null==e)return{};var r,a,n=function(e,t){if(null==e)return{};var r,a,n={},i=Object.keys(e);for(a=0;a<i.length;a++)r=i[a],t.indexOf(r)>=0||(n[r]=e[r]);return n}(e,t);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);for(a=0;a<i.length;a++)r=i[a],t.indexOf(r)>=0||Object.prototype.propertyIsEnumerable.call(e,r)&&(n[r]=e[r])}return n}var s=a.createContext({}),u=function(e){var t=a.useContext(s),r=t;return e&&(r="function"==typeof e?e(t):l(l({},t),e)),r},c=function(e){var t=u(e.components);return a.createElement(s.Provider,{value:t},e.children)},p="mdxType",d={inlineCode:"code",wrapper:function(e){var t=e.children;return a.createElement(a.Fragment,{},t)}},m=a.forwardRef((function(e,t){var r=e.components,n=e.mdxType,i=e.originalType,s=e.parentName,c=o(e,["components","mdxType","originalType","parentName"]),p=u(r),m=n,h=p["".concat(s,".").concat(m)]||p[m]||d[m]||i;return r?a.createElement(h,l(l({ref:t},c),{},{components:r})):a.createElement(h,l({ref:t},c))}));function h(e,t){var r=arguments,n=t&&t.mdxType;if("string"==typeof e||n){var i=r.length,l=new Array(i);l[0]=m;var o={};for(var s in t)hasOwnProperty.call(t,s)&&(o[s]=t[s]);o.originalType=e,o[p]="string"==typeof e?e:n,l[1]=o;for(var u=2;u<i;u++)l[u]=r[u];return a.createElement.apply(null,l)}return a.createElement.apply(null,r)}m.displayName="MDXCreateElement"},34367:(e,t,r)=>{r.r(t),r.d(t,{contentTitle:()=>l,default:()=>p,frontMatter:()=>i,metadata:()=>o,toc:()=>s});var a=r(87462),n=(r(67294),r(3905));r(26396),r(58215);const i={title:"Release 0.8.0",sidebar_position:14,layout:"releases",toc:!0},l=void 0,o={unversionedId:"release-0.8.0",id:"release-0.8.0",title:"Release 0.8.0",description:"Release 0.8.0 (docs)",source:"@site/releases/release-0.8.0.md",sourceDirName:".",slug:"/release-0.8.0",permalink:"/releases/release-0.8.0",tags:[],version:"current",sidebarPosition:14,frontMatter:{title:"Release 0.8.0",sidebar_position:14,layout:"releases",toc:!0},sidebar:"releases",previous:{title:"Release 0.9.0",permalink:"/releases/release-0.9.0"},next:{title:"Release 0.7.0",permalink:"/releases/release-0.7.0"}},s=[{value:"Release 0.8.0 (docs)",id:"release-080-docs",children:[],level:2},{value:"Migration Guide for this release",id:"migration-guide-for-this-release",children:[],level:2},{value:"Release Highlights",id:"release-highlights",children:[{value:"Flink Integration",id:"flink-integration",children:[],level:3},{value:"Parallel Writers Support",id:"parallel-writers-support",children:[],level:3},{value:"Writer side improvements",id:"writer-side-improvements",children:[],level:3},{value:"Query side improvements",id:"query-side-improvements",children:[],level:3},{value:"Raw Release Notes",id:"raw-release-notes",children:[],level:3}],level:2}],u={toc:s},c="wrapper";function p(e){let{components:t,...r}=e;return(0,n.kt)(c,(0,a.Z)({},u,r,{components:t,mdxType:"MDXLayout"}),(0,n.kt)("h2",{id:"release-080-docs"},(0,n.kt)("a",{parentName:"h2",href:"https://github.com/apache/hudi/releases/tag/release-0.8.0"},"Release 0.8.0")," (",(0,n.kt)("a",{parentName:"h2",href:"/docs/0.8.0/quick-start-guide"},"docs"),")"),(0,n.kt)("h2",{id:"migration-guide-for-this-release"},"Migration Guide for this release"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"If migrating from release older than 0.5.3, please also check the upgrade instructions for each subsequent release below."),(0,n.kt)("li",{parentName:"ul"},"Specifically check upgrade instructions for 0.6.0. This release does not introduce any new table versions."),(0,n.kt)("li",{parentName:"ul"},"The ",(0,n.kt)("inlineCode",{parentName:"li"},"HoodieRecordPayload")," interface deprecated existing methods, in favor of new ones that also lets us pass properties at runtime. Users are\nencouraged to migrate out of the deprecated methods, since they will be removed in 0.9.0."),(0,n.kt)("li",{parentName:"ul"},'"auto.offset.reset" is a config used for Kafka sources in deltastreamer utility to reset offset to be consumed from such\nsources. We had a bug around this config with 0.8.0 which has been fixed in 0.9.0. Please use "auto.reset.offsets" instead.\nPossible values for this config are "earliest" and "latest"(default). So, would recommend using "auto.reset.offsets" only in\n0.8.0 and for all other releases, you can use "auto.offset.reset".')),(0,n.kt)("h2",{id:"release-highlights"},"Release Highlights"),(0,n.kt)("h3",{id:"flink-integration"},"Flink Integration"),(0,n.kt)("p",null,"Since the initial support for the Hudi Flink Writer in the 0.7.0 release, the Hudi community made great progress on improving the Flink/Hudi integration,\nincluding redesigning the Flink writer pipeline with better performance and scalability, state-backed indexing with bootstrap support,\nFlink writer for MOR table, batch reader for COW&MOR table, streaming reader for MOR table, and Flink SQL connector for both source and sink.\nIn the 0.8.0 release, user is able to use all those features with Flink 1.11+."),(0,n.kt)("p",null,"Please see ",(0,n.kt)("a",{parentName:"p",href:"https://cwiki.apache.org/confluence/display/HUDI/RFC+-+24%3A+Hoodie+Flink+Writer+Proposal"},"RFC-24"),"\nfor more implementation details for the Flink writer and follow this ",(0,n.kt)("a",{parentName:"p",href:"/docs/flink-quick-start-guide"},"page"),"\nto get started with Flink!"),(0,n.kt)("h3",{id:"parallel-writers-support"},"Parallel Writers Support"),(0,n.kt)("p",null,"As many users requested, now Hudi supports multiple ingestion writers to the same Hudi Table with optimistic concurrency control.\nHudi supports file level OCC, i.e., for any 2 commits (or writers) happening to the same table, if they do not have writes to overlapping files being changed,\nboth writers are allowed to succeed. This feature is currently experimental and requires either Zookeeper or HiveMetastore to acquire locks."),(0,n.kt)("p",null,"Please see ",(0,n.kt)("a",{parentName:"p",href:"https://cwiki.apache.org/confluence/display/HUDI/RFC+-+22+%3A+Snapshot+Isolation+using+Optimistic+Concurrency+Control+for+multi-writers"},"RFC-22"),"\nfor more implementation details and follow this ",(0,n.kt)("a",{parentName:"p",href:"/docs/concurrency_control"},"page")," to get started with concurrency control!"),(0,n.kt)("h3",{id:"writer-side-improvements"},"Writer side improvements"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"InsertOverwrite Support for Flink writer client."),(0,n.kt)("li",{parentName:"ul"},"Support CopyOnWriteTable in Java writer client.")),(0,n.kt)("h3",{id:"query-side-improvements"},"Query side improvements"),(0,n.kt)("ul",null,(0,n.kt)("li",{parentName:"ul"},"Support Spark Structured Streaming read from Hudi table."),(0,n.kt)("li",{parentName:"ul"},"Performance improvement of Metadata table."),(0,n.kt)("li",{parentName:"ul"},"Performance improvement of Clustering.")),(0,n.kt)("h3",{id:"raw-release-notes"},"Raw Release Notes"),(0,n.kt)("p",null,"The raw release notes are available ",(0,n.kt)("a",{parentName:"p",href:"https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12322822&version=12349423"},"here")))}p.isMDXComponent=!0},58215:(e,t,r)=>{r.d(t,{Z:()=>n});var a=r(67294);const n=function(e){let{children:t,hidden:r,className:n}=e;return a.createElement("div",{role:"tabpanel",hidden:r,className:n},t)}},26396:(e,t,r)=>{r.d(t,{Z:()=>d});var a=r(87462),n=r(67294),i=r(72389),l=r(79443);const o=function(){const e=(0,n.useContext)(l.Z);if(null==e)throw new Error('"useUserPreferencesContext" is used outside of "Layout" component.');return e};var s=r(53810),u=r(86010);const c={tabItem:"tabItem_vU9c"};function p(e){const{lazy:t,block:r,defaultValue:i,values:l,groupId:p,className:d}=e,m=n.Children.map(e.children,(e=>{if((0,n.isValidElement)(e)&&void 0!==e.props.value)return e;throw new Error(`Docusaurus error: Bad <Tabs> child <${"string"==typeof e.type?e.type:e.type.name}>: all children of the <Tabs> component should be <TabItem>, and every <TabItem> should have a unique "value" prop.`)})),h=l??m.map((e=>{let{props:{value:t,label:r,attributes:a}}=e;return{value:t,label:r,attributes:a}})),f=(0,s.lx)(h,((e,t)=>e.value===t.value));if(f.length>0)throw new Error(`Docusaurus error: Duplicate values "${f.map((e=>e.value)).join(", ")}" found in <Tabs>. Every value needs to be unique.`);const v=null===i?i:i??m.find((e=>e.props.default))?.props.value??m[0]?.props.value;if(null!==v&&!h.some((e=>e.value===v)))throw new Error(`Docusaurus error: The <Tabs> has a defaultValue "${v}" but none of its children has the corresponding value. Available values are: ${h.map((e=>e.value)).join(", ")}. If you intend to show no default tab, use defaultValue={null} instead.`);const{tabGroupChoices:b,setTabGroupChoices:g}=o(),[k,y]=(0,n.useState)(v),w=[],{blockElementScrollPositionUntilNextRender:O}=(0,s.o5)();if(null!=p){const e=b[p];null!=e&&e!==k&&h.some((t=>t.value===e))&&y(e)}const N=e=>{const t=e.currentTarget,r=w.indexOf(t),a=h[r].value;a!==k&&(O(t),y(a),null!=p&&g(p,a))},P=e=>{let t=null;switch(e.key){case"ArrowRight":{const r=w.indexOf(e.currentTarget)+1;t=w[r]||w[0];break}case"ArrowLeft":{const r=w.indexOf(e.currentTarget)-1;t=w[r]||w[w.length-1];break}}t?.focus()};return n.createElement("div",{className:"tabs-container"},n.createElement("ul",{role:"tablist","aria-orientation":"horizontal",className:(0,u.Z)("tabs",{"tabs--block":r},d)},h.map((e=>{let{value:t,label:r,attributes:i}=e;return n.createElement("li",(0,a.Z)({role:"tab",tabIndex:k===t?0:-1,"aria-selected":k===t,key:t,ref:e=>w.push(e),onKeyDown:P,onFocus:N,onClick:N},i,{className:(0,u.Z)("tabs__item",c.tabItem,i?.className,{"tabs__item--active":k===t})}),r??t)}))),t?(0,n.cloneElement)(m.filter((e=>e.props.value===k))[0],{className:"margin-vert--md"}):n.createElement("div",{className:"margin-vert--md"},m.map(((e,t)=>(0,n.cloneElement)(e,{key:t,hidden:e.props.value!==k})))))}function d(e){const t=(0,i.Z)();return n.createElement(p,(0,a.Z)({key:String(t)},e))}}}]);