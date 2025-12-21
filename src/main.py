from generate_csv import *
from parallel_analysis import *

def main():
    run_benchmark_analysis()

def run_benchmark_analysis():
    path = '../data/temperature_data.csv'
    generate_csv(path)
    benchmark(path)

if __name__ == "__main__":
    main()