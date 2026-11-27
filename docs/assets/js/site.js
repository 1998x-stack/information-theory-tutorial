"use strict";
(() => {
  const h2 = p => (p <= 0 || p >= 1) ? 0 :
    -p * Math.log2(p) - (1-p) * Math.log2(1-p);
  const fmt = n => n.toFixed(4);

  function crcRemainder(bits,generator){const w=bits.split("").map(Number),g=generator.split("").map(Number);for(let i=0;i<=w.length-g.length;i++)if(w[i])for(let j=0;j<g.length;j++)w[i+j]^=g[j];return w.slice(-(g.length-1)).join("").padStart(g.length-1,"0");}
  function convEncode(bits){let state=0,out="";for(const ch of bits+"00"){const b=Number(ch),p=(state>>1)&1,o=state&1;out+=(b^p^o).toString()+(b^o).toString();state=(b<<1)|p;}return out;}
  function viterbiDecode(received){const pairs=received.match(/../g)||[];let m=[0,Infinity,Infinity,Infinity],backs=[];for(const pair of pairs){const next=[Infinity,Infinity,Infinity,Infinity],pred=[null,null,null,null];for(let s=0;s<4;s++){if(!Number.isFinite(m[s]))continue;const p=(s>>1)&1,o=s&1;for(let b=0;b<=1;b++){const out=[b^p^o,b^o],ns=(b<<1)|p,cost=(Number(pair[0])!==out[0])+(Number(pair[1])!==out[1]),v=m[s]+cost;if(v<next[ns]){next[ns]=v;pred[ns]={state:s,bit:b};}}}m=next;backs.push(pred);}let state=0,bits="";for(let t=backs.length-1;t>=0;t--){const p=backs[t][state];if(!p)return {bits:"?",metric:Infinity};bits=p.bit+bits;state=p.state;}return {bits:bits.slice(0,-2),metric:m[0]};}
  function waterFill(noise,power){let lo=Math.min(...noise),hi=Math.max(...noise)+power;for(let k=0;k<80;k++){const mid=(lo+hi)/2,total=noise.reduce((s,n)=>s+Math.max(mid-n,0),0);if(total>power)hi=mid;else lo=mid;}const level=(lo+hi)/2,powers=noise.map(n=>Math.max(level-n,0)),capacity=powers.reduce((s,p,i)=>s+.5*Math.log2(1+p/noise[i]),0);return {level,powers,capacity};}

  function macRegion(p2){const p1=2,n=1,c1=.5*Math.log2(1+p1/n),c2=.5*Math.log2(1+p2/n),cs=.5*Math.log2(1+(p1+p2)/n);return {c1,c2,cs,corner1:[c1,cs-c1],corner2:[cs-c2,c2]};}
  function softmax(z){const m=Math.max(...z),e=z.map(v=>Math.exp(v-m)),s=e.reduce((a,b)=>a+b,0);return e.map(v=>v/s);}
  function logsumexp(z){const m=Math.max(...z);return m+Math.log(z.reduce((a,v)=>a+Math.exp(v-m),0));}
  function digammaInt(n){let s=0;for(let i=1;i<n;i++)s+=1/i;return s-0.5772156649015329;}
  const ksgPairs=(()=>{let seed=20261122;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;seed>>>=0;return (seed+.5)/4294967296;};const normal=()=>{const u=Math.max(rand(),1e-12),v=rand();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);};const a=[],rho=.7,scale=Math.sqrt(1-rho*rho);for(let i=0;i<160;i++){const x=normal(),y=rho*x+scale*normal();a.push([x,y]);}return a;})();
  function ksgDemo(k){const a=ksgPairs,n=a.length,terms=[];for(let i=0;i<n;i++){let ds=[];for(let j=0;j<n;j++)if(i!==j)ds.push(Math.max(Math.abs(a[i][0]-a[j][0]),Math.abs(a[i][1]-a[j][1])));ds.sort((x,y)=>x-y);const eps=ds[k-1];let nx=0,ny=0;for(let j=0;j<n;j++)if(i!==j){if(Math.abs(a[i][0]-a[j][0])<eps)nx++;if(Math.abs(a[i][1]-a[j][1])<eps)ny++;}terms.push(digammaInt(nx+1)+digammaInt(ny+1));}const nats=digammaInt(k)+digammaInt(n)-terms.reduce((s,v)=>s+v,0)/n;return nats/Math.LN2;}

  // Capstone lab uses the same 32-bit LCG as examples/capstone.py.
  function lcg(seed){let state=seed>>>0;return ()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return (state+.5)/4294967296;};}
  function hamming74Encode(nibble){
    const [a,b,c,d]=nibble.split("").map(Number),p1=a^b^d,p2=a^c^d,p4=b^c^d;
    return [p1,p2,a,p4,b,c,d].join("");
  }
  function hamming74Decode(word){
    const bits=word.split("").map(Number);let syndrome=0;
    bits.forEach((b,i)=>{if(b)syndrome^=i+1;});
    if(syndrome)bits[syndrome-1]^=1;
    return {nibble:[bits[2],bits[4],bits[5],bits[6]].join(""),syndrome};
  }
  function capstoneLab(p){
    const message="AAAABBCD",src="00001010110111";
    const padded=src+"00";
    const encoded=padded.match(/.{4}/g).map(hamming74Encode).join("");
    const rnd=lcg(2026),flips=[];
    const received=[...encoded].map((b,i)=>{if(rnd()<p){flips.push(i);return b==="0"?"1":"0";}return b;}).join("");
    const blocks=received.match(/.{7}/g).map(hamming74Decode);
    const raw=blocks.map(x=>x.nibble).join("").slice(0,src.length);
    const residual=[...src].reduce((a,b,i)=>a+(b!==raw[i]),0);
    const codebook={0:"A",10:"B",110:"C",111:"D"};
    let prefix="",recovered="",invalid=false;
    for(const bit of raw){prefix+=bit;if(Object.prototype.hasOwnProperty.call(codebook,prefix)){recovered+=codebook[prefix];prefix="";}else if(!["1","11"].includes(prefix)){invalid=true;break;}}
    const success=!invalid&&!prefix&&recovered===message;
    return "p="+p.toFixed(2)+"；正文="+src.length+" bit；信道="+encoded.length+" bit；翻转="+flips.length+"；综合征非零="+blocks.filter(x=>x.syndrome).length+"；译后残余 bit 错误="+residual+"；消息恢复="+(success?"成功":"失败");
  }

  function typicalMass(n, p=.25, eps=.15) {
    const H = h2(p);
    let binomial = Math.pow(1-p, n), mass = 0;
    for (let k=0; k<=n; k++) {
      const rate = -(k*Math.log2(p)+(n-k)*Math.log2(1-p))/n;
      if (Math.abs(rate-H)<=eps+1e-12) mass += binomial;
      if (k<n) binomial *= (n-k)/(k+1)*p/(1-p);
    }
    return mass;
  }
  function huffmanSummary(pA) {
    const weights = {A:pA,B:(1-pA)/2,C:(1-pA)/3,D:(1-pA)/6};
    const lengths = {A:0,B:0,C:0,D:0};
    const nodes = Object.entries(weights).map(([key,weight]) => ({weight,keys:[key],name:key}));
    while (nodes.length>1) {
      nodes.sort((a,b)=>a.weight-b.weight || a.name.localeCompare(b.name));
      const a=nodes.shift(),b=nodes.shift();
      [...a.keys,...b.keys].forEach(key=>lengths[key]++);
      const keys=[...a.keys,...b.keys].sort();
      nodes.push({weight:a.weight+b.weight,keys,name:keys.join("")});
    }
    const H=Object.values(weights).reduce((sum,p)=>sum-p*Math.log2(p),0);
    const L=Object.entries(weights).reduce((sum,[key,p])=>sum+p*lengths[key],0);
    return `H=${fmt(H)}；L=${fmt(L)} bits（A:${lengths.A} B:${lengths.B} C:${lengths.C} D:${lengths.D}）`;
  }
  const stages=[
    ["—",0,1],["A",0,.6],["AB",.36,.6],["ABA",.36,.504]
  ];
  function result(kind,v) {
    switch (kind) {
      case "surprisal": return "I(x) = "+(-Math.log2(v)).toFixed(3)+" bits";
      case "bayes": return "P(患病 | 阳性) = "+(100*.9*v/(.9*v+.05*(1-v))).toFixed(2)+"%";
      case "entropy": return "h₂(p) = "+fmt(h2(v))+" bits";
      case "bsc": return "I(X;Y) = "+fmt(1-h2(v))+" bits";
      case "kl": {
        const p=.75, cross=-p*Math.log2(v)-(1-p)*Math.log2(1-v);
        return "交叉熵 "+fmt(cross)+"；KL "+fmt(cross-h2(p))+" bits";
      }
      case "cond-noise": return "H(X|Y)="+fmt(h2(v))+" bits；I(X;Y)="+fmt(1-h2(v))+" bits";
      case "aep-mass": return "n="+Math.round(v)+"：典型集概率 ≈ "+(typicalMass(Math.round(v))*100).toFixed(2)+"%";
      case "kraft-length": {
        const l=Math.round(v),kraft=.5+.25+Math.pow(2,-l)+.125;
        return "ℓ₃="+l+"：K="+fmt(kraft)+"，"+(kraft<=1+1e-12?"存在前缀码":"无法构造前缀码");
      }
      case "huffman-prob": return huffmanSummary(v);
      case "arithmetic-step": {
        const i=Math.round(v), [prefix,lo,hi]=stages[i];
        return "步骤 "+i+" / 3："+prefix+"，区间 ["+lo.toFixed(3)+", "+hi.toFixed(3)+")，宽度 "+(hi-lo).toFixed(3);
      }

      case "lz-window": {
        const d=Math.round(v);
        let result="ABC";
        for(let i=0;i<6;i++)result+=result[result.length-d];
        return "历史 ABC；d="+d+"，复制6字符 → "+result;
      }
      case "bsc-channel": return "ε="+v.toFixed(2)+"，均匀输入互信息="+fmt(1-h2(v))+" bit/次";
      case "z-capacity": return "q="+v.toFixed(2)+"，I(X;Y)="+fmt(h2(.8*v)-v*h2(.2))+" bit；理论容量约0.6182 bit";
      case "repetition-error": {
        const n=Math.round(v),p=.1;
        let sum=0;
        for(let k=(n+1)/2;k<=n;k++){
          let binomial=1;
          for(let j=1;j<=k;j++)binomial=binomial*(n-j+1)/j;
          sum+=binomial*Math.pow(p,k)*Math.pow(1-p,n-k);
        }
        return "n="+n+"，R="+fmt(1/n)+"，块错误概率 "+(sum*100).toFixed(4)+"%";
      }
      case "hamming-syndrome": {
        const position=Math.round(v),bits="0110011".split("");
        if(position===0)return "未翻转：收到0110011；syndrome=000₂";
        bits[position-1]=bits[position-1]==="0"?"1":"0";
        return "翻转位置"+position+"：收到"+bits.join("")+"；syndrome="+position.toString(2).padStart(3,"0")+"₂ → 纠正第"+position+"位";
      }
      case "crc-remainder": {
        const p=Math.round(v),bits="1101001".split("");
        if(p>0) bits[p-1]=bits[p-1]==="0"?"1":"0";
        const recv=bits.join(""),m=recv.split("").map(Number),g=[1,0,1,1];
        for(let i=0;i<m.length-3;i++) if(m[i]) for(let j=0;j<4;j++) m[i+j]^=g[j];
        const s=m.slice(-3).join("");
        return (p===0?"未翻转":"翻转第"+p+"位")+"：接收 "+recv+"；余数 s(x)="+s+(s==="000"?" → 接受":" → 检出错误");
      }
      case "viterbi-flip": {
        const states=[[0,0],[0,1],[1,0],[1,1]];
        const step=(st,b)=>{const u=[b,st[0],st[1]];return [[u[0]^u[1]^u[2],u[0]^u[2]],[b,st[0]]];};
        let st=[0,0],tx=[];
        for(const b of [1,0,1,1,0,0]){const r=step(st,b);tx.push(r[0][0],r[0][1]);st=r[1];}
        const p=Math.round(v);
        if(p>0) tx[p-1]^=1;
        const T=tx.length/2,INF=1e9;
        let met=[0,INF,INF,INF],trace=[];
        for(let t=0;t<T;t++){
          const nm=[INF,INF,INF,INF],tr=[null,null,null,null];
          for(let si=0;si<4;si++){
            if(met[si]>=INF)continue;
            for(const b of [0,1]){
              const r=step(states[si],b),o=r[0],ns=r[1];
              const ni=states.findIndex(s=>s[0]===ns[0]&&s[1]===ns[1]);
              const d=(tx[2*t]^o[0])+(tx[2*t+1]^o[1]);
              if(met[si]+d<nm[ni]){nm[ni]=met[si]+d;tr[ni]=[si,b];}
            }
          }
          met=nm;trace.push(tr);
        }
        let best=met.indexOf(Math.min(...met)),out=[];
        for(let t=T-1;t>=0;t--){const rec=trace[t][best];out.push(rec[1]);best=rec[0];}
        out.reverse();
        const msg=out.slice(0,4).join("");
        return (p===0?"未翻转":"翻转第"+p+"位")+"：接收 "+tx.join("")+" → 译码 "+msg+(msg==="1011"?" ✓":" ✗");
      }
      case "otp-reuse": {
        const k=Math.round(v).toString(2).padStart(2,"0");
        const x=(a,b)=>a.split("").map((d,i)=>d^b[i]).join("");
        const c1=x("01",k),c2=x("10",k);
        return "k="+k+"：c₁="+c1+"，c₂="+c2+"，c₁⊕c₂="+x(c1,c2)+" = m₁⊕m₂";
      }
      case "gaussian-rd": {
        const D=Math.round(v)/100;
        const R=D>=1?0:0.5*Math.log2(1/D);
        return "D="+D.toFixed(2)+"，σ²=1：R(D)="+fmt(R)+" bit/sample"+(D>=1?"（已达 D_max）":"");
      }
      case "awgn-capacity": {
        const db=Math.round(v),snr=Math.pow(10,db/10),C=0.5*Math.log2(1+snr);
        return "SNR="+db+" dB（线性 "+snr.toFixed(2)+"）：C="+fmt(C)+" bit/symbol";
      }
      case "mac-region": {
        const a=Math.round(v)/100;
        const r1m=0.5*Math.log2(3),r2m=0.5*Math.log2(2.5),rs=0.5*Math.log2(4.5);
        const c1=[r1m,rs-r1m],c2=[rs-r2m,r2m];
        const R1=a*c1[0]+(1-a)*c2[0],R2=a*c1[1]+(1-a)*c2[1];
        return "α="+a.toFixed(2)+"：R₁="+fmt(R1)+"，R₂="+fmt(R2)+"，和="+fmt(R1+R2);
      }
      case "crb-gaussian": {
        const n=Math.round(v),crb=4/n;
        return "n="+n+"，σ²=4：CRB=1/I(μ)="+crb.toFixed(5)+"（无偏估计方差下界）";
      }
      case "ce-gradient": {
        const z=Math.round(v)/10,p=1/(1+Math.exp(-z)),nll=-Math.log(p);
        return "z="+z.toFixed(1)+"，p="+p.toFixed(3)+"，NLL="+nll.toFixed(3)+"，∂L/∂z_correct=p−y="+(p-1).toFixed(3);
      }
      case "ib-tradeoff": {
        const beta=Math.round(v)/10;
        const cands=[[0,0,"常数（完全丢弃）"],[1,1,"仅保留 Y"],[1,0,"仅保留高位 B"],[2,1,"保留全部 X"]];
        let pick=cands[0], best=cands[0][0]-beta*cands[0][1];
        for(const c of cands){const L=c[0]-beta*c[1]; if(L<best-1e-9){best=L;pick=c;}}
        return "β="+beta.toFixed(1)+" 时最优表示："+pick[2]+"；I(X;T)="+pick[0].toFixed(2)+"，I(T;Y)="+pick[1].toFixed(2)+"，目标 ="+best.toFixed(2);
      }
      case "entropy-bias": {
        const N=Math.max(1,Math.round(v));
        const bias=7/(2*N*Math.LN2);
        return "N="+N+"：m=8 时经验熵平均低估约 "+bias.toFixed(3)+" bit（渐近近似），而真实熵为 3.000 bit";
      }
      case "perplexity": {
        const ppl=Math.max(1.01,Math.round(v)/10);
        const bits=Math.log2(ppl), nats=bits*Math.LN2;
        return "困惑度="+ppl.toFixed(1)+"，每 token "+bits.toFixed(3)+" bit；自然对数交叉熵="+nats.toFixed(3);
      }
      case "pid": {
        const i=Math.min(3,Math.max(0,Math.round(v)));
        const names=["复制 Y=X₁=X₂","独特 Y=X₁，X₂ 独立","XOR Y=X₁⊕X₂","独立无信息"];
        const rows=[[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,0,0]];
        const r=rows[i];
        return names[i]+"：Red="+r[0]+"，Unq₁="+r[1]+"，Unq₂="+r[2]+"，Syn="+r[3]+" bit";
      }
      default: return null;
    }
  }
  for (const element of document.querySelectorAll("[data-lab]")) {
    const range=element.querySelector('input[type="range"]');
    const output=element.querySelector("output");
    if (!range || !output) continue;
    const update=()=>{
      const value=result(element.dataset.lab,Number(range.value));
      if (value===null) return;
      output.textContent=value;
      range.setAttribute("aria-valuetext",value);
    };
    range.addEventListener("input",update);
    update();
  }
})();
