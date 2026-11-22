import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Calculate counterfactual outcomes from model files.")
parser.add_argument("--model-dir", type=Path, required=True, help="Existing directory containing model inputs; outputs are written here.")
model_dir = parser.parse_args().model_dir
if not model_dir.is_dir():
    raise FileNotFoundError(f"Model directory does not exist: {model_dir}")


# Full model

import pandas as pd
import numpy as np
import numpy.matlib
import math
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline 

def IPFP(phi,nx,ny,ncat_x,ncat_y,tol,maxiter,dxy,dyx):
    ephi2 = np.exp(phi/2)
    
    bigc = np.sqrt(1/(ncat_x+ncat_y+2*np.sum(ephi2)))
    
    txi = np.repeat(np.mat('1'),ncat_x,axis=0)*bigc
    tyi = np.repeat(np.mat('1'),ncat_x,axis=0)*bigc
    
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
        if niter >= maxiter:
            print('did not converge')
        elif err_diff <= tol_diff:
            mux0 = np.multiply(txi,txi)
            mu0y = np.multiply(tyi,tyi)
        
    muxy = np.multiply(ephi2,np.multiply(np.matlib.repmat(txi,1,ncat_y),np.matlib.repmat(np.transpose(tyi),ncat_x,1)))
    lxy = np.divide(np.multiply(muxy,dxy),np.transpose(tyi))
    lyx = np.divide(np.multiply(muxy,dyx),txi)
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
dis = pd.read_stata(model_dir / 'dist.dta')
nx = np.array(dis.nx)[np.newaxis]
ny = np.array(dis.ny)[np.newaxis]

# phi
df = pd.read_stata(model_dir / 'phi.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi']], columns = 'groupy', values = 'phi', index = 'groupx')
phi = phi.to_numpy()


# D
df_d = pd.read_stata(model_dir / 'd.dta')
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

df['Ux_1'] = np.log(df.muxy/df.mux0)
df.loc[df.muxy == 0, 'Ux_1'] = 0
df['Ux_2'] = np.log(df.lxy/df.mux0)
df.loc[df.lxy == 0, 'Ux_2'] = 0
df['Ux'] = df.muxy*df.Ux_1 + df.lxy*df.Ux_2

df['Uy_1'] = np.log(df.muxy/df.mu0y)
df.loc[df.muxy == 0, 'Uy_1'] = 0
df['Uy_2'] = np.log(df.lyx/df.mu0y)
df.loc[df.lyx == 0, 'Uy_2'] = 0
df['Uy'] = df.muxy*df.Uy_1 + df.lyx*df.Uy_2

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

utility0 = (df.groupby('rx')['Ux'].sum()/df_m.groupby('r')['nx'].sum() + df.groupby('ry')['Uy'].sum()/df_m.groupby('r')['ny'].sum())/2
utilitys0 = (df.groupby(['sx','rx'])['Ux'].sum()/df_m.groupby(['s','r'])['nx'].sum() + df.groupby(['sy','ry'])['Uy'].sum()/df_m.groupby(['s','r'])['ny'].sum())/2


df_m['px'] = np.log(df_m['mx']/df_m['lx'])
df_m['py'] = np.log(df_m['mx']/df_m['ly'])

df_m.reset_index(inplace = True)
price_f0 = df_m[(df_m['e'] != 0) & (df_m['px'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['px'], weights = x['nx']))
price_m0 = df_m[(df_m['e'] != 0) & (df_m['py'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['py'], weights = x['ny']))

#### counterfactual 1: no ethnic preferences

# phi
df = pd.read_stata(model_dir / 'phi_e.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi_e']], columns = 'groupy', values = 'phi_e', index = 'groupx')
phi = phi.to_numpy()

# estimation
tol = 1e-9
maxiter = 2000

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

group = c1*1000 + c2*100 + c3*10 + c4
df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
df_m = df_m.set_index('group')
df_m['mx'] = df.groupby('groupx')['muxy'].sum()
df_m['my'] = df.groupby('groupy')['muxy'].sum()
df_m['lx'] = df.groupby('groupx')['lxy'].sum()
df_m['ly'] = df.groupby('groupy')['lyx'].sum()
df_m['nx'] = np.transpose(nx)
df_m['ny'] = np.transpose(ny)

