import pandas as pd

try:
    df_ant = pd.read_excel('anteriores.xlsx')
    print("--- anteriores.xlsx ---")
    print(df_ant.head())
    print(df_ant.columns)
except Exception as e:
    print(f"Error reading anteriores.xlsx: {e}")

try:
    df_atu = pd.read_excel('atuais.xlsx')
    print("\n--- atuais.xlsx ---")
    print(df_atu.head())
    print(df_atu.columns)
except Exception as e:
    print(f"Error reading atuais.xlsx: {e}")
