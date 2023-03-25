import pandas as pd

ndvi_val = pd.read_csv('./data/ndvi_val.csv')['ndvi'].to_list()

validation_data = pd.read_csv('./data/validation_data.csv')

validation_data.insert(4, 'ndvi', ndvi_val)

validation_data.to_csv('./data/validation_data_ndvi.csv', index=False)
