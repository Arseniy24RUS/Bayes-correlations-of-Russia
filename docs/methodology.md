# Methodology: Bayesian-Stabilized Correlation Analysis of Russian Regions

This document describes the research workflow behind `Bayes-correlations-of-Russia`. It is intended for reviewers, contributors, students, and researchers who need to understand what the repository computes, how the workbooks are interpreted, and which assumptions must be kept in view when reading the dashboard.

The dashboard is a hypothesis-generation tool. It makes regional association patterns easier to inspect, but it does not claim causal identification, policy attribution, or a complete demographic model.

## English

## 1. Analytical Unit and Data Layout

The main input workbook is:

```text
Итоговая_база_данных_типизация_и_исправления_финальные.xlsx
```

The first sheet is treated as a regional panel. In the current repository snapshot it contains rows identified by a territorial unit and a year, with columns for demographic, migration, socio-economic, and related regional indicators. The workbook also includes rows for non-regional aggregates such as country-level, district-level, territorial, or special grouping records. The current script removes only rows where `Тип == "Страна"` automatically; other aggregate or historical categories should be reviewed by the researcher when designing a specific study.

The generated multi-region correlation workbook is:

```text
corr_all_regions_all.xlsx
```

It stores one sheet per analyzed region. Each regional sheet begins with metadata rows, followed by the Bayesian-stabilized correlation matrix. The interactive 3D analysis script reads this generated workbook rather than recomputing correlations from the source workbook.

## 2. Workbook Parsing

`corr.py` reads the input workbook with:

```python
pd.read_excel(path, engine="openpyxl")
```

The expected source columns include:

- `Регион`: territorial unit name.
- `Год`: observation year.
- `Тип`: territorial classification, used to remove country-level rows when present.
- Numeric indicator columns: demographic, migration, economic, social, and infrastructure variables.

The parsing workflow is:

1. Load the first Excel sheet with `openpyxl`.
2. Remove rows classified as `Страна` in the `Тип` column.
3. Drop the `Тип` column after this filter.
4. Optionally filter regions by regular expression through `--region`.
5. Optionally filter to a single year through `--year`.
6. Remove duplicate `(Регион, Год)` rows, keeping the first occurrence.
7. Reset the row index before numeric processing.

When `--saveall` is used, the script repeats the same basic cleaning region by region and writes an output sheet for each region that has enough observations and variables.

## 3. Numeric Preprocessing

After parsing, the script selects numeric columns with `pandas.select_dtypes(include=[numpy.number])`. Service identifiers are excluded from the correlation set:

```text
Год
Регион
```

The preprocessing rules are intentionally conservative and transparent:

- Columns are retained only if they meet the non-missingness threshold used by `dropna(axis=1, thresh=int(n_rows * 0.30))`. In practical terms, a variable must have observations for roughly 30% or more of the filtered rows.
- Variables with one or zero unique observed values are removed as constants.
- Pairwise correlation uses only rows where both variables are observed.
- If fewer than two paired observations remain, the pair is not estimable and is reported as missing.
- If either variable has zero variance in the paired observations, the pair is not estimable and is reported as missing.

These rules make the resulting matrices robust enough for exploratory inspection, but they do not replace a study-specific missing-data strategy. For publication-grade inference, researchers should document missingness patterns and consider imputation, balanced panels, or model-based alternatives where appropriate.

## 4. Pearson Correlation

For each retained pair of indicators `x` and `y`, the script first computes the Pearson product-moment correlation on complete paired observations:

```text
r = cov(x, y) / (sd(x) * sd(y))
```

In code, this is implemented through:

```python
numpy.corrcoef(x_valid, y_valid)[0, 1]
```

The raw Pearson coefficient is symmetric, ranges from `-1` to `+1`, and measures linear association. Positive values indicate that higher values of one indicator tend to appear with higher values of the other indicator. Negative values indicate that higher values of one indicator tend to appear with lower values of the other. Values near zero indicate weak linear association in the observed sample.

