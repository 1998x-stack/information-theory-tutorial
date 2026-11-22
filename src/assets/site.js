"use strict";
(() => {
  const h2 = p => (p <= 0 || p >= 1) ? 0 :
    -p * Math.log2(p) - (1-p) * Math.log2(1-p);
  const fmt = n => n.toFixed(4);

  function crcRemainder(bits,generator){const w=bits.split("").map(Number),g=generator.split("").map(Number);for(let i=0;i<=w.length-g.length;i++)if(w[i])for(let j=0;j<g.length;j++)w[i+j]^=g[j];return w.slice(-(g.length-1)).join("").padStart(g.length-1,"0");}
  function convEncode(bits){let state=0,out="";for(const ch of bits+"00"){const b=Number(ch),p=(state>>1)&1,o=state&1;out+=(b^p^o).toString()+(b^o).toString();state=(b<<1)|p;}return out;}
  function viterbiDecode(received){const pairs=received.match(/../g)||[];let m=[0,Infinity,Infinity,Infinity],backs=[];for(const pair of pairs){const next=[Infinity,Infinity,Infinity,Infinity],pred=[null,null,null,null];for(let s=0;s<4;s++){if(!Number.isFinite(m[s]))continue;const p=(s>>1)&1,o=s&1;for(let b=0;b<=1;b++){const out=[b^p^o,b^o],ns=(b<<1)|p,cost=(Number(pair[0])!==out[0])+(Number(pair[1])!==out[1]),v=m[s]+cost;if(v<next[ns]){next[ns]=v;pred[ns]={state:s,bit:b};}}}m=next;backs.push(pred);}let state=0,bits="";for(let t=backs.length-1;t>=0;t--){const p=backs[t][state];if(!p)return {bits:"?",metric:Infinity};bits=p.bit+bits;state=p.state;}return {bits:bits.slice(0,-2),metric:m[0]};}
  function waterFill(noise,power){let lo=Math.min(...noise),hi=Math.max(...noise)+power;for(let k=0;k<80;k++){const mid=(lo+hi)/2,total=noise.reduce((s,n)=>s+Math.max(mid-n,0),0);if(total>power)hi=mid;else lo=mid;}const level=(lo+hi)/2,powers=noise.map(n=>Math.max(level-n,0)),capacity=powers.reduce((s,p,i)=>s+.5*Math.log2(1+p/noise[i]),0);return {level,powers,capacity};}
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

      case "crc-syndrome": {const pos=Math.round(v),bits="1101001".split("");if(pos>0)bits[pos-1]=bits[pos-1]==="0"?"1":"0";const received=bits.join(""),syn=crcRemainder(received,"1011");return pos===0?"收到 1101001；综合征 000，码字通过校验":("翻转位置 "+pos+"：收到 "+received+"；综合征 "+syn+"，"+(syn==="000"?"未检出":"检测到错误"));}
      case "viterbi-noise": {const pos=Math.round(v),bits=convEncode("1011").split("");if(pos>0)bits[pos-1]=bits[pos-1]==="0"?"1":"0";const received=bits.join(""),decoded=viterbiDecode(received);return "接收 "+received+"；硬判决 Viterbi 解码为 "+decoded.bits+"；路径度量 "+decoded.metric;}
      case "otp-leakage": return "q="+v.toFixed(2)+"；均匀明文下泄漏 I(M;C)="+fmt(1-h2(v))+" bit";
      case "binary-rd": return "D="+v.toFixed(3)+"；R(D)="+fmt(v>=.2?0:h2(.2)-h2(v))+" bit/符号";
      case "water-filling": {const z=waterFill([1,2,4],v);return "P="+v.toFixed(1)+"；μ="+fmt(z.level)+"；分配("+z.powers.map(x=>x.toFixed(3)).join(", ")+")；容量="+fmt(z.capacity)+" bit/组三次使用";}
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
