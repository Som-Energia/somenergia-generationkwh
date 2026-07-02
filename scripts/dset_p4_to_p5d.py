#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta


# Posar aqui serial del registrador
_SERIAL = "39300206"


def season_for(dt):
    # Juny-setembre sempre estiu. Gener-febrer-novembre-desembre sempre hivern.
    if dt.month in (4, 5, 6, 7, 8, 9):
        return "1"
    if dt.month in (1, 2, 11, 12):
        return "0"

    # Març / octubre: aproximació simple per no complicar el script.
    # Si després us cal exactitud DST al límit, es pot millorar.
    return "1"


def load_quarter_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        for raw in reader:
            if not raw or len(raw) < 2:
                continue
            ts = raw[0].strip()
            val = raw[1].strip()
            if not ts:
                continue

            # sumem 1 hora perque el csv de dset posa el moment anterior, no el seguent com cnmc
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") + timedelta(hours=1)

            ae = float(val.replace(",", "."))
            rows.append((dt, ae))
    return rows

def aggregate_hourly(rows):
    hourly = defaultdict(float)
    for dt, ae in rows:
        bucket = dt.replace(minute=0, second=0, microsecond=0)
        hourly[bucket] += ae
    return sorted(hourly.items())


def main():
    if len(sys.argv) != 3:
        print("Ús: python csv_to_p5d.py input.csv output.curva")
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    quarter_rows = load_quarter_csv(input_path)
    hourly_rows = aggregate_hourly(quarter_rows)

    with open(output_path, "w", encoding="utf-8", newline="") as fh:
        for dt, ae in hourly_rows:
            season = season_for(dt)
            # P5D import: row[3]=ai, row[4]=ae
            line = "{};{};{};0;{};\n".format(
                _SERIAL,
                dt.strftime("%Y/%m/%d %H:%M"),
                season,
                int(round(ae)),
            )
            fh.write(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
