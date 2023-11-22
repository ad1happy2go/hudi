"use strict";(self.webpackChunkhudi=self.webpackChunkhudi||[]).push([[23539],{3905:(e,t,a)=>{a.d(t,{Zo:()=>d,kt:()=>g});var r=a(67294);function n(e,t,a){return t in e?Object.defineProperty(e,t,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[t]=a,e}function o(e,t){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),a.push.apply(a,r)}return a}function l(e){for(var t=1;t<arguments.length;t++){var a=null!=arguments[t]?arguments[t]:{};t%2?o(Object(a),!0).forEach((function(t){n(e,t,a[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):o(Object(a)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))}))}return e}function i(e,t){if(null==e)return{};var a,r,n=function(e,t){if(null==e)return{};var a,r,n={},o=Object.keys(e);for(r=0;r<o.length;r++)a=o[r],t.indexOf(a)>=0||(n[a]=e[a]);return n}(e,t);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);for(r=0;r<o.length;r++)a=o[r],t.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(e,a)&&(n[a]=e[a])}return n}var s=r.createContext({}),c=function(e){var t=r.useContext(s),a=t;return e&&(a="function"==typeof e?e(t):l(l({},t),e)),a},d=function(e){var t=c(e.components);return r.createElement(s.Provider,{value:t},e.children)},u="mdxType",m={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},p=r.forwardRef((function(e,t){var a=e.components,n=e.mdxType,o=e.originalType,s=e.parentName,d=i(e,["components","mdxType","originalType","parentName"]),u=c(a),p=n,g=u["".concat(s,".").concat(p)]||u[p]||m[p]||o;return a?r.createElement(g,l(l({ref:t},d),{},{components:a})):r.createElement(g,l({ref:t},d))}));function g(e,t){var a=arguments,n=t&&t.mdxType;if("string"==typeof e||n){var o=a.length,l=new Array(o);l[0]=p;var i={};for(var s in t)hasOwnProperty.call(t,s)&&(i[s]=t[s]);i.originalType=e,i[u]="string"==typeof e?e:n,l[1]=i;for(var c=2;c<o;c++)l[c]=a[c];return r.createElement.apply(null,l)}return r.createElement.apply(null,a)}p.displayName="MDXCreateElement"},6746:(e,t,a)=>{a.d(t,{Z:()=>o});var r=a(67294),n=a(72389);function o(e){let{children:t,url:o}=e;return(0,n.Z)()&&(a.g.window.location.href=o),r.createElement("span",null,t,"or click ",r.createElement("a",{href:o},"here"))}},17378:(e,t,a)=>{a.r(t),a.d(t,{assets:()=>c,contentTitle:()=>i,default:()=>p,frontMatter:()=>l,metadata:()=>s,toc:()=>d});var r=a(87462),n=(a(67294),a(3905)),o=a(6746);const l={title:"Load data incrementally from transactional data lakes to data warehouses",excerpt:"Load data incrementally from Apache Hudi table to Amazon Redshift using a Hudi incremental query",author:"Noritaka Sekiyama",category:"blog",image:"/assets/images/blog/2023-10-19-load-data-incrementally-from-transactional-data-lakes-to-data-warehouses.png",tags:["incremental updates","amazon","how to","querying","aws","redshift","apache hudi"]},i=void 0,s={permalink:"/blog/2023/10/19/load-data-incrementally-from-transactional-data-lakes-to-data-warehouses",editUrl:"https://github.com/apache/hudi/edit/asf-site/website/blog/blog/2023-10-19-load-data-incrementally-from-transactional-data-lakes-to-data-warehouses.mdx",source:"@site/blog/2023-10-19-load-data-incrementally-from-transactional-data-lakes-to-data-warehouses.mdx",title:"Load data incrementally from transactional data lakes to data warehouses",description:"Redirecting... please wait!!",date:"2023-10-19T00:00:00.000Z",formattedDate:"October 19, 2023",tags:[{label:"incremental updates",permalink:"/blog/tags/incremental-updates"},{label:"amazon",permalink:"/blog/tags/amazon"},{label:"how to",permalink:"/blog/tags/how-to"},{label:"querying",permalink:"/blog/tags/querying"},{label:"aws",permalink:"/blog/tags/aws"},{label:"redshift",permalink:"/blog/tags/redshift"},{label:"apache hudi",permalink:"/blog/tags/apache-hudi"}],readingTime:.045,truncated:!1,authors:[{name:"Noritaka Sekiyama"}],prevItem:{title:"It's Time for the Universal Data Lakehouse",permalink:"/blog/2023/10/20/Its-Time-for-the-Universal-Data-Lakehouse"},nextItem:{title:"Get started with Apache Hudi using AWS Glue by implementing key design concepts \u2013 Part 1",permalink:"/blog/2023/10/17/Get-started-with-Apache-Hudi-using-AWS-Glue-by-implementing-key-design-concepts-Part-1"}},c={authorsImageUrls:[void 0]},d=[],u={toc:d},m="wrapper";function p(e){let{components:t,...a}=e;return(0,n.kt)(m,(0,r.Z)({},u,a,{components:t,mdxType:"MDXLayout"}),(0,n.kt)(o.Z,{url:"https://aws.amazon.com/blogs/big-data/load-data-incrementally-from-transactional-data-lakes-to-data-warehouses/",mdxType:"Redirect"},"Redirecting... please wait!! "))}p.isMDXComponent=!0}}]);