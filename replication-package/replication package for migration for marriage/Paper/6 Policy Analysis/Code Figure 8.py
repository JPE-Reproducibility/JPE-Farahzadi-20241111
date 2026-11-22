
"""Simulate Muslim-population counterfactuals and produce main-text Figure 8."""

import argparse
from pathlib import Path

import pandas as pd
import numpy as np
import numpy.matlib
import matplotlib.pyplot as plt

package_root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--input-dir",
    type=Path,
    default=package_root / "Synthetic Data" / "model_out",
    help="Directory containing dist.dta, phi.dta, and d.dta from Code Table 4.do.",
)
parser.add_argument(
    "--output",
    type=Path,
    default=package_root / "Paper" / "Output" / "Figure 8.png",
    help="Output PNG path (defaults to the model-estimation Results folder).",
)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)


def require_input(filename):
    path = args.input_dir / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}. Run Code Table 4.do first."
        )
    return path

def IPFP(phi,nx,ny,ncat_x,ncat_y,tol,maxiter,dxy,dyx):
    ephi2 = np.exp(phi/2)
    
    bigc = np.sqrt(1/(ncat_x+ncat_y+2*np.sum(ephi2)))
    
    txi = np.repeat(np.asmatrix('1'),ncat_x,axis=0)*bigc
    tyi = np.repeat(np.asmatrix('1'),ncat_x,axis=0)*bigc
    
    err_diff = bigc
    tol_diff = tol*bigc
    niter = 0
    
    while (err_diff > tol_diff) & (niter < maxiter):
    
        Sx = np.sum(np.multiply(ephi2,np.transpose(tyi)) + np.multiply(ephi2,dxy),axis=1)    
        tx = (np.sqrt(np.multiply(Sx,Sx) + 4*np.transpose(nx)) - Sx)/2
        Sy = np.transpose(np.sum(np.multiply(ephi2,tx) + np.multiply(ephi2,dyx),axis=0))
        ty = (np.sqrt(np.multiply(Sy,Sy) + 4*np.transpose(ny)) - Sy)/2
        
        err_x = np.max(np.abs(tx-txi))
        err_y = np.max(np.abs(ty-tyi))
        err_diff = err_x + err_y
        
        txi = tx
        tyi = ty
        niter = niter + 1
        if err_diff <= tol_diff:
            mux0 = np.multiply(txi,txi)
            mu0y = np.multiply(tyi,tyi)

    if err_diff > tol_diff:
        raise RuntimeError(
            f"IPFP failed to converge within {maxiter} iterations "
            f"(final difference {float(err_diff):.3g})."
        )
        
    muxy = np.multiply(ephi2,np.multiply(np.matlib.repmat(txi,1,ncat_y),np.matlib.repmat(np.transpose(tyi),ncat_x,1)))
    lxy = np.divide(
        np.multiply(muxy, dxy),
        np.transpose(tyi),
        out=np.zeros_like(muxy),
        where=np.transpose(tyi) != 0,
    )
    lyx = np.divide(
        np.multiply(muxy, dyx),
        txi,
        out=np.zeros_like(muxy),
        where=txi != 0,
    )
    return [muxy, mux0, mu0y, lxy, lyx]


age = np.array([1,2,3])[np.newaxis]
ethnicity = np.array([0,1,2,3,4])[np.newaxis] 
religion = np.array([0,1])[np.newaxis] 
education = np.array([0,1])[np.newaxis] 

c1 = np.repeat(age,ethnicity.shape[1]*education.shape[1]*religion.shape[1], axis = 1)
c2 = np.matlib.repmat(np.repeat(ethnicity,education.shape[1]*religion.shape[1]), 1, age.shape[1])
c3 = np.matlib.repmat(np.repeat(religion,education.shape[1]), 1, age.shape[1]*ethnicity.shape[1])
c4 = np.matlib.repmat(education, 1, age.shape[1]*ethnicity.shape[1]*religion.shape[1])


ncat_x = c1.shape[1]
ncat_y = c1.shape[1]

xx1 = np.transpose(np.repeat(c1,ncat_y,1))
xx2 = np.transpose(np.repeat(c2,ncat_y,1))
xx3 = np.transpose(np.repeat(c3,ncat_y,1))
xx4 = np.transpose(np.repeat(c4,ncat_y,1))

