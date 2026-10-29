#!/bin/sh
# Тестовые файлы для v5–v8: CSV и gzip-TSV в /tmp
printf 'day,user_id\n31.12.2025,1\n01.01.2026,2\n' > /tmp/d.csv
printf 'ts_unix,user_id,url\n1790000000,1,https://a.com/x\n1790000100,2,https://b.org/y\n' > /tmp/e.csv
printf '1\ta\n2\tb\n' | gzip > /tmp/events.tsv.gz
