#%%
import pandas as pd
import googlemaps

key = 'AIzaSyA6if1JfmCrUVPonSe9KDdTXn0XUGDL5r8'



#%%
def get_geocode_result(place):
    gmaps = googlemaps.Client(key=key)
    # Geocoding an address
    geocode_result = gmaps.geocode(place)
    result= geocode_result[0]
    return result
get_geocode_result('Pazin')
#%%

df= pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vRS5ZC1mNadCJNC2CXrfFCxfLdm9rvJ_sbreGkjGHmSbGmk1o9vCEky6Mf9vowVgAcxBaXSSxO2KRC7/pub?gid=0&single=true&output=csv')
df.head()
#%%
df['novo'] =df['mjestopravo']



# %%
df['novo']

# %%
def dodaj_x(x):
    if x:
        y = str(x)+'novovovovovov'
    return y
df['novo'].apply(dodaj_x)


# %%
lat=[]
lon=[]
nazivlj=[]
for place in df['novo'][0:10]:
    if place:
        try:
            result= get_geocode_result(place)
            naziv= result['formatted_address']
            kratki_naziv= result['address_components'][0]['short_name']
            pozicija= result['geometry']['location']
            lat.append(pozicija['lat'])
            lon.append(pozicija['lng'])
            nazivlj.append(kratki_naziv)
        # print((kratki_naziv, lat, lon))
        except:
            lat.append(0.0)
            lon.append(0.0)
            nazivlj.append(kratki_naziv)
    else:
        lat.append(0.0)
        lon.append(0.0)
        nazivlj.append(kratki_naziv)
lat, lon, nazivlj


# %%
