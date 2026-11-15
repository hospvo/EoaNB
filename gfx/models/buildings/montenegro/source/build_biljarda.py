"""Build the Biljarda landmark. Python 3 + numpy + Pillow + scipy; no Blender required.

Dimensions are approximate metres. Map export exaggerates height for readability.
Run from any directory. OBJ/MTL are also written for editing in Blender.
"""
from pathlib import Path
import io, math, struct, json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from pdx_io import Node, dump, read

HERE=Path(__file__).resolve().parent; OUT=HERE.parent
N=2048
# The former uniform scale made the palace lower than the terrain variation.
# Keep a compact footprint and a legible silhouette beside generic factories.
MAP_SCALE=np.array([.042,.095,.034])
SITE_X=3100.00;SITE_Z=1372.20
ROOT=HERE.parents[4]
terrain=np.array(Image.open(ROOT/'map/heightmap.bmp'),dtype=float)
def ground_height(x,z):
 yy=terrain.shape[0]-1-z;xx=x
 ix=int(np.floor(xx));iy=int(np.floor(yy));fx=xx-ix;fy=yy-iy
 return ((terrain[iy,ix]*(1-fx)+terrain[iy,ix+1]*fx)*(1-fy)+(terrain[iy+1,ix]*(1-fx)+terrain[iy+1,ix+1]*fx)*fy)*.1
heights=[ground_height(SITE_X+x,SITE_Z+z) for x in np.linspace(-1.68,1.68,49) for z in np.linspace(-1.22,1.22,41)]
SITE_Y=round(max(heights)+.06,2)
ATLAS={
 'stone':(.006,.006,.494,.494), 'roof':(.506,.006,.994,.494),
 'paving':(.006,.506,.494,.994), 'wood':(.506,.506,.994,.86),
 'shutter':(.51,.90,.57,.96), 'glass':(.59,.90,.65,.96),
 'trim':(.67,.90,.73,.96), 'shadow':(.75,.90,.81,.96),
 'soil':(.83,.90,.89,.96), 'metal':(.91,.90,.97,.96),
}
P=[];NORMAL=[];UV=[];TRI=[]
def norm(v):
 v=np.asarray(v,float);return v/max(np.linalg.norm(v),1e-12)
def face(points,material='stone',normal=None,coords=None):
 q=np.asarray(points,float)
 no=norm(np.cross(q[1]-q[0],q[2]-q[0])) if normal is None else norm(normal)
 if np.dot(np.cross(q[1]-q[0],q[2]-q[0]),no)<0:
  q=q[::-1]
  if coords is not None:coords=coords[::-1]
 if coords is None:coords=[(0,0),(1,0),(1,1),(0,1)][:len(q)]
 u,v,U,V=ATLAS[material];i=len(P)
 for x,st in zip(q,coords):
  P.append(x);NORMAL.append(no);UV.append((u+(U-u)*st[0],v+(V-v)*st[1]))
 for j in range(1,len(q)-1):TRI.append((i,i+j,i+j+1))

def panel(a,b,c,d,mat='stone',tile=3):
 a,b,c,d=np.asarray([a,b,c,d],float);nu=max(1,math.ceil(np.linalg.norm(b-a)/tile));nv=max(1,math.ceil(np.linalg.norm(d-a)/tile))
 for j in range(nv):
  for i in range(nu):
   pts=[a*(1-u)*(1-v)+b*u*(1-v)+c*u*v+d*(1-u)*v for u,v in [(i/nu,j/nv),((i+1)/nu,j/nv),((i+1)/nu,(j+1)/nv),(i/nu,(j+1)/nv)]]
   face(pts,mat)

def box(x0,x1,y0,y1,z0,z1,mat='stone',tile=3):
 panel((x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),mat,tile)
 panel((x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),mat,tile)
 panel((x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0),mat,tile)
 panel((x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),mat,tile)
 panel((x0,y1,z1),(x1,y1,z1),(x1,y1,z0),(x0,y1,z0),mat,tile)

def hiproof(x0,x1,z0,z1,y,h):
 e=.38;x0-=e;x1+=e;z0-=e;z1+=e;inset=min((z1-z0)*.48,(x1-x0)*.3)
 a=(x0,y,z0);b=(x1,y,z0);c=(x1,y,z1);d=(x0,y,z1)
 r=(x0+inset,y+h,(z0+z1)/2);s=(x1-inset,y+h,(z0+z1)/2)
 panel(d,c,s,r,'roof',3)
 panel(b,a,r,s,'roof',3)
 face([a,d,r],'roof');face([c,b,s],'roof')
 # Small metal ridge cap gives the skyline a crisp highlight.
 box(r[0],s[0],y+h-.03,y+h+.07,r[2]-.10,r[2]+.10,'metal',4)

