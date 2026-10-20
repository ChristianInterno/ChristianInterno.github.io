/* The walkway: across the lake, through the portrait, around San Paolo and onto the shore,
   where it carries the dates of whatever page you are on. */
(function(){
  var NS="http://www.w3.org/2000/svg", root=document.documentElement;
  function $(id){return document.getElementById(id);}
  var lake=$("lake"), shore=$("shore");
  if(!lake||!shore) return;
  var wl=$("walk-lake"), ws=$("walk-shore"), ripples=$("ripples"), who=$("who"), me=$("me"),
      islet=$("islet"), links=$("links"), anchor=$("anchor"), lblIsle=$("lbl-isle"), lblLake=$("lbl-lake"),
      rail=document.querySelector("[data-rail]"), home=document.body.classList.contains("home");
  // remembers where the portrait sat (per window size) so every page shows the same lake,
  // and whether the walkway has already been drawn in this visit
  function keep(area){return {
    get:function(k){try{return JSON.parse(window[area].getItem(k));}catch(e){return null;}},
    set:function(k,v){try{window[area].setItem(k,JSON.stringify(v));}catch(e){}}
  };}
  var store=keep("localStorage"), visit=keep("sessionStorage");
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var animate=!reduce&&!visit.get("walked"), raf=0, lastW=-1, lastH=-1;

  function rel(el,ref){var a=el.getBoundingClientRect(),b=ref.getBoundingClientRect();
    return {l:a.left-b.left,t:a.top-b.top,r:a.right-b.left,b:a.bottom-b.top,w:a.width,h:a.height,
            cx:a.left-b.left+a.width/2,cy:a.top-b.top+a.height/2};}
  function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v));}

  // ripples on the water, kept clear of the name, the labels and the shore line
  function glints(W,H,boxes){
    var s=7,n=Math.round(W*H/30000),out="";
    function r(){s=(s*16807)%2147483647;return (s-1)/2147483646;}
    function hit(x,y,len){for(var j=0;j<boxes.length;j++){var b=boxes[j];
      if(x+len>b.l-10&&x<b.r+10&&y>b.t-10&&y<b.b+10) return true;} return false;}
    for(var i=0;i<n;i++){var x=r()*W,y=r()*H,len=6+r()*22;
      if(hit(x,y,len)) continue;
      out+='<line x1="'+x.toFixed(1)+'" y1="'+y.toFixed(1)+'" x2="'+(x+len).toFixed(1)+'" y2="'+y.toFixed(1)+'"/>';}
    ripples.innerHTML=out;
  }
  function box(el){return el&&el.offsetWidth?rel(el,lake):null;}
  function line(pts,cls,w){var p=document.createElementNS(NS,"polyline");
    p.setAttribute("points",pts.map(function(q){return q[0].toFixed(1)+","+q[1].toFixed(1);}).join(" "));
    p.setAttribute("class",cls); p.setAttribute("stroke-width",w); return p;}
  function plen(pts){var L=0;for(var i=1;i<pts.length;i++)L+=Math.abs(pts[i][0]-pts[i-1][0])+Math.abs(pts[i][1]-pts[i-1][1]);return L;}
  // draws each segment twice: the fold of the fabric (offset) and the walkway on top
  function paint(svg,segs,sw,startDelay,anim){
    svg.innerHTML=""; var acc=0, all=[], speed=1.1;
    segs.forEach(function(s){
      var side=line(s.map(function(q){return [q[0]+3,q[1]+3];}),"side",sw), top=line(s,"top",sw), L=plen(s);
      svg.appendChild(side); svg.appendChild(top);
      if(anim){
        var delay=startDelay+acc/speed, dur=L/speed;
        [side,top].forEach(function(p){p.style.strokeDasharray=L+20; p.style.strokeDashoffset=L+20;
          p.style.transition="stroke-dashoffset "+dur.toFixed(0)+"ms linear "+delay.toFixed(0)+"ms"; all.push(p);});
      }
      acc+=L;
    });
    if(anim){svg.getBoundingClientRect(); all.forEach(function(p){p.style.strokeDashoffset=0;});}
    return startDelay+acc/speed;
  }

  function layout(){
    var vw=root.clientWidth, vh=window.innerHeight, wide=vw>880;
    lastW=vw; lastH=document.body.scrollHeight;
    var LW=lake.clientWidth, LH=lake.clientHeight, SW=shore.clientWidth, SH=shore.clientHeight;
    wl.setAttribute("viewBox","0 0 "+LW+" "+LH);
    ws.setAttribute("width",SW); ws.setAttribute("height",SH); ws.setAttribute("viewBox","0 0 "+SW+" "+SH);
    var id=rel(lake.querySelector(".id"),lake);

    var a=anchor?rel(anchor,shore):null, sw=wide?13:10;
    var dates=rail?[].slice.call(rail.querySelectorAll(".date")).filter(function(d){return !d.closest("details:not([open])");}):[];
    var hasRail=dates.length>0&&a, railX=0, yIn=0, bot=0, stop=0;
    if(hasRail){
      railX=Math.round(rel(dates[0],shore).l+11); yIn=Math.round(a.b+14);
      bot=Math.round(rel(dates[dates.length-1],shore).cy);
      var nx=rail.nextElementSibling; stop=nx?Math.round(rel(nx,shore).t-18):SH-18;
    }
    function railFrom(y){return [[-4,y],[railX,y],[railX,bot]];}
    var lakeSegs=[], shoreSegs=[];

    if(wide){
      // the portrait sits where the walkway can cross straight to the shore
      var lk=rel(links,lake), mw=me.offsetWidth, mh=me.offsetHeight, ring=22, g=30,
          iw=islet.offsetWidth, ih=islet.offsetHeight;
      me.style.left=Math.round(Math.max(ring+4,Math.min(LW*.2,LW-(ring+26+2*g+iw+24)-mw)))+"px";
      var drop=Math.round(sw/2+ring+8+ih+g-4);           // how far the loop around San Paolo reaches
      var minC=Math.round(id.b+28+ring+mh/2),
          maxPhoto=Math.round(lk.t-48-ring-mh/2),         // the portrait clears "Lago d'Iseo"
          maxDown=Math.min(maxPhoto,Math.round(lk.t-20-drop-30)),
          upFrom=Math.round(id.b+14+drop+30);
      function fits(y){ if(y<minC||y>maxPhoto) return 0; if(y<=maxDown) return 1; if(y>=upFrom) return 2; return 0; }
      var want=home&&hasRail?yIn:null, c, aligned=false, saved=store.get("lake");
      if(want!==null&&fits(want)){ c=want; aligned=true; store.set("lake",{w:vw,h:vh,c:c}); }
      else if(saved&&saved.w===vw&&saved.h===vh&&fits(saved.c)) c=saved.c;
      else c=clamp(Math.round(LH*.55),minC,Math.max(minC,maxDown));
      var mode=fits(c);                                    // 1: loop below the walkway, 2: above, 0: no room
      if(mode===1&&c+drop+37>lk.t-74&&c>=upFrom&&c<=maxPhoto) mode=2;   // keep San Paolo clear of Lago d'Iseo
      me.style.top=Math.round(c-mh/2)+"px";
      var m=rel(me,lake), y0=Math.round(m.cy);
      if(mode){
        var dir=mode===2?-1:1,
            xA=Math.round(m.r+ring+Math.max(26,(LW-m.r-ring)*.2)), xc=xA+g+iw/2, xB=Math.round(xc+iw/2+g),
            near=y0+dir*(sw/2+ring+8), far=y0+dir*drop;
        islet.style.display=""; lblIsle.style.display="";
        islet.style.left=Math.round(xc-iw/2)+"px"; islet.style.top=Math.round(dir>0?near:near-ih)+"px";
        lakeSegs=[[[0,y0],[m.l,y0]],[[m.r,y0],[xA,y0],[xA,far],[xB,far],[xB,y0],[LW+4,y0]]];
        lblIsle.style.left=Math.round((xA+xB)/2)+"px"; lblIsle.style.transform="translateX(-50%)";
        lblIsle.style.top=Math.round(dir>0?far+18:far-16-lblIsle.offsetHeight)+"px";
      } else {
        islet.style.display="none"; lblIsle.style.display="none";
        lakeSegs=[[[0,y0],[m.l,y0]],[[m.r,y0],[LW+4,y0]]];
      }
      lblLake.style.left=Math.round(id.l)+"px"; lblLake.style.top=Math.round(lk.t-34)+"px";

      // on the shore: carry on through the dates if the page has any; otherwise the walkway
      // simply reaches the water's edge
      if(hasRail){
        if(aligned) shoreSegs=[railFrom(yIn)];
        else if(y0>=yIn&&y0<=Math.max(bot,stop)) shoreSegs=[[[-4,y0],[railX,y0]],[[railX,yIn],[railX,Math.max(bot,y0)]]];
        else shoreSegs=[railFrom(yIn)];
      } else lakeSegs[lakeSegs.length-1][lakeSegs[lakeSegs.length-1].length-1][0]=LW;
    } else {
      [me,islet,lblIsle,lblLake].forEach(function(el){el.removeAttribute("style");});
      if(me.offsetWidth){
        var m2=rel(me,lake);
        lakeSegs=[[[0,Math.round(m2.cy)],[Math.round(m2.l),Math.round(m2.cy)]]];
      }
      if(hasRail) shoreSegs=[railFrom(yIn)];
      else if(a) shoreSegs=[[[-4,Math.round(a.b+9)],[Math.round(a.l+56),Math.round(a.b+9)]]];
    }
    glints(LW,LH,[id,box(lblIsle),box(lblLake),box(links)].filter(Boolean));
    var t=paint(wl,lakeSegs,sw,350,animate);
    paint(ws,shoreSegs,sw,t,animate);
    if(animate) visit.set("walked",1);
    animate=false;
    lake.classList.add("ready");
  }

  function schedule(){
    if(root.clientWidth===lastW&&document.body.scrollHeight===lastH) return;
    cancelAnimationFrame(raf); raf=requestAnimationFrame(layout);
  }
  function now(){cancelAnimationFrame(raf); raf=requestAnimationFrame(layout);}
  function start(){
    layout();
    window.addEventListener("resize",schedule);
    if("ResizeObserver" in window) new ResizeObserver(schedule).observe(document.body);
    [].forEach.call(document.querySelectorAll("details"),function(d){d.addEventListener("toggle",now);});
  }
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(start,start); else window.addEventListener("load",start);

  // BibTeX: open, close, copy
  document.addEventListener("click",function(e){
    var t=e.target.closest?e.target:e.target.parentNode;
    var tog=t.closest&&t.closest(".bibtoggle");
    if(tog){
      var box=$(tog.getAttribute("aria-controls")); if(!box) return;
      var open=box.hasAttribute("hidden");
      if(open) box.removeAttribute("hidden"); else box.setAttribute("hidden","");
      tog.setAttribute("aria-expanded",open?"true":"false");
      return;
    }
    var b=t.closest&&t.closest(".copy"); if(!b) return;
    var pre=b.parentNode.querySelector("pre"); if(!pre) return;
    var done=function(){b.textContent="Copied"; setTimeout(function(){b.textContent="Copy";},1400);};
    var pick=function(){var r=document.createRange(); r.selectNodeContents(pre); var s=window.getSelection(); s.removeAllRanges(); s.addRange(r);};
    if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(pre.textContent).then(done,pick);
    else pick();
  });
})();
