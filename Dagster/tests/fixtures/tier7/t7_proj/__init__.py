"""Фикстура «уровень 6–7» без dbt: 8 raw-ассетов, 2 staging, 2 витрины (kind dbt) с checks, джоб и ежедневное расписание.
Имитирует вывод dagster-dbt, чтобы тестировать чекер быстро и без сети."""
import dagster as dg

RAW = ["olist_orders_dataset", "olist_order_items_dataset", "olist_customers_dataset", "olist_products_dataset",
       "olist_sellers_dataset", "olist_order_payments_dataset", "olist_order_reviews_dataset", "product_category_name_translation"]
STAGING = {"stg_orders": "olist_orders_dataset", "stg_customers": "olist_customers_dataset"}
MARTS = {"mart_delivery_by_state": "stg_orders", "mart_customer_profile": "stg_customers"}


def _asset(name: str, parent: str | None, kinds: set[str]):
    @dg.asset(name=name, deps=[parent] if parent else [], kinds=kinds, group_name="raw" if not parent else "dbt")
    def _a():
        return None

    return _a


raw = [_asset(n, None, {"duckdb"}) for n in RAW]
staging = [_asset(n, p, {"dbt", "duckdb"}) for n, p in STAGING.items()]
marts = [_asset(n, p, {"dbt", "duckdb"}) for n, p in MARTS.items()]


def _check(asset: str):
    @dg.asset_check(asset=asset, name=f"not_null_{asset}")
    def _c():
        return dg.AssetCheckResult(passed=True)

    return _c


job = dg.define_asset_job("daily_all", selection=dg.AssetSelection.all())
defs = dg.Definitions(
    assets=[*raw, *staging, *marts],
    asset_checks=[_check(n) for n in [*STAGING, *MARTS]],
    jobs=[job],
    schedules=[dg.ScheduleDefinition(job=job, cron_schedule="0 6 * * *")],
)
