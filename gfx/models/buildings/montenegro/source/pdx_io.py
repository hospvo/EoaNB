from pathlib import Path
import struct,sys
import numpy as np
unit=Path('gfx/models/units')
work=Path(__file__).parent
class Node:
    def __init__(self,name):
        self.name=name
        self.items=[]
    def child(self,name):
        return next(c for c in self.items if isinstance(c,Node) and c.name==name)
    def prop(self,name):
        return next(p[2] for p in self.items if not isinstance(p,Node) and p[0]==name)
    def set(self,name,val):
        for i,p in enumerate(self.items):
            if not isinstance(p,Node) and p[0]==name:
                self.items[i]=(name,p[1],val)
                return
        raise KeyError(name)
    def children(self):
        return [c for c in self.items if isinstance(c,Node)]
def read(path):
    data=path.read_bytes()
    assert data[:4]==b'@@b@'
    root=Node(''); stack=[root]; i=4
    while i<len(data):
        if data[i]==91:
            depth=0
            while data[i]==91: depth+=1;i+=1
            end=data.index(0,i)
            node=Node(data[i:end].decode('latin1'));i=end+1
            stack=stack[:depth];stack[-1].items.append(node);stack.append(node)
        else:
            assert data[i]==33,(i,data[i:i+50])
            n=data[i+1]; name=data[i+2:i+2+n].decode();i+=2+n
            typ=chr(data[i]);num=struct.unpack_from('<I',data,i+1)[0];i+=5
            if typ=='s':
                assert num==1
                n=struct.unpack_from('<I',data,i)[0];i+=4;v=data[i:i+n];i+=n
            else:
                assert typ in 'fi'
                v=np.frombuffer(data,dtype='<'+typ+'4' if typ=='f' else '<i4',count=num,offset=i);i+=num*4
            stack[-1].items.append((name,typ,v))
    return root
def dump(node,depth=0):
    out=bytearray(b'@@b@' if not depth else b'['*depth+node.name.encode('latin1')+b'\0')
    for p in node.items:
        if isinstance(p,Node):
            out+=dump(p,depth+1)
        else:
            k,t,v=p;k=k.encode();out+=b'!'+bytes([len(k)])+k+t.encode()+struct.pack('<I',1 if t=='s' else len(v))
            out+=struct.pack('<I',len(v))+v if t=='s' else np.asarray(v,dtype='<f4' if t=='f' else '<i4').tobytes()
    return out
def meshes(root):
    return [m for obj in root.child('object').children() for m in obj.children() if m.name=='mesh']
def components(m):
    pos=m.prop('p').reshape(-1,3)
    unique,inv=np.unique(np.round(pos,4),axis=0,return_inverse=True); inv=inv.ravel()
    par=list(range(len(unique)))
    def find(n):
        while n!=par[n]:par[n]=par[par[n]];n=par[n]
        return n
    for a,b,c in inv[m.prop('tri')].reshape(-1,3):
        par[find(b)]=find(a);par[find(c)]=find(a)
    groups=np.array([find(n) for n in inv])
    return sorted([np.flatnonzero(groups==n) for n in set(groups)],key=lambda g:-len(g))
if __name__=='__main__':
    for f in sys.argv[1:]:
        path=unit/f;r=read(path);assert dump(r)==path.read_bytes()
        for m in meshes(r):
            pos=m.prop('p').reshape(-1,3)
            print(f,m.child('material').items,[p[0] for p in m.items if not isinstance(p,Node)])
            for k,g in enumerate(components(m)):
                low=pos[g].min(0);hi=pos[g].max(0)
                if hi[1]>4.5:print(k,len(g),low.round(2),hi.round(2))