def cylinder(cx,cz,r,y0,y1,mat='stone',segments=40):
 rows=max(1,math.ceil((y1-y0)/2.6))
 for j in range(rows):
  low=y0+(y1-y0)*j/rows;high=y0+(y1-y0)*(j+1)/rows
  for k in range(segments):
   a=2*np.pi*k/segments;b=2*np.pi*(k+1)/segments
   pts=[(cx+r*np.cos(a),low,cz+r*np.sin(a)),(cx+r*np.cos(b),low,cz+r*np.sin(b)),(cx+r*np.cos(b),high,cz+r*np.sin(b)),(cx+r*np.cos(a),high,cz+r*np.sin(a))]
   # Three angular strips per texture repeat keep the masonry at human scale.
   u0=(k%10)/10;u1=(k%10+1)/10
   face(pts,mat,normal=(np.cos((a+b)/2),0,np.sin((a+b)/2)),coords=[(u0,0),(u1,0),(u1,1),(u0,1)])
   for i in range(4):NORMAL[-4+i]=norm((pts[i][0]-cx,0,pts[i][2]-cz))
 for k in range(segments):
  a=2*np.pi*k/segments;b=2*np.pi*(k+1)/segments
  face([(cx,y1,cz),(cx+r*np.cos(b),y1,cz+r*np.sin(b)),(cx+r*np.cos(a),y1,cz+r*np.sin(a))],mat,normal=(0,1,0))

def cone(cx,cz,r,y,h):
 for k in range(40):
  a=2*np.pi*k/40;b=2*np.pi*(k+1)/40
  face([(cx+r*np.cos(a),y,cz+r*np.sin(a)),(cx,y+h,cz),(cx+r*np.cos(b),y,cz+r*np.sin(b))],'roof')

def window(x,y,z,side=1,width=.92,height=1.45,shutters=True):
 # Recesses, projecting sills, narrow frames and separate shutters survive map zoom.
 def part(x0,x1,y0,y1,depth,mat):
  zz=z+side*depth
  face([(x0,y0,zz),(x1,y0,zz),(x1,y1,zz),(x0,y1,zz)],mat,normal=(0,0,side))
 w=width/2;part(x-w-.10,x+w+.10,y-.08,y+height+.09,.012,'shadow')
 part(x-w,x+w,y,y+height,.025,'glass')
 for xx in [x-w-.08,x+w-.01]:part(xx,xx+.09,y-.04,y+height+.06,.055,'trim')
 part(x-w-.08,x+w+.08,y+height,y+height+.09,.055,'trim')
 part(x-.025,x+.025,y,y+height,.065,'wood')
 part(x-w,x+w,y+height*.52,y+height*.52+.045,.065,'wood')
 box(x-w-.17,x+w+.17,y-.14,y-.035,min(z+side*.04,z+side*.28),max(z+side*.04,z+side*.28),'trim',3)
 if shutters:
  for xx in [x-w-.49,x+w+.12]:
   part(xx,xx+.37,y,y+height,.09,'shutter')
   for yy in [y+.17,y+height-.20]:part(xx,xx+.37,yy,yy+.055,.10,'wood')

def door(x,z,side=1):
 width=1.55;spring=1.9;r=width/2
 pts=[(x-r,0,z),(x+r,0,z),(x+r,spring,z)]
 pts.extend((x+r*np.cos(a),spring+r*np.sin(a),z) for a in np.linspace(0,np.pi,17)[1:])
 face(pts,'shadow',normal=(0,0,side),coords=[(.5,.5)]*len(pts))
 # Arch voussoirs are actual stone blocks.
 for a,b in zip(np.linspace(0,np.pi,17)[:-1],np.linspace(0,np.pi,17)[1:]):
  pts=[(x+rr*np.cos(t),spring+rr*np.sin(t),z+side*.04) for rr,t in [(r,a),(r,b),(r+.22,b),(r+.22,a)]]
  face(pts,'trim',normal=(0,0,side))
 for xx in [x-r-.22,x+r]:
  box(xx,xx+.22,0,spring,min(z,z+side*.12),max(z,z+side*.12),'trim')

