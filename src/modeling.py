from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, make_scorer, r2_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import data_preprocessing_emlakjet as dpe

import seaborn as sns

import usd_try
import re
import pandas as pd
from nltk.corpus import stopwords
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib
import matplotlib.pyplot as plt
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np
from sklearn.model_selection import RandomizedSearchCV
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from unidecode import unidecode
from sklearn.preprocessing import LabelEncoder
from scipy.spatial import cKDTree
import numpy as np

from shapely.geometry import Point, LineString
import geopandas as gpd

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt



def run_modeling():
  # Ensure NLTK resources are available
  nltk.download('stopwords')
  nltk.download('punkt')

  # Load the raw data
  raw_data = dpe.load_json_data('istanbul_emlakjet_all_records_updated.json')

  # Preprocess the data
  processed_data = dpe.cleanse_and_preprocess_data(raw_data)

  df = pd.DataFrame(processed_data)


  if 'priceDetail' in df.columns:
      price_details = pd.json_normalize(df['priceDetail'])
      df = pd.concat([df.drop(['priceDetail'], axis=1), price_details], axis=1)

  if 'info' in df.columns:
      info_details = pd.json_normalize(df['info'])
      df = pd.concat([df.drop(['info'], axis=1), info_details], axis=1)

  # Average Household Size Related Feature Implementation
  household_size_df = pd.read_excel('2022-yl-ilcelere-gore-ortalama-hanehalk-buyukluu.xlsx')
  household_size_df.rename(columns={
      'İlçe': 'district_name',
      'Ortalama Hanehalkı Büyüklüğü 2022': 'average_household_size'
  }, inplace=True)
  df['district_name'] = df['location'].apply(lambda x: x['district']['name'])
  df = df.merge(household_size_df, on='district_name', how='left')
  missing_districts_count = df['average_household_size'].isna().sum()
  df['average_household_size'].fillna(df['average_household_size'].mean(), inplace=True)


  population_data_df = pd.read_excel('2021ISTANBULILCEYERLESIMVENUFUSBILGILERI.xlsx', header=1)

  population_data_df.columns = [
      'district_name', 'population_2020', 'population_count_2021', 'difference', 'population_growth_rate',
      'neighborhood_count', 'area_km2', 'population_density'
  ]
  population_data_df['district_name'] = population_data_df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())
  df['district_name'] = df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())
  population_data_df = population_data_df[~population_data_df['district_name'].isna()]
  population_data_df = population_data_df[['district_name', 'population_density', 'population_count_2021', 'population_growth_rate']]
  df = df.merge(population_data_df, on='district_name', how='left')
  missing_density_count = df['population_density'].isna().sum()
  missing_population_count = df['population_count_2021'].isna().sum()
  missing_growth_rate = df['population_growth_rate'].isna().sum()
  missing_population_density_df = df[df['population_density'].isna()]
  df['population_density'].fillna(df['population_density'].mean(), inplace=True)
  df['population_count_2021'].fillna(df['population_count_2021'].mean(), inplace=True)
  df['population_growth_rate'].fillna(df['population_growth_rate'].mean(), inplace=True)


  social_assistance_df = pd.read_excel('21-vdym-ilce-baznda-hanelerin-kamu-kurumlarndan-sosyal-yardm-alma-durumu.xlsx')

  social_assistance_df.rename(columns={
      'İlçe': 'district_name',
      'Sosyal Yardım Alma_Evet': 'social_assistance_yes',
      'Sosyal Yardım Alma_Hayır': 'social_assistance_no'
  }, inplace=True)

  # Step 3: Normalize district names in the social assistance DataFrame
  social_assistance_df['district_name'] = social_assistance_df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())

  # Step 4: Normalize district names in the main DataFrame
  df['district_name'] = df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())

  # Step 5: Merge social assistance data into the main DataFrame
  df = df.merge(social_assistance_df, on='district_name', how='left')

  # Step 6: Handle any missing values after the merge
  missing_social_assistance_count = df['social_assistance_yes'].isna().sum()

  df['social_assistance_yes'].fillna(0, inplace=True)
  df['social_assistance_no'].fillna(0, inplace=True)


  # Step 1: Load the district-level average household size in square meters data from Excel
  household_size_area_df = pd.read_excel('9-vdym-ilce-bazl-ortalama-hane-buyuklukleri-m2.xlsx')

  # Step 2: Rename columns for easier access
  household_size_area_df.rename(columns={
      'İlçe': 'district_name',
      'Ortalama Brüt (m2)': 'average_gross_area_m2',
      'Ortalama Net (m2)': 'average_net_area_m2'
  }, inplace=True)

  # Step 3: Normalize district names in the household size area DataFrame using unidecode
  household_size_area_df['district_name'] = household_size_area_df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())

  # Step 4: Normalize district names in the main DataFrame using unidecode
  df['district_name'] = df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())

  # Step 5: Merge household size area data into the main DataFrame
  df = df.merge(household_size_area_df, on='district_name', how='left')

  # Step 6: Handle any missing values after the merge
  missing_household_size_area_count = df['average_gross_area_m2'].isna().sum()

  df['average_gross_area_m2'].fillna(df['average_gross_area_m2'].mean(), inplace=True)
  df['average_net_area_m2'].fillna(df['average_net_area_m2'].mean(), inplace=True)



  district_data_df = pd.read_csv('ilce_data.csv')
  district_data_df.rename(columns={
      'District': 'district_name',
      'n': 'sample_size',
      'Sosyo-demografi': 'socio_demographic_score',
      'Sosyo-ekonomi': 'socio_economic_score',
      'Risk Algısı ve Tutumlar': 'risk_perception_attitudes',
      'Değerler': 'values_score',
      'Score': 'overall_score'
  }, inplace=True)
  district_data_df['district_name'] = district_data_df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())
  df['district_name'] = df['district_name'].apply(lambda x: unidecode(str(x)).lower().strip())
  df = df.merge(district_data_df, on='district_name', how='left')
  missing_district_data_count = df['socio_demographic_score'].isna().sum()
  df['socio_demographic_score'].fillna(df['socio_demographic_score'].mean(), inplace=True)
  df['socio_economic_score'].fillna(df['socio_economic_score'].mean(), inplace=True)
  df['risk_perception_attitudes'].fillna(df['risk_perception_attitudes'].mean(), inplace=True)
  df['values_score'].fillna(df['values_score'].mean(), inplace=True)
  df['overall_score'].fillna(df['overall_score'].mean(), inplace=True)



  # Extract and encode location-based features
  df['district_name'] = df['location'].apply(lambda x: x.get('district', {}).get('name', None))
  df['locality_name'] = df['location'].apply(lambda x: x.get('locality', {}).get('name', None))
  df['town_name'] = df['location'].apply(lambda x: x.get('town', {}).get('name', None))
  district_encoder = LabelEncoder()
  locality_encoder = LabelEncoder()
  town_encoder = LabelEncoder()
  df['district_name_encoded'] = district_encoder.fit_transform(df['district_name'].astype(str))
  df['locality_name_encoded'] = locality_encoder.fit_transform(df['locality_name'].astype(str))
  df['town_name_encoded'] = town_encoder.fit_transform(df['town_name'].astype(str))
  df['district_name_encoded'].unique()

  #LOCATION
  if 'location' in df.columns:
      location_details = pd.json_normalize(df['location'])
      df = pd.concat([df.drop(['location'], axis=1), location_details], axis=1)

  if 'coordinate.lat' in df.columns and 'coordinate.lon' in df.columns:
      df['lat'] = df['coordinate.lat']
      df['lon'] = df['coordinate.lon']
      df = df.drop(['coordinate.lat', 'coordinate.lon'], axis=1)

  # Load the Excel file
  park_df = pd.read_excel('istanbul-park-ve-yeil-alan-koordinatlar.xlsx')

  # Step 2: Filter only park-related entries, handling NaN values
  park_df = park_df[park_df['TÜR '].fillna('').str.contains('Park', case=False)]

  # Step 3: Ensure latitude and longitude are numeric
  park_df['LATITUDE'] = pd.to_numeric(park_df['LATITUDE'], errors='coerce')
  park_df['LONGITUDE'] = pd.to_numeric(park_df['LONGITUDE'], errors='coerce')

  # Step 4: Drop rows with NaN values in LATITUDE or LONGITUDE
  park_df = park_df.dropna(subset=['LATITUDE', 'LONGITUDE'])

  # Convert to numpy array
  park_coords = park_df[['LONGITUDE', 'LATITUDE']].to_numpy()

  # Step 5: Verify that all values are finite
  if not np.all(np.isfinite(park_coords)):
      raise ValueError("There are still non-finite values in park coordinates.")

  # Step 6: Create a KDTree for efficient nearest-neighbor search
  park_tree = cKDTree(park_coords)

  # Step 7: Define a function to calculate the distance to the nearest park
  def find_nearest_park_distance(row):
      point = [row['lon'], row['lat']]
      distance, _ = park_tree.query(point)
      return distance

  # Step 8: Apply the function to the real estate data
  df['distance_to_park'] = df.apply(find_nearest_park_distance, axis=1)


  mall_coordinates = [
      (41.11057129506558, 29.03324286718944),  # Istinye Park – Sarıyer
      (41.06268087107968, 28.807461223056364),  # Mall of Istanbul – Başakşehir
      (41.06711470503005, 29.015554896070412),  # Zorlu Center – Beşiktaş
      (40.999637820565226, 29.072885881479465), # Emaar Square Mall – Üsküdar
      (41.0786964086412, 29.010972596070914),   # Kanyon Shopping Center – Şişli
      (40.96562649212199, 28.797951696065073),  # Aqua Florya – Bakırköy
      (41.0804931294411, 28.877394451892833),   # Venezia Mega Outlet – Gaziosmanpaşa
      (41.04768078876212, 28.89691088257621),   # Forum Istanbul – Bayrampaşa
      (41.06327573080746, 28.991669082577122),  # Cevahir Mall – Şişli
      (41.021045606256955, 29.03949739606786),  # Capitol – Üsküdar
      (40.93786408646402, 29.326173282570437),  # Viaport Asia Outlet – Pendik
      (41.07639443902365, 29.013501082577847),  # Metrocity – Levent, Beşiktaş
      (40.986014245704126, 29.09975372490178),  # Palladium Mall – Ataşehir
      (40.974266074895134, 28.87005201140803),  # Galleria Mall – Bakırköy
      (40.9528418304794, 29.12186246722875),    # Hilltown AVM – Küçükyalı, Maltepe
      (41.0077, 29.0404),                        # Akasya Mall – Acıbadem, Üsküdar
      (41.07775811202652, 29.01151465189268),   # ÖzdilekPark – Levent, Beşiktaş
      (41.10755845009085, 28.986842742100134),  # Vadistanbul – Sarıyer
      (41.05115668007445, 28.992617851891364),  # City’s Nişantaşı – Şişli
      (40.9749, 28.8741)                         # Carousel Mall – Bakırköy
  ]


  # Step 1: Create a KDTree for efficient nearest-neighbor search
  mall_tree = cKDTree(mall_coordinates)

  # Step 2: Define a function to calculate the distance to the nearest mall
  def find_nearest_mall_distance(row):
      point = [row['lat'], row['lon']]
      distance, _ = mall_tree.query(point)
      return distance

  # Step 3: Apply the function to the DataFrame and add the 'distance_to_mall' feature
  df['distance_to_mall'] = df.apply(find_nearest_mall_distance, axis=1)


  #LOCATION
  if 'location' in df.columns:
      location_details = pd.json_normalize(df['location'])
      df = pd.concat([df.drop(['location'], axis=1), location_details], axis=1)

  if 'coordinate.lat' in df.columns and 'coordinate.lon' in df.columns:
      df['lat'] = df['coordinate.lat']
      df['lon'] = df['coordinate.lon']
      df = df.drop(['coordinate.lat', 'coordinate.lon'], axis=1)


  # Assuming you have already loaded the GeoJSON into rail_df
  rail_df = gpd.read_file('rayli_sistem_istasyon_poi_verisi.geojson')

  # Extract latitude and longitude
  rail_df['lat'] = rail_df.geometry.y
  rail_df['lon'] = rail_df.geometry.x

  # Combine PROJE_ADI and ISTASYON into a new column
  rail_df['Station_Info'] = rail_df['PROJE_ADI'] + ' - ' + rail_df['ISTASYON']

  # Create a new DataFrame with the desired format
  result_df = rail_df[['Station_Info', 'lat', 'lon']]

  rail_coords = rail_df[['lon', 'lat']].to_numpy()

  # Create a KDTree for efficient nearest neighbor search
  tree = cKDTree(rail_coords)

  # Function to find the closest rail station and its distance
  def find_closest_station(row):
      point = [row['lon'], row['lat']]
      distance, index = tree.query(point)
      closest_station = rail_df.iloc[index]['Station_Info']
      return closest_station, distance

  # Apply the function to each row in df
  df[['closest_rail_station', 'rail_distance']] = df.apply(find_closest_station, axis=1, result_type='expand')

  df['lat_rank'] = df['lat'].rank(method='min').astype(int)
  df['lon_rank'] = df['lon'].rank(method='min').astype(int)

  # DISTANCE TO SEA
  # Define the coastline coordinates from your provided GeoJSON
  coastline_coords = [
            [
              28.522819568625778,
              40.99369981821462
            ],
            [
              28.54137407604358,
              40.98592075106728
            ],
            [
              28.549663706365976,
              41.00768420183087
            ],
            [
              28.56403614018177,
              41.01703504465905
            ],
            [
              28.589465457545742,
              41.018584284755065
            ],
            [
              28.6011574456534,
              41.01027315669273
            ],
            [
              28.598407836707338,
              40.99110352438646
            ],
            [
              28.599080336079624,
              40.970877505531774
            ],
            [
              28.600454096169074,
              40.96465120279177
            ],
            [
              28.619693513681455,
              40.9620596550607
            ],
            [
              28.664353653203932,
              40.96309598227651
            ],
            [
              28.671915619716373,
              40.958943080489234
            ],
            [
              28.676033141487324,
              40.96413397146523
            ],
            [
              28.696649333447994,
              40.973990187829514
            ],
            [
              28.716537224978936,
              40.970364657603426
            ],
            [
              28.72956427189422,
              40.971923232432374
            ],
            [
              28.743340330409097,
              40.969843968043506
            ],
            [
              28.74881114463443,
              40.97918051245665
            ],
            [
              28.763987987250516,
              40.980215049051594
            ],
            [
              28.77599707412128,
              40.97740185619756
            ],
            [
              28.80862860440945,
              40.95713302705485
            ],
            [
              28.822410879609265,
              40.95548803724549
            ],
            [
              28.83546609743715,
              40.95822778342924
            ],
            [
              28.853590494469046,
              40.97520838367953
            ],
            [
              28.86955547026767,
              40.96973003019545
            ],
            [
              28.881159624012724,
              40.976301725971695
            ],
            [
              28.89638279114604,
              40.98232563773149
            ],
            [
              28.90509986053914,
              40.98122950227767
            ],
            [
              28.914514393697488,
              40.99053763369389
            ],
            [
              28.922502946156442,
              40.9878002190803
            ],
            [
              28.938404562087072,
              41.002576299542625
            ],
            [
              28.93987371610325,
              40.99765259858745
            ],
            [
              28.94929597836591,
              40.99819964400288
            ],
            [
              28.950521648869255,
              40.99799466463776
            ],
            [
              28.95448829611331,
              40.999490525663106
            ],
            [
              28.957443133723757,
              41.003228199883864
            ],
            [
              28.971867023929235,
              41.001733469212695
            ],
            [
              28.980823698137982,
              41.00248771436634
            ],
            [
              28.98774636936082,
              41.00847446519202
            ],
            [
              28.98674167837865,
              41.0159678347745
            ],
            [
              28.986241151935303,
              41.01709061487938
            ],
            [
              28.9708471453757,
              41.018594328901884
            ],
            [
              28.95793903303914,
              41.024974663307404
            ],
            [
              28.949491849077788,
              41.03247234679404
            ],
            [
              28.941325818294644,
              41.04174160571668
            ],
            [
              28.937435739509112,
              41.04736685835584
            ],
            [
              28.93677474934526,
              41.05322236154308
            ],
            [
              28.945838650070243,
              41.05687912000511
            ],
            [
              28.945205625772104,
              41.06275803133721
            ],
            [
              28.94781346358687,
              41.06375084297426
            ],
            [
              28.949095302839225,
              41.05738137108341
            ],
            [
              28.94260527382866,
              41.0529756181723
            ],
            [
              28.94131582598976,
              41.047115095438926
            ],
            [
              28.948110952935025,
              41.042954858283736
            ],
            [
              28.95235247323214,
              41.03685071465972
            ],
            [
              28.960763761119182,
              41.03342480802712
            ],
            [
              28.96918178990967,
              41.028779350730986
            ],
            [
              28.967262534339397,
              41.0263329150618
            ],
            [
              28.972781475412006,
              41.02192900824693
            ],
            [
              28.977977771162386,
              41.02217268849242
            ],
            [
              28.987973449200013,
              41.027801571550725
            ],
            [
              28.998143869843375,
              41.038020541785414
            ],
            [
              29.015574526465286,
              41.04264617486004
            ],
            [
              29.026239116978417,
              41.04655340958885
            ],
            [
              29.0362376045278,
              41.05701307579869
            ],
            [
              29.04234782240826,
              41.06623701645839
            ],
            [
              29.04658516302004,
              41.0689580079694
            ],
            [
              29.043631234154475,
              41.07838636553058
            ],
            [
              29.05559927351618,
              41.081342908818016
            ],
            [
              29.056247174460054,
              41.08767144117789
            ],
            [
              29.05433603034325,
              41.09692798708545
            ],
            [
              29.060484041579144,
              41.109360190905136
            ],
            [
              29.05692441876363,
              41.11326251512946
            ],
            [
              29.05886578359045,
              41.11570115718686
            ],
            [
              29.062425731782724,
              41.113749308166234
            ],
            [
              29.068897794917604,
              41.11984445611111
            ],
            [
              29.071167827978115,
              41.12618548273079
            ],
            [
              29.063070691496677,
              41.1315390311743
            ],
            [
              29.059189588564777,
              41.13739832171518
            ],
            [
              29.054661736994262,
              41.14566184521837
            ],
            [
              29.045937445481087,
              41.14954090092249
            ],
            [
              29.038476307205144,
              41.15421318310942
            ],
            [
              29.03655175972864,
              41.15735067978548
            ],
            [
              29.04301740115841,
              41.15954767588778
            ],
            [
              29.052403325288992,
              41.165101346501245
            ],
            [
              29.057571819168885,
              41.166374143022466
            ],
            [
              29.06242284691629,
              41.17195552094023
            ],
            [
              29.07178303532561,
              41.17577312324278
            ],
            [
              29.07553133780658,
              41.18310035231434
            ],
            [
              29.081064642131878,
              41.18872089991274
            ],
            [
              29.08920392238761,
              41.197259826886835
            ],
            [
              29.09540124428645,
              41.2030717332521
            ],
            [
              29.100563595290907,
              41.20607215225303
            ],
            [
              29.103809285281642,
              41.20583876539038
            ],
            [
              29.110957686331744,
              41.21220520075158
            ],
            [
              29.107061812902742,
              41.218285775274126
            ],
            [
              29.109657103691347,
              41.22541324189987
            ],
            [
              29.115509136311914,
              41.23108119546174
            ],
            [
              29.10870932716054,
              41.23978087321578
            ],
            [
              29.093850177934115,
              41.245122060063494
            ],
            [
              29.080607460367617,
              41.251921057644836
            ],
            [
              29.06640319636918,
              41.25313002918466
            ],
            [
              29.044121723523887,
              41.25531392868274
            ],
            [
              29.036030384240462,
              41.24900671435509
            ],
            [
              29.02314400594838,
              41.24535574756558
            ],
            [
              28.97516884551058,
              41.25268385387136
            ],
            [
              28.92634122813385,
              41.26983579644292
            ],
            [
              28.712374670726888,
              41.32917260812539
            ],
            [
              28.45972512010306,
              41.42086464836149
            ],
            [
              28.277189456985298,
              41.49392714868435
            ],
            [
              28.15165578675567,
              41.58304165131335
            ],
            [
              28.017072567066577,
              41.037340265463
            ],
            [
              28.101253043405194,
              41.060986548534345
            ],
            [
              28.20196581509896,
              41.073432230078424
            ],
            [
              28.23663464869591,
              41.08090582705793
            ],
            [
              28.261409367812774,
              41.062224029970736
            ],
            [
              28.398445018829136,
              41.04977882351275
            ],
            [
              28.520627981711215,
              40.99496836641865
            ],
            [
              29.91157506034412,
              41.14027555587799
            ],
            [
              29.842369380909645,
              41.142763699147736
            ],
            [
              29.77798247804995,
              41.15767227557123
            ],
            [
              29.702098360049035,
              41.15891821941912
            ],
            [
              29.619587343655382,
              41.176313460723065
            ],
            [
              29.596478140908857,
              41.17258317032196
            ],
            [
              29.40506258871696,
              41.20734816483417
            ],
            [
              29.253153200048246,
              41.234688002728234
            ],
            [
              29.160901796638825,
              41.21850811494113
            ],
            [
              29.08826193953209,
              41.175061601726924
            ],
            [
              29.08412577224027,
              41.1675524985815
            ],
            [
              29.077937855444134,
              41.16759326993943
            ],
            [
              29.072172881564512,
              41.16123944560189
            ],
            [
              29.07884171294924,
              41.15693295820421
            ],
            [
              29.072158749390525,
              41.143742727729915
            ],
            [
              29.079284991741474,
              41.14016679544977
            ],
            [
              29.079755846938923,
              41.139095911110786
            ],
            [
              29.082598102755526,
              41.13552348459305
            ],
            [
              29.089733119511777,
              41.135519572225974
            ],
            [
              29.098275961230485,
              41.12480700129481
            ],
            [
              29.09638926305655,
              41.117672019733305
            ],
            [
              29.081694101563784,
              41.10945722298655
            ],
            [
              29.071240549665305,
              41.106228449404
            ],
            [
              29.06511633902099,
              41.09767881811641
            ],
            [
              29.067949116932738,
              41.093743512134694
            ],
            [
              29.067923732784323,
              41.08514738230369
            ],
            [
              29.067911030439035,
              41.08084541697846
            ],
            [
              29.064604554289275,
              41.07764176659751
            ],
            [
              29.058462356878863,
              41.075518113228156
            ],
            [
              29.054205264737817,
              41.073382304112755
            ],
            [
              29.057549341259346,
              41.070194664717434
            ],
            [
              29.054667945462427,
              41.06265111610844
            ],
            [
              29.05321766644488,
              41.05832958127425
            ],
            [
              29.053489422335986,
              41.04967995459623
            ],
            [
              29.006861410187156,
              41.02374064393598
            ],
            [
              29.007332565270588,
              41.02018569119488
            ],
            [
              29.01110122926542,
              41.01165643874654
            ],
            [
              29.008747166040877,
              41.00773473921163
            ],
            [
              29.02288409802884,
              40.994580666064394
            ],
            [
              29.017229575312797,
              40.99173320536676
            ],
            [
              29.021943398972894,
              40.97856686821257
            ],
            [
              29.034650993203826,
              40.980732284028676
            ],
            [
              29.040316502106208,
              40.97537709926735
            ],
            [
              29.031843546143023,
              40.970020556792036
            ],
            [
              29.043630386268404,
              40.96574458624514
            ],
            [
              29.047388592391883,
              40.970034667442235
            ],
            [
              29.06200900333826,
              40.96219190804473
            ],
            [
              29.071423154780007,
              40.96362869231211
            ],
            [
              29.077092196101347,
              40.95614061167396
            ],
            [
              29.08838320084857,
              40.95473640125189
            ],
            [
              29.10725066928609,
              40.94226318871071
            ],
            [
              29.14533476592112,
              40.901052121289126
            ],
            [
              29.15902896987771,
              40.90034214367765
            ],
            [
              29.177910357657083,
              40.887144451000296
            ],
            [
              29.187351732577355,
              40.884286213570675
            ],
            [
              29.190651463012045,
              40.88786251432731
            ],
            [
              29.229841733589495,
              40.871074593984446
            ],
            [
              29.238313391499247,
              40.87501936071175
            ],
            [
              29.25768219609739,
              40.86644178902347
            ],
            [
              29.259115309614003,
              40.862860691914676
            ],
            [
              29.261007020818255,
              40.85464566764978
            ],
            [
              29.270443433765564,
              40.856435203480345
            ],
            [
              29.27845951974365,
              40.85644104382982
            ],
            [
              29.28643219214925,
              40.85647067863542
            ],
            [
              29.28741159965182,
              40.85180958424564
            ],
            [
              29.28697196397539,
              40.84286160705582
            ],
            [
              29.281783026755335,
              40.838215048315305
            ],
            [
              29.27800710290171,
              40.83642808256954
            ],
            [
              29.269506949725695,
              40.84178735370463
            ],
            [
              29.271391919375475,
              40.84893314565508
            ],
            [
              29.26761600081963,
              40.84857523456719
            ],
            [
              29.265728869560263,
              40.84143101814274
            ],
            [
              29.26762078127328,
              40.833569557592
            ],
            [
              29.27611976527612,
              40.83249756641763
            ],
            [
              29.280841251044308,
              40.83249756641763
            ],
            [
              29.278446812162827,
              40.82465755637023
            ],
            [
              29.255819623126683,
              40.81359824990997
            ],
            [
              29.25676236134578,
              40.80360753433527
            ],
            [
              29.281274004313218,
              40.813956887239385
            ],
            [
              29.31238227434102,
              40.813600705077306
            ],
            [
              29.326045053420415,
              40.81681289396579
            ],
            [
              29.3392446558299,
              40.81039135038429
            ],
            [
              29.122767348698574,
              40.83947966590489
            ],
            [
              29.139319666388644,
              40.87262992618426
            ],
            [
              29.121877679159212,
              40.87441165124105
            ],
            [
              29.114319306759768,
              40.86585300676185
            ],
            [
              29.114267957299603,
              40.8523065651396
            ],
            [
              29.114264827897983,
              40.843401397651434
            ],
            [
              29.123235530232336,
              40.8401927053406
            ],
            [
              29.07851297386432,
              40.867283246176555
            ],
            [
              29.103469367018022,
              40.87083799095009
            ],
            [
              29.096883093532142,
              40.88545110206363
            ],
            [
              29.079446486744246,
              40.875830738890016
            ],
            [
              29.0794551198652,
              40.86799584445663
            ],
            [
              29.05541636254017,
              40.87726503363598
            ],
            [
              29.055415361485956,
              40.886171825082215
            ],
            [
              29.070966000697183,
              40.88616612024606
            ],
            [
              29.071904632367847,
              40.88081691459993
            ],
            [
              29.065312914300222,
              40.87441013736867
            ],
            [
              29.04033462342332,
              40.91320572302973
            ],
            [
              29.05305183399986,
              40.91426725416528
            ],
            [
              29.054936342090798,
              40.910355029806965
            ],
            [
              29.056351576730663,
              40.90573760368895
            ],
            [
              29.04740104747208,
              40.90432064509994
            ]
  ]
  # Transform coastline_coords into a list of tuples
  coastline_coords_tuples = [(coord[0], coord[1]) for coord in coastline_coords]

  # Create a LineString object for the coastline
  coastline = LineString(coastline_coords_tuples)

  # Function to calculate the closest distance to the sea for each real estate listing
  def closest_distance_to_sea(row):
      point = Point(row['lon'], row['lat'])
      return point.distance(coastline)

  # Assuming your DataFrame is named rail_df and contains 'longitude' and 'latitude' columns
  df['distance_to_sea'] = df.apply(closest_distance_to_sea, axis=1)

  # Load health services data
  health_services_df = pd.read_csv('saglik-tesisleri.csv')

  # Define important categories
  important_categories = [
      'Eczane',  # Pharmacy
      'Diş Hekimi',  # Dentist
      'Özel Ağız ve Diş Sağlığı Merkezleri',  # Private Dental Health Centers
      'Doktor/Muayenehane',  # General Practitioners / Private Clinics
      'Aile Sağlığı Merkezi',  # Family Health Center
      'Özel Hastane',  # Private Hospital
      'Devlet Hastanesi',  # State Hospital
      'Şehir Hastanesi'  # City Hospital
  ]

  # Filter relevant categories
  filtered_health_services_df = health_services_df[
      health_services_df['Alt Kategori'].isin(important_categories)
  ].copy()

  # Extract latitude and longitude as NumPy arrays
  health_service_coords = filtered_health_services_df[['Longitude', 'Latitude']].to_numpy()

  # Create a general KDTree for all health services
  health_service_tree = cKDTree(health_service_coords)

  # Precompute KD-Trees for each specific service type
  service_type_trees = {}
  for service_type in important_categories:
      specific_services = filtered_health_services_df[filtered_health_services_df['Alt Kategori'] == service_type]
      if not specific_services.empty:
          specific_coords = specific_services[['Longitude', 'Latitude']].to_numpy()
          service_type_trees[service_type] = cKDTree(specific_coords)
      else:
          service_type_trees[service_type] = None  # No services of this type

  # Assume 'df' is your main DataFrame with 'lon' and 'lat' columns
  # Ensure 'df' has 'lon' and 'lat' columns as float
  df['lon'] = df['lon'].astype(float)
  df['lat'] = df['lat'].astype(float)

  # Extract coordinates from 'df' as a NumPy array
  df_coords = df[['lon', 'lat']].to_numpy()

  # Query the general KDTree for all points at once
  df['health_service_distance'], _ = health_service_tree.query(df_coords, k=1)

  # Initialize distance columns with infinity
  for service_type in important_categories:
      df[f'{service_type}_distance'] = np.inf

  # Iterate through each service type and compute distances
  for service_type in important_categories:
      tree = service_type_trees[service_type]
      if tree is not None:
          distances, _ = tree.query(df_coords, k=1)
          df[f'{service_type}_distance'] = distances
      # If tree is None, the distance remains as infinity





  # Step 1: Prepare the data for clustering
  # Extract latitude and longitude from your DataFrame
  location_data = df[['lat', 'lon']].dropna()

  # Step 2: Standardize the coordinates
  scaler = StandardScaler()
  location_scaled = scaler.fit_transform(location_data)

  # Step 3: Determine the optimal number of clusters (optional step)
  # the elbow method to find the optimal number of clusters
  inertia = []
  cluster_range = range(1, 15)
  for k in cluster_range:
      kmeans = KMeans(n_clusters=k, random_state=42)
      kmeans.fit(location_scaled)
      inertia.append(kmeans.inertia_)

  # Step 4: Fit the KMeans model with an appropriate number of clusters
  optimal_clusters = 10
  kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
  location_data['location_cluster'] = kmeans.fit_predict(location_scaled)

  if 'location_cluster' in df.columns:
      df.drop(columns=['location_cluster'], inplace=True)

  # Step 6: Assign cluster labels back to the main DataFrame
  df = df.join(location_data[['location_cluster']])

  # Step 7: Handle NaN values if there were any rows without lat/lon
  df['location_cluster'].fillna(-1, inplace=True)

  # Step 8: Convert cluster labels to categorical data type
  df['location_cluster'] = df['location_cluster'].astype('category')

  numerical_features = df.select_dtypes(include='number').columns
  #duplicate_columns = df.columns[df.columns.duplicated()]
  #df.drop(columns=['id'], inplace=True)
  df = df.loc[:, ~df.columns.duplicated()]



  # Flatten nested lists in DataFrame
  def flatten_nested_lists(df):
      for col in df.columns:
          df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)
      return df

  df = flatten_nested_lists(df)

  def flatten_nested_dicts(df):
      for col in df.columns:
          if df[col].apply(lambda x: isinstance(x, dict)).all():
              df[col] = df[col].apply(lambda x: list(x.values())[0])
      return df

  df = flatten_nested_dicts(df)

  # Define preprocessing steps for numerical and categorical features
  numerical_transformer = Pipeline(steps=[
      ('imputer', SimpleImputer(strategy='mean')),  
      ('scaler', StandardScaler())
  ])

  categorical_transformer = Pipeline(steps=[
      ('imputer', SimpleImputer(strategy='most_frequent')),  
      ('onehot', OneHotEncoder(handle_unknown='ignore'))
  ])

  # Define which columns are numerical and categorical
  numerical_features = df.select_dtypes(include='number').columns
  categorical_features = df.select_dtypes(include='object').columns

  # Combine preprocessing steps
  preprocessor = ColumnTransformer(
      transformers=[
          ('num', numerical_transformer, numerical_features),
          ('cat', categorical_transformer, categorical_features)
      ])

  # Fit and transform the data
  processed_data = preprocessor.fit_transform(df)

  # Convert the processed data back to a DataFrame
  processed_df = pd.DataFrame(processed_data)

  # Filling missing values for numerical features with the mean
  numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
  df[numerical_cols] = df[numerical_cols].apply(lambda x: x.fillna(x.mean()))

  # For categorical features, fill missing values with the mode (most common value)
  categorical_cols = df.select_dtypes(include=['object']).columns
  df[categorical_cols] = df[categorical_cols].apply(lambda x: x.fillna(x.mode().iloc[0]))

  # Define a threshold for rare categories
  threshold = 0.01  # Categories with less than 1% frequency will be combined

  # Combine rare categories for categoryTypeName
  category_type_counts = df['categoryTypeName'].value_counts(normalize=True)
  rare_category_types = category_type_counts[category_type_counts < threshold].index
  df['categoryTypeName'] = df['categoryTypeName'].apply(lambda x: 'Other' if x in rare_category_types else x)

  # Combine rare categories for estateTypeName
  estate_type_counts = df['estateTypeName'].value_counts(normalize=True)
  rare_estate_types = estate_type_counts[estate_type_counts < threshold].index
  df['estateTypeName'] = df['estateTypeName'].apply(lambda x: 'Other' if x in rare_estate_types else x)

  df = pd.get_dummies(df, columns=['categoryTypeName', 'estateTypeName'], drop_first=False)

  df['build_age'] = df['build_age'].apply(lambda x: int(re.findall('\d+', x)[0]) if pd.notnull(x) else x)

  # Function to convert room_count like "4+1" into an integer by summing the parts
  def convert_room_count_to_int(room_count):
      if pd.isnull(room_count):
          return None  # Handle missing values
      parts = room_count.split('+')
      try:
          # Convert each part to integer and sum them
          return sum(int(part) for part in parts)
      except ValueError:
          # Handle edge cases where conversion to integer might fail
          return None

  df['room_count'] = df['room_count'].apply(convert_room_count_to_int)



  usd_try.update_usd_data()

  # Load your USD rates data
  usd_rates_df = pd.read_csv('usd_try_rates.csv')

  # Ensure the 'Date' column is in datetime format, specifying utc=True
  usd_rates_df['Date'] = pd.to_datetime(usd_rates_df['Date'], errors='coerce', utc=True)

  # Drop rows with NaT in the 'Date' column
  usd_rates_df = usd_rates_df.dropna(subset=['Date'])


  # Iterate through your main DataFrame (df)
  for index, row in df.iterrows():
      # Check if 'is_active' exists or is missing (NaN), if missing, fallback to 'created_at'
      if pd.isna(row.get('is_active', None)) or not row['is_active']:
          # If 'is_active' is missing or False, fallback to using 'created_at' to determine the rate
          #print(f"Warning: 'is_active' is missing or False, using 'created_at' for row {index}")
          
          # Check if 'ilan_bitis' exists and is valid
          if pd.isna(row.get('ilan_bitis', None)):  # Check if 'ilan_bitis' is missing or NaN
              # Fallback to 'created_at' if 'ilan_bitis' is not available
              #print(f"Warning: 'ilan_bitis' is missing, using 'created_at' instead for row {index}")
              ilan_bitis_date = pd.to_datetime(row['created_at'])
          else:
              # Use 'ilan_bitis' if it exists
              ilan_bitis_date = pd.to_datetime(row['ilan_bitis'])

          
          # Convert ilan_bitis_date to UTC for comparison
          ilan_bitis_date = ilan_bitis_date.tz_localize('UTC')

          # Find the closest date to ilan_bitis_date
          closest_index = (usd_rates_df['Date'] - ilan_bitis_date).abs().idxmin()
          closest_rate = usd_rates_df.at[closest_index, 'USD/TRY']
          latest_rate = closest_rate

      else:
          # If 'is_active' exists and is True, use the latest rate
          latest_rate = usd_rates_df.iloc[-1]['USD/TRY']

      # Calculate usd_price
      usd_price = row['price'] / latest_rate
      df.at[index, 'usd_price'] = usd_price

  # Check if 'ilan_bitis' exists in the DataFrame
  if 'ilan_bitis' in df.columns:
      df['ilan_bitis'] = pd.to_datetime(df['ilan_bitis'], errors='coerce')  # Coerce invalid values to NaT

  # Ensure that 'created_at' is in datetime format
  df['created_at'] = pd.to_datetime(df['created_at'])

  # Create a DataFrame to hold the mean prices by date
  date_range = pd.date_range(start=df['created_at'].min(), end=pd.Timestamp.now())
  mean_price_by_date = pd.DataFrame(index=date_range, columns=['mean_price'])

  # Calculate active ads for each date
  for date in date_range:
      if 'ilan_bitis' in df.columns:
          active_ads = df[(df['created_at'] <= date) & (df['ilan_bitis'] >= date)]
      else:
          active_ads = df[df['created_at'] <= date]  # If 'ilan_bitis' is missing, consider only 'created_at'

      # If there are active ads, calculate the mean price for that date
      if not active_ads.empty:
          mean_price_by_date.at[date, 'mean_price'] = active_ads['usd_price'].mean()
      else:
          mean_price_by_date.at[date, 'mean_price'] = None  # Handle case with no active ads

  # Forward fill to ensure all future dates inherit the last available mean price
  mean_price_by_date['mean_price'].ffill(inplace=True)

  # Check the last date and fill with the latest mean price if not present
  if pd.Timestamp.now() not in mean_price_by_date.index:
      mean_price_by_date.loc[pd.Timestamp.now()] = mean_price_by_date['mean_price'].iloc[-1]

  # Calculate the total mean price if both 'ilan_bitis' and 'is_active' are missing
  total_mean_price = df['usd_price'].mean()

  # Map the moving_estate_index back to the original DataFrame
  df['moving_estate_index'] = df.apply(
      lambda row: mean_price_by_date['mean_price'].loc[row['ilan_bitis']] if 'ilan_bitis' in row and pd.notna(row['ilan_bitis']) and 'is_active' in row else total_mean_price,
      axis=1
  )

  # USD PRICE / MEAN USD PRICE 
  df['usd_price/index'] = df['usd_price'] / df['moving_estate_index']
  df['usd_price/index'].fillna(0, inplace=True)

  df['usd_price/index'] = np.log(df['usd_price/index'])


  # Function to extract number from strings for 'floor_number' and 'floor_count'
  def extract_number_from_string(s):
      # If the string is 'ground floor' or similar, return 0
      if pd.isnull(s):
          return None
      if 'ground' in s.lower():
          return 0
      # Extract number from string
      nums = re.findall('\d+', s)
      return int(nums[0]) if nums else None

  # Apply the function to the 'floor_number' and 'floor_count' columns
  df['floor_number'] = df['floor_number'].apply(extract_number_from_string)
  df['floor_count'] = df['floor_count'].apply(extract_number_from_string)

  df['floor_count'] = df['floor_count'].fillna(df['floor_count'].median())


  # Define a threshold for rare categories
  threshold = 0.01  # Categories with less than 1% frequency will be combined

  # Combine rare heating types
  heating_type_counts = df['heating_type'].value_counts(normalize=True)
  rare_heating_types = heating_type_counts[heating_type_counts < threshold].index
  df['heating_type'] = df['heating_type'].apply(lambda x: 'Other' if x in rare_heating_types else x)

  # Combine rare build statuses similarly
  build_status_counts = df['build_status'].value_counts(normalize=True)
  rare_build_statuses = build_status_counts[build_status_counts < threshold].index
  df['build_status'] = df['build_status'].apply(lambda x: 'Other' if x in rare_build_statuses else x)

  # Reapply one-hot encoding
  df = pd.get_dummies(df, columns=['heating_type', 'build_status'], drop_first=False)


  numerical_features = df.select_dtypes(include='number').columns

  # Adding a few more features
  ## Description Length
  df['description_length'] = df['description'].apply(len)

  ## Unique Amenities in Description
  amenities = ['havuzlu', 'balkon', 'teras', 'asansörlü', 'güvenlik', 'eşyalı']
  for amenity in amenities:
      df[f'amenity_{amenity}'] = df['description'].apply(lambda x: 1 if amenity in x.lower() else 0)

  ## Province Score - to be done

  ## Listing age days
  df['listing_age_days'] = (pd.to_datetime('today') - pd.to_datetime(df['created_at'])).dt.days
  df['days_since_update'] = (pd.to_datetime('today') - pd.to_datetime(df['updated_at'])).dt.days

  df['is_furnished'] = df['furniture_status'].apply(lambda x: 1 if x == 'Furnished' else 0)
  df['is_mortgageable'] = df['mortgage_status'].apply(lambda x: 1 if x == 'Yes' else 0)

  df['bath_count'] = pd.to_numeric(df['bath_count'], errors='coerce').fillna(0)
  df['balcony_count'] = pd.to_numeric(df['balcony_count'], errors='coerce').fillna(0)

  df['credit_suitable'] = df['suitability_for_credit'].apply(lambda x: 1 if x == 'Yes' else 0)
  df['investment_suitable'] = df['suitability_for_investor'].apply(lambda x: 1 if x == 'Yes' else 0)

  df['image_count'] = df['images'].apply(lambda x: len(x.split(',')) if pd.notnull(x) else 0)


  # 1. Room to Bathroom Ratio
  # Calculate the ratio of rooms to bathrooms
  df['room_to_bathroom_ratio'] = df.apply(lambda row: row['room_count'] / row['bath_count'] if row['bath_count'] > 0 else np.nan, axis=1)

  # 2. Floor Ratio
  # Ratio of floor number to total floor count
  df['floor_ratio'] = df.apply(lambda row: row['floor_number'] / row['floor_count'] if row['floor_count'] > 0 else np.nan, axis=1)

  # 3. Amenity Score
  # Composite amenity score based on selected amenities
  df['amenity_score'] = df[['amenity_havuzlu', 'amenity_balkon', 'amenity_güvenlik']].sum(axis=1)

  # 4. Age to Floor Ratio
  # Ratio of building age to the total number of floors
  df['age_to_floor_ratio'] = df.apply(lambda row: row['build_age'] / row['floor_count'] if row['floor_count'] > 0 else np.nan, axis=1)

  # 6. Net to Gross Area Ratio
  # Calculate net to gross area ratio
  df['net_to_gross_ratio'] = df.apply(lambda row: row['net_square'] / row['gross_square'] if row['gross_square'] > 0 else np.nan, axis=1)

  # 7. Average Room Size
  # Average room size derived from net square footage
  df['average_room_size'] = df.apply(lambda row: row['net_square'] / row['room_count'] if row['room_count'] > 0 else np.nan, axis=1)

  # 8. Unique Word Count
  # Count the unique words in the description
  df['unique_word_count'] = df['description'].apply(lambda desc: len(set(desc.split())) if isinstance(desc, str) else 0)

  # 9. Positive Adjective Count
  # Define a set of positive adjectives for the count, tailored for Turkish real estate listings
  positive_adjectives = [
      'lüks', 'şahane', 'geniş', 'yeni','yatırım','yepyeni', 'ulaşımı kolay', 'yatırıma uygun', 'manzaralı', 'bakımlı',
      'güvenlikli', 'asansörlü', 'çift banyolu', 'balkonlu', 'teraslı', 'havuzlu', 'modern', 'rahat', 'konforlu',
      'güzel', 'temiz', 'özel', 'gözde', 'şık', 'kaliteli', 'sıcak', 'huzurlu'
  ]

  # Count the occurrences of positive adjectives in the description
  df['positive_adjective_count'] = df['description'].apply(
      lambda desc: sum(1 for word in desc.lower().split() if word in positive_adjectives) if isinstance(desc, str) else 0
  )


  # New feature ideas
  ####### new feature 1 -
  df['title_length'] = df['title'].apply(lambda x: len(x.split()))

  ####### new feature 2 -
  keywords = ['lüks', 'deniz manzaralı','yakın','temiz', 'sıfır', 'fırsat', 'yatırımlık', 'acil', 'yatırım', 'yeni', 'modern', 'kaçmaz']

  # Count how many keywords appear in each title
  df['title_keyword_count'] = df['title'].apply(lambda x: sum(kw in x.lower() for kw in keywords))

  df['number_in_title'] = df['title'].apply(lambda x: 1 if re.search(r'\d', x) else 0)

  # Set up Turkish stopwords
  turkish_stopwords = stopwords.words('turkish')

  # Function to preprocess text: tokenize, remove non-alphabetic words, stopwords
  def preprocess_text(text):
      # Tokenize by word
      tokens = word_tokenize(text, language='turkish')
      # Remove non-alphabetic words and stopwords
      tokens = [word.lower() for word in tokens if word.isalpha() and word.lower() not in turkish_stopwords]
      return tokens

  # Apply preprocessing to each document in the property description column
  df['tokens'] = df['description'].fillna('').apply(preprocess_text)

  # Flatten the list of tokens and compute frequency distribution
  all_tokens = [token for sublist in df['tokens'] for token in sublist]
  fdist = FreqDist(all_tokens)

  # Get the 25 most common words
  most_common_words = fdist.most_common(25)

  exclude_features = {'previousValueValid', 'quickInfos', 'suitability_for_investor', 'deed_status', 'square_of_room', 'loan_price', 'subscription_price', 'square_of_balcony', 'balcony_condition', 'parcel_of_land', 'trade', 'opportunity', 'ground_survey', 'category', 'flat_per_floor', 'images', 'tokens', 'square_of_wc', 'balcony_type', 'wc_count', 'suitability_for_credit', 'location', 'tlPrice', 'alternativeValue', 'furniture_status', 'build_type', 'video_navigable', 'trendType', 'previousCurrency', 'currency', 'block_of_buildings', 'trade_type', 'in_site', 'sheet', 'locationSummary', 'tradeTypeName', 'usability', 'updated_at', 'show_unit_price', 'square_of_bath', 'mortgage_status'}

  # Filter out unwanted features
  df = df.drop(columns=[col for col in exclude_features if col in df.columns])


  # Keywords with and without Turkish characters
  keywords_to_filter = [
      'prefabrik', 'kira', 'kiralık', 'kiralik', 'gecekondu', 'devirli', 'devir', 'devren',
      'konteyner', 'kabin', 'masrafı var', 'masrafi var', 'tamire ihtiyacı var', 'tamire ihtiyaci var',
      'tadilata ihtiyacı var', 'tadilata ihtiyaci var', 'tamire ve tadilata ihtiyacı var',
      'tamire ve tadilata ihtiyaci var', 'çatı katı', 'çatı kat', 'cati kati', 'çatı kat', 'ihtiyacı var',
      'ihtiyaci var', 'bakım gereklidir', 'bakim gereklidir', 'gece kondu', 'konteynır', 'bodrum',
      'konteynir', 'kaba sıvalı', 'kaba sivali', 'ahşap ev', 'ahsap ev', 'tamamlanmamış', 'tamamlanmamis', 'RESİMLER TEMSİLİDİR',
      'kaba inşaat', 'KABA İNŞAAT', 'tiny house', 'tinyhouse', 'kara sıva', 'kaba insaat'
  ]

  # Remove rows where the title or description contains any of the specified keywords
  df = df[~df['title'].str.contains('|'.join(keywords_to_filter), case=False, na=False) &
                  ~df['description'].str.contains('|'.join(keywords_to_filter), case=False, na=False)]

  # Remove rows where 'net_square' is less than x or is NaN
  df = df[df['net_square'] >= 45].copy()
  df = df[df['net_square'] <= 600].copy()

  # Remove rows where 'estateTypeName_Other' is 1
  df = df[df['estateTypeName_Other'] != 1].copy()

  # price too high too low eliminated
  df = df[(df['price'] > 750_000) & (df['price'] <= 100_000_000)].copy()













  # Load the sentiment analysis model
  tokenizer = AutoTokenizer.from_pretrained("savasy/bert-base-turkish-sentiment-cased")
  model = AutoModelForSequenceClassification.from_pretrained("savasy/bert-base-turkish-sentiment-cased")
  sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, framework='pt')

  def preprocess_text(text):
      tokens = nltk.word_tokenize(text, language='turkish')
      tokens = [word for word in tokens if word.isalpha() and word.lower() not in turkish_stopwords]
      return ' '.join(tokens)

  def batch_sentiment_analysis(texts, batch_size=64):
      results = []
      for i in range(0, len(texts), batch_size):
          batch_texts = texts[i:i + batch_size]
          batch_encoded = tokenizer(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
          with torch.no_grad():
              outputs = model(**batch_encoded)
          predictions = torch.argmax(outputs.logits, dim=1)
          results.extend(predictions.numpy())
      return results

  def extract_features(df):
      df['description_preprocessed'] = df['description'].fillna('').apply(preprocess_text)
      # df['description_sentiment'] = batch_sentiment_analysis(df['description_preprocessed'].tolist())
      keywords = ['kelepir', 'acil', 'yürüme', 'yakin', 'uygun', 'metro', 'ferah']
      for keyword in keywords:
          df[f'keyword_{keyword}'] = df['description_preprocessed'].apply(lambda x: 1 if keyword in x.lower() else 0)
      return df


  df = extract_features(df)

  # Initialize and apply TF-IDF Vectorizer
  tfidf_vectorizer = TfidfVectorizer(max_features=7, ngram_range=(1, 2))
  tfidf_matrix = tfidf_vectorizer.fit_transform(df['description_preprocessed'])
  tfidf_feature_names = tfidf_vectorizer.get_feature_names_out()


  # Check if TF-IDF features are already present in DataFrame
  if not set(tfidf_feature_names).issubset(df.columns):
      tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=tfidf_feature_names)
      df = pd.concat([df.reset_index(drop=True), tfidf_df], axis=1)

  # Ensure the features list includes both original and TF-IDF features
  filtered_features = [
      #'location_cluster',
      'average_household_size',
      'population_density',
      'population_count_2021',
      'population_growth_rate',
      'social_assistance_yes',
      'title_length', 'health_service_distance',
      'bath_count', 'description_length', 'listing_age_days', 'days_since_update',
      'lat', 'lon', 'distance_to_sea', 'rail_distance', 'room_to_bathroom_ratio', 'floor_ratio',
      'age_to_floor_ratio', 'net_to_gross_ratio', 'average_room_size', 'unique_word_count',
      'net_square', 'gross_square', 'room_count', 'build_age', 'floor_number', 'floor_count',
      'estateTypeName_bina', 'estateTypeName_daire', 'estateTypeName_villa',
      'heating_type_Kombi Doğalgaz', 'heating_type_Merkezi (Pay Ölçer)',
      'Eczane_distance',  # Distance to nearest pharmacy
      'Diş Hekimi_distance',  # Distance to nearest dentist
      'Özel Ağız ve Diş Sağlığı Merkezleri_distance',  # Distance to nearest private dental health center
      'Doktor/Muayenehane_distance',  # Distance to nearest general practitioner or private clinic
      'Aile Sağlığı Merkezi_distance',  # Distance to nearest family health center
      'Özel Hastane_distance',  # Distance to nearest private hospital
      'Devlet Hastanesi_distance',  # Distance to nearest state hospital
      'Şehir Hastanesi_distance',  # Distance to nearest city hospital
      'district_name_encoded', 'locality_name_encoded', 'town_name_encoded', 'distance_to_park', 'distance_to_mall',
  ] #+ list(tfidf_feature_names)


  """
  # Harun'un feature'ları:
  filtered_features = [
      'ilanda_kalis_suresi',
      'gross_square',
      'socio_demographic_score',
      'average_household_size',
      'bath_count',
      'estateTypeName_daire',
      'estateTypeName_villa',
      'distance_to_mall',
      'heating_type_Kombi Doğalgaz',
      'net_square',
      'age_to_floor_ratio',
      'Devlet Hastanesi_distance',
      'lat',
      'lon',
      'distance_to_sea',
      'rail_distance',
      'Aile Sağlığı Merkezi_distance',
      'average_room_size',
      'net_to_gross_ratio',
      'Şehir Hastanesi_distance',
      'Özel Hastane_distance',
      'locality_name_encoded',
      'floor_count',
      'distance_to_park',
      'Doktor/Muayenehane_distance',
      'build_age'
  ]
  """

  # Remove duplicates from the feature list
  filtered_features = list(set(filtered_features))

  # Filter the DataFrame for outliers

  Q1 = df['usd_price/index'].quantile(0.15)
  Q3 = df['usd_price/index'].quantile(0.85)
  IQR = Q3 - Q1
  lower_bound = Q1 - 1.5 * IQR
  upper_bound = Q3 + 1.5 * IQR

  df_filtered = df[(df['usd_price/index'] >= lower_bound) & (df['usd_price/index'] <= upper_bound)]

  #df_filtered = df.copy()
  # Recalculate the numerical features from the filtered DataFrame
  X_numerical_filtered = df_filtered[filtered_features].fillna(df_filtered[filtered_features].median())

  # Scale numerical features
  scaler = StandardScaler()
  X_numerical_scaled_filtered = scaler.fit_transform(X_numerical_filtered)

  X_filtered = X_numerical_scaled_filtered

  # Labels
  y_filtered = df_filtered['usd_price/index']

  # iterative_outlier_removal_with_test_metrics(X_filtered, y_filtered, max_iters=3, threshold=2)

  all_feature_names = filtered_features

  # Splitting the data
  X_train_filtered, X_test_filtered, y_train_filtered, y_test_filtered = train_test_split(X_filtered, y_filtered, test_size=0.2, random_state=42)

  def train_evaluate_model(model, X_train, X_test, y_train, y_test, feature_names, df_filtered):
      print("Training model...")
      model.fit(X_train, y_train)
      y_pred = model.predict(X_test)

      mse = mean_squared_error(y_test, y_pred)
      rmse = np.sqrt(mse)
      r2 = r2_score(y_test, y_pred)
      print(f'Model: {model.__class__.__name__}')
      print(f'MSE: {mse}')
      print(f'RMSE: {rmse}')
      print(f'R² score: {r2}')

      # Identify listings where the actual price is less than predicted (good value)
      results_df = pd.DataFrame({
          'actual_price': y_test.tolist(),
          'predicted_price': y_pred,
          'price_difference': y_pred - y_test.tolist(),
          'percentage_difference': ((y_pred - y_test.tolist()) / y_test.tolist()) * 100
      }, index=y_test.index)

      # Filter out extreme outliers where percentage difference is over 1000%
      filtered_good_value_listings = results_df[
          (results_df['percentage_difference'] > 0) &
          (results_df['percentage_difference'] < 1000)
      ]

      # Sort by percentage difference to find the top listings
      top_20_value_listings = filtered_good_value_listings.sort_values(
          by='percentage_difference', ascending=False
      ).head(20)

      # **Add the URL column to the top 20 listings**
      # Fetch the URLs for the top 20 listings from df_filtered
      top_20_urls = df_filtered.loc[top_20_value_listings.index, 'url'].copy()

      # **Modify the URLs by replacing 'imaj.emlakjet.com' with 'www.emlakjet.com'**
      top_20_urls_modified = top_20_urls.apply(
          lambda x: x.replace('https://imaj.emlakjet.com', 'https://www.emlakjet.com') if isinstance(x, str) else x
      )

      # Add the modified URLs to the top 20 listings DataFrame
      top_20_value_listings = top_20_value_listings.copy()
      top_20_value_listings['url'] = top_20_urls_modified.values

      # However, to double-check, we can assert that
      # assert df_filtered.loc[top_20_value_listings.index, 'is_active'].all(), "Some top listings are not active."

      # Extract IDs from modified URLs
      top_20_ids = top_20_urls_modified.apply(lambda x: re.findall(r'(\d+)(?:/)?$', x)[0] if isinstance(x, str) else None)

      # **Print and save the IDs and URLs to a TXT file**
      top_20_output = pd.DataFrame({
          'id': top_20_ids,
          'url': top_20_urls_modified
      })

      # **Save to TXT File**
      # Define the output file name
      output_file = 'top_listings_ids_and_urls.txt'

      # Open the file in write mode
      with open(output_file, 'w', encoding='utf-8') as file:
          # Write a header
          file.write("Top 20 Best Valued Listings:\n")
          file.write("="*40 + "\n\n")
          # Iterate through each row and write the ID and URL
          for index, row in top_20_output.iterrows():
              file.write(f"ID: {row['id']}\nURL: {row['url']}\n\n")


  feature_names = all_feature_names 
  model = RandomForestRegressor(bootstrap=False, max_depth=30, max_features='sqrt', min_samples_leaf=2, min_samples_split=2, n_estimators=300, random_state=42)
  train_evaluate_model(model, X_train_filtered, X_test_filtered, y_train_filtered, y_test_filtered, feature_names, df_filtered)



if __name__ == "__main__":
    run_modeling()