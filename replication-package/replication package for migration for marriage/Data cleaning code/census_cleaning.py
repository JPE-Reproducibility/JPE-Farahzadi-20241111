
import argparse
from pathlib import Path

import pandas as pd


parser = argparse.ArgumentParser(description="Prepare the intermediate Census cleaning CSV.")
parser.add_argument("--input-csv", type=Path, required=True)
parser.add_argument("--output-csv", type=Path, required=True)
args = parser.parse_args()
df = pd.read_csv(args.input_csv)


df['ID'] = df.HHID.astype(str) + df.PERSID.astype(str)

# Define ethnicity variable
df['ethnicity'] = -9
df.loc[(df.ETHNICITYEW >= 1) & (df.ETHNICITYEW <= 4) , 'ethnicity'] = 1 # white
df.loc[(df.ETHNICITYEW >= 5) & (df.ETHNICITYEW <= 8) , 'ethnicity'] = 2 # mixed
df.loc[df.ETHNICITYEW == 9, 'ethnicity'] = 3 # indian
df.loc[df.ETHNICITYEW == 10, 'ethnicity'] = 4 # pakistani
df.loc[df.ETHNICITYEW == 11, 'ethnicity'] = 5 # bangladeshi
df.loc[(df.ETHNICITYEW >= 12) & (df.ETHNICITYEW <= 13) , 'ethnicity'] = 6 # other asian
df.loc[(df.ETHNICITYEW >= 14) & (df.ETHNICITYEW <= 16) , 'ethnicity'] = 7 # black
df.loc[df.ETHNICITYEW == 17, 'ethnicity'] = 8 # arab
df.loc[df.ETHNICITYEW == 18, 'ethnicity'] = 9 # others

# Define immigrant variables
df['immigrant'] = (df.COB < 921) | (df.COB > 926)
df['immigrant18'] = ((df.AGEC - (2011 - df.YRARR_YEAR)) >= 18) & (df.immigrant == 1)
df.loc[(df.immigrant == 1) & (df.YRARR_YEAR == -9), 'immigrant18'] = -9 

# Define never married (single) variable 
df['single'] = df.MARSTAT == 1

# Define married variable
df['married'] = (df.MARSTAT == 2) | (df.MARSTAT == 6)

# Education variables
# ISCED: Education Level
df['edu_level'] = df.ISCED
df['tertiary_education'] = df.ISCED > 4
df.loc[df.ISCED == -9,'tertiary_education'] = -9

# Employment variables
df['employed'] = df.ACTLWO == 1 
df['unemployed'] = df.ACTLWO == 2

# rename
df.rename(columns = {'AGEC':'age', 'SEX': 'sex', 'HEALTH': 'health', 'RELIGIONEW': 'religion', 'REGION': 'region', 'LANGPRF':'lang_prof'}, inplace = True)

#### Married Couples Data
df_married = df[df.HSPOUSE == 2].copy()

# generate an id for present spouses
df_married['SPOUID'] = ((df_married.REL1 == 1)*1 + (df_married.REL2 == 1)*2 + (df_married.REL3 == 1)*3 + \
                 (df_married.REL4 == 1)*4 + (df_married.REL5 == 1)*5 + (df_married.REL6 == 1)*6 + \
                 (df_married.REL7 == 1)*7 + (df_married.REL8 == 1)*8 + (df_married.REL9 == 1)*9 + \
                 (df_married.REL10 == 1)*10 + (df_married.REL11 == 1)*11 + (df_married.REL12 == 1)*12 + \
                 (df_married.REL13 == 1)*13 + (df_married.REL14 == 1)*14 + (df_married.REL15 == 1)*15)
df_married.SPOUID = df_married.SPOUID.astype(int)


df_married['coupleid'] = ""
df_married.loc[(df_married.sex == 1) & (df_married.SPOUID > 0), 'coupleid'] = df_married.HHID.astype(str) + df_married.PERSID.astype(str) + df_married.SPOUID.astype(str)
df_married.loc[(df_married.sex == 2) & (df_married.SPOUID > 0), 'coupleid'] = df_married.HHID.astype(str) + df_married.SPOUID.astype(str) + df_married.PERSID.astype(str)
df_married = df_married[df_married.coupleid != ""]
couplesize = df_married.groupby(['coupleid']).size()
df_married = df_married.merge(couplesize.rename('couplesize'), on = 'coupleid')
df_married = df_married[df_married.couplesize == 2]

