#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interactive_3d_analysis.py - Интерактивный 3D-анализ корреляций на основе готовых данных

Веб-интерфейс для интерактивного анализа байесовских корреляций
на основе файла corr_all_regions_all.xlsx, созданного старым функционалом.

Запуск:
$ python interactive_3d_analysis.py --file corr_all_regions_all.xlsx [--port 8050]

Функции:
- Загрузка готовых корреляционных матриц из Excel
- Выбор региона из списка доступных листов
- Динамическая фильтрация по порогу корреляции
- Интерактивный 3D-график корреляций
- Автоматическое обновление таблицы и графика
- Исключение автокорреляций (r = 1.0)
"""

import argparse
import numpy as np
import pandas as pd
import warnings
from pathlib import Path

try:
    from dash import Dash, dcc, html, Input, Output, dash_table
    import plotly.express as px
    import plotly.graph_objs as go
    from plotly.subplots import make_subplots
except ImportError:
    print("Ошибка: Необходимо установить dash и plotly")
    print("Выполните: pip install dash plotly")
    exit(1)

warnings.simplefilter("ignore")

def parse_args():
    """
    Парсинг аргументов командной строки для интерактивного анализа
    """
    p = argparse.ArgumentParser(description="Интерактивный 3D-анализ готовых корреляций")
    p.add_argument("--file", required=True, help="Путь к файлу corr_all_regions_all.xlsx")
    p.add_argument("--port", type=int, default=8050, help="Порт веб-сервера")
    p.add_argument("--debug", action="store_true", help="Режим отладки")
    return p.parse_args()

def load_correlation_matrices(excel_path):
    """
    Загружает готовые корреляционные матрицы из Excel файла
    ИСПРАВЛЕНО для корректной обработки структуры файла
    """
    print("📊 Загрузка готовых корреляционных матриц...")
    
    try:
        excel_file = pd.ExcelFile(excel_path)
        regions = excel_file.sheet_names
        
        print(f"✅ Найдено {len(regions)} регионов в файле")
        
        correlation_data = {}
        region_info = {}
        
        for region in regions:
            print(f"📋 Загрузка данных для: {region}")
            
            try:
                df = pd.read_excel(excel_path, sheet_name=region, engine='openpyxl')
                
                if df.empty:
                    print(f"  ⚠️  Пустой лист для {region}")
                    continue
                
                region_info[region] = {}
                matrix_start_row = None
                
                for i in range(len(df)):
                    row = df.iloc[i]
                    if (pd.notna(row.iloc[0]) and 
                        isinstance(row.iloc[0], str) and
                        any(keyword in str(row.iloc[0]).lower() for keyword in 
                            ['параметр', 'количество', 'наблюдений', 'переменных', 'период'])):
                        
                        if len(row) >= 2 and pd.notna(row.iloc[1]):
                            region_info[region][str(row.iloc[0]).strip()] = str(row.iloc[1]).strip()
                        continue
                    
                    if (pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == ''):
                        if (len(row) >= 2 and 
                            pd.notna(row.iloc[1]) and 
                            isinstance(row.iloc[1], str) and
                            str(row.iloc[1]).strip() != ''):
                            matrix_start_row = i
                            print(f"  DEBUG: Найдена заголовочная строка матрицы в строке {i}")
                            break
                
                if matrix_start_row is None:
                    print(f"  ⚠️  Не удалось найти начало корреляционной матрицы для {region}")
                    continue
                
                header_row = df.iloc[matrix_start_row]
                variable_names = []
                
                for j in range(1, len(header_row)):
                    if pd.notna(header_row.iloc[j]):
                        var_name = str(header_row.iloc[j]).strip()
                        if var_name:
                            variable_names.append(var_name)
                
                if len(variable_names) < 2:
                    print(f"  ⚠️  Недостаточно переменных для {region}: {len(variable_names)}")
                    continue
                
                print(f"  DEBUG: Найдено {len(variable_names)} переменных")
                print(f"  DEBUG: Первые переменные: {variable_names[:3]}...")
                
                correlation_matrix = pd.DataFrame(
                    index=variable_names,
                    columns=variable_names,
                    dtype=float
                )
                
                data_start_row = matrix_start_row + 1
                for i in range(data_start_row, len(df)):
                    if i - data_start_row >= len(variable_names):
                        break
                    
                    row = df.iloc[i]
                    
                    if pd.notna(row.iloc[0]):
                        row_var_name = str(row.iloc[0]).strip()
                        
                        if row_var_name in variable_names:
                            for j in range(1, min(len(row), len(variable_names) + 1)):
                                if j <= len(variable_names):
                                    col_var_name = variable_names[j-1]
                                    try:
                                        val = row.iloc[j]
                                        if pd.notna(val):
                                            correlation_matrix.loc[row_var_name, col_var_name] = float(val)
                                    except (ValueError, TypeError):
                                        correlation_matrix.loc[row_var_name, col_var_name] = np.nan
                
                clean_matrix = correlation_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')
                
                if (not clean_matrix.empty and 
                    len(clean_matrix.index) >= 2 and 
                    len(clean_matrix.columns) >= 2):
                    
                    clean_matrix.index = [str(idx).strip() for idx in clean_matrix.index]
                    clean_matrix.columns = [str(col).strip() for col in clean_matrix.columns]
                    
                    correlation_data[region] = clean_matrix
                    print(f"  ✅ Загружено: {clean_matrix.shape[0]}x{clean_matrix.shape[1]} матрица")
                    
                    print(f"  DEBUG: Пример корреляции: {clean_matrix.iloc[0, 1]:.3f}")
                else:
                    print(f"  ⚠️  Матрица пустая или слишком маленькая для {region}")
                    
            except Exception as e:
                print(f"  ❌ Ошибка загрузки {region}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"🎉 Успешно загружено {len(correlation_data)} корреляционных матриц")
        return correlation_data, region_info
        
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки файла: {e}")
        import traceback
        traceback.print_exc()
        raise

def create_3d_data(corr_matrix, threshold=0.5):
    """
    Создает данные для 3D-визуализации из корреляционной матрицы
    ИСПРАВЛЕНИЕ: Улучшенная обработка ошибок
    """
    correlation_pairs = []
    
    if corr_matrix.empty:
        return pd.DataFrame()
    
    for i, var1 in enumerate(corr_matrix.index):
        for j, var2 in enumerate(corr_matrix.columns):
            if i < j:
                try:
                    r_val = corr_matrix.loc[var1, var2]
                    if (pd.notna(r_val) and 
                        abs(r_val) >= threshold and 
                        abs(r_val) < 1.0):
                        correlation_pairs.append({
                            'var1': str(var1),
                            'var2': str(var2),
                            'correlation': float(r_val),
                            'abs_correlation': abs(float(r_val)),
                            'correlation_strength': 'Сильная' if abs(r_val) >= 0.7 else 
                                                  'Умеренная' if abs(r_val) >= 0.5 else 'Слабая',
                            'correlation_type': 'Положительная' if r_val > 0 else 'Отрицательная'
                        })
                except Exception as e:
                    print(f"DEBUG: Ошибка обработки корреляции {var1} - {var2}: {e}")
                    continue
    
    return pd.DataFrame(correlation_pairs)

def create_display_table(corr_matrix, threshold=0.5):
    """
    Создает таблицу для отображения с фильтрацией по порогу
    ИСПРАВЛЕНИЕ: Полностью переработанная логика с правильной обработкой названий переменных
    """
    print(f"DEBUG: Создание таблицы для матрицы {corr_matrix.shape}")
    print(f"DEBUG: Индексы матрицы: {list(corr_matrix.index)[:3]}...")
    print(f"DEBUG: Колонки матрицы: {list(corr_matrix.columns)[:3]}...")
    
    if corr_matrix.empty:
        print("DEBUG: Матрица пустая")
        return [], []
    
    correlation_pairs = []
    
    matrix_index = list(corr_matrix.index)
    matrix_columns = list(corr_matrix.columns)
    
    for i, var1 in enumerate(matrix_index):
        for j, var2 in enumerate(matrix_columns):
            if i < j and str(var1) != str(var2):
                try:
                    correlation_value = corr_matrix.loc[var1, var2]
                    
                    if (pd.notna(correlation_value) and 
                        abs(correlation_value) >= threshold and 
                        abs(correlation_value) < 1.0):
                        
                        var1_str = str(var1).strip()
                        var2_str = str(var2).strip()
                        corr_val = float(correlation_value)
                        
                        if var1_str and var2_str and var1_str != var2_str:
                            correlation_pairs.append({
                                'Переменная 1': var1_str,
                                'Переменная 2': var2_str,
                                'Корреляция': f"{corr_val:.3f}",
                                'Сила связи': 'Сильная' if abs(corr_val) >= 0.7 else 'Умеренная' if abs(corr_val) >= 0.5 else 'Слабая',
                                'Тип связи': 'Положительная' if corr_val > 0 else 'Отрицательная'
                            })
                            
                            print(f"DEBUG: Добавлена пара {var1_str} - {var2_str}: {corr_val:.3f}")
                            
                except Exception as e:
                    print(f"DEBUG: Ошибка обработки пары {var1} - {var2}: {e}")
                    continue
    
    print(f"DEBUG: Всего найдено {len(correlation_pairs)} значимых корреляций")
    
    correlation_pairs.sort(key=lambda x: abs(float(x['Корреляция'])), reverse=True)
    
    columns = [
        {'name': 'Переменная 1', 'id': 'Переменная 1'},
        {'name': 'Переменная 2', 'id': 'Переменная 2'},
        {'name': 'Корреляция', 'id': 'Корреляция'},
        {'name': 'Сила связи', 'id': 'Сила связи'},
        {'name': 'Тип связи', 'id': 'Тип связи'}
    ]
    
    if correlation_pairs:
        print(f"DEBUG: Первая пара: {correlation_pairs[0]}")
    
    return correlation_pairs, columns

def create_dash_app(correlation_data, region_info, port=8050, debug=False):
    """
    Создание интерактивного Dash приложения с фильтрацией таблицы
    """
    app = Dash(__name__)
    
    regions = list(correlation_data.keys())
    
    # Layout приложения с добавленными фильтрами
    app.layout = html.Div([
        html.H1('🔍 Интерактивный 3D-анализ готовых корреляций региональной статистики РФ', 
                style={'textAlign': 'center', 'marginBottom': '30px', 'color': '#2c3e50'}),
        
        # Панель управления
        html.Div([
            html.Div([
                html.Label('📍 Выберите регион для анализа:', 
                          style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='region-select',
                    options=[{'label': region, 'value': region} for region in regions],
                    value=regions[0] if regions else None,
                    clearable=False,
                    style={'marginBottom': '20px'}
                ),
                
                html.Label('🎯 Минимальный порог корреляции |r| ≥', 
                          style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Slider(
                    id='r-threshold',
                    min=0,
                    max=1,
                    step=0.01,
                    value=0.5,
                    marks={
                        0: '0.0',
                        0.3: '0.3',
                        0.5: '0.5',
                        0.7: '0.7',
                        0.9: '0.9',
                        1.0: '1.0'
                    },
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                # Информационная панель
                html.Div(id='region-info', 
                        style={'marginTop': '20px', 'padding': '15px', 
                              'backgroundColor': '#ecf0f1', 'borderRadius': '8px',
                              'border': '1px solid #bdc3c7'})
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 
                     'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px',
                     'marginRight': '2%'}),
            
            # Статистика корреляций
            html.Div([
                html.H3('📊 Статистика корреляций', style={'color': '#2c3e50'}),
                html.Div(id='correlation-stats', 
                        style={'padding': '15px', 'backgroundColor': '#e8f4f8', 
                              'borderRadius': '8px', 'border': '1px solid #3498db'})
            ], style={'width': '66%', 'display': 'inline-block', 'verticalAlign': 'top', 
                     'padding': '20px'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.H3('🔍 Фильтры таблицы', style={'color': '#2c3e50', 'marginBottom': '20px'}),
            
            html.Div([
                # Поиск по переменным
                html.Div([
                    html.Label('🔎 Поиск по переменным:', style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='variable-search',
                        type='text',
                        placeholder='Введите название переменной...',
                        style={'width': '100%', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '4px'}
                    )
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                
                # Диапазон корреляций
                html.Div([
                    html.Label('📈 Диапазон корреляций:', style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.RangeSlider(
                        id='correlation-range',
                        min=-1,
                        max=1,
                        step=0.01,
                        value=[-1, 1],
                        marks={
                            -1: '-1.0',
                            -0.5: '-0.5',
                            0: '0.0',
                            0.5: '0.5',
                            1: '1.0'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                
                # Тип связи
                html.Div([
                    html.Label('🔗 Тип связи:', style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='correlation-type',
                        options=[
                            {'label': 'Все', 'value': 'all'},
                            {'label': 'Положительная', 'value': 'positive'},
                            {'label': 'Отрицательная', 'value': 'negative'}
                        ],
                        value='all',
                        clearable=False,
                        style={'fontSize': '14px'}
                    )
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                
                # Сила связи
                html.Div([
                    html.Label('💪 Сила связи:', style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='correlation-strength',
                        options=[
                            {'label': 'Все', 'value': 'all'},
                            {'label': 'Сильная (≥0.7)', 'value': 'strong'},
                            {'label': 'Умеренная (0.5-0.7)', 'value': 'moderate'},
                            {'label': 'Слабая (<0.5)', 'value': 'weak'}
                        ],
                        value='all',
                        clearable=False,
                        style={'fontSize': '14px'}
                    )
                ], style={'width': '24%', 'display': 'inline-block'})
            ], style={'marginBottom': '20px'}),
            
            # Кнопка сброса фильтров
            html.Div([
                html.Button('🔄 Сбросить фильтры', id='reset-filters', 
                           style={'padding': '10px 20px', 'backgroundColor': '#3498db', 
                                 'color': 'white', 'border': 'none', 'borderRadius': '5px',
                                 'cursor': 'pointer', 'fontSize': '14px'})
            ], style={'textAlign': 'center', 'marginBottom': '20px'})
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 
                 'marginBottom': '30px'}),
        
        # Таблица корреляций
        html.Div([
            html.H3('📋 Таблица корреляций', style={'color': '#2c3e50'}),
            html.Div(id='table-info', style={'marginBottom': '10px', 'fontSize': '14px', 'color': '#666'}),
            html.Div([
                dash_table.DataTable(
                    id='corr-table',
                    columns=[],
                    data=[],
                    style_table={'overflowX': 'auto', 'height': '500px'},
                    style_cell={
                        'textAlign': 'center', 
                        'padding': '10px',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '13px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {'filter_query': '{Сила связи} = Сильная'},
                            'backgroundColor': '#e8f5e8',
                            'color': '#2d5e2d'
                        },
                        {
                            'if': {'filter_query': '{Сила связи} = Умеренная'},
                            'backgroundColor': '#fff3cd',
                            'color': '#856404'
                        },
                        {
                            'if': {'filter_query': '{Сила связи} = Слабая'},
                            'backgroundColor': '#f8d7da',
                            'color': '#721c24'
                        }
                    ],
                    style_header={
                        'backgroundColor': '#34495e',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'fontSize': '14px'
                    },
                    filter_action='none',
                    sort_action='native',
                    page_size=20,
                    page_action='native'
                )
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                     'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'marginBottom': '30px'}),
        
        # 3D-график
        html.Div([
            html.H3('🎯 3D-визуализация корреляций', style={'color': '#2c3e50'}),
            dcc.Graph(id='corr-3d', style={'height': '700px'})
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px',
                 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    ], style={'margin': '20px', 'backgroundColor': '#f1f2f6', 'minHeight': '100vh'})
    
    @app.callback(
        [Output('corr-table', 'data'),
        Output('corr-table', 'columns'),
        Output('corr-3d', 'figure'),
        Output('region-info', 'children'),
        Output('correlation-stats', 'children'),
        Output('table-info', 'children')],
        [Input('region-select', 'value'),
        Input('r-threshold', 'value'),
        Input('variable-search', 'value'),
        Input('correlation-range', 'value'),
        Input('correlation-type', 'value'),
        Input('correlation-strength', 'value')]
    )
    def update_analysis(selected_region, threshold, search_text, corr_range, corr_type, corr_strength):
        """
        Обновление анализа с учетом всех фильтров
        ИСПРАВЛЕНИЯ: Убрана цветовая шкала, увеличен размер графика, убраны подписи осей XY
        """
        if not selected_region or selected_region not in correlation_data:
            return [], [], {}, "❌ Регион не выбран", "", ""
        
        try:
            corr_matrix = correlation_data[selected_region]
            
            correlation_pairs = []
            
            for i, var1 in enumerate(corr_matrix.index):
                for j, var2 in enumerate(corr_matrix.columns):
                    if i < j:
                        try:
                            r_val = corr_matrix.loc[var1, var2]
                            if (pd.notna(r_val) and 
                                abs(r_val) >= threshold and 
                                abs(r_val) < 1.0):
                                correlation_pairs.append({
                                    'var1': str(var1),
                                    'var2': str(var2),
                                    'correlation': float(r_val),
                                    'abs_correlation': abs(float(r_val))
                                })
                        except:
                            continue
            
            filtered_pairs = []
            
            for pair in correlation_pairs:
                if search_text:
                    search_lower = search_text.lower()
                    if (search_lower not in pair['var1'].lower() and 
                        search_lower not in pair['var2'].lower()):
                        continue
                
                if not (corr_range[0] <= pair['correlation'] <= corr_range[1]):
                    continue
                
                if corr_type == 'positive' and pair['correlation'] < 0:
                    continue
                elif corr_type == 'negative' and pair['correlation'] > 0:
                    continue
                
                if corr_strength == 'strong' and pair['abs_correlation'] < 0.7:
                    continue
                elif corr_strength == 'moderate' and not (0.5 <= pair['abs_correlation'] < 0.7):
                    continue
                elif corr_strength == 'weak' and pair['abs_correlation'] >= 0.5:
                    continue
                
                filtered_pairs.append(pair)
            
            filtered_pairs.sort(key=lambda x: x['abs_correlation'], reverse=True)
            
            table_data = []
            for pair in filtered_pairs:
                r_val = pair['correlation']
                table_data.append({
                    'Переменная 1': pair['var1'],
                    'Переменная 2': pair['var2'],
                    'Корреляция': f"{r_val:.3f}",
                    'Сила связи': 'Сильная' if abs(r_val) >= 0.7 else 'Умеренная' if abs(r_val) >= 0.5 else 'Слабая',
                    'Тип связи': 'Положительная' if r_val > 0 else 'Отрицательная'
                })
            
            columns = [
                {'name': 'Переменная 1', 'id': 'Переменная 1'},
                {'name': 'Переменная 2', 'id': 'Переменная 2'},
                {'name': 'Корреляция', 'id': 'Корреляция'},
                {'name': 'Сила связи', 'id': 'Сила связи'},
                {'name': 'Тип связи', 'id': 'Тип связи'}
            ]
            
            df_3d = pd.DataFrame(filtered_pairs)
            
            if len(df_3d) > 0:
                fig = px.scatter_3d(
                    df_3d,
                    x='var1',
                    y='var2',
                    z='correlation',
                    color='correlation',
                    size='abs_correlation',
                    title=f'3D-корреляции: {selected_region} (отфильтровано: {len(df_3d)})',
                    color_continuous_scale='RdBu_r',
                    range_color=[-1, 1],
                    size_max=20
                )
                
                fig.update_layout(
                    width=1400,
                    height=900,
                    
                    scene=dict(
                        xaxis_title="",
                        yaxis_title="",
                        zaxis_title="Байесовская корреляция",
                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=False, showticklabels=False),
                        zaxis=dict(showgrid=True, showticklabels=True)
                    ),
                    title_font_size=16,
                    font=dict(size=12)
                )
                
                fig.update_traces(
                    marker=dict(
                        colorbar=dict(
                            thickness=0,
                            len=0
                        ),
                        showscale=False
                    )
                )
                
                for trace in fig.data:
                    if hasattr(trace, 'marker') and hasattr(trace.marker, 'colorbar'):
                        trace.marker.colorbar = None
                        trace.marker.showscale = False
                
            else:
                fig = px.scatter_3d(
                    title=f"Нет корреляций, соответствующих фильтрам для {selected_region}"
                )
                fig.update_layout(width=1400, height=900)
            
            region_info_display = []
            if selected_region in region_info and region_info[selected_region]:
                info = region_info[selected_region]
                region_info_display.append(html.H4(f"📍 {selected_region}"))
                for param, value in info.items():
                    region_info_display.append(html.P(f"📊 {param}: {value}"))
            else:
                region_info_display.append(html.H4(f"📍 {selected_region}"))
                region_info_display.append(html.P("📊 Информация о регионе не найдена"))
            
            total_variables = len(corr_matrix.columns)
            filtered_count = len(filtered_pairs)
            total_count = len(correlation_pairs)
            
            if filtered_count > 0:
                avg_correlation = sum(pair['abs_correlation'] for pair in filtered_pairs) / filtered_count
                max_correlation = max(pair['abs_correlation'] for pair in filtered_pairs)
                positive_corr = sum(1 for pair in filtered_pairs if pair['correlation'] > 0)
                negative_corr = sum(1 for pair in filtered_pairs if pair['correlation'] < 0)
                
                stats_display = [
                    html.P(f"🔢 Всего переменных: {total_variables}"),
                    html.P(f"🔗 Отфильтровано: {filtered_count} из {total_count}"),
                    html.P(f"📈 Средняя |r|: {avg_correlation:.3f}"),
                    html.P(f"🎯 Максимальная |r|: {max_correlation:.3f}"),
                    html.P(f"➕ Положительные: {positive_corr}"),
                    html.P(f"➖ Отрицательные: {negative_corr}")
                ]
            else:
                stats_display = [
                    html.P(f"🔢 Всего переменных: {total_variables}"),
                    html.P(f"❌ Нет корреляций, соответствующих фильтрам"),
                    html.P("💡 Попробуйте изменить настройки фильтров")
                ]
            
            active_filters = []
            if search_text:
                active_filters.append(f"поиск: '{search_text}'")
            if corr_range != [-1, 1]:
                active_filters.append(f"диапазон: {corr_range[0]:.2f} - {corr_range[1]:.2f}")
            if corr_type != 'all':
                active_filters.append(f"тип: {corr_type}")
            if corr_strength != 'all':
                active_filters.append(f"сила: {corr_strength}")
            
            table_info = f"Показано {len(table_data)} из {total_count} корреляций"
            if active_filters:
                table_info += f" | Активные фильтры: {', '.join(active_filters)}"
            
            return table_data, columns, fig, region_info_display, stats_display, table_info
            
        except Exception as e:
            print(f"DEBUG: Ошибка в callback: {e}")
            error_msg = f"❌ Ошибка анализа: {str(e)}"
            return [], [], {}, error_msg, "", ""

    @app.callback(
        [Output('variable-search', 'value'),
         Output('correlation-range', 'value'),
         Output('correlation-type', 'value'),
         Output('correlation-strength', 'value')],
        [Input('reset-filters', 'n_clicks')]
    )
    def reset_filters(n_clicks):
        """
        Сброс всех фильтров
        """
        if n_clicks:
            return '', [-1, 1], 'all', 'all'
        return '', [-1, 1], 'all', 'all'
    
    return app

def main():
    """
    Основная функция запуска интерактивного анализа готовых данных
    """
    args = parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ Файл не найден: {args.file}")
        print("💡 Сначала создайте файл с корреляциями используя:")
        print("   python corr_bayes_rf.py --file your_data.xlsx --saveall")
        return
    
    print("🚀 Запуск интерактивного анализа готовых корреляций...")
    print(f"📁 Файл: {args.file}")
    
    try:
        correlation_data, region_info = load_correlation_matrices(args.file)
        
        if not correlation_data:
            print("❌ Не найдено корреляционных данных в файле")
            return
        
        print(f"✅ Готово к анализу: {len(correlation_data)} регионов")
        
        app = create_dash_app(correlation_data, region_info, args.port, args.debug)
        
        print(f"\n🌐 Запуск веб-сервера на порту {args.port}...")
        print(f"📱 Откройте браузер и перейдите по адресу: http://127.0.0.1:{args.port}/")
        print("⏹️  Для остановки нажмите Ctrl+C")
        
        try:
            app.run(debug=args.debug, port=args.port, host='127.0.0.1')
        except AttributeError:
            app.run_server(debug=args.debug, port=args.port, host='127.0.0.1')
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("\n📋 Проверьте:")
        print("  - Корректность пути к файлу корреляций")
        print("  - Формат файла Excel")
        print("  - Установку зависимостей: pip install dash plotly")

if __name__ == "__main__":
    main()
