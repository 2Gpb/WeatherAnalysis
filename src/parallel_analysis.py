from analysis import *
import multiprocessing as mp
import time


def process_city(df_city):
    df_city = df_city.sort_values("timestamp").reset_index(drop=True)
    df_city = count_rolling_mean(df_city)
    df_city = mean_temperature_and_standard_deviation(df_city)
    df_city = find_anomalies(df_city)
    return df_city

def analysis_pipeline_parallel(file_path, processes=None):
    df = read_data(file_path)
    city_dfs = [g.copy() for _, g in df.groupby("city", sort=False)]

    with mp.Pool(processes=processes) as pool:
        parts = pool.map(process_city, city_dfs)

    return pd.concat(parts, ignore_index=True)

def benchmark(file_path) -> None:
    t0 = time.perf_counter()
    _ = analysis_pipeline(file_path)
    t1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = analysis_pipeline_parallel(file_path)
    t2 = time.perf_counter() - t0

    print(f"Последовательно: {t1:.4f}s")
    print(f"Параллельно: {t2:.4f}s")
    print(f"Ускорение: {t1 / t2:.2f}x")