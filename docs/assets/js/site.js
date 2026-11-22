"use strict";
(() => {
  const h2 = p => (p <= 0 || p >= 1) ? 0 :
    -p * Math.log2(p) - (1-p) * Math.log2(1-p);
  const fmt = n => n.toFixed(4);
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