inter_eth_f1 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m1 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_eth_m_f1 = df[df.rx == 1].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 1].groupby('ex')['muxy'].sum()+df[df.rx == 1].groupby('ex')['lxy'].sum())
inter_eth_m_m1 = df[df.ry == 1].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 1].groupby('ey')['muxy'].sum()+df[df.ry == 1].groupby('ey')['lyx'].sum())

inter_eth_n_f1 = df[df.rx == 0].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 0].groupby('ex')['muxy'].sum()+df[df.rx == 0].groupby('ex')['lxy'].sum())
inter_eth_n_m1 = df[df.ry == 0].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 0].groupby('ey')['muxy'].sum()+df[df.ry == 0].groupby('ey')['lyx'].sum())


inter_rel_f1 = (df[df.ex != 0].groupby('rx')['muxy_interrel'].sum()+df[df.ex != 0].groupby('rx')['lxy_interrel'].sum())/(df[df.ex != 0].groupby('rx')['muxy'].sum()+df[df.ex != 0].groupby('rx')['lxy'].sum())
inter_rel_m1 = (df[df.ey != 0].groupby('ry')['muxy_interrel'].sum()+df[df.ey != 0].groupby('ry')['lyx_interrel'].sum())/(df[df.ey != 0].groupby('ry')['muxy'].sum()+df[df.ey != 0].groupby('ry')['lyx'].sum())

mig_eth_f1 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m1 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f1 = df_m[df_m.e != 0].groupby('r')['lx'].sum()/(df_m[df_m.e != 0].groupby('r')['mx'].sum()+df_m[df_m.e != 0].groupby('r')['lx'].sum())
mig_rel_m1 = df_m[df_m.e != 0].groupby('r')['ly'].sum()/(df_m[df_m.e != 0].groupby('r')['my'].sum()+df_m[df_m.e != 0].groupby('r')['ly'].sum())

mig_er_f1 = df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['mx'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum())
mig_er_m1 = df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['my'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum())

inter_edu1 = ((df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_eth1 = (inter_eth_f1+inter_eth_m1)/2
inter_rel1 = (inter_rel_f1+inter_rel_m1)/2
single1 = (df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2

df_m['px'] = np.log(df_m['mx']/df_m['lx'])
df_m['py'] = np.log(df_m['mx']/df_m['ly'])

df_m.reset_index(inplace = True)
price_f1 = df_m[(df_m['e'] != 0) & (df_m['px'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['px'], weights = x['nx']))
price_m1 = df_m[(df_m['e'] != 0) & (df_m['py'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['py'], weights = x['ny']))

#### counterfactual 2: no religious preferences

# phi
df = pd.read_stata(model_dir / 'phi_r.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi_r']], columns = 'groupy', values = 'phi_r', index = 'groupx')
phi = phi.to_numpy()

# estimation
tol = 1e-9
maxiter = 2000

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

group = c1*1000 + c2*100 + c3*10 + c4
df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
df_m = df_m.set_index('group')
df_m['mx'] = df.groupby('groupx')['muxy'].sum()
df_m['my'] = df.groupby('groupy')['muxy'].sum()
df_m['lx'] = df.groupby('groupx')['lxy'].sum()
df_m['ly'] = df.groupby('groupy')['lyx'].sum()
df_m['nx'] = -np.transpose(nx)
df_m['ny'] = -np.transpose(ny)

inter_eth_f2 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m2 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_eth_m_f2 = df[df.rx == 1].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 1].groupby('ex')['muxy'].sum()+df[df.rx == 1].groupby('ex')['lxy'].sum())
inter_eth_m_m2 = df[df.ry == 1].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 1].groupby('ey')['muxy'].sum()+df[df.ry == 1].groupby('ey')['lyx'].sum())

inter_eth_n_f2 = df[df.rx == 0].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 0].groupby('ex')['muxy'].sum()+df[df.rx == 0].groupby('ex')['lxy'].sum())
inter_eth_n_m2 = df[df.ry == 0].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 0].groupby('ey')['muxy'].sum()+df[df.ry == 0].groupby('ey')['lyx'].sum())


