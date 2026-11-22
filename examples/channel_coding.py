"""Deterministic models for chapters 11–15 of the information theory tutorial.

LZ77/LZ78 are educational token streams, not RFC 1951 wire formats.
DMC, capacity and Hamming routines use finite alphabets and GF(2).
"""
from __future__ import annotations
from math import comb, isclose, log2


def lz77_tokens(message: str, *, window: int = 32, min_match: int = 3):
    if not isinstance(message,str) or window<1 or min_match<2:
        raise ValueError("invalid input or LZ77 parameters")
    result=[]
    i=0
    while i<len(message):
        distance,length=0,0
        for d in range(1,min(window,i)+1):
            length_at_d=0
            while i+length_at_d<len(message) and message[i+length_at_d]==message[i+length_at_d-d]:
                length_at_d+=1  # comparison permits overlapping copied spans
            if length_at_d>length:
                distance,length=d,length_at_d
        if length>=min_match:
            result.append(("ref",distance,length))
            i+=length
        else:
            result.append(("lit",message[i]))
            i+=1
    return result


def lz77_decode(tokens):
    out=[]
    for token in tokens:
        if token[0]=="lit" and len(token)==2 and isinstance(token[1],str) and len(token[1])==1:
            out.append(token[1])
        elif token[0]=="ref" and len(token)==3:
            _,distance,length=token
            if not isinstance(distance,int) or not isinstance(length,int) or distance<1 or length<1 or distance>len(out):
                raise ValueError("invalid LZ77 reference")
            for _ in range(length):
                out.append(out[-distance])  # one character at a time, permits overlap
        else:
            raise ValueError("invalid token")
    return "".join(out)


def lz78_tokens(message: str):
    if not isinstance(message,str):
        raise ValueError("string required")
    seen={"":0}
    out=[]
    word=""
    for char in message:
        candidate=word+char
        if candidate in seen:
            word=candidate
        else:
            out.append((seen[word],char))
            seen[candidate]=len(seen)
            word=""
    if word:
        out.append((seen[word],None))  # final phrase already in dictionary
    return out


def lz78_decode(tokens):
    words=[""]
    result=[]
    for index,char in tokens:
        if not isinstance(index,int) or not 0<=index<len(words):
            raise ValueError("unknown dictionary entry")
        if char is not None and (not isinstance(char,str) or len(char)!=1):
            raise ValueError("invalid LZ78 literal")
        word=words[index]+(char or "")
        if not word:
            raise ValueError("empty LZ78 phrase")
        result.append(word)
        if char is not None:
            words.append(word)
    return "".join(result)


def binary_entropy(p:float):
    if not 0<=p<=1:
        raise ValueError("expected probability")
    return 0. if p in (0,1) else -p*log2(p)-(1-p)*log2(1-p)


def bsc_matrix(error: float):
    if not 0<=error<=1:
        raise ValueError("error outside [0,1]")
    return ((1-error,error),(error,1-error))


def bec_matrix(erasure: float):
    if not 0<=erasure<=1:
        raise ValueError("erasure outside [0,1]")
    return ((1-erasure,0.,erasure),(0.,1-erasure,erasure))


def cascade_bsc(p:float,q:float):
    if not all(0<=v<=1 for v in (p,q)):
        raise ValueError("crossover outside [0,1]")
    return p*(1-q)+(1-p)*q


def _validated_dmc(prior, rows):
    W=tuple(tuple(float(v) for v in row) for row in rows)
    p=tuple(float(v) for v in prior)
    if not W or len(W)!=len(p) or not W[0] or any(len(row)!=len(W[0]) for row in W):
        raise ValueError("bad DMC shape")
    if not isclose(sum(p),1.,rel_tol=0,abs_tol=1e-10) or any(not 0<=v<=1 for v in p):
        raise ValueError("invalid prior")
    for row in W:
        if any(not 0<=v<=1 for v in row) or not isclose(sum(row),1.,rel_tol=0,abs_tol=1e-10):
            raise ValueError("rows must be probability distributions")
    return p,W


def mutual_information(prior, rows):
    p,W=_validated_dmc(prior,rows)
    q=[sum(p[i]*W[i][j] for i in range(len(p))) for j in range(len(W[0]))]
    return sum(p[i]*w*log2(w/q[j]) for i,row in enumerate(W)
               for j,w in enumerate(row) if p[i]>0 and w>0)


def blahut_arimoto(rows, *, tolerance=1e-12, iterations=20000):
    W=tuple(tuple(float(v) for v in row) for row in rows)
    m=len(W)
    if m<1 or tolerance<=0 or iterations<1:
        raise ValueError("invalid BA options")
    p=tuple(1/m for _ in range(m))
    _,W=_validated_dmc(p,W)
    for _ in range(iterations):
        q=[sum(p[i]*W[i][j] for i in range(m)) for j in range(len(W[0]))]
        divergences=[
            sum(w*log2(w/q[j]) for j,w in enumerate(W[i]) if w>0)
            for i in range(m)
        ]
        scale=max(divergences)
        unnormalized=[p[i]*2**(divergences[i]-scale) for i in range(m)]
        normalizer=sum(unnormalized)
        updated=tuple(v/normalizer for v in unnormalized)
        difference=max(abs(updated[i]-p[i]) for i in range(m))
        p=updated
        if difference<tolerance:
            break
    return mutual_information(p,W),p


