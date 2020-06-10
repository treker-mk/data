import pathlib
import os
import os.path
import hashlib
import time
import pandas as pd

import sheet2csv

SHEET_ID_DEV = "157FidK6pugBrnPRcdUdEKRfR7sJACLh84t2qLM1GDrY"
SHEET_ID_PROD = "157FidK6pugBrnPRcdUdEKRfR7sJACLh84t2qLM1GDrY"

SHEET_ID = SHEET_ID_PROD

RANGE_STATS = "Podatki!A3:ZZ"
RAGNE_PATIENTS = "Pacienti!A3:ZZ"
RANGE_REGIONS = "Kraji!A1:ZZ"
RANGE_HOSPITALS = "Zdr.sistem!A3:ZZ"
RANGE_ICU = "ICU!A3:ZZ"
RANGE_SAFETY_MEASURES = "Ukrepi!A2:ZZ"
RANGE_DSO = "DSO!A3:ZZ"
RANGE_DECEASED_REGIONS = "Umrli:Kraji!A1:ZZ"

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

def sha1sum(fname):
    h = hashlib.sha1()
    try:
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None

def key_mapper_kraji(values):
  def clean(x):
    return x.lower().replace(" - ", "-").replace(" ", "_").split('/')[0]
  
  keys = list(map( lambda x: '.'.join(['region', clean(x[0]), clean(x[1])]), zip(values[1][1:], values[0][1:])))
  keys.insert(0, 'date')

  return keys, values[2:]

def import_sheet(update_time, range, filename, **kwargs):
    pathlib.Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
    old_hash = sha1sum(filename)
    try:
        sheet2csv.sheet2csv(id=SHEET_ID, range=range, api_key=GOOGLE_API_KEY, filename=filename, **kwargs)
    except Exception as e:
        print("Failed to import {}".format(filename))
        raise e
    new_hash = sha1sum(filename)
    if old_hash != new_hash:
        with open("{}.timestamp".format(filename), "w") as f:
            f.write(str(update_time))

def computeMunicipalities(update_time):
    filename = 'csv/municipality.csv'
    old_hash = sha1sum(filename)
    dfRegions = pd.read_csv('csv/regions.csv', index_col='date') 
    dfDeceased = pd.read_csv('csv/deceased-regions.csv', index_col='date')
    dfRegions.columns = [str(col) + '.cases.confirmed.todate' for col in dfRegions.columns]
    dfDeceased.columns = [str(col) + '.deceased.todate' for col in dfDeceased.columns]
    # merged = pd.concat([dfRegions, dfDeceased], axis=1, join='outer').sort_index(axis=1)
    merged = dfRegions.join(dfDeceased).sort_index(axis=1)
    merged.to_csv(filename, float_format='%.0f', index_label='date')
    new_hash = sha1sum(filename)
    if old_hash != new_hash:
        with open("{}.timestamp".format(filename), "w") as f:
            f.write(str(update_time))

if __name__ == "__main__":
    update_time = int(time.time())
    import_sheet(update_time, RANGE_STATS, "csv/stats.csv")
    time.sleep(2)
    import_sheet(update_time, RAGNE_PATIENTS, "csv/patients.csv")
    time.sleep(2)
    import_sheet(update_time, RANGE_HOSPITALS, "csv/hospitals.csv")
    time.sleep(2)
    import_sheet(update_time, RANGE_ICU, "csv/icu.csv")
    time.sleep(2)
    import_sheet(update_time, RANGE_REGIONS, "csv/regions.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    time.sleep(2)
    import_sheet(update_time, RANGE_SAFETY_MEASURES, "csv/safety_measures.csv")
    time.sleep(2)
    import_sheet(update_time, RANGE_DSO, "csv/retirement_homes.csv")
    time.sleep(2)
    import_sheet(update_time, RANGE_DECEASED_REGIONS, "csv/deceased-regions.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    time.sleep(2)
    computeMunicipalities(update_time)