inter_rel_f2 = (df[df.ex != 0].groupby('rx')['muxy_interrel'].sum()+df[df.ex != 0].groupby('rx')['lxy_interrel'].sum())/(df[df.ex != 0].groupby('rx')['muxy'].sum()+df[df.ex != 0].groupby('rx')['lxy'].sum())
inter_rel_m2 = (df[df.ey != 0].groupby('ry')['muxy_interrel'].sum()+df[df.ey != 0].groupby('ry')['lyx_interrel'].sum())/(df[df.ey != 0].groupby('ry')['muxy'].sum()+df[df.ey != 0].groupby('ry')['lyx'].sum())

mig_eth_f2 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m2 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f2 = df_m[df_m.e != 0].groupby('r')['lx'].sum()/(df_m[df_m.e != 0].groupby('r')['mx'].sum()+df_m[df_m.e != 0].groupby('r')['lx'].sum())
mig_rel_m2 = df_m[df_m.e != 0].groupby('r')['ly'].sum()/(df_m[df_m.e != 0].groupby('r')['my'].sum()+df_m[df_m.e != 0].groupby('r')['ly'].sum())

mig_er_f2 = df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['mx'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum())
mig_er_m2 = df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['my'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum())

inter_edu2 = ((df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_eth2 = (inter_eth_f2+inter_eth_m2)/2
inter_rel2 = (inter_rel_f2+inter_rel_m2)/2
single2 = (df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2

df_m['px'] = np.log(df_m['mx']/df_m['lx'])
df_m['py'] = np.log(df_m['mx']/df_m['ly'])

df_m.reset_index(inplace = True)
price_f2 = df_m[(df_m['e'] != 0) & (df_m['px'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['px'], weights = x['nx']))
price_m2 = df_m[(df_m['e'] != 0) & (df_m['py'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['py'], weights = x['ny']))

#### counterfactual 3: no ethnic or religious preferences

# phi
df = pd.read_stata(model_dir / 'phi_er.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi_er']], columns = 'groupy', values = 'phi_er', index = 'groupx')
phi = phi.to_numpy()

# estimation
tol = 1e-9
maxiter = 2000
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

group = c1*1000 + c2*100 + c3*10 + c4
df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
df_m = df_m.set_index('group')
df_m['mx'] = df.groupby('groupx')['muxy'].sum()
df_m['my'] = df.groupby('groupy')['muxy'].sum()
df_m['lx'] = df.groupby('groupx')['lxy'].sum()
df_m['ly'] = df.groupby('groupy')['lyx'].sum()
df_m['nx'] = np.transpose(nx)
df_m['ny'] = np.transpose(ny)

inter_eth_f3 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m3 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_eth_m_f3 = df[df.rx == 1].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 1].groupby('ex')['muxy'].sum()+df[df.rx == 1].groupby('ex')['lxy'].sum())
inter_eth_m_m3 = df[df.ry == 1].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 1].groupby('ey')['muxy'].sum()+df[df.ry == 1].groupby('ey')['lyx'].sum())

inter_eth_n_f3 = df[df.rx == 0].groupby('ex')['muxy_intereth'].sum()/(df[df.rx == 0].groupby('ex')['muxy'].sum()+df[df.rx == 0].groupby('ex')['lxy'].sum())
inter_eth_n_m3 = df[df.ry == 0].groupby('ey')['muxy_intereth'].sum()/(df[df.ry == 0].groupby('ey')['muxy'].sum()+df[df.ry == 0].groupby('ey')['lyx'].sum())


inter_rel_f3 = (df[df.ex != 0].groupby('rx')['muxy_interrel'].sum()+df[df.ex != 0].groupby('rx')['lxy_interrel'].sum())/(df[df.ex != 0].groupby('rx')['muxy'].sum()+df[df.ex != 0].groupby('rx')['lxy'].sum())
inter_rel_m3 = (df[df.ey != 0].groupby('ry')['muxy_interrel'].sum()+df[df.ey != 0].groupby('ry')['lyx_interrel'].sum())/(df[df.ey != 0].groupby('ry')['muxy'].sum()+df[df.ey != 0].groupby('ry')['lyx'].sum())

mig_eth_f3 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m3 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f3 = df_m[df_m.e != 0].groupby('r')['lx'].sum()/(df_m[df_m.e != 0].groupby('r')['mx'].sum()+df_m[df_m.e != 0].groupby('r')['lx'].sum())
mig_rel_m3 = df_m[df_m.e != 0].groupby('r')['ly'].sum()/(df_m[df_m.e != 0].groupby('r')['my'].sum()+df_m[df_m.e != 0].groupby('r')['ly'].sum())

