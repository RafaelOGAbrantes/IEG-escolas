import pandas as pd
import os

def compare_spreadsheets(file_ant, file_atu, output_file='relatorio_diferencas.xlsx'):
    print(f"Loading files: {file_ant} and {file_atu}...")
    try:
        df_ant = pd.read_excel(file_ant)
        df_atu = pd.read_excel(file_atu)
        
        # Drop rows where 'Escola' is NaN
        df_ant = df_ant.dropna(subset=['Escola'])
        df_atu = df_atu.dropna(subset=['Escola'])
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    # Check for duplicates in 'Escola'
    if df_ant['Escola'].duplicated().any():
        print("WARNING: Duplicate 'Escola' found in previous file.")
        print(df_ant[df_ant['Escola'].duplicated()]['Escola'])
    
    if df_atu['Escola'].duplicated().any():
        print("WARNING: Duplicate 'Escola' found in current file.")
        print(df_atu[df_atu['Escola'].duplicated()]['Escola'])

    # Ensure 'Escola' is string and strip whitespace
    df_ant['Escola'] = df_ant['Escola'].astype(str).str.strip()
    df_atu['Escola'] = df_atu['Escola'].astype(str).str.strip()

    # Merge dataframes
    print("Merging dataframes...")
    # Suffixes: _ant (anterior), _atu (atual)
    merged = pd.merge(df_ant, df_atu, on='Escola', how='outer', suffixes=('_ant', '_atu'), indicator=True)

    differences = []

    for index, row in merged.iterrows():
        escola = row['Escola']
        
        # Check if school exists in both
        if row['_merge'] == 'left_only':
            differences.append({
                'Escola': escola,
                'inep': row.get('inep_ant', 'N/A'),
                'Coluna': 'Status',
                'Valor Anterior': 'Presente',
                'Valor Atual': 'Ausente'
            })
            continue
        elif row['_merge'] == 'right_only':
            differences.append({
                'Escola': escola,
                'inep': row.get('inep_atu', 'N/A'),
                'Coluna': 'Status',
                'Valor Anterior': 'Ausente',
                'Valor Atual': 'Presente'
            })
            continue

        # Compare columns for schools present in both
        # Get common columns (excluding 'Escola' and '_merge')
        # We need to map columns from original dfs to merged columns
        common_cols = [c for c in df_ant.columns if c in df_atu.columns and c != 'Escola']
        
        for col in common_cols:
            val_ant = row[f"{col}_ant"]
            val_atu = row[f"{col}_atu"]

            # Handle NaN comparison
            if pd.isna(val_ant) and pd.isna(val_atu):
                continue
            
            if val_ant != val_atu:
                differences.append({
                    'Escola': escola,
                    'inep': row.get('inep_atu', row.get('inep_ant', 'N/A')), # Try to get inep from current, then previous
                    'Coluna': col,
                    'Valor Anterior': val_ant,
                    'Valor Atual': val_atu
                })

    if differences:
        print(f"Found {len(differences)} differences.")
        df_diff = pd.DataFrame(differences)
        try:
            df_diff.to_excel(output_file, index=False)
            print(f"Report saved to {output_file}")
        except Exception as e:
            print(f"Error saving report: {e}")
    else:
        print("No differences found.")

if __name__ == "__main__":
    compare_spreadsheets('anteriores.xlsx', 'atuais.xlsx')