Pearson correlation is sensitive to outliers, nonlinear relationships, shared trends, and compositional constraints. In a regional time panel, it can also reflect long-run period effects rather than a direct substantive relationship between two indicators.

## 5. Empirical Bayesian Stabilization

Short regional time series can produce extreme sample correlations, especially when the number of paired observations is small. The project therefore reports a stabilized coefficient:

```text
r_bayes = r * (1 - ((1 - r^2) / (n - 2)))
```

where:

- `r` is the complete-pair Pearson correlation.
- `n` is the number of valid paired observations.
- `r_bayes` is the coefficient used in the output matrices, heatmap, ranked lists, and 3D view.

The formula can be read as empirical shrinkage toward zero. When sample evidence is weak, the multiplier reduces the magnitude of the observed Pearson coefficient. When the sample is larger or the observed relationship is very close to a perfect linear association, the multiplier approaches one.

Important implementation details:

- The formula is used only after the pair passes missingness and variance checks.
- Pairs with two observations are effectively not reliable for this adjustment and may become missing because the denominator is `n - 2`.
- The diagonal/self-correlation values should not be interpreted as evidence; visual tools generally exclude exact `|r| == 1` pairs when listing substantive relationships.
- The term "Bayesian" here refers to an empirical stabilization/shrinkage layer, not to a full generative Bayesian model with explicit priors, likelihood, posterior simulation, or credible intervals.

For confirmatory research, this shrinkage coefficient should be supplemented with uncertainty intervals, permutation or bootstrap sensitivity checks, and substantive model specification.

## 6. Thresholds and Strength Labels

The repository uses thresholds as visual filters, not as universal rules of statistical significance.

The interactive 3D analysis defaults to:

```text
|r_bayes| >= 0.50
```

Strength labels follow the dashboard convention:

```text
|r_bayes| >= 0.70        strong
0.50 <= |r_bayes| < 0.70 moderate
|r_bayes| < 0.50         weak or filtered out by default
```

These labels are intentionally practical. They help users scan the dashboard, but they do not account for multiple testing, sampling design, serial dependence, or the substantive importance of a coefficient. A moderate coefficient can be meaningful in a noisy demographic process; a strong coefficient can be spurious if both variables share a time trend.

## 7. Heatmap Interpretation

The heatmap displays the stabilized correlation matrix for a selected region or filtered dataset:

- Red/positive cells indicate variables moving in the same linear direction.
- Blue/negative cells indicate variables moving in opposite linear directions.
- Color intensity corresponds to the magnitude of `r_bayes`.
- Blank or missing cells indicate pairs that could not be estimated after preprocessing.

Researchers should read the heatmap by clusters rather than isolated cells. Blocks of related indicators often reflect shared measurement families, common denominators, or demographic accounting identities. Isolated high-magnitude cells deserve additional inspection of the underlying time series before being interpreted as meaningful.

## 8. 3D View Interpretation

`interactive_3d_analysis.py` reads the generated regional workbook and constructs a pairwise table of correlations above the selected threshold. The 3D scatter plot encodes:

- X axis: first indicator name.
- Y axis: second indicator name.
- Z axis: stabilized correlation value.
- Color: sign and magnitude of the stabilized correlation.
- Marker size: absolute magnitude of the stabilized correlation.

The 3D view is useful for navigating dense matrices and prioritizing relationships for follow-up. It is not a geometric statistical model. Distances on the categorical X/Y axes should not be interpreted as metric distances between variables.

## 9. Data Sources and Versioning

The repository contains both source and derived data artifacts. To keep research outputs reproducible:

- Treat `Итоговая_база_данных_типизация_и_исправления_финальные.xlsx` as the versioned source workbook for the current analysis snapshot.
- Treat `corr_all_regions_all.xlsx` as a derived workbook generated from the source workbook by `corr.py`.
- Record the Git commit hash, source workbook filename, generated workbook filename, command-line arguments, and Python/package versions when citing or comparing results.
- If replacing the source workbook, preserve the old file externally or in a release archive before recalculating outputs.
- If official statistical sources are updated, document the provider, publication date, access date, indicator definitions, and any territorial reclassification decisions.

