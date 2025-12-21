import pandas as pd


def read_data(file_path):
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(["city", "timestamp"])
    df = df.reset_index(drop=True)
    return df

def count_rolling_mean(df):
    df['rolling_mean'] = df.groupby('city')['temperature'].rolling(window=30).mean().reset_index(drop=True)
    return df

def mean_temperature_and_standard_deviation(df):
    df_stats = df.groupby(['city', 'season'])['temperature'].agg(["mean", "std"])
    return df.merge(df_stats, on=["city", "season"], how="left", validate="many_to_one")

def find_anomalies(df):
    df['lower'] = df['mean'] - 2 * df['std']
    df['upper'] = df['mean'] + 2 * df['std']

    df['is_anomaly'] = (df['temperature'] > df['upper']) | (df['temperature'] < df['lower'])
    df = df.drop(columns=['lower', 'upper'])
    return df

def is_anomalies(df, temp, season, city):
    row = df.loc[(df['city'] == city) & (df['season'] == season), ["mean", "std"]]

    mean = float(row["mean"].iloc[0])
    std = float(row["std"].iloc[0])

    lower = mean - 2 * std
    upper = mean + 2 * std

    return (temp < lower) or (temp > upper)


def analysis_pipeline(df):
    df = count_rolling_mean(df)
    df = mean_temperature_and_standard_deviation(df)
    df = find_anomalies(df)
    return df
