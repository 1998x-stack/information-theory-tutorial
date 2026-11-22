"""Deterministic source-coding teaching examples (Python standard library).

Huffman: symbol-by-symbol binary prefix code under known static weights.
Arithmetic: exact rational interval model, NOT a finite precision stream format.
Both sender and receiver must agree on symbol order and model.
"""
from __future__ import annotations
from fractions import Fraction
from itertools import count
from heapq import heappush, heappop
from math import comb, isclose, log2


def entropy(weights):
    ps = tuple(float(p) for p in weights)
    if not ps or any(not 0 <= p <= 1 for p in ps) or not isclose(sum(ps),1,abs_tol=1e-12):
        raise ValueError("distribution must be normalized")
    return -sum(p*log2(p) for p in ps if p)


def kraft_sum(lengths):
    ls=tuple(lengths)
    if not ls or any(not isinstance(l,int) or isinstance(l,bool) or l<1 for l in ls):
        raise ValueError("binary code lengths must be positive integers")
    return sum(2.0**(-l) for l in ls)


def shannon_lengths(weights):
    p=tuple(float(v) for v in weights)
    entropy(p)  # validates normalization
    from math import ceil
    return tuple(ceil(-log2(v)) for v in p if v>0)


def huffman_codebook(weights):
    if not weights or not hasattr(weights, "items"):
        raise ValueError("provide a nonempty dictionary")
    p=dict(weights)
    if any(not isinstance(s,str) or not s or float(w)<=0 for s,w in p.items()):
        raise ValueError("nonempty symbols and positive weights required")
    entropy(p.values())
    serial=count()
    queue=[]
    for symbol in sorted(p):
        heappush(queue,(float(p[symbol]),next(serial),symbol))
    if len(queue)==1:
        return {next(iter(p)):"0"}  # transport-friendly convention
    while len(queue)>1:
        a=heappop(queue)
        b=heappop(queue)
        heappush(queue,(a[0]+b[0],next(serial),(a[2],b[2])))
    code={}
    def visit(node,prefix):
        if isinstance(node,str):
            code[node]=prefix
            return
        visit(node[0],prefix+"0")
        visit(node[1],prefix+"1")
    visit(queue[0][2],"")
    assert kraft_sum(len(c) for c in code.values()) <= 1+1e-12
    return code


def decode_prefix(bits, codebook):
    if not codebook:
        raise ValueError("empty codebook")
    root={}
    for symbol,word in codebook.items():
        if not word or any(c not in "01" for c in word):
            raise ValueError("nonempty binary codewords required")
        node=root
        for i,bit in enumerate(word):
            if "_leaf" in node:
                raise ValueError("prefix collision")
            node=node.setdefault(bit,{})
            if i==len(word)-1:
                if node:
                    raise ValueError("prefix or duplicate collision")
                node["_leaf"]=symbol
    result=[]
    node=root
    for bit in bits:
        if bit not in "01" or bit not in node:
            raise ValueError("invalid encoded bitstream")
        node=node[bit]
        if "_leaf" in node:
            result.append(node["_leaf"])
            node=root
    if node is not root:
        raise ValueError("truncated bitstream")
    return "".join(result)


def _rational_probabilities(weights):
    if not weights or not hasattr(weights,"items"):
        raise ValueError("probability table must be an ordered mapping")
    p={symbol:Fraction(prob) for symbol,prob in weights.items()}
    if any(not isinstance(symbol,str) or not symbol or prob<=0 for symbol,prob in p.items()):
        raise ValueError("symbols must be names and probabilities positive")
    if sum(p.values())!=1:
        raise ValueError("use exact fractions summing to one")
    return p


def arithmetic_interval(message, weights):
    """Return the exact half-open [lo,hi) interval for a sequence."""
    p=_rational_probabilities(weights)
    lo,hi=Fraction(0),Fraction(1)
    for symbol in message:
        if symbol not in p:
            raise ValueError(f"unknown symbol: {symbol}")
        old_lo,old_hi=lo,hi
        width=old_hi-old_lo
        cumulative=Fraction(0)
        for current,prob in p.items():
            if current==symbol:
                lo=old_lo+width*cumulative
                hi=old_lo+width*(cumulative+prob)
                break
            cumulative+=prob
    return lo,hi


def arithmetic_decode(value, length, weights):
    """Recover 'length' symbols from any rational value inside the final interval."""
    p=_rational_probabilities(weights)
    value=Fraction(value)
    if not 0<=value<1 or not isinstance(length,int) or length<0:
        raise ValueError("invalid value or sequence length")
    lo,hi=Fraction(0),Fraction(1)
    result=[]
    for _ in range(length):
        old_lo,old_hi=lo,hi
        scaled=(value-old_lo)/(old_hi-old_lo)
        cumulative=Fraction(0)
        for symbol,prob in p.items():
            if cumulative <= scaled < cumulative+prob:
                width=old_hi-old_lo
                lo=old_lo+width*cumulative
                hi=old_lo+width*(cumulative+prob)
                result.append(symbol)
                break
            cumulative+=prob
        else:
            raise ValueError("value not contained in coding interval")
    return "".join(result)