The repository license covers original documentation, scripts, dashboards, and derived content only where the project has the right to license them. Official statistics and third-party materials remain subject to the terms of their original providers.

## 10. Assumptions

The current workflow assumes:

- Regional rows are comparable after filtering by `Регион`, `Год`, and `Тип`.
- Indicator names are stable enough to be used as matrix labels.
- Numeric values are already harmonized into comparable units or rates where needed.
- Pairwise deletion is acceptable for exploratory work.
- Linear association is an informative first-pass summary of regional relationships.
- Shrinkage toward zero is preferable to showing unadjusted extreme correlations from short series.

These assumptions should be revisited whenever the workbook schema changes, new indicators are added, or the analysis is used for formal publication.

## 11. Sensitivity Checks

Recommended checks before relying on a relationship:

- Recompute results with and without aggregate or historical territorial categories.
- Compare raw Pearson `r` with stabilized `r_bayes`.
- Test alternative missingness thresholds, for example 50% or 70% non-missing observations.
- Inspect time-series plots for both variables in the selected region.
- Remove obvious outlier years and check whether the sign and magnitude persist.
- Detrend variables or include year controls when common national trends may dominate.
- Compare results across related regions or federal districts.
- Use rank correlation or robust correlation as a nonparametric comparison.
- Apply multiple-testing discipline when many indicator pairs are screened.

## 12. Limits

The project does not establish causality. The current workflow does not estimate lagged effects, mediation, spatial dependence, panel fixed effects, measurement uncertainty, or posterior credible intervals. It also does not automatically harmonize administrative boundary changes or resolve all source-data definition changes.

Results should therefore be used as:

- An exploratory map of associations.
- A teaching aid for regional statistical reasoning.
- A queue of candidate relationships for deeper demographic, econometric, or GIS analysis.

They should not be used alone as:

- Proof of policy effect.
- Evidence of individual-level behavior.
- A substitute for official statistics.
- A final basis for operational decisions.

## 13. Reproducible Commands

Create and activate an environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the Python packages used by the scripts:

```bash
python -m pip install pandas numpy openpyxl xlsxwriter matplotlib seaborn plotly dash
```

Rebuild the all-region workbook:

```bash
python corr.py --file "Итоговая_база_данных_типизация_и_исправления_финальные.xlsx" --saveall
```

Run a single-region console and heatmap analysis:

```bash
python corr.py --file "Итоговая_база_данных_типизация_и_исправления_финальные.xlsx" --region "Алтайский край" --top 30
```

Launch the auxiliary 3D analysis app:

```bash
python interactive_3d_analysis.py --file corr_all_regions_all.xlsx --port 8050
```

Install JavaScript dependencies and run dashboard i18n tests:

```bash
npm install
npm run test:i18n
```