def gate(x,z,orientation=1):
 # Gate is a true opening through the enclosure, with a rounded stone arch.
 radius=1.65;spring=1.85;top=4.2;thick=.75
 for sign in [-1,1]:
  zz=z+sign*thick/2
  for a,b in zip(np.linspace(0,np.pi,21)[:-1],np.linspace(0,np.pi,21)[1:]):
   pts=[(x+radius*np.cos(a),spring+radius*np.sin(a),zz),(x+radius*np.cos(b),spring+radius*np.sin(b),zz),(x+radius*np.cos(b),top,zz),(x+radius*np.cos(a),top,zz)]
   face(pts,'stone',normal=(0,0,sign))
 for a,b in zip(np.linspace(0,np.pi,21)[:-1],np.linspace(0,np.pi,21)[1:]):
  xa=x+radius*np.cos(a);xb=x+radius*np.cos(b);ya=spring+radius*np.sin(a);yb=spring+radius*np.sin(b)
  face([(xa,ya,z-thick/2),(xb,yb,z-thick/2),(xb,yb,z+thick/2),(xa,ya,z+thick/2)],'trim')
 box(x-radius-.7,x-radius,0,top,z-thick/2,z+thick/2)
 box(x+radius,x+radius+.7,0,top,z-thick/2,z+thick/2)
 box(x-radius-.85,x+radius+.85,top,top+.18,z-.52,z+.52,'trim')

# Terrain-fitted retaining terrace: the upper court is level and fully above the
# hillside; its lower edge follows the heightmap instead of floating in space.
ring=[]
for cx,cz,start in [(36.2,32,0),(-36.2,32,90),(-36.2,-32,180),(36.2,-32,270)]:
 for angle in np.linspace(start,start+90,9):
  angle=np.deg2rad(angle);ring.append((cx+3.48*np.cos(angle),cz+3.48*np.sin(angle)))
for (x,z),(X,Z) in zip(ring,ring[1:]+ring[:1]):
 y=(ground_height(SITE_X+x*MAP_SCALE[0],SITE_Z+z*MAP_SCALE[2])-SITE_Y-.12)/MAP_SCALE[1]
 Y=(ground_height(SITE_X+X*MAP_SCALE[0],SITE_Z+Z*MAP_SCALE[2])-SITE_Y-.12)/MAP_SCALE[1]
 panel((x,y,z),(X,Y,Z),(X,-.08,Z),(x,-.08,z),'stone',3)
 # A pale coping course separates the residence from the dark political map.
 panel((x,-.10,z),(X,-.10,Z),(X*.99,-.10,Z*.99),(x*.99,-.10,z*.99),'trim',3)
 # Close the terrace deck between the court rectangle and the rounded towers.
 face([(0,-.08,0),(x,-.08,z),(X,-.08,Z)],'paving',normal=(0,1,0),coords=[(.5,.5),((x+40)/80,(z+36)/72),((X+40)/80,(Z+36)/72)])
# Enclosure and shallow paved court. The 1916 relief pavilion is deliberately absent.
box(-36.2,36.2,-.08,0,-32,32,'paving',4.5)
for z in [-32,32]:
 for left,right in ([(-36.2,-2.35),(2.35,36.2)] if z<0 else [(-36.2,36.2)]):
  box(left,right,0,3.15,z-.37,z+.37)
  box(left,right,3.15,3.33,z-.50,z+.50,'trim')
for x in [-36.2,36.2]:
 box(x-.37,x+.37,0,3.15,-32,32)
 box(x-.50,x+.50,3.15,3.33,-32,32,'trim')
# Central two-storey residence, with deeper end pavilions.
box(-36.2,36.2,0,7.5,-3.75,3.75)
hiproof(-29.4,29.4,-3.75,3.75,7.5,2.2)
for x0,x1 in [(-36.2,-29.4),(29.4,36.2)]:
 box(x0,x1,0,7.5,-3.75,9.75)
 hiproof(x0,x1,-3.75,9.75,7.5,2.0)
# Ground plinth, eaves and slightly projecting corner quoins.
for side in [-1,1]:
 z=side*3.75
 box(-36.2,36.2,0,.38,min(z,z+side*.12),max(z,z+side*.12),'trim',3)
 box(-36.5,36.5,7.27,7.50,min(z,z+side*.17),max(z,z+side*.17),'trim',3)
 for x in np.linspace(-33.8,33.8,23):
  for y in [1.05,4.63]:
   if y<2 and abs(x)<2.0:continue
   if side>0 and abs(x)>28.5:continue
   window(x,y,z,side)
 door(0,z+side*.028,side)
for x in [-33,33]:
 for y in [1.05,4.63]:window(x,y,9.75,1)
