# data_utils.py
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

def load_raw_inmet_data() -> pd.DataFrame:
    """
    Lê todos os CSVs dentro de data/dados_20XX e concatena em um único DataFrame.
    Adapta separador/encoding se precisar.
    """
    all_dfs = []

    for year_dir in sorted(DATA_DIR.glob("dados_*")):
        year = year_dir.name.split("_")[1]  # "2020", "2021", ...
        for csv_path in sorted(year_dir.glob("*.csv")):
            print(f"Lendo {csv_path}...")
            df = pd.read_csv(
                csv_path,
                sep=";",           # mude para "," se seus CSVs forem separados por vírgula
                encoding="latin1", # ou "utf-8" dependendo da origem
            )
            df["ano"] = int(year)
            df["arquivo_origem"] = csv_path.name
            all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)
    return full_df
