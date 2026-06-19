## Быстрый запуск через Docker

```bash
docker compose up -d postgres
docker compose run --rm etl
docker compose run --rm analytics
```

Также можно выполнить одной командой:

```bash
make all
```

Остановить и удалить контейнеры вместе с volume:

```bash
make down
```

## Локальный запуск без Docker

Требуется PostgreSQL и Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.run_pipeline
python -m src.run_analytics
```

## DWH-модель

Использована star schema:

- `dwh.dim_customers` — клиенты;
- `dwh.dim_products` — товары;
- `dwh.fact_orders` — заказы;
- `dwh.fact_payments` — платежи;
- `dwh.fact_events` — события пользовательской активности;
- `dwh.etl_bad_records` — лог проблемных записей;
- `dwh.etl_run_summary` — краткая статистика загрузки.

Для отсутствующих или некорректных ссылок на клиента/товар используется техническая строка `Unknown` с ключом `0`. Такие случаи не удаляются из фактов, но пишутся в `dwh.etl_bad_records`.

## Data Quality

В пайплайне обрабатываются основные проблемы исходных файлов:

- дубли ключей в клиентах, товарах, заказах и платежах;
- битые даты в заказах, платежах, событиях и датах создания клиентов;
- пропуски customer_id;
- некорректные суммы платежей и цены товаров;
- платежи по несуществующим заказам;
- заказы и события с несуществующими клиентами или товарами;
- пропуски payment_method.

Дубли по бизнес-ключу удаляются с сохранением первой валидной записи. Проблемные строки логируются с исходным payload.

## Валюты

В исходниках есть RUB, USD и EUR. Для единой аналитики добавлены поля `gross_amount_rub` и `amount_rub`. Используются фиксированные коэффициенты:

- RUB = 1;
- USD = 90;
- EUR = 100.

Это для воспроизводимости результата без внешних API и плавающих курсов.

## Аналитические запросы

В `sql/`:

1. `01_top_10_customers_by_purchase_amount.sql` — топ-10 клиентов по сумме покупок;
2. `02_monthly_revenue.sql` — выручка по месяцам;
3. `03_most_popular_products.sql` — самые популярные товары;
4. `04_top_5_buyers_last_activity.sql` — последняя активность топ-5 покупателей;
5. `05_users_without_orders.sql` — пользователи без заказов;
6. `06_data_quality_summary.sql` — сводка по проблемным записям.

## Повторяемость результата

`src.run_pipeline` каждый раз пересоздает схемы `stg` и `dwh`, поэтому запуск идемпотентный.