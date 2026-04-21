import pandas as pd 
df = pd.read_csv("cicids2017_cleaned.csv")
print(df.head())
print(df.isnull().sum())
print(df.describe())
X = df.iloc[:,:-1].values
y = df.iloc[:,-1].values
print(X)
print(y)