df_married = df_married[['ID','coupleid','age','sex','edu_level','tertiary_education','employed','unemployed','religion','ethnicity','immigrant','immigrant18','lang_prof','ETHNICITYEW','ETHNIC_INDEX', 'COB', 'IDENTITY', 'ISCO', 'QUALS01','QUALS02','QUALS03','QUALS04','QUALS05','QUALS06','QUALS07','QUALS08','QUALS09','QUALS10','QUALS11','QUALS12','QUALS13','QUALS14']]


for x in ['QUALS01','QUALS02','QUALS03','QUALS04','QUALS05','QUALS06','QUALS07','QUALS08','QUALS09','QUALS10','QUALS11','QUALS12','QUALS13','QUALS14']:
    df_married = df_married.sort_values(['coupleid','sex'])
    df_married = df_married.merge(df_married[['coupleid', x]].groupby(['coupleid']).first().rename(columns={x:'husb'}), on = 'coupleid')
    df_married = df_married.merge(df_married[['coupleid', x]].groupby(['coupleid']).last().rename(columns={x:'wife'}), on = 'coupleid')
    df_married['s'+x] = df_married.wife*(2 - df_married.sex) + df_married.husb*(df_married.sex - 1)
    df_married = df_married.drop(columns = ['husb','wife'])

# religion by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'religion']].groupby(['coupleid']).first().rename(columns={'religion':'religion_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'religion']].groupby(['coupleid']).last().rename(columns={'religion':'religion_wife'}), on = 'coupleid')
df_married['sreligion'] = df_married.religion_wife*(2 - df_married.sex) + df_married.religion_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['religion_husb','religion_wife'])

# ethnicity by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'ethnicity']].groupby(['coupleid']).first().rename(columns={'ethnicity':'ethnicity_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'ethnicity']].groupby(['coupleid']).last().rename(columns={'ethnicity':'ethnicity_wife'}), on = 'coupleid')
df_married['sethnicity'] = df_married.ethnicity_wife*(2 - df_married.sex) + df_married.ethnicity_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['ethnicity_husb','ethnicity_wife'])

# ethnicity by spouse 
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'ETHNICITYEW']].groupby(['coupleid']).first().rename(columns={'ETHNICITYEW':'ETHNICITYEW_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'ETHNICITYEW']].groupby(['coupleid']).last().rename(columns={'ETHNICITYEW':'ETHNICITYEW_wife'}), on = 'coupleid')
df_married['sETHNICITYEW'] = df_married.ETHNICITYEW_wife*(2 - df_married.sex) + df_married.ETHNICITYEW_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['ETHNICITYEW_husb','ETHNICITYEW_wife'])

# ethnicity by spouse 
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'ETHNIC_INDEX']].groupby(['coupleid']).first().rename(columns={'ETHNIC_INDEX':'ETHNIC_INDEX_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'ETHNIC_INDEX']].groupby(['coupleid']).last().rename(columns={'ETHNIC_INDEX':'ETHNIC_INDEX_wife'}), on = 'coupleid')
df_married['sETHNIC_INDEX'] = df_married.ETHNIC_INDEX_wife*(2 - df_married.sex) + df_married.ETHNIC_INDEX_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['ETHNIC_INDEX_husb','ETHNIC_INDEX_wife'])


# tertiaty education by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'tertiary_education']].groupby(['coupleid']).first().rename(columns={'tertiary_education':'tertiary_education_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'tertiary_education']].groupby(['coupleid']).last().rename(columns={'tertiary_education':'tertiary_education_wife'}), on = 'coupleid')
df_married['stertiary_education'] = df_married.tertiary_education_wife*(2 - df_married.sex) + df_married.tertiary_education_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['tertiary_education_husb','tertiary_education_wife'])

# education level by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'edu_level']].groupby(['coupleid']).first().rename(columns={'edu_level':'edu_level_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'edu_level']].groupby(['coupleid']).last().rename(columns={'edu_level':'edu_level_wife'}), on = 'coupleid')
df_married['sedu_level'] = df_married.edu_level_wife*(2 - df_married.sex) + df_married.edu_level_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['edu_level_husb','edu_level_wife'])


# immigrant by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'immigrant']].groupby(['coupleid']).first().rename(columns={'immigrant':'immigrant_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'immigrant']].groupby(['coupleid']).last().rename(columns={'immigrant':'immigrant_wife'}), on = 'coupleid')
df_married['simmigrant'] = df_married.immigrant_wife*(2 - df_married.sex) + df_married.immigrant_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['immigrant_husb','immigrant_wife'])

