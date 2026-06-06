# Roadmap

This roadmap is practical rather than promotional. It lists research-readiness work that would make the project easier to review, reproduce, and extend.

## Near Term

- Add a small command-line smoke test for `corr.py` on a synthetic workbook.
- Document the exact data provenance of each major indicator family.
- Add a local Markdown link/image existence check to the npm scripts.
- Clarify handling of aggregate and historical territorial categories beyond `Тип == "Страна"`.
- Add a compact data dictionary for the main workbook.

## Methodology

- Compare raw Pearson correlations with stabilized `r_bayes` in an exported diagnostics sheet.
- Add optional Spearman correlation as a robustness comparison.
- Add sensitivity settings for the missingness threshold.
- Add optional detrending or year-centered correlations for common trend sensitivity.
- Record package versions and command arguments in generated workbooks.

## Dashboard and Accessibility

- Add keyboard-focused checks for filters and language switching.
- Improve mobile behavior for dense indicator labels.
- Add downloadable methodology and citation metadata from the dashboard.
- Add a compact "interpret with caution" panel for high-correlation pairs.

## Русский

## Ближайшие задачи

- Добавить smoke-test для `corr.py` на небольшой синтетической Excel-книге.
- Описать происхождение основных групп показателей.
- Добавить npm-скрипт для проверки локальных ссылок и изображений в Markdown.
- Уточнить обработку агрегированных и исторических территориальных категорий помимо `Тип == "Страна"`.
- Добавить краткий словарь данных для основной книги.

## Методология

- Сравнивать исходные корреляции Пирсона со стабилизированным `r_bayes` в диагностическом листе.
- Добавить опциональную корреляцию Спирмена как проверку устойчивости.
- Сделать настраиваемым порог пропусков.
- Добавить детрендирование или центрирование по году для проверки общих трендов.
- Записывать версии пакетов и аргументы команд в сформированные книги.
