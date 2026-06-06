# Contributing

Thank you for helping improve `Bayes-correlations-of-Russia`. Contributions are welcome when they make the dashboard more reproducible, interpretable, accessible, or methodologically transparent.

## Scope

Good contributions include:

- fixes to dashboard behavior, localization, accessibility, or documentation;
- reproducibility improvements for `corr.py` and `interactive_3d_analysis.py`;
- clearer methodology, limitations, and data provenance notes;
- tests for language switching, dashboard rendering, and local links;
- small data-quality notes with clear provenance.

Please avoid unrelated rewrites, large visual redesigns, or new dependencies unless the benefit is explicit.

## Local Setup

```bash
npm install
npm run test:i18n
```

For Python analysis scripts:

```bash
python -m pip install pandas numpy openpyxl xlsxwriter matplotlib seaborn plotly dash
python corr.py --file "Итоговая_база_данных_типизация_и_исправления_финальные.xlsx" --saveall
```

## Research and Data Changes

When changing methodology or data:

- explain the research reason in the pull request;
- name the source workbook or data source;
- include provider, access date, and license/terms when adding external data;
- update `docs/methodology.md` if preprocessing, thresholds, formulas, or interpretation changes;
- update `THIRD_PARTY_NOTICES.md` if new third-party material is introduced.

## Pull Requests

Before opening a pull request:

- keep changes focused;
- run available tests;
- check that local README/documentation links point to existing files;
- include screenshots only when visual behavior changes;
- note any warnings, skipped checks, or data limitations.

## Русский

Спасибо за вклад в `Bayes-correlations-of-Russia`. Особенно полезны изменения, которые улучшают воспроизводимость, интерпретацию, доступность и методологическую прозрачность.

Перед pull request, пожалуйста:

- делайте изменения небольшими и связанными с одной задачей;
- запускайте доступные проверки;
- указывайте источник данных, дату доступа и условия использования при добавлении внешних материалов;
- обновляйте `docs/methodology.md`, если меняются предобработка, пороги, формулы или интерпретация;
- обновляйте `THIRD_PARTY_NOTICES.md`, если появляются новые сторонние материалы.

Код распространяется по MIT, а документация/данные/контент проекта - по CC BY 4.0. Сторонние материалы сохраняют условия первоначальных правообладателей.
