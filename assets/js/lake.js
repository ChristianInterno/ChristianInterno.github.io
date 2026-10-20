/* Lago d'Iseo, simulated, and drawn by hand.
   The water is a small solver for the 2D wave equation, drawn as pencil lines. The orange walkway
   floats on it, moored at the shore, at the island (the portrait) and where it reaches the page;
   on the page it carries the dates. Move across the water, or tap it, and the ripples travel,
   reflect off the island and fade. */
(function(){
  "use strict";
  var NS="http://www.w3.org/2000/svg", root=document.documentElement;
  function $(id){return document.getElementById(id);}
  var lake=$("lake"), shore=$("shore");
  if(!lake||!shore) return;
  var water=$("water"), ws=$("walk-shore"), me=$("me"), who=$("who"), links=$("links"), cap=$("lbl-lake"),
      anchor=$("anchor"), rail=document.querySelector("[data-rail]"), home=document.body.classList.contains("home");

  // where the island sat (per window size), so every page shows the same lake;
  // and whether the walkway has already been laid out in this visit
  function keep(area){return {
    get:function(k){try{return JSON.parse(window[area].getItem(k));}catch(e){return null;}},
    set:function(k,v){try{window[area].setItem(k,JSON.stringify(v));}catch(e){}}
  };}
  var store=keep("localStorage"), visit=keep("sessionStorage");
  var still=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var drawIn=!still&&!visit.get("walked"), layoutRaf=0, lastW=-1, lastH=-1;

  function rel(el,ref){var a=el.getBoundingClientRect(),b=ref.getBoundingClientRect();
    return {l:a.left-b.left,t:a.top-b.top,r:a.right-b.left,b:a.bottom-b.top,w:a.width,h:a.height,
            cx:a.left-b.left+a.width/2,cy:a.top-b.top+a.height/2};}
  function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v));}
  function node(tag,cls){var e=document.createElementNS(NS,tag); if(cls) e.setAttribute("class",cls); return e;}
  function pts(a){var s="";for(var i=0;i<a.length;i+=2) s+=(i?" ":"")+a[i].toFixed(1)+","+a[i+1].toFixed(1);return s;}
  function rand(seed){var s=(seed*7919+13)%2147483647||1; return function(){s=(s*16807)%2147483647;return (s-1)/2147483646;};}
  // a hand is never ruler-straight: a slow, seeded wobble for every stroke
  function hand(seed,amp){
    var r=rand(seed), p0=r()*6.283, p1=r()*6.283, p2=r()*6.283; amp=amp||1;
    return function(x){return amp*(0.55*Math.sin(x/61+p0)+0.32*Math.sin(x/27+p1)+0.16*Math.sin(x/11.5+p2));};
  }
  function breaks(seed,len){       // pencil strokes: long runs with short lifts, different on every line
    var r=rand(seed), out=[], total=0; r(); r();
    while(total<len+400){var on=50+r()*230, off=5+r()*16; out.push(on.toFixed(0),off.toFixed(0)); total+=on+off;}
    return out.join(" ");
  }

  /* ---------- the water: height h(x,y,t) on a coarse grid, leapfrog steps of the wave equation ---------- */
  var W=null, V=null, simRaf=0, running=false, quiet=0;

  function makeWater(width,top,bottom,isle){
    var cs=7, nx=Math.ceil(width/cs)+2, ny=Math.max(4,Math.ceil((bottom-top)/cs)+2), n=nx*ny;
    var fixed=new Uint8Array(n), damp=new Float32Array(n);
    for(var j=0;j<ny;j++) for(var i=0;i<nx;i++){
      var k=j*nx+i, x=i*cs, y=top+j*cs, edge=Math.min(i,j,nx-1-i,ny-1-j);
      if(edge===0) fixed[k]=1;                                     // beyond the drawing
      if(isle){var dx=x-isle.x, dy=y-isle.y; if(dx*dx+dy*dy<isle.r*isle.r) fixed[k]=1;}   // waves reflect off the island
      damp[k]=0.995*(edge<5?0.9+0.02*edge:1);                      // a soft sponge, so the edges don't echo
    }
    W={top:top,cs:cs,nx:nx,ny:ny,h:new Float32Array(n),p:new Float32Array(n),fixed:fixed,damp:damp};
  }
  function step(){
    var h=W.h,p=W.p,f=W.fixed,d=W.damp,nx=W.nx,ny=W.ny,c2=0.2,top=0;
    for(var j=1;j<ny-1;j++){var r=j*nx;
      for(var i=1;i<nx-1;i++){var k=r+i;
        if(f[k]){p[k]=0;continue;}
        var v=(2*h[k]-p[k]+c2*(h[k-1]+h[k+1]+h[k-nx]+h[k+nx]-4*h[k]))*d[k];
        p[k]=v; v=v<0?-v:v; if(v>top) top=v;
      }}
    W.h=p; W.p=h; return top;
  }
  // a long, low swell frozen in place: the lake at rest is never perfectly flat
  function swell(x,y){
    return 1.1*Math.sin(x/53+y/37)+0.7*Math.sin(x/23-y/61+1.3)+0.45*Math.sin(x/11+y/17+2.1);
  }
  function height(x,y){
    if(!W) return 0;
    var gx=x/W.cs, gy=(y-W.top)/W.cs, nx=W.nx;
    if(gx<0||gy<0||gx>W.nx-1.001||gy>W.ny-1.001) return 0;
    var i=gx|0, j=gy|0, fx=gx-i, fy=gy-j, k=j*nx+i, h=W.h;
    return (h[k]*(1-fx)+h[k+1]*fx)*(1-fy)+(h[k+nx]*(1-fx)+h[k+nx+1]*fx)*fy;
  }
  function poke(x,y,amount){
    if(!W||still) return;
    var gi=Math.round(x/W.cs), gj=Math.round((y-W.top)/W.cs);
    for(var dj=-3;dj<=3;dj++) for(var di=-3;di<=3;di++){
      var i=gi+di, j=gj+dj; if(i<1||j<1||i>=W.nx-1||j>=W.ny-1) continue;
      var k=j*W.nx+i; if(!W.fixed[k]) W.h[k]+=amount*Math.exp(-(di*di+dj*dj)/4);
    }
    if(!running&&!document.hidden){running=true; quiet=0; simRaf=requestAnimationFrame(tick);}
  }
  function tick(){
    var top=step(); draw();
    if(top<0.05){ if(++quiet>45){running=false; return;} } else quiet=0;
    simRaf=requestAnimationFrame(tick);
  }

  /* ---------- drawing ---------- */
  // the walkway is coloured in like pastel: four strokes side by side, each with its own wobble
  var BAND=[[-3.4,3.6,.9],[-1.15,4,1],[1.15,4,1],[3.4,3.6,.85]];
  function strokes(parent,cls,sw,seed){
    return BAND.map(function(b,k){var p=node("polyline",cls); p.setAttribute("stroke-width",(b[1]*sw/10).toFixed(2));
      p.setAttribute("opacity",b[2]); parent.appendChild(p); return {el:p,o:b[0]*sw/10,h:hand(seed*10+k,0.55)};});
  }
  function colour(band,a){
    var n=a.length/2, across=[];      // wobble across the stroke: up and down on level runs, sideways on steep ones
    for(var i=0;i<n;i++){var j=i<n-1?i+1:i-1, dx=Math.abs(a[2*j]-a[2*i]), dy=Math.abs(a[2*j+1]-a[2*i+1]); across.push(dy>dx);}
    band.forEach(function(s){var b=[];
      for(var i=0;i<n;i++){var x=a[2*i], y=a[2*i+1], w=s.h(x+y);
        b.push(x+s.o+(across[i]?w:0), y+s.o+(across[i]?0:w));}
      s.el.setAttribute("points",pts(b));});
  }
  function draw(){
    if(!V) return;
    var dx=6, i, x, a;
    V.lines.forEach(function(ln){
      var m=[], g=[];
      for(x=ln.x0;x<=ln.x1;x+=dx){
        var w=ln.g*(ln.s*swell(x,ln.y)+height(x,ln.y));
        m.push(x, ln.y+w+ln.h(x)); g.push(x+0.6, ln.y+0.95+w+ln.h2(x));
      }
      ln.el.setAttribute("points",pts(m)); ln.el2.setAttribute("points",pts(g));
    });
    V.spans.forEach(function(sp){
      a=[];
      sp.legs.forEach(function(lg){                 // each straight run floats, moored at both ends
        var len=lg.b-lg.a, n=Math.max(1,Math.ceil(len/6));
        for(i=0;i<=n;i++){ x=lg.a+len*i/n;
          a.push(x, lg.y+0.75*Math.sin(Math.PI*i/n)*(0.6*swell(x,lg.y)+height(x,lg.y))); }
      });
      colour(sp.band,a);
    });
  }
  function spanLen(sp){var L=0; sp.legs.forEach(function(lg,k){L+=lg.b-lg.a; if(k) L+=Math.abs(lg.y-sp.legs[k-1].y);}); return L;}
  function sketch(parent,cls,a,b){   // a pencil line drawn twice, the second time lighter
    var p=node("polyline",cls); p.setAttribute("points",pts(a)); parent.appendChild(p);
    if(b){var q=node("polyline",cls+" ghost"); q.setAttribute("points",pts(b)); parent.appendChild(q);}
  }
  function ridge(parent,LW,base,scale,xmax){  // the far shore: mountains, sketched, with a fainter range behind
    function profile(peaks,seed,amp){
      var h=hand(seed,amp), crag=hand(seed+7,amp*0.9), a=[];
      for(var x=0;x<=xmax;x+=4){
        var u=x/LW, y=base;
        peaks.forEach(function(p){y-=scale*p[1]*Math.exp(-Math.abs(u-p[0])/p[2]);});
        a.push(x,y+h(x)+crag(x*3.1));
      }
      return a;
    }
    var back=profile([[0.2,20,0.09],[0.42,30,0.07],[0.66,26,0.08],[0.92,18,0.06]],81,1.2).map(function(v,i){return i%2?v-9:v;});
    var bk=node("polyline","ink ghost"); bk.setAttribute("points",pts(back)); bk.setAttribute("opacity",".3"); parent.appendChild(bk);
    var front=[[0.07,16,0.05],[0.27,30,0.07],[0.5,44,0.085],[0.73,24,0.06],[0.9,13,0.05]];
    sketch(parent,"ink",profile(front,71,1.1),profile(front,72,1.4).map(function(v,i){return i%2?v+1.1:v+0.8;}));
    // a little shading down the far side of the highest peak
    var hs=node("g","hatch"), px=LW*0.5;
    for(var k=0;k<8&&px+6+k*6.5<xmax;k++){
      var x=px+6+k*6.5, u=x/LW, y=base;
      front.forEach(function(p){y-=scale*p[1]*Math.exp(-Math.abs(u-p[0])/p[2]);});
      var l=node("line","ln"); l.setAttribute("x1",x.toFixed(1)); l.setAttribute("y1",(y+3).toFixed(1));
      l.setAttribute("x2",(x-5).toFixed(1)); l.setAttribute("y2",(y+3+Math.min(14,base-y-2)).toFixed(1)); l.setAttribute("opacity",".55");
      hs.appendChild(l);
    }
    parent.appendChild(hs);
  }
  function ring(parent,cx,cy,r){             // the island's shore, one loop of the pencil
    var h=hand(91,1.2), a=[], b=[];
    for(var t=0;t<=6.283*1.07;t+=0.05){var rr=r+h(t*90)+t*0.22, q=t-1.9; a.push(cx+rr*Math.cos(q),cy+rr*Math.sin(q));}
    for(t=0.3;t<=6.283*0.98;t+=0.06){var r2=r+1.4+h(t*90+200)*0.8, q2=t-1.6; b.push(cx+r2*Math.cos(q2),cy+r2*Math.sin(q2));}
    sketch(parent,"ink",a,b);
  }

  // On the About page the walkway reaches for the news: when the "Recently" landing is level with the
  // water, the last stretch of the walkway bends to meet it, and follows it while you scroll.
  var tRaf=0;
  function requestTether(){ if(!tRaf) tRaf=requestAnimationFrame(function(){tRaf=0; tether(true);}); }
  function tether(redraw){
    var T=V&&V.tether; if(!T) return;
    var entry=T.yIn+shore.getBoundingClientRect().top-lake.getBoundingClientRect().top;
    var near=entry>=T.lo&&entry<=T.hi, goal=near?entry:T.y0;
    if(T.locked&&near) T.cur=goal;
    else { T.cur+=(goal-T.cur)*0.22; if(Math.abs(goal-T.cur)<0.6){T.cur=goal; T.locked=near;} else requestTether(); }
    if(!near) T.locked=false;
    var y=Math.round(T.cur);
    T.sp.legs=Math.abs(y-T.y0)<1?[{a:T.a,b:V.LW,y:T.y0}]:[{a:T.a,b:T.xb,y:T.y0},{a:T.xb,b:V.LW,y:y}];
    if(redraw) draw();
  }

  /* ---------- the walkway on the page ---------- */
  function plen(p){var L=0;for(var i=1;i<p.length;i++)L+=Math.abs(p[i][0]-p[i-1][0])+Math.abs(p[i][1]-p[i-1][1]);return L;}
  function lay(el,delay){           // draw a line in, once, the first time the walkway is laid out
    var BIG=10000;                   // longer than any walkway, so later bends never fall into the gap
    el.style.strokeDasharray=BIG+" "+BIG; el.style.strokeDashoffset=BIG;
    el.style.transition="stroke-dashoffset "+Math.round(BIG/1.1)+"ms linear "+Math.round(delay)+"ms";
  }

  function layout(){
    cancelAnimationFrame(simRaf); running=false;
    var vw=root.clientWidth, vh=window.innerHeight, wide=vw>880;
    lastW=vw; lastH=document.body.scrollHeight;
    var LW=lake.clientWidth, LH=lake.clientHeight, SW=shore.clientWidth, SH=shore.clientHeight;
    water.setAttribute("viewBox","0 0 "+LW+" "+LH);
    ws.setAttribute("width",SW); ws.setAttribute("height",SH); ws.setAttribute("viewBox","0 0 "+SW+" "+SH);
    var id=rel(lake.querySelector(".id"),lake), a=anchor?rel(anchor,shore):null, sw=wide?10:8;

    var dates=rail?[].slice.call(rail.querySelectorAll(".date")).filter(function(d){return !d.closest("details:not([open])");}):[];
    var hasRail=dates.length>0&&!!a, railX=0, yIn=0, bot=0, stop=0;
    if(hasRail){
      railX=Math.round(rel(dates[0],shore).l+11); yIn=Math.round(a.b+14);
      bot=Math.round(rel(dates[dates.length-1],shore).cy);
      var nx=rail.nextElementSibling; stop=nx?Math.round(rel(nx,shore).t-18):SH-18;
    }
    function railFrom(y){return [[-4,y],[railX,y],[railX,bot]];}

    var spans=[], shoreSegs=[], top=0, bottom=0, isle=null, tie=null, ringR=0;
    if(wide){
      var lk=rel(links,lake), mw=me.offsetWidth, gap=14;
      me.style.left=Math.round(Math.max(gap+16,LW*.22))+"px";
      cap.style.left=Math.round(id.l)+"px"; cap.style.top=Math.round(lk.t-36)+"px";
      top=Math.round(id.b+74); bottom=Math.round(lk.t-36-22);
      var minC=Math.round(top+gap+mw/2+12), maxC=Math.round(bottom-gap-mw/2-12);
      var want=home&&hasRail?yIn:null, saved=store.get("isle"), c, aligned=false;
      if(want!==null&&want>=minC&&want<=maxC){ c=want; aligned=true; store.set("isle",{w:vw,h:vh,c:c}); }
      else if(saved&&saved.w===vw&&saved.h===vh&&saved.c>=minC&&saved.c<=maxC) c=saved.c;
      else c=clamp(Math.round(top+(bottom-top)*.45),minC,Math.max(minC,maxC));
      me.style.top=Math.round(c-mw/2)+"px";
      var m=rel(me,lake), y0=Math.round(m.cy);
      isle={x:m.cx,y:m.cy,r:m.w/2+gap}; ringR=m.w/2+6;
      spans=[{legs:[{a:0,b:m.l+2,y:y0}]},{legs:[{a:m.r-2,b:LW,y:y0}]}];
      if(home&&hasRail){
        shoreSegs=[railFrom(yIn)];
        tie={sp:spans[1],a:m.r-2,xb:Math.round(LW-30),y0:y0,lo:top+10,hi:bottom-10,yIn:yIn};
        var e0=yIn+shore.getBoundingClientRect().top-lake.getBoundingClientRect().top;
        tie.locked=e0>=tie.lo&&e0<=tie.hi; tie.cur=tie.locked?e0:y0;
      } else if(hasRail){
        if(aligned) shoreSegs=[railFrom(yIn)];
        else if(y0>=yIn&&y0<=Math.max(bot,stop)) shoreSegs=[[[-4,y0],[railX,y0]],[[railX,yIn],[railX,Math.max(bot,y0)]]];
        else shoreSegs=[railFrom(yIn)];
      }
    } else {
      me.removeAttribute("style"); cap.removeAttribute("style");
      if(me.offsetWidth){
        var m2=rel(me,lake);
        top=Math.round(rel(who,lake).b+56); bottom=Math.round(rel(links,lake).t-14);
        isle={x:m2.cx,y:m2.cy,r:m2.w/2+10}; ringR=m2.w/2+5;
        spans=[{legs:[{a:0,b:m2.l+2,y:Math.round(m2.cy)}]}];
      }
      if(hasRail) shoreSegs=[railFrom(yIn)];
      else if(a) shoreSegs=[[[-4,Math.round(a.b+9)],[Math.round(a.l+56),Math.round(a.b+9)]]];
    }

    // the drawing: the far shore, the water's surface, the island, the walkway
    water.innerHTML=""; V={LW:LW,lines:[],spans:[],tether:tie}; W=null;
    if(bottom-top>60){
      ridge(water,LW,top-6,clamp(LW/500,0.6,1.1),wide||!isle?LW*0.98:isle.x-isle.r-4);
      var n=clamp(Math.round((bottom-top)/30),5,13), g=node("g","lines"), r=rand(5);
      water.appendChild(g);
      for(var i=0;i<n;i++){
        var u=i/(n-1), y=top+(bottom-top)*(0.04+0.96*Math.pow(u,1.4)), op=(0.3+0.7*u).toFixed(2);
        var l1=node("polyline","ln"), l2=node("polyline","ln ghost");
        l1.setAttribute("opacity",op); l1.setAttribute("stroke-dasharray",breaks(i*2+1,LW));
        l2.setAttribute("opacity",(op*0.5).toFixed(2)); l2.setAttribute("stroke-dasharray",breaks(i*2+2,LW));
        g.appendChild(l1); g.appendChild(l2);
        var x0=r()<0.3?Math.round(r()*40):0, x1=Math.round(LW-(10+r()*70));
        V.lines.push({y:y,g:0.7+1.1*u,s:(0.35+0.65*u)/(0.7+1.1*u),el:l1,el2:l2,h:hand(i*3+1,0.8),h2:hand(i*3+2,1),x0:x0,x1:x1});
      }
      if(isle){
        var cl=node("circle","clear"); cl.setAttribute("cx",isle.x); cl.setAttribute("cy",isle.y); cl.setAttribute("r",isle.r); water.appendChild(cl);
        ring(water,isle.x,isle.y,ringR);
      }
      makeWater(LW,top-24,bottom+24,isle);
    }
    var pierG=node("g","piers"); water.appendChild(pierG);
    spans.forEach(function(sp,k){sp.band=strokes(pierG,"pier",sw,k+1); V.spans.push(sp);});
    tether(false); draw();

    ws.innerHTML="";
    var shoreBands=shoreSegs.map(function(s,k){
      var b=strokes(ws,"",sw,20+k), flat=[]; s.forEach(function(q){flat.push(q[0],q[1]);});
      // more points along the walkway, so the hand shows on long runs too
      var dense=[]; for(var j=0;j<flat.length-2;j+=2){var x0=flat[j],y0=flat[j+1],x1=flat[j+2],y1=flat[j+3],
        L=Math.abs(x1-x0)+Math.abs(y1-y0), m=Math.max(1,Math.ceil(L/12));
        for(var t=0;t<m;t++) dense.push(x0+(x1-x0)*t/m, y0+(y1-y0)*t/m);}
      dense.push(flat[flat.length-2],flat[flat.length-1]);
      colour(b,dense); return b;
    });

    if(drawIn){
      var t=350;
      V.spans.forEach(function(sp){sp.band.forEach(function(s){lay(s.el,t);}); sp.at=t; t+=spanLen(sp)/1.1;});
      shoreBands.forEach(function(b,k){b.forEach(function(s){lay(s.el,t);}); t+=plen(shoreSegs[k])/1.1;});
      water.getBoundingClientRect(); ws.getBoundingClientRect();
      V.spans.forEach(function(sp){sp.band.forEach(function(s){s.el.style.strokeDashoffset=0;});});
      shoreBands.forEach(function(b){b.forEach(function(s){s.el.style.strokeDashoffset=0;});});
      // laying the walkway on the water sets it rocking, once
      if(isle&&V.spans.length) setTimeout(function(){
        poke(isle.x-isle.r-10,isle.y,14); poke(isle.x+isle.r+10,isle.y,14);
      }, V.spans[0].at+spanLen(V.spans[0])/1.1);
      visit.set("walked",1); drawIn=false;
    }
    lake.classList.add("ready");
  }

  // the water answers the pointer: faster moves leave a bigger wake
  var last=null;
  function local(e){var r=lake.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top,t:e.timeStamp};}
  lake.addEventListener("pointermove",function(e){
    if(!W) return; var q=local(e);
    if(q.y<W.top+20||q.y>W.top+(W.ny-1)*W.cs-20){last=null;return;}
    if(last){var dt=Math.max(8,q.t-last.t), v=Math.sqrt((q.x-last.x)*(q.x-last.x)+(q.y-last.y)*(q.y-last.y))/dt;
      if(v>0.05) poke(q.x,q.y,Math.min(6,v*4.5));}
    last=q;
  });
  lake.addEventListener("pointerleave",function(){last=null;});
  lake.addEventListener("pointerdown",function(e){if(!W) return; var q=local(e); poke(q.x,q.y,24);});
  document.addEventListener("visibilitychange",function(){if(document.hidden){cancelAnimationFrame(simRaf); running=false;}});

  function schedule(){
    if(root.clientWidth===lastW&&document.body.scrollHeight===lastH) return;
    cancelAnimationFrame(layoutRaf); layoutRaf=requestAnimationFrame(layout);
  }
  function now(){cancelAnimationFrame(layoutRaf); layoutRaf=requestAnimationFrame(layout);}
  function start(){
    layout();
    window.addEventListener("resize",schedule);
    window.addEventListener("scroll",function(){ if(V&&V.tether) requestTether(); },{passive:true});
    if("ResizeObserver" in window) new ResizeObserver(schedule).observe(document.body);
    [].forEach.call(document.querySelectorAll("details"),function(d){d.addEventListener("toggle",now);});
  }
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(start,start); else window.addEventListener("load",start);

  /* ---------- publications: filter by line of work ---------- */
  var filter=document.querySelector(".filter");
  if(filter){
    var buttons=[].slice.call(filter.querySelectorAll("button"));
    var show=function(line,remember){
      buttons.forEach(function(b){b.setAttribute("aria-pressed",b.getAttribute("data-line")===line?"true":"false");});
      [].forEach.call(document.querySelectorAll(".pubs li[data-line]"),function(li){li.hidden=!!line&&li.getAttribute("data-line")!==line;});
      [].forEach.call(document.querySelectorAll("#content > section"),function(sec){
        var items=sec.querySelectorAll(".pubs li");
        sec.hidden=items.length?![].some.call(items,function(li){return !li.hidden;}):!!line;
      });
      if(remember){try{var u=new URL(location.href); if(line) u.searchParams.set("line",line); else u.searchParams.delete("line");
        history.replaceState(null,"",u);}catch(e){}}
    };
    filter.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("button"); if(b) show(b.getAttribute("data-line"),true);});
    var asked=null; try{asked=new URLSearchParams(location.search).get("line");}catch(e){}
    if(asked&&buttons.some(function(b){return b.getAttribute("data-line")===asked;})) show(asked,false);
  }

  /* ---------- BibTeX: open, close, copy ---------- */
  document.addEventListener("click",function(e){
    var t=e.target, tog=t.closest&&t.closest(".bibtoggle");
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
