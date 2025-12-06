#!/usr/bin/env python3
"""
corr_bayes_rf.py - Расширенный байесовский корреляционный анализ

Автоматизированный корреляционный анализ региональной статистики РФ
с возможностью мульти-регионального анализа.

Запуск:
$ python corr_bayes_rf.py --file data.xlsx [--region "Новосибирская область"] 
                          [--year 2020] [--top 30] [--saveall]

Опции:
--file      путь к .xlsx (обязательно)
--region    фильтр по названию региона (regex, необязателен)
--year      фильтр по году (int или 'all')
--top       сколько сильнейших корреляций показать в консоли
--saveall   сохранить анализ для всех регионов в Excel
"""

import argparse
import io
import re
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.simplefilter("ignore")

def parse_args():
    p = argparse.ArgumentParser(description="Байесовский корреляционный анализ")
    p.add_argument("--file", required=True, help="Путь к xlsx-файлу")
    p.add_argument("--region", default=".*", help="Регион-regex (по умолчанию все)")
    p.add_argument("--year", default="all", help="'all' или конкретный год")
    p.add_argument("--top", type=int, default=30, help="Сколько топ-корреляций вывести")
    p.add_argument("--saveall", action="store_true", help="Сохранить корреляции по всем регионам в Excel")
    return p.parse_args()

def load_data(xl_path, region_regex, year_filter):
    df = pd.read_excel(xl_path, engine="openpyxl")
    
    if "Тип" in df.columns:
        df = df.loc[~df["Тип"].eq("Страна")]
        df = df.drop(columns=["Тип"])
    
    if region_regex != ".*":
        mask = df["Регион"].str.contains(region_regex, flags=re.I, regex=True, na=False)
        df = df[mask]
    
    if year_filter != "all":
        df = df[df["Год"] == int(year_filter)]
    
    df = df.drop_duplicates(subset=['Регион', 'Год'], keep='first')
    df = df.reset_index(drop=True)
    
    if len(df) < 2:
        available_years = sorted(df["Год"].unique()) if len(df) > 0 else []
        regions = df["Регион"].unique() if len(df) > 0 else []
        
        error_msg = f"Недостаточно данных для анализа. Найдено {len(df)} наблюдений, необходимо минимум 2 для расчета корреляций."
        if len(regions) > 0:
            error_msg += f"\nДоступные регионы: {', '.join(regions)}"
        if len(available_years) > 0:
            error_msg += f"\nДоступные годы: {min(available_years)}-{max(available_years)}"
        error_msg += "\nПопробуйте изменить фильтры --region или --year."
        
        raise ValueError(error_msg)
    
    thresh = int(len(df) * 0.30)
    df = df.dropna(axis=1, thresh=thresh)
    
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    service_cols = ['Год', 'Регион']
    num_cols = [col for col in num_cols if col not in service_cols]

    constant_cols = []
    for col in num_cols:
        if col in df.columns and df[col].nunique() <= 1:
            constant_cols.append(col)
    
    if constant_cols:
        print(f"Удалены константные столбцы: {constant_cols}")
        num_cols = [col for col in num_cols if col not in constant_cols]
    
    return df[num_cols + ["Регион", "Год"]], num_cols

def pirson_corr(x, y):
    """
    Корреляция Пирсона
    """
    x_array = np.array(x)
    y_array = np.array(y)
    
    valid_mask = ~(np.isnan(x_array) | np.isnan(y_array))
    x_valid = x_array[valid_mask]
    y_valid = y_array[valid_mask]
    
    n = len(x_valid)
    if n < 2:
        return np.nan
    
    try:
        x_var = float(x_valid.var())
        y_var = float(y_valid.var())
        if x_var == 0 or y_var == 0:
            return np.nan
    except (TypeError, ValueError):
        return np.nan
    
    try:
        r = np.corrcoef(x_valid, y_valid)[0, 1]
        if np.isnan(r):
            return np.nan
        return r * (1 - ((1 - r**2) / (n - 2)))
    except:
        return np.nan

def make_corr_matrix(df, cols):
    """
    Создание корреляционной матрицы с улучшенной обработкой ошибок
    """
    n_vars = len(cols)
    mat = pd.DataFrame(index=cols, columns=cols, dtype=float)
    
    print(f"Вычисляем корреляции для {n_vars} переменных...")
    
    for i, col1 in enumerate(cols):
        for j, col2 in enumerate(cols):
            if i <= j:
                try:
                    r_b = pirson_corr(df[col1], df[col2])
                    mat.loc[col1, col2] = r_b
                    mat.loc[col2, col1] = r_b
                except Exception as e:
                    print(f"Ошибка при вычислении корреляции {col1} - {col2}: {e}")
                    mat.loc[col1, col2] = np.nan
                    mat.loc[col2, col1] = np.nan
    
    return mat