Serve the static dashboard locally:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/
```

---

# Методология: байесовски стабилизированный корреляционный анализ регионов России

## Русский

Этот документ описывает исследовательский процесс проекта `Bayes-correlations-of-Russia`. Он предназначен для рецензентов, контрибьюторов, студентов и исследователей, которым важно понимать, что именно вычисляет репозиторий, как интерпретируются рабочие книги и какие ограничения нужно учитывать при чтении дашборда.

Дашборд является инструментом генерации гипотез. Он помогает увидеть региональные паттерны ассоциаций, но не заявляет причинную идентификацию, оценку эффекта политики или полную демографическую модель.

## 1. Единица анализа и структура данных

Основная входная книга:

```text
Итоговая_база_данных_типизация_и_исправления_финальные.xlsx
```

Первый лист рассматривается как региональная панель. В текущем снимке репозитория строки задаются территориальной единицей и годом, а столбцы содержат демографические, миграционные, социально-экономические и смежные региональные показатели. В книге также есть строки для нерегиональных агрегатов: страны, округов, территориальных группировок и специальных категорий. Текущий скрипт автоматически удаляет только строки, где `Тип == "Страна"`; остальные агрегированные или исторические категории должны отдельно проверяться исследователем при постановке конкретной задачи.

Сформированная книга корреляций:

```text
corr_all_regions_all.xlsx
```

Она содержит отдельный лист для каждого проанализированного региона. В начале листа записываются метаданные, затем идет байесовски стабилизированная корреляционная матрица. Скрипт интерактивного 3D-анализа читает именно эту сформированную книгу, а не пересчитывает корреляции из исходной базы.

## 2. Чтение рабочей книги

`corr.py` читает входной Excel-файл так:

```python
pd.read_excel(path, engine="openpyxl")
```

Ожидаемые служебные столбцы:

- `Регион`: название территориальной единицы.
- `Год`: год наблюдения.
- `Тип`: классификация территориальной записи; используется для удаления строк уровня страны, если столбец присутствует.
- Числовые столбцы показателей: демографические, миграционные, экономические, социальные и инфраструктурные переменные.

Последовательность обработки:

1. Загрузка первого листа Excel через `openpyxl`.
2. Удаление строк со значением `Страна` в столбце `Тип`.
3. Удаление столбца `Тип` после фильтрации.
4. Опциональная фильтрация регионов регулярным выражением через `--region`.
5. Опциональная фильтрация по одному году через `--year`.
6. Удаление дублей `(Регион, Год)` с сохранением первой строки.
7. Сброс индекса перед числовой обработкой.

При запуске с `--saveall` скрипт повторяет ту же базовую очистку по каждому региону и записывает листы только для регионов, где достаточно наблюдений и переменных.

## 3. Числовая предобработка

После чтения данных скрипт выбирает числовые столбцы через `pandas.select_dtypes(include=[numpy.number])`. Служебные идентификаторы исключаются из набора корреляций:

```text
Год
Регион
```

Правила предобработки сделаны консервативными и прозрачными:

- Столбцы сохраняются, если проходят порог непустых значений `dropna(axis=1, thresh=int(n_rows * 0.30))`. На практике переменная должна иметь наблюдения примерно в 30% или более отфильтрованных строк.
- Переменные с одним или нулем уникальных наблюдаемых значений удаляются как константы.
- Для каждой пары корреляция считается только по строкам, где обе переменные наблюдаются.
- Если после парного удаления пропусков остается меньше двух наблюдений, пара не оценивается и записывается как пропуск.
- Если у одной из переменных нулевая дисперсия на парных наблюдениях, пара не оценивается и записывается как пропуск.

Эти правила достаточны для разведочного анализа, но не заменяют специальную стратегию работы с пропусками. Для публикационного исследования необходимо отдельно описывать структуру пропусков и при необходимости использовать импутацию, сбалансированные панели или модельные подходы.

## 4. Корреляция Пирсона

Для каждой пары сохраненных показателей `x` и `y` сначала считается парная корреляция Пирсона:

```text
r = cov(x, y) / (sd(x) * sd(y))
```

В коде используется:

```python
numpy.corrcoef(x_valid, y_valid)[0, 1]
```

Коэффициент Пирсона симметричен, лежит в диапазоне от `-1` до `+1` и измеряет линейную связь. Положительные значения означают, что более высокие значения одного показателя обычно наблюдаются вместе с более высокими значениями другого. Отрицательные значения означают противоположное направление. Значения около нуля указывают на слабую линейную связь в наблюдаемой выборке.

Корреляция Пирсона чувствительна к выбросам, нелинейности, общим трендам и композиционным ограничениям. В региональной временной панели она может отражать общий эффект периода, а не прямую содержательную связь между двумя показателями.

## 5. Эмпирическая байесовская стабилизация

Короткие региональные временные ряды могут давать экстремальные выборочные корреляции, особенно при малом числе парных наблюдений. Поэтому проект выводит стабилизированный коэффициент:

```text
r_bayes = r * (1 - ((1 - r^2) / (n - 2)))
```

где:

- `r` — корреляция Пирсона по валидным парным наблюдениям.
- `n` — число валидных парных наблюдений.
- `r_bayes` — коэффициент, который попадает в матрицы, тепловую карту, ранжированные списки и 3D-представление.

Формулу можно читать как эмпирическое сжатие коэффициента к нулю. Когда данных мало, множитель уменьшает модуль наблюдаемой корреляции. Когда наблюдений больше или связь почти идеально линейна, множитель приближается к единице.

Важные детали реализации:

- Формула применяется только после проверок на пропуски и дисперсию.
- Пары с двумя наблюдениями ненадежны для этой корректировки и могут становиться пропущенными, поскольку в знаменателе стоит `n - 2`.
- Диагональные значения и самокорреляции не следует интерпретировать как содержательное свидетельство; визуальные инструменты обычно исключают пары с точным `|r| == 1`.
- Слово «байесовский» здесь относится к эмпирической стабилизации/сжатию, а не к полной генеративной байесовской модели с явным априорным распределением, правдоподобием, posterior simulation или доверительными/байесовскими интервалами.

Для подтверждающего исследования этот коэффициент следует дополнять интервалами неопределенности, перестановочными или bootstrap-проверками и содержательной спецификацией модели.

## 6. Пороги и обозначения силы связи

Пороги в репозитории являются визуальными фильтрами, а не универсальными правилами статистической значимости.

Интерактивный 3D-анализ по умолчанию использует:

```text
|r_bayes| >= 0.50
```

Обозначения силы связи соответствуют дашборду:

```text
|r_bayes| >= 0.70        сильная связь
0.50 <= |r_bayes| < 0.70 умеренная связь
|r_bayes| < 0.50         слабая связь или отфильтровано по умолчанию
```

Эти метки нужны для удобного просмотра. Они не учитывают множественные проверки, дизайн выборки, серийную зависимость или содержательную важность коэффициента. Умеренный коэффициент может быть важным в шумном демографическом процессе; сильный коэффициент может быть ложным, если обе переменные имеют общий временной тренд.

## 7. Интерпретация тепловой карты

Тепловая карта показывает стабилизированную корреляционную матрицу для выбранного региона или отфильтрованного набора данных:

- Красные/положительные ячейки обозначают совместное движение переменных в одном линейном направлении.
- Синие/отрицательные ячейки обозначают движение в противоположных направлениях.
- Интенсивность цвета отражает модуль `r_bayes`.
- Пустые ячейки означают, что пара не была оценена после предобработки.

Тепловую карту лучше читать блоками, а не по одиночным ячейкам. Группы связанных показателей часто отражают общие семейства измерений, общие знаменатели или демографические балансовые тождества. Изолированные высокие коэффициенты требуют проверки исходных временных рядов.

## 8. Интерпретация 3D-представления

`interactive_3d_analysis.py` читает сформированную региональную книгу и строит таблицу пар корреляций выше выбранного порога. В 3D-диаграмме кодируется:

- Ось X: название первого показателя.
- Ось Y: название второго показателя.
- Ось Z: стабилизированная корреляция.
- Цвет: знак и модуль стабилизированной корреляции.
- Размер маркера: абсолютная величина стабилизированной корреляции.

3D-представление удобно для навигации по плотным матрицам и выбора связей для дальнейшего анализа. Оно не является геометрической статистической моделью. Расстояния по категориальным осям X/Y нельзя трактовать как метрические расстояния между переменными.

## 9. Источники данных и версионирование

Репозиторий содержит как исходные, так и производные артефакты. Для воспроизводимости:

- Рассматривайте `Итоговая_база_данных_типизация_и_исправления_финальные.xlsx` как версионированную исходную книгу текущего снимка анализа.
- Рассматривайте `corr_all_regions_all.xlsx` как производную книгу, рассчитанную из исходной книги скриптом `corr.py`.
- При цитировании или сравнении результатов фиксируйте хеш Git-коммита, имя исходной книги, имя сформированной книги, аргументы командной строки и версии Python/пакетов.
- При замене исходной книги сохраняйте старую версию вне рабочей ветки или в релизном архиве до пересчета результатов.
- При обновлении официальных статистических источников документируйте поставщика, дату публикации, дату доступа, определения показателей и решения по территориальной переклассификации.

Лицензия репозитория покрывает оригинальную документацию, скрипты, дашборды и производный контент только в той мере, в какой проект вправе их лицензировать. Официальная статистика и сторонние материалы остаются на условиях первоначальных поставщиков.

## 10. Предпосылки

Текущий процесс предполагает:

- Региональные строки сопоставимы после фильтрации по `Регион`, `Год` и `Тип`.
- Названия показателей достаточно стабильны, чтобы использоваться как подписи матриц.
- Числовые значения уже приведены к сопоставимым единицам измерения или коэффициентам там, где это необходимо.
- Попарное удаление пропусков допустимо для разведочного анализа.
- Линейная связь является информативным первым резюме региональных отношений.
- Сжатие коэффициентов к нулю предпочтительнее показа нестабильных экстремальных корреляций коротких рядов.

Эти предпосылки нужно пересматривать при изменении схемы книги, добавлении новых показателей или использовании анализа для формальной публикации.

## 11. Проверки чувствительности

Перед тем как опираться на конкретную связь, рекомендуется:

- Пересчитать результаты с агрегированными/историческими территориальными категориями и без них.
- Сравнить исходный Pearson `r` со стабилизированным `r_bayes`.
- Проверить альтернативные пороги заполненности, например 50% или 70% непустых наблюдений.
- Посмотреть временные ряды обеих переменных в выбранном регионе.
- Исключить очевидные годы-выбросы и проверить сохранение знака и величины.
- Детрэндировать переменные или добавить контроль года, если общий национальный тренд может доминировать.
- Сравнить результат с родственными регионами или федеральными округами.
- Использовать ранговую или робастную корреляцию как непараметрическое сравнение.
- Учитывать множественные проверки при массовом просмотре пар показателей.

## 12. Ограничения

Проект не устанавливает причинность. Текущий процесс не оценивает лаговые эффекты, медиацию, пространственную зависимость, панельные фиксированные эффекты, измерительную неопределенность или байесовские интервалы. Он также не гармонизирует автоматически изменения административных границ и не разрешает все изменения определений исходных показателей.

Результаты следует использовать как:

- Разведочную карту ассоциаций.
- Учебный инструмент для регионального статистического мышления.
- Очередь потенциальных связей для более глубокого демографического, эконометрического или ГИС-анализа.

Их не следует использовать отдельно как:

- Доказательство эффекта политики.
- Свидетельство об индивидуальном поведении.
- Замену официальной статистики.
- Окончательное основание для операционных решений.

## 13. Воспроизводимые команды

Создать и активировать окружение:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Установить Python-пакеты для скриптов:

```bash
python -m pip install pandas numpy openpyxl xlsxwriter matplotlib seaborn plotly dash
```

Пересобрать книгу по всем регионам:

```bash
python corr.py --file "Итоговая_база_данных_типизация_и_исправления_финальные.xlsx" --saveall
```

Запустить анализ одного региона с консольным выводом и тепловой картой:

```bash
python corr.py --file "Итоговая_база_данных_типизация_и_исправления_финальные.xlsx" --region "Алтайский край" --top 30
```

Запустить вспомогательное приложение 3D-анализа:

```bash
python interactive_3d_analysis.py --file corr_all_regions_all.xlsx --port 8050
```

Установить JavaScript-зависимости и запустить i18n-тесты дашборда:

```bash
npm install
npm run test:i18n
```

Запустить статический дашборд локально:

```bash
python -m http.server 8000
```

Затем открыть:

```text
http://localhost:8000/
```
