/* Lago d'Iseo, simulated, and drawn by hand.

   The water follows linear wave theory for deep water. Every wave travels at the speed its length
   allows, from the dispersion relation for gravity–capillary waves,
       ω(k)² = g·k + (σ/ρ)·k³ ,
   and fades through viscosity at the rate γ(k) = γ₀ + 2νk². A light breeze keeps a few wave trains
   moving across the lake; a touch or a sweep of the pointer drops a disturbance into the same water,
   evolved exactly mode by mode in Fourier space, so long waves run ahead of short ones, as they do
   when a stone falls in. The orange walkway is moored and stays put; on the page it carries the dates. */
(function(){
  "use strict";
  var NS="http://www.w3.org/2000/svg", root=document.documentElement, TAU=Math.PI*2;
  function $(id){return document.getElementById(id);}
  var lake=$("lake"), shore=$("shore");
  if(!lake||!shore) return;
  var water=$("water"), ws=$("walk-shore"), me=$("me"), who=$("who"), links=$("links"), cap=$("lbl-lake"),
      anchor=$("anchor"), rail=document.querySelector("[data-rail]"), home=document.body.classList.contains("home");

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
    var r=rand(seed), p0=r()*TAU, p1=r()*TAU, p2=r()*TAU; amp=amp||1;
    return function(x){return amp*(0.55*Math.sin(x/61+p0)+0.32*Math.sin(x/27+p1)+0.16*Math.sin(x/11.5+p2));};
  }

  /* ---------- physics ---------- */
  // units: pixels and seconds. g and σ/ρ put the gravity–capillary crossover near 100 px, so the
  // breeze's long waves roll by slowly while the short ripples from a touch run out fast ahead of them
  var G=160, SIG=40000, NU=0.9, GAM0=0.2;
  function omega(k){return Math.sqrt(G*k+SIG*k*k*k);}
  function decay(k){return GAM0+2*NU*k*k;}

  // the breeze: a handful of wave trains from the west, each moving at its own phase speed ω/k
  var trains=(function(){
    var r=rand(17), out=[];
    for(var j=0;j<7;j++){
      var lam=70+r()*190, k=TAU/lam, th=(r()-0.5)*0.8;
      out.push({kx:k*Math.cos(th),ky:k*Math.sin(th),w:omega(k),a:(0.55+0.6*r())*Math.pow(lam/160,0.9),p:r()*TAU});
    }
    return out;
  })();
  var A_TOT=trains.reduce(function(s,w){return s+w.a;},0);
  function breeze(x,y,t){var s=0; for(var j=0;j<trains.length;j++){var w=trains[j]; s+=w.a*Math.cos(w.kx*x+w.ky*y-w.w*t+w.p);} return s;}

  // ripples: the same water, held as Fourier modes on a periodic grid and stepped exactly
  var R=null;
  function fft(re,im,n,stride,off,inv,tmpR,tmpI,rev,cs,sn){
    var i,j,len,half,step,k,a,b,tr,ti,wr,wi,ur,ui;
    for(i=0;i<n;i++){j=rev[i]; tmpR[i]=re[off+j*stride]; tmpI[i]=im[off+j*stride];}
    for(len=2;len<=n;len<<=1){
      half=len>>1; step=n/len;
      for(i=0;i<n;i+=len){
        for(k=0;k<half;k++){
          wr=cs[k*step]; wi=inv?sn[k*step]:-sn[k*step];
          a=i+k; b=a+half;
          tr=tmpR[b]*wr-tmpI[b]*wi; ti=tmpR[b]*wi+tmpI[b]*wr;
          ur=tmpR[a]; ui=tmpI[a];
          tmpR[a]=ur+tr; tmpI[a]=ui+ti; tmpR[b]=ur-tr; tmpI[b]=ui-ti;
        }
      }
    }
    for(i=0;i<n;i++){re[off+i*stride]=tmpR[i]; im[off+i*stride]=tmpI[i];}
  }
  function tables(n){
    var bits=Math.log2(n)|0, rev=new Int32Array(n), cs=new Float64Array(n/2), sn=new Float64Array(n/2);
    for(var i=0;i<n;i++){var r=0,x=i; for(var b=0;b<bits;b++){r=(r<<1)|(x&1); x>>=1;} rev[i]=r;}
    for(var k=0;k<n/2;k++){cs[k]=Math.cos(TAU*k/n); sn[k]=Math.sin(TAU*k/n);}
    return {rev:rev,cs:cs,sn:sn,tr:new Float64Array(n),ti:new Float64Array(n)};
  }
  function makeRipples(LW,top,bottom){
    // twice the width of the drawing, so ripples fade out long before the periodic grid could bring them back
    var N=256, M=64, Lx=LW*2, Ly=(bottom-top)*1.6, x0=-LW*0.5, y0=top-(bottom-top)*0.3, dt=1/60;
    var n=N*M, kx=new Float64Array(n), ky=new Float64Array(n), C=new Float64Array(n), S=new Float64Array(n),
        E=new Float64Array(n), Wk=new Float64Array(n);
    for(var j=0;j<M;j++) for(var i=0;i<N;i++){
      var q=j*N+i, fx=i<N/2?i:i-N, fy=j<M/2?j:j-M, ax=TAU*fx/Lx, ay=TAU*fy/Ly, k=Math.sqrt(ax*ax+ay*ay), w=omega(k);
      kx[q]=ax; ky[q]=ay; Wk[q]=w; C[q]=Math.cos(w*dt); S[q]=Math.sin(w*dt); E[q]=Math.exp(-decay(k)*dt);
    }
    R={N:N,M:M,Lx:Lx,Ly:Ly,x0:x0,y0:y0,dx:Lx/N,dy:Ly/M,kx:kx,ky:ky,C:C,S:S,E:E,W:Wk,
       hr:new Float64Array(n),hi:new Float64Array(n),vr:new Float64Array(n),vi:new Float64Array(n),
       fr:new Float64Array(n),fi:new Float64Array(n),tx:tables(N),ty:tables(M),live:0,energy:0,peak:0};
  }
  function stepRipples(){
    var n=R.N*R.M, hr=R.hr, hi=R.hi, vr=R.vr, vi=R.vi, C=R.C, S=R.S, E=R.E, W=R.W, e=0;
    for(var q=1;q<n;q++){             // each mode turns in its own phase space, and loses a little energy
      var w=W[q], c=C[q], s=S[q], f=E[q];
      var a=hr[q], b=hi[q], u=vr[q], v=vi[q];
      hr[q]=(a*c+u/w*s)*f; hi[q]=(b*c+v/w*s)*f;
      vr[q]=(-a*w*s+u*c)*f; vi[q]=(-b*w*s+v*c)*f;
      e+=hr[q]*hr[q]+hi[q]*hi[q];
    }
    R.energy=e; if(e>R.peak) R.peak=e;
    // back to the surface: an inverse FFT along rows, then along columns
    var N=R.N, M=R.M, fr=R.fr, fi=R.fi;
    fr.set(hr); fi.set(hi);
    for(var j=0;j<M;j++) fft(fr,fi,N,1,j*N,true,R.tx.tr,R.tx.ti,R.tx.rev,R.tx.cs,R.tx.sn);
    for(var i=0;i<N;i++) fft(fr,fi,M,N,i,true,R.ty.tr,R.ty.ti,R.ty.rev,R.ty.cs,R.ty.sn);
  }
  function ripple(x,y){
    if(!R||!R.live) return 0;
    var gx=(x-R.x0)/R.dx, gy=(y-R.y0)/R.dy, N=R.N, M=R.M;
    if(gx<0||gy<0||gx>N-1.001||gy>M-1.001) return 0;
    var i=gx|0, j=gy|0, fx=gx-i, fy=gy-j, q=j*N+i, f=R.fr;
    return (f[q]*(1-fx)+f[q+1]*fx)*(1-fy)+(f[q+N]*(1-fx)+f[q+N+1]*fx)*fy;
  }
  // a stone, or a fingertip: a small Gaussian dent in the surface, added to every mode at once
  function drop(x,y,amp,width){
    if(!R||still) return;
    var n=R.N*R.M, s=width||9, norm=amp*TAU*s*s/(R.Lx*R.Ly), X=x-R.x0, Y=y-R.y0;
    for(var q=1;q<n;q++){
      var kx=R.kx[q], ky=R.ky[q], g=norm*Math.exp(-(kx*kx+ky*ky)*s*s/2), ph=-(kx*X+ky*Y);
      R.hr[q]+=g*Math.cos(ph); R.hi[q]+=g*Math.sin(ph);
    }
    R.live=1; wake();
  }

  /* ---------- the drawing ---------- */
  var V=null, raf=0, running=false, t0=0, tNow=0;

  // the walkway is coloured in like pastel: four strokes side by side, each with its own wobble
  var BAND=[[-3.4,3.6,.9],[-1.15,4,1],[1.15,4,1],[3.4,3.6,.85]];
  function strokes(parent,cls,sw,seed){
    return BAND.map(function(b,k){var p=node("polyline",cls); p.setAttribute("stroke-width",(b[1]*sw/10).toFixed(2));
      p.setAttribute("opacity",b[2]); parent.appendChild(p); return {el:p,o:b[0]*sw/10,h:hand(seed*10+k,0.55)};});
  }
  function colour(band,a){
    var n=a.length/2, steep=[];
    for(var i=0;i<n;i++){var j=i<n-1?i+1:i-1, dx=Math.abs(a[2*j]-a[2*i]), dy=Math.abs(a[2*j+1]-a[2*i+1]); steep.push(dy>dx);}
    band.forEach(function(s){var b=[];
      for(var i=0;i<n;i++){var x=a[2*i], y=a[2*i+1], w=s.h(x+y); b.push(x+s.o+(steep[i]?w:0), y+s.o+(steep[i]?0:w));}
      s.el.setAttribute("points",pts(b));});
  }
  function dense(segs,step){
    var out=[];
    for(var j=0;j<segs.length-1;j++){var a=segs[j], b=segs[j+1], m=Math.max(1,Math.ceil((Math.abs(b[0]-a[0])+Math.abs(b[1]-a[1]))/step));
      for(var t=0;t<m;t++) out.push(a[0]+(b[0]-a[0])*t/m, a[1]+(b[1]-a[1])*t/m);}
    var z=segs[segs.length-1]; out.push(z[0],z[1]); return out;
  }
  function plen(p){var L=0;for(var i=1;i<p.length;i++)L+=Math.abs(p[i][0]-p[i-1][0])+Math.abs(p[i][1]-p[i-1][1]);return L;}
  function lay(el,delay){           // the pen draws the walkway in, once, the first time you visit
    var BIG=10000;
    el.style.strokeDasharray=BIG+" "+BIG; el.style.strokeDashoffset=BIG;
    el.style.transition="stroke-dashoffset "+Math.round(BIG/1.1)+"ms linear "+Math.round(delay)+"ms";
  }
  function line(parent,cls,a,attrs){var p=node("polyline",cls); p.setAttribute("points",pts(a));
    if(attrs) for(var k in attrs) p.setAttribute(k,attrs[k]); parent.appendChild(p); return p;}

  // value noise and fractal sums of it: the roughness of real ridgelines repeats at every scale
  function noise1(seed){
    var r=rand(seed), v=new Float64Array(1024); for(var i=0;i<1024;i++) v[i]=r()*2-1;
    return function(x){var i=Math.floor(x), f=x-i, u=f*f*(3-2*f), a=v[i&1023], b=v[(i+1)&1023]; return a+(b-a)*u;};
  }
  function fbm(n,x,oct){var s=0,amp=1,f=1,norm=0; for(var o=0;o<oct;o++){s+=amp*n(x*f+o*17.31); norm+=amp; amp*=0.52; f*=2.07;} return s/norm;}

  // the mountains around the lake: three ranges, the nearest one wooded and shaded
  function mountains(parent,LW,shoreY,scale,xmax){
    function range(masses,seed,freq,oct,rough){
      var n=noise1(seed), n2=noise1(seed+5), a=[];
      for(var x=0;x<=xmax;x+=3){
        var u=x/LW, env=0;
        for(var j=0;j<masses.length;j++){var m=masses[j], z=(u-m[0])/m[2]; env+=m[1]*Math.exp(-z*z);}
        var detail=fbm(n,u*freq,oct), crag=1-Math.abs(fbm(n2,u*freq*2.3,3));
        var hgt=env*(0.78+rough*detail)+env*0.12*crag;
        a.push(x,shoreY-scale*Math.max(0,hgt));
      }
      return a;
    }
    var g=node("g","hills"); parent.appendChild(g);
    var fa=range([[0.1,84,0.15],[0.5,104,0.2],[0.88,80,0.13]],61,5,4,0.28),
        ma=range([[0.04,46,0.09],[0.3,74,0.12],[0.6,60,0.11],[0.9,54,0.1]],71,8,5,0.34),
        na=range([[0.13,30,0.08],[0.37,44,0.075],[0.6,26,0.08],[0.84,48,0.07]],81,11,5,0.4);
    var hf=hand(62,0.6), hm=hand(72,0.7), hn=hand(82,0.8);
    function wob(a,h,dy){return a.map(function(v,i){return i%2?v+h(a[i-1])+(dy||0):v;});}
    line(g,"ink",wob(fa,hf),{opacity:".24","stroke-width":".8"});
    line(g,"ink",wob(ma,hm),{opacity:".55","stroke-width":"1"});
    line(g,"ink",wob(na,hn),{"stroke-width":"1.35"});
    line(g,"ink",wob(na,hand(83,1),1.1),{opacity:".38","stroke-width":".7"});
    // shading: short strokes down the slopes that turn away from the light (it comes from the left)
    var sh=node("g","shade"), r=rand(23);
    [[ma,0.6,7,0.45,9],[na,1,4.5,0.7,15]].forEach(function(set){
      var a=set[0];
      for(var i=6;i<a.length-6;i+=2){
        var x=a[i], y=a[i+1], slope=(a[i+7]-a[i-5])/(a[i+6]-a[i-6]);
        if(slope>0.18&&r()<set[3]){
          var depth=shoreY-y, len=Math.min(depth-4,set[4],(5+r()*10)*set[1]+Math.min(slope,1.5)*4);
          if(len<3) continue;
          var l=node("line","hatch"); l.setAttribute("x1",x.toFixed(1)); l.setAttribute("y1",(y+2).toFixed(1));
          l.setAttribute("x2",(x-len*0.42).toFixed(1)); l.setAttribute("y2",(y+2+len).toFixed(1));
          l.setAttribute("opacity",(0.3+0.4*set[1]).toFixed(2)); sh.appendChild(l);
          i+=2*Math.round(set[2]);          // skip a few points; stay on x entries of the flat [x,y,x,y…] list
        }
      }
    });
    g.appendChild(sh);
    // woods on the near slopes: little conifers in clumps, thinning out where the hills drop to the water
    var woods=node("g","woods"), rr=rand(29), forest=noise1(31);
    for(var i3=0;i3<na.length;i3+=2){
      var x=na[i3], ridgeY=na[i3+1], relief=shoreY-ridgeY;
      var dens=clamp(0.55+0.9*fbm(forest,x/70,3),0,1);
      if(rr()>dens*0.55||relief<4) continue;
      var y=shoreY-rr()*Math.min(relief*0.55,16), hgt=3.5+rr()*5.5;
      var tree=node("path","tree");
      tree.setAttribute("d","M"+x.toFixed(1)+","+y.toFixed(1)+"v"+(-hgt).toFixed(1)+
        "M"+(x-hgt*0.32).toFixed(1)+","+(y-hgt*0.3).toFixed(1)+"L"+x.toFixed(1)+","+(y-hgt*1.05).toFixed(1)+"L"+(x+hgt*0.32).toFixed(1)+","+(y-hgt*0.3).toFixed(1));
      woods.appendChild(tree);
    }
    g.appendChild(woods);
    // the hills again, upside down and broken up by the water just below the shore
    var refl=node("g","refl");
    for(var i2=0;i2<na.length-2;i2+=14){
      var xx=na[i2], depth2=shoreY-na[i2+1];
      for(var k=0;k<2;k++){
        var yy=shoreY+5+k*6+rr()*2, w2=(3+depth2*0.35)*(1-k*0.3)*(0.5+rr()*0.7);
        if(w2<3) continue;
        var l2=node("line","ln"); l2.setAttribute("x1",(xx-w2/2).toFixed(1)); l2.setAttribute("x2",(xx+w2/2).toFixed(1));
        l2.setAttribute("y1",yy.toFixed(1)); l2.setAttribute("y2",yy.toFixed(1)); l2.setAttribute("opacity",(0.45-k*0.15).toFixed(2));
        refl.appendChild(l2);
      }
    }
    g.appendChild(refl);
  }
  function birds(parent,x0,y0,n,seed){
    var r=rand(seed), g=node("g","birds");
    for(var i=0;i<n;i++){
      var x=x0+i*(16+r()*14), y=y0+(r()-0.5)*18, s=4.5+r()*3.5, tilt=(r()-0.5)*0.4;
      var p=node("path","ink");
      p.setAttribute("d","M"+(x-s).toFixed(1)+","+(y+tilt*s).toFixed(1)+"q"+(s*0.45).toFixed(1)+","+(-s*0.75).toFixed(1)+" "+s.toFixed(1)+","+(-tilt*s+s*0.1).toFixed(1)+
        "q"+(s*0.5).toFixed(1)+","+(-s*0.9).toFixed(1)+" "+(s*1.05).toFixed(1)+","+(-s*0.25).toFixed(1));
      p.setAttribute("stroke-width","1.1"); g.appendChild(p);
    }
    parent.appendChild(g);
  }
  function ring(parent,cx,cy,r){             // the island's shore, one loop of the pencil
    var h=hand(91,1.2), a=[], b=[];
    for(var t=0;t<=TAU*1.07;t+=0.04){var rr=r+h(t*90)+t*0.22, q=t-1.9; a.push(cx+rr*Math.cos(q),cy+rr*Math.sin(q));}
    for(t=0.3;t<=TAU*0.98;t+=0.05){var r2=r+1.6+h(t*90+200)*0.8, q2=t-1.6; b.push(cx+r2*Math.cos(q2),cy+r2*Math.sin(q2));}
    line(parent,"ink",a,{"stroke-width":"1.3"}); line(parent,"ink",b,{"stroke-width":".7",opacity:".45"});
  }

  // the surface, every frame: a pencil line per row of water, darker and heavier where the crests stand up
  function draw(){
    if(!V) return;
    var t=tNow, dx=5;
    for(var i=0;i<V.rows.length;i++){
      var ln=V.rows[i], base=[], crest="", on=false, y, x;
      for(x=ln.x0;x<=ln.x1;x+=dx){
        var hb=breeze(x*ln.zoom,ln.y*2.2,t), hr=ripple(x,ln.y), hn=(hb+ln.rip*hr)/A_TOT;
        y=ln.y+ln.g*(hb+ln.rip*hr)+ln.h(x);
        base.push(x,y);
        if(hn>ln.th){ crest+=(on?"L":"M")+x.toFixed(1)+","+(y-0.4).toFixed(1); on=true; } else on=false;
      }
      ln.el.setAttribute("points",pts(base));
      ln.cr.setAttribute("d",crest||"M0,0");
    }
  }
  function frame(now){
    if(!running) return;
    if(!t0) t0=now;
    tNow=(now-t0)/1000;
    if(R&&R.live){ stepRipples(); if(R.energy<R.peak*2e-3){R.live=0; R.peak=0; R.hr.fill(0); R.hi.fill(0); R.vr.fill(0); R.vi.fill(0); R.fr.fill(0);} }
    draw();
    raf=requestAnimationFrame(frame);
  }
  var visible=true;
  function wake(){ if(still||running||document.hidden||!visible||!V||!V.rows.length) return; running=true; raf=requestAnimationFrame(frame); }
  function sleep(){ running=false; cancelAnimationFrame(raf); }

  function layout(){
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

    var lakeSegs=[], shoreSegs=[], top=0, bottom=0, isle=null, ringR=0, peakScale=1;
    me.style.width="";
    if(wide){
      var lk=rel(links,lake), gap=16;
      if(cap){cap.style.left=Math.round(id.l)+"px"; cap.style.top=Math.round(lk.t-36)+"px";}
      peakScale=clamp(LW/500,0.65,1.1)*clamp((LH-560)/340,0.45,1);
      top=Math.round(id.b+26+102*peakScale); bottom=Math.round(lk.t-30);
      var mw=me.offsetWidth;
      if(mw>bottom-top-2*gap-24){ mw=Math.max(96,bottom-top-2*gap-24); me.style.width=mw+"px"; }
      me.style.left=Math.round(Math.max(gap+16,LW*.2))+"px";
      var minC=Math.round(top+gap+mw/2+12), maxC=Math.round(bottom-gap-mw/2-12);
      var want=home&&hasRail?yIn:null, saved=store.get("isle"), c, aligned=false;
      if(want!==null&&want>=minC&&want<=maxC){ c=want; aligned=true; store.set("isle",{w:vw,h:vh,c:c}); }
      else if(saved&&saved.w===vw&&saved.h===vh&&saved.c>=minC&&saved.c<=maxC) c=saved.c;
      else c=clamp(Math.round(top+(bottom-top)*.48),minC,Math.max(minC,maxC));
      me.style.top=Math.round(c-mw/2)+"px";
      var m=rel(me,lake), y0=Math.round(m.cy);
      isle={x:m.cx,y:m.cy,r:m.w/2+gap}; ringR=m.w/2+7;
      var right=[[m.r-2,y0],[LW,y0]];
      if(home&&hasRail){
        shoreSegs=[railFrom(yIn)];
        if(!aligned&&yIn>=top+12&&yIn<=bottom-12){ var xb=Math.round(LW-30); right=[[m.r-2,y0],[xb,y0],[xb,yIn],[LW,yIn]]; }
      } else if(hasRail){
        if(aligned) shoreSegs=[railFrom(yIn)];
        else if(y0>=yIn&&y0<=Math.max(bot,stop)) shoreSegs=[[[-4,y0],[railX,y0]],[[railX,yIn],[railX,Math.max(bot,y0)]]];
        else shoreSegs=[railFrom(yIn)];
      }
      lakeSegs=[[[0,y0],[m.l+2,y0]],right];
    } else {
      me.removeAttribute("style"); if(cap) cap.removeAttribute("style");
      if(me.offsetWidth){
        var m2=rel(me,lake);
        peakScale=clamp(LW/520,0.55,0.8);
        top=Math.round(rel(who,lake).b+20+100*peakScale); bottom=Math.round(rel(links,lake).t-14);
        isle={x:m2.cx,y:m2.cy,r:m2.w/2+11}; ringR=m2.w/2+6;
        lakeSegs=[[[0,Math.round(m2.cy)],[m2.l+2,Math.round(m2.cy)]]];
      }
      if(hasRail) shoreSegs=[railFrom(yIn)];
      else if(a) shoreSegs=[[[-4,Math.round(a.b+9)],[Math.round(a.l+56),Math.round(a.b+9)]]];
    }

    // compose the drawing
    sleep(); water.innerHTML=""; V={LW:LW,rows:[]}; R=null;
    if(bottom-top>60){
      var xmax=wide||!isle?LW*0.99:isle.x-isle.r-2;
      mountains(water,LW,top,peakScale,xmax);
      birds(water,LW*(wide?0.62:0.38),top-118*peakScale-6,wide?3:2,37);
      // rows of water: crowded and fine towards the far shore, broad and heavy close to you
      var n=clamp(Math.round((bottom-top)/21),7,20), g=node("g","lines"), r=rand(5);
      water.appendChild(g);
      for(var i=0;i<n;i++){
        var u=i/(n-1), y=top+14+(bottom-top-14)*(0.02+0.98*Math.pow(u,1.3));
        var el=node("polyline","ln"), cr=node("path","crest");
        el.setAttribute("opacity",(0.28+0.55*u).toFixed(2)); el.setAttribute("stroke-width",(0.55+0.75*u).toFixed(2));
        cr.setAttribute("opacity",(0.22+0.38*u).toFixed(2)); cr.setAttribute("stroke-width",(0.6+0.75*u).toFixed(2));
        g.appendChild(el); g.appendChild(cr);
        var x0=r()<0.25?Math.round(r()*30):0, x1=Math.round(LW-(8+r()*60));
        V.rows.push({y:y,g:0.25+1.6*u,rip:2.2,zoom:1+1.6*(1-u),th:0.42-0.12*u,el:el,cr:cr,h:hand(i*3+1,0.5+0.4*u),x0:x0,x1:x1});
      }
      if(isle){
        var cl=node("circle","clear"); cl.setAttribute("cx",isle.x); cl.setAttribute("cy",isle.y); cl.setAttribute("r",isle.r); water.appendChild(cl);
        ring(water,isle.x,isle.y,ringR);
      }
      makeRipples(LW,top,bottom);
    }
    // the walkway: moored at the shore, at the island and at the page, and steady
    var pg=node("g","piers"); water.appendChild(pg);
    var bands=lakeSegs.map(function(s,k){var b=strokes(pg,"pier",sw,k+1); colour(b,dense(s,6)); return b;});
    draw();

    ws.innerHTML="";
    var shoreBands=shoreSegs.map(function(s,k){var b=strokes(ws,"",sw,20+k); colour(b,dense(s,12)); return b;});

    if(drawIn){
      var t=350;
      bands.forEach(function(b,k){b.forEach(function(s){lay(s.el,t);}); t+=plen(lakeSegs[k])/1.1;});
      shoreBands.forEach(function(b,k){b.forEach(function(s){lay(s.el,t);}); t+=plen(shoreSegs[k])/1.1;});
      water.getBoundingClientRect(); ws.getBoundingClientRect();
      bands.concat(shoreBands).forEach(function(b){b.forEach(function(s){s.el.style.strokeDashoffset=0;});});
      visit.set("walked",1); drawIn=false;
    }
    lake.classList.add("ready");
    wake();
  }

  // the water answers the pointer: a sweep leaves a wake, a tap drops a stone
  var last=null, lastDrop=0;
  function local(e){var r=lake.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top,t:e.timeStamp};}
  function onWater(q){return R&&V&&V.rows.length&&q.y>V.rows[0].y-6&&q.y<V.rows[V.rows.length-1].y+10;}
  lake.addEventListener("pointermove",function(e){
    var q=local(e); if(!onWater(q)){last=null;return;}
    if(last&&q.t-lastDrop>28){
      var dt=Math.max(8,q.t-last.t), v=Math.sqrt((q.x-last.x)*(q.x-last.x)+(q.y-last.y)*(q.y-last.y))/dt;
      if(v>0.05){ drop(q.x,q.y,-Math.min(2.6,v*1.8),8); lastDrop=q.t; }
    }
    last=q;
  });
  lake.addEventListener("pointerleave",function(){last=null;});
  lake.addEventListener("pointerdown",function(e){var q=local(e); if(onWater(q)) drop(q.x,q.y,-10,12);});
  document.addEventListener("visibilitychange",function(){ if(document.hidden) sleep(); else wake(); });
  if("IntersectionObserver" in window) new IntersectionObserver(function(es){ visible=es[0].isIntersecting; if(visible) wake(); else sleep(); }).observe(lake);

  function schedule(){
    if(root.clientWidth===lastW&&document.body.scrollHeight===lastH) return;
    cancelAnimationFrame(layoutRaf); layoutRaf=requestAnimationFrame(layout);
  }
  function now(){cancelAnimationFrame(layoutRaf); layoutRaf=requestAnimationFrame(layout);}
  function start(){
    layout();
    window.addEventListener("resize",schedule);
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