def save_heatmap(mat, out_png="corr_heatmap", region=""):
    """
    Создание тепловой карты корреляций с увеличенным размером
    """
    plt.figure(figsize=(24, 20))
    
    clean_mat = mat.dropna(axis=0, how='all').dropna(axis=1, how='all')
    
    if clean_mat.empty:
        print("Нет данных для создания тепловой карты")
        return
    
    sns.heatmap(clean_mat, 
                cmap="coolwarm", 
                vmin=-1, vmax=1, 
                square=True,
                linewidths=0.1, 
                cbar_kws={"label": "r_bayes"},
                xticklabels=True, 
                yticklabels=True)
    
    plt.title("Корреляция региональных показателей", fontsize=16)
    
    plt.xticks(rotation=90, ha='center', fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    
    plt.tight_layout(pad=2.0)
    
    plt.savefig(f"{out_png}_{region}.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Тепловая карта сохранена: {out_png}")

def save_all_regions_analysis(xl_path, year_filter="all"):
    """
    Создает корреляционные матрицы для всех регионов и сохраняет в Excel
    ИСПРАВЛЕНИЕ: Используем точно такую же логику как в load_data()
    """
    print("Загрузка данных для мульти-регионального анализа...")
    
    df_all = pd.read_excel(xl_path, engine="openpyxl")
    
    if "Тип" in df_all.columns:
        df_all = df_all.loc[~df_all["Тип"].eq("Страна")]
        df_all = df_all.drop(columns=["Тип"])
    
    if year_filter != "all":
        df_all = df_all[df_all["Год"] == int(year_filter)]
    
    df_all = df_all.drop_duplicates(subset=['Регион', 'Год'], keep='first')
    df_all = df_all.reset_index(drop=True)

    regions = sorted(df_all['Регион'].unique())
    print(f"Найдено {len(regions)} регионов для анализа")

    output_file = f"corr_all_regions_{year_filter}.xlsx"
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for region in regions:
            print(f"Обрабатываем регион: {region}")

            df_region = df_all[df_all['Регион'] == region].copy()
            
            if len(df_region) < 2:
                print(f"  Недостаточно данных для {region}: {len(df_region)} наблюдений")
                continue

            thresh = int(len(df_region) * 0.30)
            df_region = df_region.dropna(axis=1, thresh=thresh)
            
            num_cols = df_region.select_dtypes(include=[np.number]).columns.tolist()
            
            service_cols = ['Год', 'Регион']
            num_cols = [col for col in num_cols if col not in service_cols]
            
            constant_cols = []
            for col in num_cols:
                if col in df_region.columns and df_region[col].nunique() <= 1:
                    constant_cols.append(col)
            
            if constant_cols:
                print(f"  Удалены константные столбцы для {region}: {constant_cols}")
                num_cols = [col for col in num_cols if col not in constant_cols]
            
            if len(num_cols) < 2:
                print(f"  Недостаточно переменных для {region}: {len(num_cols)}")
                continue
            
            corr_mat = make_corr_matrix(df_region, num_cols)
            
            corr_mat = corr_mat.dropna(axis=0, how='all').dropna(axis=1, how='all')
            
            if corr_mat.empty:
                print(f"  Нет корреляций для {region}")
                continue
            
            sheet_name = region[:31] if len(region) > 31 else region
            
            info_df = pd.DataFrame({
                'Параметр': ['Количество наблюдений', 'Количество переменных', 'Период'],
                'Значение': [len(df_region), len(num_cols), 
                           f"{df_region['Год'].min()}-{df_region['Год'].max()}"]
            })
            
            info_df.to_excel(writer, sheet_name=sheet_name, 
                           startrow=0, startcol=0, index=False)
            
            corr_mat.to_excel(writer, sheet_name=sheet_name, 
                            startrow=len(info_df)+2, startcol=0, 
                            float_format="%.3f")
            
            print(f"  Сохранено: {len(corr_mat)} переменных, {len(df_region)} наблюдений")
    
    print(f"Мульти-региональный анализ сохранен: {output_file}")
    return output_file

def main():
    args = parse_args()
    
    if args.saveall:
        try:
            output_file = save_all_regions_analysis(args.file, args.year)
            print(f"Успешно создан файл: {output_file}")
        except Exception as e:
            print(f"Ошибка при создании мульти-регионального анализа: {e}")
        return

    try:
        df, num_cols = load_data(args.file, args.region, args.year)
    except ValueError as e:
        print(f"Ошибка: {e}")
        return
    
    print(f"Загружено данных: {len(df)} наблюдений, {len(num_cols)} числовых переменных")
    
    if args.region != ".*":
        unique_regions = df['Регион'].unique()
        print(f"Регионы: {', '.join(unique_regions)}")
    
    if args.year != "all":
        print(f"Год: {args.year}")
    else:
        min_year = int(df['Год'].min())
        max_year = int(df['Год'].max())
        print(f"Годы: {min_year}-{max_year}")
    
    corr_mat = make_corr_matrix(df, num_cols)
    
    corr_mat = corr_mat.dropna(axis=0, how='all').dropna(axis=1, how='all')
    
    if corr_mat.empty:
        print("Не удалось рассчитать корреляции - недостаточно данных")
        return
    
    corr_mat.to_csv(f"corr_matrix_{args.region if args.region else ''}.csv", float_format="%.3f")
    save_heatmap(corr_mat, region=args.region if args.region else "")
    
    tril = corr_mat.where(np.tril(np.ones(corr_mat.shape), k=-1).astype(bool))
    pairs = (tril.stack()
             .dropna()
             .reindex_like(tril.stack().abs().sort_values(ascending=False)))
    
    print(f"\nТоп-{args.top} корреляций (|r_bayes|):")
    for (var1, var2), r in pairs.head(args.top).items():
        print(f"{var1:<55} ↔ {var2:<55} r_bayes={r:+.3f}")

if __name__ == "__main__":
    main()