yy1 = np.matlib.repmat(np.transpose(c1),ncat_x,1)
yy2 = np.matlib.repmat(np.transpose(c2),ncat_x,1)
yy3 = np.matlib.repmat(np.transpose(c3),ncat_x,1)
yy4 = np.matlib.repmat(np.transpose(c4),ncat_x,1)

group_x = xx1*1000 + xx2*100 + xx3*10 + xx4
group_y = yy1*1000 + yy2*100 + yy3*10 + yy4

# distributions
dis = pd.read_stata(require_input("dist.dta"))
nx = np.array(dis.nx)[np.newaxis]
ny = np.array(dis.ny)[np.newaxis]

# phi
df = pd.read_stata(require_input("phi.dta"))
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi']], columns = 'groupy', values = 'phi', index = 'groupx')
phi = phi.to_numpy()


# D
df_d = pd.read_stata(require_input("d.dta"))
df_d = df_d.sort_values(by=['groupx','groupy'])

dxy = pd.pivot(df_d[['groupx','groupy','D_women']], columns = 'groupy', values = 'D_women', index = 'groupx')
dxy = dxy.to_numpy()

dyx = pd.pivot(df_d[['groupx','groupy','D_men']], columns = 'groupy', values = 'D_men', index = 'groupx')
dyx = dyx.to_numpy()

# estimation
tol = 1e-9
maxiter = 2000

[muxy, mux0, mu0y, lxy, lyx] = IPFP(phi,nx,ny,ncat_x,ncat_y,tol,maxiter,dxy,dyx)


df = pd.DataFrame(np.concatenate((group_x,group_y,xx1,xx2,xx3,xx4,yy1,yy2,yy3,yy4), axis = 1), columns = ['groupx','groupy','ax','ex','rx','sx','ay','ey','ry','sy'])
df = df.sort_values(by=['groupx','groupy'])
df['muxy']= muxy.reshape(ncat_x*ncat_y,1)
df['lxy']= lxy.reshape(ncat_x*ncat_y,1)
df['lyx']= lyx.reshape(ncat_x*ncat_y,1)
df['mux0'] = np.matlib.repmat(np.transpose(mu0y),ncat_x,1).reshape(ncat_x*ncat_y,1)
df['mu0y'] = np.repeat(mux0,ncat_y,1).reshape(ncat_x*ncat_y,1)


df['muxy_intereth'] = df.muxy
df.loc[df.ex == df.ey, 'muxy_intereth'] = 0
df['muxy_interrel'] = df.muxy
df.loc[df.rx == df.ry, 'muxy_interrel'] = 0
df['muxy_interedu'] = df.muxy
df.loc[df.sx == df.sy, 'muxy_interedu'] = 0

df['lxy_intereth'] = df.lxy
df.loc[df.ex == df.ey, 'lxy_intereth'] = 0
df['lxy_interrel'] = df.lxy
df.loc[df.rx == df.ry, 'lxy_interrel'] = 0
df['lxy_interedu'] = df.lxy
df.loc[df.sx == df.sy, 'lxy_interedu'] = 0

df['lyx_intereth'] = df.lyx
df.loc[df.ex == df.ey, 'lyx_intereth'] = 0
df['lyx_interrel'] = df.lyx
df.loc[df.rx == df.ry, 'lyx_interrel'] = 0
df['lyx_interedu'] = df.lyx
df.loc[df.sx == df.sy, 'lyx_interedu'] = 0

group = c1*1000 + c2*100 + c3*10 + c4
df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
df_m = df_m.set_index('group')
df_m['mx'] = df.groupby('groupx')['muxy'].sum()
df_m['my'] = df.groupby('groupy')['muxy'].sum()
df_m['lx'] = df.groupby('groupx')['lxy'].sum()
df_m['ly'] = df.groupby('groupy')['lyx'].sum()
df_m['nx'] = np.transpose(nx)
df_m['ny'] = np.transpose(ny)

inter_eth_f0 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m0 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_eth_m_f0 = df[df.rx == 1].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 1].groupby('ex')['muxy'].sum()+df[df.rx == 1].groupby('ex')['lxy'].sum())
inter_eth_m_m0 = df[df.ry == 1].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 1].groupby('ey')['muxy'].sum()+df[df.ry == 1].groupby('ey')['lyx'].sum())