def dyadic_prefix(lo,hi,max_bits=128):
    """Shortest dyadic cylinder interval wholly contained in [lo,hi)."""
    lo,hi=Fraction(lo),Fraction(hi)
    if not (0<=lo<hi<=1):
        raise ValueError("invalid interval")
    for bits in range(1,max_bits+1):
        denominator=1<<bits
        numerator=lo.numerator*denominator
        k=(numerator+lo.denominator-1)//lo.denominator
        if k < denominator and Fraction(k+1,denominator)<=hi:
            return format(k,f"0{bits}b")
    raise ValueError("dyadic interval not found within bit limit")


def typical_mass(n,p=0.25,epsilon=0.15):
    if not isinstance(n,int) or n<1 or not 0<p<1 or epsilon<=0:
        raise ValueError("invalid typical-set parameters")
    H=entropy((p,1-p))
    return sum(comb(n,k)*p**k*(1-p)**(n-k) for k in range(n+1)
        if abs(-(k*log2(p)+(n-k)*log2(1-p))/n-H)<=epsilon+1e-12)



def adaptive_interval(message, symbols=("A","B"), initial_count=1):
    """Exact adaptive arithmetic intervals using synchronized pseudocounts."""
    if not isinstance(initial_count,int) or initial_count<1 or len(set(symbols))!=len(symbols) or not symbols:
        raise ValueError("invalid initial adaptive counts")
    counts={symbol:initial_count for symbol in symbols}
    lo,hi=Fraction(0),Fraction(1)
    for symbol in message:
        if symbol not in counts:
            raise ValueError("unknown adaptive symbol")
        total=sum(counts.values())
        cumulative=0
        for current in counts:
            if current==symbol:
                old_lo,old_hi=lo,hi
                width=old_hi-old_lo
                lo=old_lo+width*Fraction(cumulative,total)
                hi=old_lo+width*Fraction(cumulative+counts[current],total)
                break
            cumulative+=counts[current]
        counts[symbol]+=1
    return lo,hi


def adaptive_decode(value, length, symbols=("A","B"), initial_count=1):
    """Reverse adaptive_interval with the same symbol order and update rule."""
    if not isinstance(initial_count,int) or initial_count<1 or not isinstance(length,int) or length<0 or len(set(symbols))!=len(symbols) or not symbols:
        raise ValueError("invalid adaptive decoding parameters")
    value=Fraction(value)
    if not 0<=value<1:
        raise ValueError("invalid dyadic code value")
    counts={symbol:initial_count for symbol in symbols}
    lo,hi=Fraction(0),Fraction(1)
    decoded=[]
    for _ in range(length):
        total=sum(counts.values())
        cumulative=0
        scaled=(value-lo)/(hi-lo)
        for symbol in counts:
            p_lower=Fraction(cumulative,total)
            p_upper=Fraction(cumulative+counts[symbol],total)
            if p_lower<=scaled<p_upper:
                old_lo,old_hi=lo,hi
                width=old_hi-old_lo
                lo=old_lo+width*p_lower
                hi=old_lo+width*p_upper
                decoded.append(symbol)
                counts[symbol]+=1
                break
            cumulative+=counts[symbol]
        else:
            raise ValueError("value outside adaptive interval")
    return "".join(decoded)

def gaussian_rate_distortion(D, sigma2=1.0):
    """R(D)=0.5*log2(sigma2/D) for 0<D<=sigma2, else 0. Squared-error distortion."""
    if sigma2 <= 0 or D <= 0:
        raise ValueError("D and sigma2 must be positive")
    return 0.0 if D >= sigma2 else 0.5 * log2(sigma2 / D)


def bernoulli_rate_distortion(D):
    """R(D)=1-h2(D) for a fair Bernoulli source under Hamming distortion (0<D<=0.5)."""
    if not 0 < D <= 0.5:
        raise ValueError("D must lie in (0, 0.5]")
    return 1 - (-D * log2(D) - (1 - D) * log2(1 - D))


if __name__=="__main__":
    weights={"A":.4,"B":.3,"C":.2,"D":.1}
    codebook=huffman_codebook(weights)
    print("Huffman",codebook,"L=",sum(weights[s]*len(c) for s,c in codebook.items()))
    p={"A":Fraction(3,5),"B":Fraction(2,5)}
    lo,hi=arithmetic_interval("ABA",p)
    prefix=dyadic_prefix(lo,hi)
    print("Arithmetic",lo,hi,"prefix",prefix,
        "decoded",arithmetic_decode(Fraction(int(prefix,2),1<<len(prefix)),3,p))
