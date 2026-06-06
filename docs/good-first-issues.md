# Good First Issues

These are small, useful entry points for contributors. Each task should be handled in a focused pull request.

## Documentation

- Add a short data dictionary for 10-15 core indicators from the source workbook.
- Add a reproducibility checklist to `docs/methodology.md`.
- Add examples of responsible citation for derived figures and screenshots.
- Check README and documentation links after file renames.

## Testing

- Add a Markdown local-link checker to `package.json`.
- Add a synthetic workbook smoke test for `corr.py`.
- Add a test that verifies the dashboard does not show missing translation keys.
- Add a check that required visual assets exist before Playwright runs.

## Methodology

- Add a diagnostics export with pairwise `n` for each correlation.
- Add a note comparing Pearson and Spearman correlation use cases.
- Create a short example of how to inspect an outlier year before interpreting a strong correlation.

## Русский

## Документация

- Добавить краткий словарь данных для 10-15 ключевых показателей.
- Добавить чеклист воспроизводимости в `docs/methodology.md`.
- Добавить примеры корректного цитирования производных графиков и скриншотов.

## Тесты

- Добавить проверку локальных Markdown-ссылок в `package.json`.
- Добавить smoke-test для `corr.py` на синтетической книге.
- Проверить, что дашборд не показывает отсутствующие ключи перевода.

## Методология

- Экспортировать диагностическое число парных наблюдений `n` для каждой корреляции.
- Кратко сравнить случаи применения корреляций Пирсона и Спирмена.
- Добавить пример проверки года-выброса перед интерпретацией сильной связи.
