#%%
import re
import pandas as pd 
lat = '''44°46'44.4"N'''
deg, minutes, seconds, direction =  re.split('[°\'"]', lat)
dd= (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1)
print(dd)


def degree_to_dec(degree_value):
    degree_value=degree_value.replace(' ', '')
    deg, minutes, seconds, direction =  re.split('[°\'"]', degree_value)
    decimal_value = (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1)
    return (decimal_value)


#%%
degree_to_dec('''44°46'44.4"N''')
#%%
df=pd.read_excel('data/data_main.xlsx')
#%%
df2=df[['naziv', 'gpx', 'gpy']].dropna()
print(df2['gpx'])
#%%
for row in df['gpx'][:500]:
    r=degree_to_dec(row)
    print(row)

# %%