for x in [-36.2,36.2]:
 for y in [0.5,2.0,3.5,5.0,6.5]:
  box(x-.13,x+.13,y,y+.5,-3.87,-3.64,'trim')
# Corner towers have continuous smooth sides, shallow conical lead roofs and stone cornices.
for x in [-36.2,36.2]:
 for z in [-32,32]:
  cylinder(x,z,3.05,0,6.45)
  cylinder(x,z,3.18,2.95,3.12,'trim')
  cylinder(x,z,3.20,6.23,6.48,'trim')
  cone(x,z,3.48,6.5,.95)
  window(x,4.3,z+3.055,1,.64,1.15,False)
  window(x,4.3,z-3.055,-1,.64,1.15,False)
# Entrance opening in the front enclosure.
gate(0,-32)
# A modest stair connects the gateway to the hillside, rather than leaving a
# sheer retaining wall across the only entrance.
foot_y=(ground_height(SITE_X,SITE_Z-45*MAP_SCALE[2])-SITE_Y-.035)/MAP_SCALE[1]
for step in range(8):
 near=-32-step*13/8;far=-32-(step+1)*13/8;top=foot_y*(step+1)/8
 box(-2.25,2.25,foot_y-.25,top,far,near,'trim',3)
# Roof chimneys with collars and dark recessed flues.
for x in [-25,-11,11,25]:
 box(x-.48,x+.48,8.2,10.65,-.5,.5)
 box(x-.61,x+.61,10.60,10.85,-.63,.63,'trim')
 face([(x-.35,10.86,-.35),(x+.35,10.86,-.35),(x+.35,10.86,.35),(x-.35,10.86,.35)],'shadow',normal=(0,1,0))
# Two modest courtyard wells, appropriate to the documented historic court.
for z in [-18,19]:
 cylinder(-17,z,.85,0,.8,'trim',24)
 face([(-17+ .65*np.cos(a),.81,z+.65*np.sin(a)) for a in np.linspace(0,2*np.pi,25)[:-1]],'shadow',normal=(0,1,0),coords=[(.5,.5)]*24)

# Texture atlas: preserve generated material samples; add exact shader palette swatches.
diff=np.array(Image.open(HERE/'biljarda_materials.png').convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)
colors={'shutter':[119,42,31],'glass':[26,34,37],'trim':[187,181,163],'shadow':[28,26,23],'soil':[98,91,74],'metal':[123,126,122]}
for key,color in colors.items():
 u,v,U,V=ATLAS[key];diff[int((v-.008)*N):int((V+.008)*N),int((u-.008)*N):int((U+.008)*N)]=color
# Brighter, slightly warm limestone and quieter texture detail stay readable
# under the map's night/overcast tint, without emissive or unlit materials.
stone=diff[:1024,:1024];stone[:]=gaussian_filter(stone,sigma=(1.2,1.2,0))*.99+np.array([7,6,3])
roof=diff[:1024,1024:];roof[:]=gaussian_filter(roof,sigma=(1,1,0))*.93+np.array([15,16,16])
paving=diff[1024:,:1024];paving[:]=gaussian_filter(paving,sigma=(1.8,1.8,0))*.93+np.array([11,7,0])
normal=np.tile(np.array([128,128,0,128],float),(N,N,1));spec=np.tile(np.array([0,65,0,65],float),(N,N,1))
lum=diff@[.299,.587,.114];dy,dx=np.gradient(gaussian_filter(lum,.8))
normal[:,:,0]-=np.clip(dx*.65,-15,15);normal[:,:,1]-=np.clip(dy*.65,-15,15);normal[:,:,3]=normal[:,:,0]
spec[:1024,1024:]=[0,81,100,89]
for key in ['glass','metal']:
 u,v,U,V=ATLAS[key];spec[int((v-.008)*N):int((V+.008)*N),int((u-.008)*N):int((U+.008)*N)]=[0,92,0 if key=='glass' else 175,140]

