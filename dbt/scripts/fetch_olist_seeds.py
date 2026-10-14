#!/usr/bin/env python3
"""Скачивает Olist с Kaggle (kagglehub, токен не нужен) и кладёт CSV в seeds/ вашего dbt-проекта.

Дальше — обычный `dbt seed` (или `dbt build`, он включает seed). Это ровно то, что описано в ДЗ:

    path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")   # каталог с 9 CSV
    # скопировать нужные CSV в <dbt-проект>/seeds/

По умолчанию берутся 8 нужных таблиц; огромную geolocation (1 млн строк) можно добавить флагом --with-geolocation.
Каталог проекта: --project или $HW_DBT_PROJECT_DIR.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import ROOT, load_env  # noqa: E402
from settings import section  # noqa: E402
from utils import resolve_path  # noqa: E402

load_env()
S = section("fetch_olist_seeds")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=os.environ.get("HW_DBT_PROJECT_DIR"), help="каталог dbt-проекта (где dbt_project.yml)")
    ap.add_argument("--with-geolocation", action="store_true")
    ap.add_argument("--only-missing", action="store_true", help="не перезаписывать уже лежащие в seeds/ файлы")
    a = ap.parse_args()
    if not a.project:
        print("❌ укажите --project или HW_DBT_PROJECT_DIR (`make wizard`)")
        return 2
    proj = resolve_path(a.project, ROOT)
    if not (proj / "dbt_project.yml").exists():
        print(f"❌ нет dbt_project.yml в {proj}")
        return 2

    import kagglehub

    dataset = S["kaggle_dataset"]
    print(f"⬇️  kagglehub.dataset_download('{dataset}')…", flush=True)
    src = Path(kagglehub.dataset_download(dataset))
    dst = proj / "seeds"
    dst.mkdir(exist_ok=True)
    for name in S["files"] + ([S["geolocation_file"]] if a.with_geolocation else []):
        f, t = src / f"{name}.csv", dst / f"{name}.csv"
        if a.only_missing and t.exists():
            print(f"🆗 {t.name}: уже есть")
            continue
        shutil.copy2(f, t)
        print(f"✅ {t.name}")
    print(f"➡️  Дальше: cd {proj} && dbt seed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