def repetition_error_probability(n:int,p:float):
    if not isinstance(n,int) or n<1 or n%2==0 or not 0<=p<=1:
        raise ValueError("odd positive n and probability required")
    return sum(comb(n,k)*p**k*(1-p)**(n-k) for k in range((n+1)//2,n+1))


def exact_bsc_block_error(codewords, p:float):
    """Exhaustively integrate BSC noise; equal-prior messages, nearest Hamming decoding.

    Ties break in favor of earliest codeword index. n<=16 for runtime bound.
    """
    words=tuple(codewords)
    if not words or not 0<=p<=1:
        raise ValueError("invalid codebook or noise")
    n=len(words[0])
    if not 1<=n<=16 or len(set(words))!=len(words) or any(len(w)!=n or set(w)-{"0","1"} for w in words):
        raise ValueError("binary equal-length unique codewords required (1..16)")
    total=0.
    for index,word in enumerate(words):
        for mask in range(1<<n):
            errors=mask.bit_count()
            chance=p**errors*(1-p)**(n-errors)
            r="".join(str(int(bit)^((mask>>pos)&1)) for pos,bit in enumerate(word))
            winner=min(range(len(words)),key=lambda i:sum(a!=b for a,b in zip(r,words[i])))
            if winner!=index:
                total+=chance/len(words)
    return total


def _bits(value, count):
    if not isinstance(value,str) or len(value)!=count or set(value)-{"0","1"}:
        raise ValueError(f"expected {count} binary characters")
    return [int(c) for c in value]


def hamming74_encode(message:str):
    data=_bits(message,4)
    c=[0]*8  # position 0 unused; checks at positions 1,2,4
    for position,bit in zip((3,5,6,7),data):
        c[position]=bit
    c[1]=c[3]^c[5]^c[7]
    c[2]=c[3]^c[6]^c[7]
    c[4]=c[5]^c[6]^c[7]
    return "".join(str(c[i]) for i in range(1,8))


def hamming74_syndrome(received:str):
    c=[0]+_bits(received,7)
    s1=c[1]^c[3]^c[5]^c[7]
    s2=c[2]^c[3]^c[6]^c[7]
    s4=c[4]^c[5]^c[6]^c[7]
    return s1+2*s2+4*s4


def hamming74_correct(received:str):
    c=_bits(received,7)
    position=hamming74_syndrome(received)
    if position:
        c[position-1]^=1
    return "".join(map(str,c))


def hamming74_extract(codeword:str):
    if hamming74_syndrome(codeword):
        raise ValueError("expected a valid Hamming codeword; correct first")
    return "".join(codeword[i-1] for i in (3,5,6,7))


def crc32_reflected(data: bytes) -> int:
    """CRC-32/ISO-HDLC (zlib, PNG, Ethernet): reflected polynomial 0xEDB88320."""
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("CRC input must be bytes")
    poly, crc = 0xEDB88320, 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def crc32_msb(data: bytes) -> int:
    """Non-reflected CRC-32/BZIP2 variant: polynomial 0x04C11DB7."""
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("CRC input must be bytes")
    poly, crc = 0x04C11DB7, 0xFFFFFFFF
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFFFFFF if crc & 0x80000000 else (crc << 1) & 0xFFFFFFFF
    return crc ^ 0xFFFFFFFF


def conv_encode(bits, tail: int = 0):
    """Rate 1/2, K=3 convolutional encoder with g0=111, g1=101 (octal 7,5)."""
    if not all(b in (0, 1) for b in bits):
        raise ValueError("convolutional input must be bits")
    state = [0, 0]
    out = []
    for b in list(bits) + [0] * tail:
        u = (b, state[0], state[1])
        out.append(u[0] ^ u[1] ^ u[2])
        out.append(u[0] ^ u[2])
        state = [b, state[0]]
    return out


def viterbi_decode(received):
    """Hard-decision Viterbi decoder for the (2,1,3) code above."""
    if not all(b in (0, 1) for b in received) or len(received) % 2:
        raise ValueError("received must be an even number of bits")
    states = [(0, 0), (0, 1), (1, 0), (1, 1)]
    steps = len(received) // 2
    inf = float("inf")
    metric = [0.0, inf, inf, inf]
    trace = []
    for t in range(steps):
        o = (received[2 * t], received[2 * t + 1])
        nxt = [inf] * 4
        back = [None] * 4
        for si, st in enumerate(states):
            if metric[si] == inf:
                continue
            for b in (0, 1):
                u = (b, st[0], st[1])
                oo = (u[0] ^ u[1] ^ u[2], u[0] ^ u[2])
                ns = (b, st[0])
                ni = states.index(ns)
                d = (o[0] ^ oo[0]) + (o[1] ^ oo[1])
                if metric[si] + d < nxt[ni]:
                    nxt[ni] = metric[si] + d
                    back[ni] = (si, b)
        metric = nxt
        trace.append(back)
    best = min(range(4), key=lambda i: metric[i])
    bits = []
    for t in range(steps - 1, -1, -1):
        si, b = trace[t][best]
        bits.append(b)
        best = si
    return list(reversed(bits))


if __name__ == "__main__":
    text="ABCABCABC"
    print("LZ77",lz77_tokens(text))
    print("LZ78",lz78_tokens("ABABABA"))
    print("Z channel capacity",blahut_arimoto(((1,0),(.2,.8))))
    print("Hamming",hamming74_encode("1011"))