def dds(arr,path,fmt):
 im=Image.fromarray(np.uint8(np.clip(arr,0,255)));levels=[]
 while True:
  buf=io.BytesIO();im.save(buf,format='DDS',pixel_format=fmt);data=buf.getvalue()
  if not levels:header=bytearray(data[:128])
  levels.append(data[128:])
  if im.size==(1,1):break
  im=im.resize(tuple(max(1,x//2) for x in im.size),Image.Resampling.BOX)
 struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000);struct.pack_into('<I',header,28,len(levels));struct.pack_into('<I',header,108,0x401008)
 path.write_bytes(header+b''.join(levels))
for suffix,arr,fmt in [('diffuse',diff,'DXT1'),('normal',normal,'DXT5'),('spec',spec,'DXT5')]:dds(arr,OUT/('MNT_biljarda_'+suffix+'.dds'),fmt)
Image.fromarray(np.uint8(np.clip(diff,0,255))).save(HERE/'MNT_biljarda_diffuse.png')

p=np.asarray(P)*MAP_SCALE;n=np.asarray(NORMAL)/MAP_SCALE;n/=np.linalg.norm(n,axis=1,keepdims=True);uv=np.asarray(UV);tri=np.asarray(TRI)
# Remove degenerate triangles (arch crown and any collapsed wedges).
valid=np.linalg.norm(np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]),axis=1)>1e-10;tri=tri[valid]
a=p[tri[:,1]]-p[tri[:,0]];b=p[tri[:,2]]-p[tri[:,0]];du=uv[tri[:,1]]-uv[tri[:,0]];dv=uv[tri[:,2]]-uv[tri[:,0]]
det=du[:,0]*dv[:,1]-du[:,1]*dv[:,0];factor=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-10)
tf=(a*dv[:,1,None]-b*du[:,1,None])*factor[:,None];bf=(b*du[:,0,None]-a*dv[:,0,None])*factor[:,None]
tan=np.zeros_like(p);bit=np.zeros_like(p)
for j in range(3):np.add.at(tan,tri[:,j],tf);np.add.at(bit,tri[:,j],bf)
tan-=n*(tan*n).sum(1)[:,None];bad=np.linalg.norm(tan,axis=1)<1e-10
tan[bad]=np.cross(n[bad],np.array([.37,.61,.17]));tan/=np.linalg.norm(tan,axis=1,keepdims=True)
hand=np.where((np.cross(n,tan)*bit).sum(1)>=0,-1,1)
root=Node('');root.items=[('pdxasset','i',np.array([1,0]))]
obj=Node('object');shape=Node('MNT_biljardaShape');mesh=Node('mesh');obj.items=[shape];shape.items=[mesh];root.items.append(obj)
for key,val,typ in [('p',p,'f'),('n',n,'f'),('ta',np.c_[tan,hand],'f'),('u0',uv,'f'),('tri',tri,'i')]:mesh.items.append((key,typ,val.ravel()))
bb=Node('aabb');bb.items=[('min','f',p.min(0)),('max','f',p.max(0))];mesh.items.append(bb)
material=Node('material');mesh.items.append(material)
for key,val in [('shader','PdxMeshAdvancedSnow'),('diff','MNT_biljarda_diffuse.dds'),('n','MNT_biljarda_normal.dds'),('spec','MNT_biljarda_spec.dds')]:material.items.append((key,'s',(val+'\0').encode()))
path=OUT/'MNT_biljarda.mesh';path.write_bytes(dump(root));assert dump(read(path))==path.read_bytes()
assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(tan).all()
assert tri.min()>=0 and tri.max()<len(p) and ((uv>=0)&(uv<=1)).all()
assert np.allclose(np.linalg.norm(n,axis=1),1) and np.allclose(np.linalg.norm(tan,axis=1),1)
# Editable geometry uses metres and a conventional OBJ texture orientation.
with (HERE/'MNT_biljarda.obj').open('w') as f:
 f.write('mtllib MNT_biljarda.mtl\no MNT_biljarda\nusemtl Biljarda\n')
 for v in np.asarray(P):f.write('v '+' '.join(f'{x:.6f}' for x in v)+'\n')
 for u,v in uv:f.write(f'vt {u:.6f} {1-v:.6f}\n')
 for v in n:f.write('vn '+' '.join(f'{x:.6f}' for x in v)+'\n')
 for t in tri:f.write('f '+' '.join(f'{i+1}/{i+1}/{i+1}' for i in t)+'\n')
(HERE/'MNT_biljarda.mtl').write_text('newmtl Biljarda\nKd 1 1 1\nmap_Kd MNT_biljarda_diffuse.png\n')
(HERE/'map-placement.json').write_text(json.dumps({'state':942,'province':9821,'x':SITE_X,'y':SITE_Y,'z':SITE_Z,'rotation':0,'map_scale':MAP_SCALE.tolist(),'terrain_min':min(heights),'terrain_max':max(heights)},indent=2))
print(f'Exported {len(p)} vertices, {len(tri)} triangles; bounds {p.min(0)} to {p.max(0)}')
print(f'Placement: {SITE_X};{SITE_Y};{SITE_Z}; terrain {min(heights):.2f} to {max(heights):.2f}')