# immigrant18 by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'immigrant18']].groupby(['coupleid']).first().rename(columns={'immigrant18':'immigrant18_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'immigrant18']].groupby(['coupleid']).last().rename(columns={'immigrant18':'immigrant18_wife'}), on = 'coupleid')
df_married['simmigrant18'] = df_married.immigrant18_wife*(2 - df_married.sex) + df_married.immigrant18_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['immigrant18_husb','immigrant18_wife'])

# age by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'age']].groupby(['coupleid']).first().rename(columns={'age':'age_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'age']].groupby(['coupleid']).last().rename(columns={'age':'age_wife'}), on = 'coupleid')
df_married['sage'] = df_married.age_wife*(2 - df_married.sex) + df_married.age_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['age_husb','age_wife'])

# employed by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'employed']].groupby(['coupleid']).first().rename(columns={'employed':'employed_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'employed']].groupby(['coupleid']).last().rename(columns={'employed':'employed_wife'}), on = 'coupleid')
df_married['semployed'] = df_married.employed_wife*(2 - df_married.sex) + df_married.employed_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['employed_husb','employed_wife'])

# language proficiency by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'lang_prof']].groupby(['coupleid']).first().rename(columns={'lang_prof':'lang_prof_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'lang_prof']].groupby(['coupleid']).last().rename(columns={'lang_prof':'lang_prof_wife'}), on = 'coupleid')
df_married['slang_prof'] = df_married.lang_prof_wife*(2 - df_married.sex) + df_married.lang_prof_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['lang_prof_husb','lang_prof_wife'])


# country of birth by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'COB']].groupby(['coupleid']).first().rename(columns={'COB':'COB_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'COB']].groupby(['coupleid']).last().rename(columns={'COB':'COB_wife'}), on = 'coupleid')
df_married['sCOB'] = df_married.COB_wife*(2 - df_married.sex) + df_married.COB_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['COB_husb','COB_wife'])

# identity by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'IDENTITY']].groupby(['coupleid']).first().rename(columns={'IDENTITY':'IDENTITY_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'IDENTITY']].groupby(['coupleid']).last().rename(columns={'IDENTITY':'IDENTITY_wife'}), on = 'coupleid')
df_married['sIDENTITY'] = df_married.IDENTITY_wife*(2 - df_married.sex) + df_married.IDENTITY_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['IDENTITY_husb','IDENTITY_wife'])

# identity by spouse
df_married = df_married.sort_values(['coupleid','sex'])
df_married = df_married.merge(df_married[['coupleid', 'ISCO']].groupby(['coupleid']).first().rename(columns={'ISCO':'ISCO_husb'}), on = 'coupleid')
df_married = df_married.merge(df_married[['coupleid', 'ISCO']].groupby(['coupleid']).last().rename(columns={'ISCO':'ISCO_wife'}), on = 'coupleid')
df_married['sISCO'] = df_married.ISCO_wife*(2 - df_married.sex) + df_married.ISCO_husb*(df_married.sex - 1)
df_married = df_married.drop(columns = ['ISCO_husb','ISCO_wife'])


# Merging dataframes 

df = df[['ID','region','age','sex','immigrant','immigrant18','single','married','ethnicity','religion','edu_level','tertiary_education','employed','unemployed','health','lang_prof','ETHNICITYEW','ETHNIC_INDEX','COB','IDENTITY','ISCO','QUALS01','QUALS02','QUALS03','QUALS04','QUALS05','QUALS06','QUALS07','QUALS08','QUALS09','QUALS10','QUALS11','QUALS12','QUALS13','QUALS14','LA','MOVEREGION']]
df_married = df_married[['ID','coupleid','sage','simmigrant','simmigrant18','sethnicity','sreligion','sedu_level','stertiary_education','semployed','slang_prof','sETHNICITYEW','sETHNIC_INDEX','sCOB','sIDENTITY','sISCO','sQUALS01','sQUALS02','sQUALS03','sQUALS04','sQUALS05','sQUALS06','sQUALS07','sQUALS08','sQUALS09','sQUALS10','sQUALS11','sQUALS12','sQUALS13','sQUALS14']]

data = pd.merge(df,df_married,how='outer',on=['ID'])

data.to_csv(args.output_csv)