inter_eth_n_f0 = df[df.rx == 0].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 0].groupby('ex')['muxy'].sum()+df[df.rx == 0].groupby('ex')['lxy'].sum())
inter_eth_n_m0 = df[df.ry == 0].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 0].groupby('ey')['muxy'].sum()+df[df.ry == 0].groupby('ey')['lyx'].sum())


inter_rel_f0 = (df[df.ex != 0].groupby('rx')['muxy_interrel'].sum()+df[df.ex != 0].groupby('rx')['lxy_interrel'].sum())/(df[df.ex != 0].groupby('rx')['muxy'].sum()+df[df.ex != 0].groupby('rx')['lxy'].sum())
inter_rel_m0 = (df[df.ey != 0].groupby('ry')['muxy_interrel'].sum()+df[df.ey != 0].groupby('ry')['lyx_interrel'].sum())/(df[df.ey != 0].groupby('ry')['muxy'].sum()+df[df.ey != 0].groupby('ry')['lyx'].sum())

mig_eth_f0 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m0 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f0 = df_m[df_m.e != 0].groupby('r')['lx'].sum()/(df_m[df_m.e != 0].groupby('r')['mx'].sum()+df_m[df_m.e != 0].groupby('r')['lx'].sum())
mig_rel_m0 = df_m[df_m.e != 0].groupby('r')['ly'].sum()/(df_m[df_m.e != 0].groupby('r')['my'].sum()+df_m[df_m.e != 0].groupby('r')['ly'].sum())

mig_er_f0 = df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['mx'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum())
mig_er_m0 = df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['my'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum())