mig_er_f3 = df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['mx'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['lx'].sum())
mig_er_m3 = df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum()/(df_m[df_m.e != 0].groupby(['r','e'])['my'].sum()+df_m[df_m.e != 0].groupby(['r','e'])['ly'].sum())

inter_edu3 = ((df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_eth3 = (inter_eth_f3+inter_eth_m3)/2
inter_rel3 = (inter_rel_f3+inter_rel_m3)/2
single3 = (df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2

df_m['px'] = np.log(df_m['mx']/df_m['lx'])
df_m['py'] = np.log(df_m['mx']/df_m['ly'])

df_m.reset_index(inplace = True)
price_f3 = df_m[(df_m['e'] != 0) & (df_m['px'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['px'], weights = x['nx']))
price_m3 = df_m[(df_m['e'] != 0) & (df_m['py'] != np.Inf)].groupby(['r','e']).apply(lambda x: np.average(x['py'], weights = x['ny']))

migration_counter = pd.concat([(mig_rel_f0 + mig_rel_m0)/2, (mig_rel_f1 + mig_rel_m1)/2, (mig_rel_f2 + mig_rel_m2)/2,  (mig_rel_f3 + mig_rel_m3)/2], axis = 1)
migration_counter_m = pd.concat([mig_rel_m0, mig_rel_m1, mig_rel_m2, mig_rel_m3], axis = 1)
migration_counter_f = pd.concat([mig_rel_f0, mig_rel_f1, mig_rel_f2, mig_rel_f3], axis = 1)

migration_er_counter = pd.concat([(mig_er_f0 + mig_er_m0)/2, (mig_er_f1 + mig_er_m1)/2, (mig_er_f2 + mig_er_m2)/2,  (mig_er_f3 + mig_er_m3)/2], axis = 1)

interrelig_counter = pd.concat([(inter_rel_f0 + inter_rel_m0)/2, (inter_rel_f1 + inter_rel_f1)/2, (inter_rel_f2 + inter_rel_f2)/2,  (inter_rel_f3 + inter_rel_f3)/2], axis = 1)
interrethnic_counter = pd.concat([(inter_eth_f0 + inter_eth_m0)/2, (inter_eth_f1 + inter_eth_m1)/2, (inter_eth_f2 + inter_eth_m2)/2,  (inter_eth_f3 + inter_eth_m3)/2], axis = 1)
interrethnic_m_counter = pd.concat([(inter_eth_m_f0 + inter_eth_m_m0)/2, (inter_eth_m_f1 + inter_eth_m_m1)/2, (inter_eth_m_f2 + inter_eth_m_m2)/2,  (inter_eth_m_f3 + inter_eth_m_m3)/2], axis = 1)
interrethnic_n_counter = pd.concat([(inter_eth_n_f0 + inter_eth_n_m0)/2, (inter_eth_n_f1 + inter_eth_n_m1)/2, (inter_eth_n_f2 + inter_eth_n_m2)/2,  (inter_eth_n_f3 + inter_eth_n_m3)/2], axis = 1)
price_counter = pd.concat([(price_f0 + price_m0)/2, (price_f1 + price_m1)/2, (price_f2 + price_m2)/2,  (price_f3 + price_m3)/2], axis = 1)

#### counterfactual 4: original preferences, no possibility of migration

# phi
df = pd.read_stata(model_dir / 'phi.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi']], columns = 'groupy', values = 'phi', index = 'groupx')
phi = phi.to_numpy()

dxy = np.array([[0]*60]*60)
dyx = np.array([[0]*60]*60)

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

df['Ux_1'] = np.log(df.muxy/df.mux0)
df.loc[df.muxy == 0, 'Ux_1'] = 0
df['Ux_2'] = np.log(df.lxy/df.mux0)
df.loc[df.lxy == 0, 'Ux_2'] = 0
df['Ux'] = df.muxy*df.Ux_1 + df.lxy*df.Ux_2

df['Uy_1'] = np.log(df.muxy/df.mu0y)
df.loc[df.muxy == 0, 'Uy_1'] = 0
df['Uy_2'] = np.log(df.lyx/df.mu0y)
df.loc[df.lyx == 0, 'Uy_2'] = 0
df['Uy'] = df.muxy*df.Uy_1 + df.lyx*df.Uy_2


inter_eth_f4 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m4 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_rel_f4 = (df.groupby('rx')['muxy_interrel'].sum()+df.groupby('rx')['lxy_interrel'].sum())/(df.groupby('rx')['muxy'].sum()+df.groupby('rx')['lxy'].sum())
inter_rel_m4 = (df.groupby('ry')['muxy_interrel'].sum()+df.groupby('ry')['lyx_interrel'].sum())/(df.groupby('ry')['muxy'].sum()+df.groupby('ry')['lyx'].sum())

inter_edu_f4 = (df.groupby('sx')['muxy_interedu'].sum()+df.groupby('sx')['lxy_interedu'].sum())/(df.groupby('sx')['muxy'].sum()+df.groupby('sx')['lxy'].sum())
inter_edu_m4 = (df.groupby('sy')['muxy_interedu'].sum()+df.groupby('sy')['lyx_interedu'].sum())/(df.groupby('sy')['muxy'].sum()+df.groupby('sy')['lyx'].sum())

mig_eth_f4 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m4 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f4 = df_m.groupby('r')['lx'].sum()/(df_m.groupby('r')['mx'].sum()+df_m.groupby('r')['lx'].sum())
mig_rel_m4 = df_m.groupby('r')['ly'].sum()/(df_m.groupby('r')['my'].sum()+df_m.groupby('r')['ly'].sum())

single_rel_f4 = df_m.groupby('r')['mux0'].sum()/df_m.groupby('r')['nx'].sum()
single_rel_m4 = df_m.groupby('r')['mu0y'].sum()/df_m.groupby('r')['ny'].sum()

mig_rel_m = pd.DataFrame({'model': mig_rel_m0,'no eth': mig_rel_m1,'no rel': mig_rel_m2, 'no eth-rel': mig_rel_m3})
mig_rel_f = pd.DataFrame({'model': mig_rel_f0,'no eth': mig_rel_f1,'no rel': mig_rel_f2, 'no eth-rel': mig_rel_f3})

mig_er_m = pd.DataFrame({'model': mig_er_m0,'no eth': mig_er_m1,'no rel': mig_er_m2, 'no eth-rel': mig_er_m3})
mig_er_f = pd.DataFrame({'model': mig_er_f0,'no eth': mig_er_f1,'no rel': mig_er_f2, 'no eth-rel': mig_er_f3})

inter_edu4 = ((df[df['ex'] != 0].groupby('rx')['muxy_interedu'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interedu'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interedu'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interedu'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_eth4 = ((df[df['ex'] != 0].groupby('rx')['muxy_intereth'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_intereth'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_intereth'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_intereth'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
inter_rel4 = ((df[df['ex'] != 0].groupby('rx')['muxy_interrel'].sum()+df[df['ex'] != 0].groupby('rx')['lxy_interrel'].sum())/(df[df['ex'] != 0].groupby('rx')['muxy'].sum()+df[df['ex'] != 0].groupby('rx')['lxy'].sum())+(df[df['ey'] != 0].groupby('ry')['muxy_interrel'].sum()+df[df['ey'] != 0].groupby('ry')['lyx_interrel'].sum())/(df[df['ey'] != 0].groupby('ry')['muxy'].sum()+df[df['ey'] != 0].groupby('ry')['lyx'].sum()))/2
single4 = (df_m[df_m['e'] != 0].groupby('r')['mux0'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df_m[df_m['e'] != 0].groupby('r')['mu0y'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2

utility4 = (df.groupby('rx')['Ux'].sum()/df_m.groupby('r')['nx'].sum() + df.groupby('ry')['Uy'].sum()/df_m.groupby('r')['ny'].sum())/2
utilitys4 = (df.groupby(['sx','rx'])['Ux'].sum()/df_m.groupby(['s','r'])['nx'].sum() + df.groupby(['sy','ry'])['Uy'].sum()/df_m.groupby(['s','r'])['ny'].sum())/2

utility4 = (df[df['ex'] != 0].groupby('rx')['Ux'].sum()/df_m[df_m['e'] != 0].groupby('r')['nx'].sum() + df[df['ey'] != 0].groupby('ry')['Uy'].sum()/df_m[df_m['e'] != 0].groupby('r')['ny'].sum())/2
utilitys4 = (df[df['ex'] != 0].groupby(['sx','rx'])['Ux'].sum()/df_m[df_m['e'] != 0].groupby(['s','r'])['nx'].sum() + df[df['ey'] != 0].groupby(['sy','ry'])['Uy'].sum()/df_m[df_m['e'] != 0].groupby(['s','r'])['ny'].sum())/2

pd.concat([inter_edu0,inter_edu4],axis=1)
pd.concat([inter_eth0,inter_eth4],axis=1)
pd.concat([inter_rel0,inter_rel4],axis=1)
pd.concat([single0,single4],axis=1)
pd.concat([utility0,utility4],axis=1)
pd.concat([utilitys0,utilitys4],axis=1)

df.to_csv(model_dir / 'counter_data.csv')

#### counterfactual 5: no ethnic or religious preferences, no possibility of migration

# phi
df = pd.read_stata(model_dir / 'phi_er.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi_er']], columns = 'groupy', values = 'phi_er', index = 'groupx')
phi = phi.to_numpy()

dxy = np.array([[0]*60]*60)
dyx = np.array([[0]*60]*60)

# estimation
tol = 1e-9
maxiter = 2000

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

group = c1*1000 + c2*100 + c3*10 + c4
df_m = pd.DataFrame(np.concatenate((np.transpose(group),np.transpose(c1),np.transpose(c2),np.transpose(c3),np.transpose(c4),mux0,mu0y), axis = 1), columns = ['group','a','e','r','s','mux0','mu0y'])
df_m = df_m.set_index('group')
df_m['mx'] = df.groupby('groupx')['muxy'].sum()
df_m['my'] = df.groupby('groupy')['muxy'].sum()
df_m['lx'] = df.groupby('groupx')['lxy'].sum()
df_m['ly'] = df.groupby('groupy')['lyx'].sum()
df_m['nx'] = np.transpose(nx)
df_m['ny'] = np.transpose(ny)

inter_eth_f5 = df.groupby('ex')['muxy_intereth'].sum()/(df.groupby('ex')['muxy'].sum()+df.groupby('ex')['lxy'].sum())
inter_eth_m5 = df.groupby('ey')['muxy_intereth'].sum()/(df.groupby('ey')['muxy'].sum()+df.groupby('ey')['lyx'].sum())

inter_rel_f5 = (df.groupby('rx')['muxy_interrel'].sum()+df.groupby('rx')['lxy_interrel'].sum())/(df.groupby('rx')['muxy'].sum()+df.groupby('rx')['lxy'].sum())
inter_rel_m5 = (df.groupby('ry')['muxy_interrel'].sum()+df.groupby('ry')['lyx_interrel'].sum())/(df.groupby('ry')['muxy'].sum()+df.groupby('ry')['lyx'].sum())

inter_edu_f5 = (df.groupby('sx')['muxy_interedu'].sum()+df.groupby('sx')['lxy_interedu'].sum())/(df.groupby('sx')['muxy'].sum()+df.groupby('sx')['lxy'].sum())
inter_edu_m5 = (df.groupby('sy')['muxy_interedu'].sum()+df.groupby('sy')['lyx_interedu'].sum())/(df.groupby('sy')['muxy'].sum()+df.groupby('sy')['lyx'].sum())

mig_eth_f5 = df_m.groupby('e')['lx'].sum()/(df_m.groupby('e')['mx'].sum()+df_m.groupby('e')['lx'].sum())
mig_eth_m5 = df_m.groupby('e')['ly'].sum()/(df_m.groupby('e')['my'].sum()+df_m.groupby('e')['ly'].sum())

mig_rel_f5 = df_m.groupby('r')['lx'].sum()/(df_m.groupby('r')['mx'].sum()+df_m.groupby('r')['lx'].sum())
mig_rel_m5 = df_m.groupby('r')['ly'].sum()/(df_m.groupby('r')['my'].sum()+df_m.groupby('r')['ly'].sum())

single_rel_f5 = df_m.groupby('r')['mux0'].sum()/df_m.groupby('r')['nx'].sum()
single_rel_m5 = df_m.groupby('r')['mu0y'].sum()/df_m.groupby('r')['ny'].sum()

#### counterfactual 6: original preferences, increase in costs

# phi
df = pd.read_stata(model_dir / 'phi.dta')
df = df.sort_values(by=['groupx','groupy'])
phi = pd.pivot(df[['groupx','groupy','phi']], columns = 'groupy', values = 'phi', index = 'groupx')
phi = phi.to_numpy()

# D
df_d = pd.read_stata(model_dir / 'd.dta')
df_d = df_d.sort_values(by=['groupx','groupy'])

tax = np.arange(1,25,.1)
mig_rel = np.empty((len(tax),2))
inter_rel = np.empty((len(tax),2))
inter_eth = np.empty((len(tax),2))
inter_edu = np.empty((len(tax),2))
single_rel = np.empty((len(tax),2))

for i, c in enumerate(tax):

    dxy = pd.pivot(df_d[['groupx','groupy','D_women']], columns = 'groupy', values = 'D_women', index = 'groupx')
    dxy = dxy.to_numpy()
    dyx = pd.pivot(df_d[['groupx','groupy','D_men']], columns = 'groupy', values = 'D_men', index = 'groupx')
    dyx = dyx.to_numpy()
    
    dxy = np.divide(dxy,tax[i])
    dyx = np.divide(dyx,tax[i])
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


plt.figure(figsize=(6.4,5.4))
ax1 = plt.subplot2grid(shape=(3,8), loc=(0,0), colspan=4)
y1 = np.array([i[0] for i in mig_rel])
y2 = np.array([i[1] for i in mig_rel])
ax1.plot(tax, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax1.plot(tax, y2, color = "darkblue", label = "Muslim")
ax1.set_ylabel("marriage migration (%)", fontsize=7)
ax1.tick_params(axis='x',labelsize=6)
ax1.tick_params(axis='y',labelsize=6)

ax2 = plt.subplot2grid(shape=(3,8), loc=(0,4), colspan=4)
y1 = np.array([i[0] for i in inter_rel])
y2 = np.array([i[1] for i in inter_rel])
ax2.plot(tax, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax2.plot(tax, y2, color = "darkblue", label = "Muslim")
ax2.set_ylabel("inter-religious marriage (%)", fontsize=7)
ax2.tick_params(axis='x',labelsize=6)
ax2.tick_params(axis='y',labelsize=6)

ax3 = plt.subplot2grid(shape=(3,8), loc=(1,0), colspan=4)
y1 = np.array([i[0] for i in inter_eth])
y2 = np.array([i[1] for i in inter_eth])
ax3.plot(tax, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax3.plot(tax, y2, color = "darkblue", label = "Muslim")
ax3.set_ylabel("inter-ethnic marriage (%)", fontsize=7)
ax3.tick_params(axis='x',labelsize=6)
ax3.tick_params(axis='y',labelsize=6)

ax4 = plt.subplot2grid(shape=(3,8), loc=(1,4), colspan=4)
y1 = np.array([i[0] for i in inter_edu])
y2 = np.array([i[1] for i in inter_edu])
ax4.plot(tax, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax4.plot(tax, y2, color = "darkblue", label = "Muslim")
ax4.set_ylabel("inter-education marriage (%)", fontsize=7)
ax4.tick_params(axis='x',labelsize=6)
ax4.tick_params(axis='y',labelsize=6)

ax5 = plt.subplot2grid(shape=(3,8), loc=(2,2), colspan=4)
single_rel[0] = np.nan
y1 = np.array([i[0] for i in single_rel])
y2 = np.array([i[1] for i in single_rel])
ax5.plot(tax, y1, color = "darkred", linestyle = 'dashed', label="Non-Muslim")
ax5.plot(tax, y2, color = "darkblue", label = "Muslim")
ax5.set_ylabel("single (%)", fontsize=7)
ax5.set_xlabel("migration tax", fontsize=7)
ax5.tick_params(axis='x',labelsize=6)
ax5.tick_params(axis='y',labelsize=6)

plt.figlegend(['Non-Muslim','Muslim'], ncol = 2, fontsize=8, loc='upper center',borderaxespad=1.5,edgecolor='k')
plt.subplots_adjust(wspace=2, hspace=0.38)
plt.savefig(model_dir / 'taxes.png', bbox_inches = 'tight', dpi = 300)

