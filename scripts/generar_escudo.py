"""Escudo Solar. Modelado y texturas originales, reproducibles sin Blender.
Python 3 + numpy + Pillow. Exporta glTF 2.0 binario con UV y tangentes.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import json, struct, math, io

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT; TEX=OUT/'texturas'; ASSET=OUT/'assets'
TEX.mkdir(parents=True,exist_ok=True); ASSET.mkdir(parents=True,exist_ok=True)
N=512; rng=np.random.default_rng(806)
y,x=np.mgrid[0:N,0:N]/N

def png(name,arr):
    im=Image.fromarray(np.uint8(np.clip(arr,0,1)*255))
    im.save(TEX/name,optimize=True)

def normals(height,strength):
    dy,dx=np.gradient(height)
    a=np.stack([-dx*strength,dy*strength,np.ones_like(dx)],axis=-1)
    a/=np.linalg.norm(a,axis=-1,keepdims=True)
    return a*.5+.5

for name in ['madera','acero','bronce']:
    noise=rng.normal(0,1,(N,N))
    noise=np.asarray(Image.fromarray(np.uint8(np.clip(noise*30+128,0,255))).filter(ImageFilter.GaussianBlur(1.1)),float)/30-128/30
    if name=='madera':
        # Vertical grain, knots and recessed joints; all details live in textures.
        grain=np.sin(x*460+np.sin(y*17)*2+np.sin(y*43)*.7)
        fine=np.sin(x*1400+np.sin(y*30)*3)
        plank=np.floor(x*9).astype(int)
        planktone=np.array([.88,1.06,.96,.82,1.08,.92,1.02,.89,.98])[np.minimum(plank,8)]
        seam=np.exp(-(np.sin(x*9*np.pi)/.045)**2)
        knots=np.zeros_like(x)
        for kx,ky in [(.18,.28),(.65,.71),(.83,.36),(.43,.56)]:
            d=((x-kx)*2)**2+((y-ky)*.4)**2
            knots+=np.exp(-d*1600)*np.sin(np.sqrt(d)*700)*.45
        h=grain*.15+fine*.025+noise*.015-seam*.6+knots
        value=(.78+.09*grain+.025*fine+.025*noise+knots*.12)*planktone*(1-.66*seam)
        base=value[:,:,None]*np.array([.52,.30,.145])
        rough=np.clip(.77+.08*grain+noise*.025+seam*.15,.3,1)
        metal=np.zeros_like(x); strength=2.2
    else:
        pits=rng.random((N,N))
        scratches=np.sin(x*1500+y*18)*.02
        h=noise*.025+np.sin(x*100)*np.sin(y*125)*.025+scratches*.3
        # Scattered micro pits and brushed streaks, no painted lighting.
        value=.89+noise*.045+np.sin(x*400+y*13)*.015-(pits>.994)*.22
        tint=[.56,.61,.64] if name=='acero' else [.72,.47,.19]
        base=value[:,:,None]*np.array(tint)
        rough=np.clip((.70 if name=='acero' else .64)+noise*.04+(pits>.98)*.05,.15,.95)
        metal=np.full_like(x,.98 if name=='acero' else .95); strength=1.5
    png(f'{name}_BaseColor.png',base)
    png(f'{name}_Roughness.png',rough)
    png(f'{name}_Metallic.png',metal)
    png(f'{name}_Normal.png',normals(h,strength))
    # glTF metallic-roughness uses green=roughness, blue=metallic.
    png(f'{name}_MetallicRoughness.png',np.stack([np.ones_like(x),rough,metal],axis=-1))

class Mesh:
    def __init__(self,name,material):
        self.name=name; self.material=material
        self.pos=[]; self.norm=[]; self.uv=[]; self.tan=[]; self.idx=[]
    def tri(self,points,uvs,norms=None):
        p=np.array(points,float); uv=np.array(uvs,float)
        cross=np.cross(p[1]-p[0],p[2]-p[0]); area=np.linalg.norm(cross)
        if area<1e-12:return
        face=cross/area
        ns=np.tile(face,(3,1)) if norms is None else np.array(norms,float)
        dp1=p[1]-p[0]; dp2=p[2]-p[0]; duv1=uv[1]-uv[0]; duv2=uv[2]-uv[0]
        det=duv1[0]*duv2[1]-duv2[0]*duv1[1]
        t=(dp1*duv2[1]-dp2*duv1[1])/det if abs(det)>1e-10 else np.array([1.,0,0])
        b=(dp2*duv1[0]-dp1*duv2[0])/det if abs(det)>1e-10 else np.array([0.,1,0])
        for pp,uu,nn in zip(p,uv,ns):
            nn=nn/np.linalg.norm(nn); tt=t-nn*np.dot(nn,t)
            if np.linalg.norm(tt)<1e-10:tt=np.cross(nn,[0,1,.01])
            tt/=np.linalg.norm(tt)
            self.idx.append(len(self.pos)); self.pos.append(pp.tolist()); self.uv.append(uu.tolist()); self.norm.append(nn.tolist())
            self.tan.append([*tt.tolist(),-1. if np.dot(np.cross(nn,tt),b)<0 else 1.])
    def quad(self,p,uv,n=None):
        for ids in [(0,1,2),(0,2,3)]:self.tri([p[i] for i in ids],[uv[i] for i in ids],None if n is None else [n[i] for i in ids])

wood=Mesh('01 · Cuerpo de tablones',0); steel=Mesh('02 · Borde y asa de acero',1); bronze=Mesh('03 · Sol, molduras y remaches de bronce',2)
meshes=[wood,steel,bronze]
TAU=math.tau
def surface(r):return .035+.034*(1-(r/.46)**2)
def lathe(mesh,profile,segments=64,origin=(0,0,0),scaleuv=1):
    # Profile travels counterclockwise around section (r,z); outward normals.
    ox,oy,oz=origin; prof=np.array(profile,float)
    dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(prof,axis=0),axis=1))]; dist/=dist[-1] or 1
    for j in range(len(profile)-1):
        r1,z1=profile[j]; r2,z2=profile[j+1]
        dr=r2-r1; dz=z2-z1
        for i in range(segments):
            a=i/segments*TAU; b=(i+1)/segments*TAU
            p=[(ox+r1*math.cos(a),oy+r1*math.sin(a),oz+z1),(ox+r2*math.cos(a),oy+r2*math.sin(a),oz+z2),(ox+r2*math.cos(b),oy+r2*math.sin(b),oz+z2),(ox+r1*math.cos(b),oy+r1*math.sin(b),oz+z1)]
            n=[(-dz*math.cos(ang),-dz*math.sin(ang),dr) for ang in [a,a,b,b]]
            uv=[(i/segments*scaleuv,dist[j]),(i/segments*scaleuv,dist[j+1]),((i+1)/segments*scaleuv,dist[j+1]),((i+1)/segments*scaleuv,dist[j])]
            mesh.quad(p,uv,n)

# Radial body front and rear; planar UV projection preserves continuous grain.
S=64
for front in [True,False]:
    rings=[0,.14,.28,.415]
    for inner,outer in zip(rings[:-1],rings[1:]):
        for i in range(S):
            a=i/S*TAU; b=(i+1)/S*TAU
            p=[(r*math.cos(t),r*math.sin(t),surface(r) if front else -.033) for r,t in [(inner,a),(outer,a),(outer,b),(inner,b)]]
            uv=[(px/.83+.5,.5-py/.83) for px,py,pz in p]
            n=[(px*.068/.46**2,py*.068/.46**2,1) if front else (0,0,-1) for px,py,pz in p]
            if not front:p.reverse();uv.reverse();n.reverse()
            wood.quad(p,uv,n)
lathe(wood,[(.415,surface(.415)),(.415,-.033)],64)
# Six-step steel rim with front chamfer and back lip.
lathe(steel,[(.403,.031),(.411,.052),(.450,.052),(.463,.038),(.463,-.032),(.450,-.045),(.408,-.045)],64)

def torus(mesh,R,r,z,segments=64,sides=6):
    prof=[(R+r*math.cos(t),z+r*math.sin(t)) for t in np.linspace(0,-TAU,sides+1)]
    lathe(mesh,prof,segments)
torus(bronze,.411,.0055,.053)
torus(bronze,.450,.004,.054)
# Low-poly bronze central boss, closed on its base.
lathe(bronze,[(0,.163),(.032,.160),(.066,.146),(.093,.111),(.111,.080),(.115,.074),(.110,.065),(0,.065)],48)
torus(steel,.113,.004,.076,48,6)

# Eight beveled sun rays with intentionally faceted ridges.
for k in range(8):
    a=k/8*TAU+math.pi/8
    local=[(.108,0),(.166,-.026),(.322,0),(.166,.026)]
    def rot(r,t,z):return (r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a),z)
    bottom=[rot(r,t,surface(r)+.002) for r,t in local]
    edge=[rot(r,t,surface(r)+.009) for r,t in local]
    center=rot(.178,0,surface(.178)+.024)
    for i in range(4):
        j=(i+1)%4
        uv=lambda p:(p[0]/.75+.5,.5-p[1]/.75)
        bronze.tri([edge[i],edge[j],center],[uv(edge[i]),uv(edge[j]),uv(center)])
        bronze.quad([bottom[j],bottom[i],edge[i],edge[j]],[(0,1),(.2,1),(.2,0),(0,0)])

# 24 domed rivets, 8 sides, five rings.
for i in range(24):
    a=i/24*TAU
    lathe(bronze,[(0,.012),(.006,.010),(.009,.004),(.009,0),(0,0)],8,(.431*math.cos(a),.431*math.sin(a),.053))

def box(mesh,center,size):
    c=np.array(center);s=np.array(size)/2
    v=[c+s*np.array(p) for p in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:mesh.quad([v[i] for i in f],[(0,1),(1,1),(1,0),(0,0)])
# Rear mounting plates and raised transverse wood grip.
for xx in [-.155,.155]:
    box(steel,(xx,0,-.047),(.048,.13,.022))
    box(steel,(xx,0,-.092),(.022,.038,.09))
box(wood,(0,0,-.133),(.31,.042,.042))

# Export all assets as an embedded, self-contained binary glTF.
binary=bytearray(); views=[]; accessors=[]; images=[]; textures=[]
def append(data,target=None):
    while len(binary)%4:binary.append(0)
    view={'buffer':0,'byteOffset':len(binary),'byteLength':len(data)}
    if target:view['target']=target
    views.append(view);binary.extend(data);return len(views)-1
def accessor(arr,dtype,ctype,kind,bounds=False):
    arr=np.asarray(arr,dtype=dtype); v=append(arr.tobytes(),34963 if kind=='SCALAR' else 34962)
    obj={'bufferView':v,'componentType':ctype,'count':len(arr),'type':kind}
    if bounds:obj.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
    accessors.append(obj);return len(accessors)-1
def texture(file):
    images.append({'name':file,'bufferView':append((TEX/file).read_bytes()),'mimeType':'image/png'})
    textures.append({'sampler':0,'source':len(images)-1});return len(textures)-1
materials=[]
for name,label in [('madera','Madera · roble oscuro'),('acero','Acero · forjado'),('bronce','Bronce · solar')]:
    bc=texture(name+'_BaseColor.png'); mr=texture(name+'_MetallicRoughness.png'); normal=texture(name+'_Normal.png')
    materials.append({'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':bc},'baseColorFactor':[1,1,1,1],'metallicRoughnessTexture':{'index':mr},'metallicFactor':1,'roughnessFactor':1 if name=='madera' else .7},'normalTexture':{'index':normal,'scale':.5 if name=='madera' else .25},'extras':{'descripcion':label}})
gmeshes=[]
for m in meshes:
    # Weld identical attributes; preserve normal/UV seams and tangent handedness.
    table={}; pos=[]; norm=[]; uv=[]; tan=[]; idx=[]
    for p,n,u,t in zip(m.pos,m.norm,m.uv,m.tan):
        key=tuple(round(v,6) for v in p+n+u+t)
        if key not in table:
            table[key]=len(pos);pos.append(p);norm.append(n);uv.append(u);tan.append(t)
        idx.append(table[key])
    m.pos,m.norm,m.uv,m.tan,m.idx=pos,norm,uv,tan,idx
    attributes={'POSITION':accessor(m.pos,'<f4',5126,'VEC3',True),'NORMAL':accessor(m.norm,'<f4',5126,'VEC3'),'TEXCOORD_0':accessor(m.uv,'<f4',5126,'VEC2'),'TANGENT':accessor(m.tan,'<f4',5126,'VEC4')}
    gmeshes.append({'name':m.name,'primitives':[{'attributes':attributes,'indices':accessor(m.idx,'<u2',5123,'SCALAR'),'material':m.material,'mode':4}]})
gltf={'asset':{'version':'2.0','generator':'Escudo Solar / Python procedural original'},'scene':0,'scenes':[{'nodes':[0,1,2]}],'nodes':[{'name':m.name,'mesh':i} for i,m in enumerate(meshes)],'meshes':gmeshes,'materials':materials,'textures':textures,'images':images,'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}],'extras':{'units':'meters','textureResolution':512,'originalAsset':True}}
j=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4)
binary+=b'\x00'*((-len(binary))%4)
glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
(ASSET/'escudo-solar.glb').write_bytes(glb)
allpos=np.vstack([m.pos for m in meshes])
stats={'triangulos':sum(len(m.idx)//3 for m in meshes),'vertices_exportados':sum(len(m.pos) for m in meshes),'materiales':3,'texturas':'512 × 512 px','glb_bytes':len(glb),'dimensiones_m':np.round(allpos.max(axis=0)-allpos.min(axis=0),4).tolist(), 'por_material':{m.name:len(m.idx)//3 for m in meshes}}
(ASSET/'datos-modelo.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf8')
# UV evidence. Faces and mirrored back intentionally share wood UVs.
for mesh,name in zip(meshes,['madera','acero','bronce']):
    im=Image.new('RGB',(N,N),'#111b23');d=ImageDraw.Draw(im)
    for start in range(0,len(mesh.idx),3):
        coords=[(int(mesh.uv[i][0]*N),int(mesh.uv[i][1]*N)) for i in mesh.idx[start:start+3]]
        d.line(coords+[coords[0]],fill='#c9a766',width=1)
    im.save(TEX/f'{name}_UV.png')
print(json.dumps(stats,ensure_ascii=False,indent=2))
