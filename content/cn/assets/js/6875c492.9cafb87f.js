/*! For license information please see 6875c492.9cafb87f.js.LICENSE.txt */
(self.webpackChunkhudi=self.webpackChunkhudi||[]).push([[48610],{69404:(e,t,a)=>{"use strict";a.r(t),a.d(t,{default:()=>m});var l=a(67294),s=a(39960),r=a(76200),n=a(42544),i=a(95999),o=a(53810);function m(e){const{metadata:t,items:a,sidebar:m}=e,{allTagsPath:c,name:g,count:d}=t,u=function(){const{selectMessage:e}=(0,o.c2)();return t=>e(t,(0,i.I)({id:"theme.blog.post.plurals",description:'Pluralized label for "{count} posts". Use as much plural forms (separated by "|") as your language support (see https://www.unicode.org/cldr/cldr-aux/charts/34/supplemental/language_plural_rules.html)',message:"One post|{count} posts"},{count:t}))}(),p=(0,i.I)({id:"theme.blog.tagTitle",description:"The title of the page for a blog tag",message:'{nPosts} tagged with "{tagName}"'},{nPosts:u(d),tagName:g});return l.createElement(r.Z,{title:p,wrapperClassName:o.kM.wrapper.blogPages,pageClassName:o.kM.page.blogTagPostListPage,searchMetadata:{tag:"blog_tags_posts"},sidebar:m},l.createElement("header",{className:"margin-bottom--xl"},l.createElement("h1",null,p),l.createElement(s.Z,{href:c},l.createElement(i.Z,{id:"theme.tags.tagsPageLink",description:"The label of the link targeting the tag list page"},"View All Tags"))),a.map((e=>{let{content:t}=e;return l.createElement(n.Z,{key:t.metadata.permalink,frontMatter:t.frontMatter,assets:t.assets,metadata:t.metadata,truncated:!0},l.createElement(t,null))})))}},86753:(e,t,a)=>{"use strict";a.d(t,{Z:()=>c});var l=a(67294),s=a(95999),r=a(87462),n=a(86010);const i="iconEdit_mS5F";const o=function(e){let{className:t,...a}=e;return l.createElement("svg",(0,r.Z)({fill:"currentColor",height:"20",width:"20",viewBox:"0 0 40 40",className:(0,n.Z)(i,t),"aria-hidden":"true"},a),l.createElement("g",null,l.createElement("path",{d:"m34.5 11.7l-3 3.1-6.3-6.3 3.1-3q0.5-0.5 1.2-0.5t1.1 0.5l3.9 3.9q0.5 0.4 0.5 1.1t-0.5 1.2z m-29.5 17.1l18.4-18.5 6.3 6.3-18.4 18.4h-6.3v-6.2z"})))};var m=a(53810);function c(e){let{editUrl:t}=e;return l.createElement("a",{href:t,target:"_blank",rel:"noreferrer noopener",className:m.kM.common.editThisPage},l.createElement(o,null),l.createElement(s.Z,{id:"theme.common.editThisPage",description:"The link label to edit the current page"},"Edit this page"))}},7774:(e,t,a)=>{"use strict";a.d(t,{Z:()=>m});var l=a(67294),s=a(86010),r=a(39960);const n="tag_WK-t",i="tagRegular_LXbV",o="tagWithCount_S5Zl";const m=function(e){const{permalink:t,name:a,count:m}=e;return l.createElement(r.Z,{href:t,className:(0,s.Z)(n,{[i]:!m,[o]:m})},a,m&&l.createElement("span",null,m))}},59477:(e,t,a)=>{"use strict";a.d(t,{Z:()=>r});var l=a(67294),s=a(39960);const r=e=>{let{authors:t=[],className:a,withLink:r=!0}=e;const n=e=>l.createElement("span",{className:a,itemProp:"name"},e.name);return l.createElement(l.Fragment,null,t.map(((e,a)=>l.createElement("div",{key:a},l.createElement("div",null,e.name&&l.createElement("div",null,0!==a?a!==t.length-1?",":"and":"",r?l.createElement(s.Z,{href:e.url,itemProp:"url"},n(e)):n(e)))))))}},76200:(e,t,a)=>{"use strict";a.d(t,{Z:()=>c});var l=a(67294),s=a(86010),r=a(77498),n=a(39960);const i={sidebar:"sidebar_q+wC",sidebarItemTitle:"sidebarItemTitle_9G5K",sidebarItemList:"sidebarItemList_6T4b",sidebarItem:"sidebarItem_cjdF",sidebarItemLink:"sidebarItemLink_zyXk",sidebarItemLinkActive:"sidebarItemLinkActive_wcJs"};var o=a(95999);function m(e){let{sidebar:t}=e;return 0===t.items.length?null:l.createElement("nav",{className:(0,s.Z)(i.sidebar,"thin-scrollbar"),"aria-label":(0,o.I)({id:"theme.blog.sidebar.navAriaLabel",message:"Blog recent posts navigation",description:"The ARIA label for recent posts in the blog sidebar"})},l.createElement("div",{className:(0,s.Z)(i.sidebarItemTitle,"margin-bottom--md")},t.title),l.createElement("ul",{className:i.sidebarItemList},t.items.map((e=>l.createElement("li",{key:e.permalink,className:i.sidebarItem},l.createElement(n.Z,{isNavLink:!0,to:e.permalink,className:i.sidebarItemLink,activeClassName:i.sidebarItemLinkActive},e.title))))))}const c=function(e){const{sidebar:t,toc:a,children:n,...i}=e,o=t&&t.items.length>0,c="blog-list-page"===e.pageClassName,g="blog-tags-post-list-page"===e.pageClassName;return l.createElement(r.Z,i,l.createElement("div",{className:"container margin-vert--lg"},l.createElement("div",{className:"row"},o&&l.createElement("aside",{className:"col col--3"},l.createElement(m,{sidebar:t})),l.createElement("main",{className:(0,s.Z)("col",{"col--7":o,"col--9 col--offset-2":!o,row:c||g,"tags-post-list":g}),itemScope:!0,itemType:"http://schema.org/Blog"},n),a&&l.createElement("div",{className:"col col--2"},a))))}},42544:(e,t,a)=>{"use strict";a.d(t,{Z:()=>E});var l=a(67294),s=a(86010),r=a(3905),n=a(95999),i=a(39960),o=a(44996),m=a(53810),c=a(67707),g=a(86753);const d={blogPostTitle:"blogPostTitle_RC3s",videoImage:"videoImage_nxqj",blogPostPageTitle:"blogPostPageTitle_bKZt",blogPostPageTile:"blogPostPageTile_BsLs",blogPostData:"blogPostData_A2Le",blogpostReadingTime:"blogpostReadingTime_Mwxf",tagsWrapperPostPage:"tagsWrapperPostPage_VdId",blogPostDetailsFull:"blogPostDetailsFull_2lop","blog-list-page":"blog-list-page_Jl5M",container:"container_EXwA",row:"row_DZ33",authorsList:"authorsList_svFt",authorsListLong:"authorsListLong_kl47",authorTimeTags:"authorTimeTags_oN88",tag:"tag_MgfY",tagPostPage:"tagPostPage_gnvv",postHeader:"postHeader_Ipb1",greyLink:"greyLink_9KrM",blogPostText:"blogPostText_jBA8",blogInfo:"blogInfo_1FPd",blogPostAuthorsList:"blogPostAuthorsList_dlEG"};var u=a(7774),p=a(59477),b=a(16550),h=a(94184),P=a.n(h);const E=function(e){const t=function(){const{selectMessage:e}=(0,m.c2)();return t=>{const a=Math.ceil(t);return e(a,(0,n.I)({id:"theme.blog.post.readingTime.plurals",description:'Pluralized label for "{readingTime} min read". Use as much plural forms (separated by "|") as your language support (see https://www.unicode.org/cldr/cldr-aux/charts/34/supplemental/language_plural_rules.html)',message:"One min read|{readingTime} min read"},{readingTime:a}))}}(),a=(0,b.TH)(),{withBaseUrl:h}=(0,o.C)(),{children:E,frontMatter:v,assets:f,metadata:T,truncated:N,isBlogPostPage:Z=!1}=e,{date:k,formattedDate:_,permalink:w,tags:L,readingTime:I,title:y,editUrl:A,authors:C}=T,M=f.image??v.image??"/assets/images/hudi-logo-medium.png",x=L.length>0,F=e=>{e&&window.open(e,"_blank","noopener noreferrer")};return l.createElement("article",{className:(0,s.Z)({"blog-list-item":!Z}),itemProp:"blogPost",itemScope:!0,itemType:"http://schema.org/BlogPosting"},(()=>{const e=Z?"h1":"h2";return l.createElement("header",{className:d.postHeader},l.createElement("div",null,!Z&&M&&l.createElement("div",{className:"col blogThumbnail",itemProp:"blogThumbnail"},a.pathname.startsWith("/blog")?l.createElement(i.Z,{itemProp:"url",to:w},l.createElement("img",{src:h(M,{absolute:!0}),className:"blog-image"})):l.createElement("img",{onClick:()=>F(v?.navigate),src:h(M,{absolute:!0}),className:P()(d.videoImage,"blog-image")})),l.createElement(e,{className:d.blogPostTitle,itemProp:"headline"},Z?l.createElement(e,{className:d.blogPostPageTitle,itemProp:"headline"},y):a.pathname.startsWith("/blog")?l.createElement(i.Z,{itemProp:"url",to:w},l.createElement(e,{className:d.blogPostTitle,itemProp:"headline"},y)):l.createElement(e,{onClick:()=>F(v?.navigate),className:d.blogPostTitle,itemProp:"headline"},y)),l.createElement("div",{className:(0,s.Z)(d.blogInfo,"margin-top--sm margin-bottom--sm")},0===C.length?l.createElement("div",{className:(0,s.Z)(d.authorTimeTags,"row 'margin-vert--md'")},l.createElement("time",{dateTime:k,itemProp:"datePublished"},_)):l.createElement(l.Fragment,null,Z?l.createElement("div",{className:(0,s.Z)(d.blogPostText,"row")},l.createElement("time",{dateTime:k,itemProp:"datePublished"},_),l.createElement(p.Z,{authors:C,className:d.blogPostAuthorsList})):l.createElement("div",{className:(0,s.Z)(d.authorTimeTags,"row 'margin-vert--md'")},l.createElement("time",{dateTime:k,itemProp:"datePublished"},_," by"),l.createElement(p.Z,{authors:C,className:d.authorsList}))),Z&&I&&l.createElement("div",{className:(0,s.Z)(d.blogPostData,{[d.blogpostReadingTime]:!Z})},l.createElement(l.Fragment,null,void 0!==I&&l.createElement(l.Fragment,null,t(I)))))),!!L.length&&l.createElement(l.Fragment,null,l.createElement("ul",{className:(0,s.Z)(d.tags,d.authorTimeTags,"padding--none","margin-left--sm",{[d.tagsWrapperPostPage]:Z})},L.map((e=>{let{label:t,permalink:a}=e;return l.createElement("li",{key:a,className:(0,s.Z)(d.tag,{[d.tagPostPage]:Z})},l.createElement(u.Z,{className:(0,s.Z)(d.greyLink),name:t,permalink:a}))})))))})(),Z&&l.createElement("div",{className:"markdown",itemProp:"articleBody"},l.createElement(r.Zo,{components:c.Z},E)),(x||N)&&Z&&A&&l.createElement("footer0",{className:(0,s.Z)("row docusaurus-mt-lg",{[d.blogPostDetailsFull]:Z})},l.createElement("div",{className:"col margin-top--sm"},l.createElement(g.Z,{editUrl:A}))))}},94184:(e,t)=>{var a;!function(){"use strict";var l={}.hasOwnProperty;function s(){for(var e=[],t=0;t<arguments.length;t++){var a=arguments[t];if(a){var r=typeof a;if("string"===r||"number"===r)e.push(a);else if(Array.isArray(a)){if(a.length){var n=s.apply(null,a);n&&e.push(n)}}else if("object"===r){if(a.toString!==Object.prototype.toString&&!a.toString.toString().includes("[native code]")){e.push(a.toString());continue}for(var i in a)l.call(a,i)&&a[i]&&e.push(i)}}}return e.join(" ")}e.exports?(s.default=s,e.exports=s):void 0===(a=function(){return s}.apply(t,[]))||(e.exports=a)}()}}]);