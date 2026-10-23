"""Фикстура «уровень 8–9» без dbt: граф как у tier7 + eager на витринах, freshness, retry, сенсор на сбой → Telegram,
ресурс по DAGSTER_ENV. Рядом — .pre-commit-config.yaml, .github/workflows/ci.yml и tests/ (их читает чекер, а не pytest)."""
import os
from datetime import timedelta

import dagster as dg

RAW = ["olist_orders_dataset", "olist_order_items_dataset", "olist_customers_dataset", "olist_products_dataset",
       "olist_sellers_dataset", "olist_order_payments_dataset", "olist_order_reviews_dataset", "product_category_name_translation"]
STAGING = {"stg_orders": "olist_orders_dataset", "stg_customers": "olist_customers_dataset"}
MARTS = {"mart_delivery_by_state": "stg_orders", "mart_customer_profile": "stg_customers"}
FRESH = dg.FreshnessPolicy.time_window(fail_window=timedelta(hours=48), warn_window=timedelta(hours=26))


def _asset(name: str, parent: str | None, kinds: set[str], mart: bool = False):
    @dg.asset(name=name, deps=[parent] if parent else [], kinds=kinds, group_name="raw" if not parent else "dbt",
              automation_condition=dg.AutomationCondition.eager() if mart else None,
              freshness_policy=FRESH if mart else None, retry_policy=dg.RetryPolicy(max_retries=2))
    def _a():
        return None

    return _a


raw = [_asset(n, None, {"duckdb"}) for n in RAW]
staging = [_asset(n, p, {"dbt", "duckdb"}) for n, p in STAGING.items()]
marts = [_asset(n, p, {"dbt", "duckdb"}, mart=True) for n, p in MARTS.items()]


def _check(asset: str):
    @dg.asset_check(asset=asset, name=f"not_null_{asset}", blocking=True)
    def _c():
        return dg.AssetCheckResult(passed=True)

    return _c


class TelegramNotifier(dg.ConfigurableResource):
    bot_token: str

    def send(self, text: str) -> None:   # в фикстуре ничего не шлём
        pass


@dg.run_failure_sensor
def telegram_on_failure(context: dg.RunFailureSensorContext, telegram: TelegramNotifier):
    telegram.send(context.dagster_run.run_id)


job = dg.define_asset_job("daily_all", selection=dg.AssetSelection.all())
ENV = os.environ.get("DAGSTER_ENV", "dev")       # фикстура: дефолт допустим
defs = dg.Definitions(
    assets=[*raw, *staging, *marts],
    asset_checks=[_check(n) for n in [*STAGING, *MARTS]],
    jobs=[job],
    schedules=[dg.ScheduleDefinition(job=job, cron_schedule="0 6 * * *")],
    sensors=[telegram_on_failure],
    resources={"telegram": TelegramNotifier(bot_token="fixture" if ENV != "prod" else dg.EnvVar("TELEGRAM_BOT_TOKEN"))},
)