inter_edu0 = ((df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_eth0 = ((df[df['ex'] != 0].groupby('rx')['muxy_intereth'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_intereth'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_intereth'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_intereth'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_rel0 = (inter_rel_f0+inter_rel_m0)/2
single0 = (df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2

#### counterfactual: increase in Muslim population


dis2 = dis.copy()
dis2['muslim'] = (dis['group'] - (dis['group']//100)*100)//10

changes = np.linspace(1, 3, 201)
mig_rel = np.empty((len(changes),2))
inter_rel = np.empty((len(changes),2))
inter_eth = np.empty((len(changes),2))
inter_edu = np.empty((len(changes),2))
single_rel = np.empty((len(changes),2))

for i, c in enumerate(changes):
    
    dis2 = dis.copy()
    dis2['muslim'] = (dis['group'] - (dis['group']//100)*100)//10
    
    dis2['nx'] = dis2['nx'] + dis2['nx']*(changes[i]-1)*dis2['muslim']
    dis2['ny'] = dis2['ny'] + dis2['ny']*(changes[i]-1)*dis2['muslim']
    
    nx = np.array(dis2.nx)[np.newaxis]
    ny = np.array(dis2.ny)[np.newaxis]

    [muxy, mux0, mu0y, lxy, lyx] = IPFP(phi,nx,ny,ncat_x,ncat_y,tol,maxiter,dxy,dyx)
    df = pd.DataFrame(np.concatenate((group_x,group_y,xx1,xx2,xx3,xx4,yy1,yy2,yy3,yy4), axis = 1), columns = ['groupx','groupy','ax','ex','rx','sx','ay','ey','ry','sy'])
    df = df.sort_values(by=['groupx','groupy'])
    df['muxy']= muxy.reshape(ncat_x*ncat_y,1)
    df['lxy']= lxy.reshape(ncat_x*ncat_y,1)
    df['lyx']= lyx.reshape(ncat_x*ncat_y,1)
            
    df['muxy_intereth'] = df.muxy
    df.loc[df.ex == df.ey, 'muxy_intereth'] = 0
    df['muxy_interrel'] = df.muxy
    df.loc[df.rx == df.ry, 'muxy_interrel'] = 0
    df['muxy_interedu'] = df.muxy
    df.loc[df.sx == df.sy, 'muxy_interedu'] = 0
    
    df['lxy_intereth'] = df.lxy
    df.loc[df.ex == df.ey, 'lxy_intereth'] = 0
    df['lxy_interrel'] = df.lxy
    df.loc[df.rx == df.ry, 'lxy_interrel'] = 0
    df['lxy_interedu'] = df.lxy
    df.loc[df.sx == df.sy, 'lxy_interedu'] = 0
    
    df['lyx_intereth'] = df.lyx
    df.loc[df.ex == df.ey, 'lyx_intereth'] = 0
    df['lyx_interrel'] = df.lyx
    df.loc[df.rx == df.ry, 'lyx_interrel'] = 0
    df['lyx_interedu'] = df.lyx
    df.loc[df.sx == df.sy, 'lyx_interedu'] = 0

    inter_eth_f = df[df['ex'] != 0].groupby('rx')['muxy_intereth'].sum()/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())
    inter_eth_m = df[df['ey'] != 0].groupby('ry')['muxy_intereth'].sum()/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum())
    
    inter_rel_f = (df[df['ex'] != 0].groupby('rx')['muxy_interrel'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interrel'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())
    inter_rel_m = (df[df['ey'] != 0].groupby('ry')['muxy_interrel'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interrel'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum())
    
    inter_edu_f = (df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())
    inter_edu_m = (df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum())
    
    single_rel_f = df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum()
    single_rel_m = df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum()

    inter_rel[i,] = (inter_rel_f + inter_rel_m)/2*100
    inter_eth[i,] = (inter_eth_f + inter_eth_m)/2*100
    inter_edu[i,] = (inter_edu_f + inter_edu_m)/2*100
    single_rel[i,] = (single_rel_f + single_rel_m)/2*100
    
    group = c1*1000 + c2*100 + c3*10 + c4
    df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
    df_m = df_m.set_index('group')
    df_m['mx'] = df.groupby('groupx')['muxy'].sum()
    df_m['my'] = df.groupby('groupy')['muxy'].sum()
    df_m['lx'] = df.groupby('groupx')['lxy'].sum()
    df_m['ly'] = df.groupby('groupy')['lyx'].sum()
    df_m['nx'] = np.transpose(nx)
    df_m['ny'] = np.transpose(ny)
    mig_rel_f = df_m[df_m['e'] != 0].groupby('r')['lx'].sum()/(df_m[df_m['e'] != 0].groupby('r')['mx'].sum()+df_m[df_m['e'] != 0].groupby('r')['lx'].sum())
    mig_rel_m = df_m[df_m['e'] != 0].groupby('r')['ly'].sum()/(df_m[df_m['e'] != 0].groupby('r')['my'].sum()+df_m[df_m['e'] != 0].groupby('r')['ly'].sum())
    mig_rel[i,] = (mig_rel_f + mig_rel_m)/2*100
    
plt.figure(figsize=(6.4,5.7))
ax1 = plt.subplot2grid(shape=(3,8), loc=(0,0), colspan=4)
y1 = np.array([i[0] for i in mig_rel])
y2 = np.array([i[1] for i in mig_rel])
ax1.plot(changes, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax1.plot(changes, y2, color = "darkblue", label = "Muslim")
ax1.set_ylabel("marriage migration (%)", fontsize=7)
ax1.set_xlabel("relative size of Muslim population \n (x baseline)", fontsize=7)
ax1.tick_params(axis='x',labelsize=6)
ax1.tick_params(axis='y',labelsize=6)

ax2 = plt.subplot2grid(shape=(3,8), loc=(0,4), colspan=4)
y1 = np.array([i[0] for i in inter_rel])
y2 = np.array([i[1] for i in inter_rel])
ax2.plot(changes, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax2.plot(changes, y2, color = "darkblue", label = "Muslim")
ax2.set_ylabel("inter-religious marriage (%)", fontsize=7)
ax2.set_xlabel("relative size of Muslim population \n (x baseline)", fontsize=7)
ax2.tick_params(axis='x',labelsize=6)
ax2.tick_params(axis='y',labelsize=6)


plt.figlegend(['Non-Muslim','Muslim'], ncol = 2, fontsize=8, loc='upper center',borderaxespad=1.5,edgecolor='k')
plt.subplots_adjust(wspace=2, hspace=0.38)
plt.savefig(args.output, bbox_inches = 'tight', dpi = 300)
print(f"Figure 8 saved to {args.output}")