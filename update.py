import pathlib
import os
import os.path
import hashlib
import time
import pandas as pd

import sheet2csv

SHEET_ID_DEV = "1dIv9DjXFoMst4_AiMUcQZNbSJSVs1MxlIdj7fxjGhA0"
SHEET_ID_PROD = "1dIv9DjXFoMst4_AiMUcQZNbSJSVs1MxlIdj7fxjGhA0"

SHEET_MAIN = "1dIv9DjXFoMst4_AiMUcQZNbSJSVs1MxlIdj7fxjGhA0"

RANGE_STATS = "Podatki!A3:ZZ"
RANGE_PATIENTS = "Pacienti!A3:ZZ"
RANGE_REGIONS = "Kraji!A1:ZZ"
RANGE_HOSPITALS = "Zdr.sistem!A3:ZZ"
RANGE_ICU = "ICU!A3:ZZ"
RANGE_DSO = "DSO!A3:ZZ"
RANGE_SCHOOLS = "Šole!A3:ZZ"
RANGE_DECEASED_REGIONS = "Umrli:Kraji!A1:ZZ"
RANGE_ACTIVE_REGIONS = "Aktivni:Kraji!A1:ZZ"
RANGE_SKOPJE_MUNICIPALITIES = "SkopjeOpstini!A1:ZZ"
RANGE_DECEASED_SKOPJE_MUNICIPALITIES = "Umrli:SkopjeOpstini!A1:ZZ"
RANGE_ACTIVE_SKOPJE_MUNICIPALITIES = "Aktivni:SkopjeOpstini!A1:ZZ"
RANGE_STATS_WEEKLY = "EPI:weekly!A3:ZZ"

SHEET_MEAS = "1AzBziQ5ySEaY8cv4NMYfc1LopTWbBRX0hWzMVP8Q52M"
RANGE_SAFETY_MEASURES = "E:Measures!A3:ZZ"

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

def import_sheet(update_time, sheet, range, filename, **kwargs):
    print("Processing", filename)
    pathlib.Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
    old_hash = sha1sum(filename)
    try:
        sheet2csv.sheet2csv(id=sheet, range=range, api_key=GOOGLE_API_KEY, filename=filename, **kwargs)
    except Exception as e:
        print("Failed to import {}".format(filename))
        raise e
    new_hash = sha1sum(filename)
    if old_hash != new_hash:
        with open("{}.timestamp".format(filename), "w") as f:
            f.write(str(update_time))

def computeMunicipalities(update_time):
    filename = 'csv/municipality.csv'
    print("Processing", filename)
    old_hash = sha1sum(filename)
    dfRegions = pd.read_csv('csv/regions.csv', index_col='date') 
    dfActive = pd.read_csv('csv/active-regions.csv', index_col='date')
    dfDeceased = pd.read_csv('csv/deceased-regions.csv', index_col='date')
    dfRegions.columns = [str(col) + '.cases.confirmed.todate' for col in dfRegions.columns]
    dfActive.columns = [str(col) + '.cases.active' for col in dfActive.columns]
    dfDeceased.columns = [str(col) + '.deceased.todate' for col in dfDeceased.columns]
    # merged = pd.concat([dfRegions, dfDeceased], axis=1, join='outer').sort_index(axis=1)
    merged = dfRegions.join(dfActive).join(dfDeceased).sort_index(axis=1)
    merged.to_csv(filename, float_format='%.0f', index_label='date')
    new_hash = sha1sum(filename)
    if old_hash != new_hash:
        with open("{}.timestamp".format(filename), "w") as f:
            f.write(str(update_time))

def computeSkopjeMunicipalities(update_time):
    filename = 'csv/skopje.csv'
    old_hash = sha1sum(filename)
    dfRegions = pd.read_csv('csv/skopje-municipalities.csv', index_col='date') 
    dfActive = pd.read_csv('csv/active-skopje-municipalities.csv', index_col='date')
    dfDeceased = pd.read_csv('csv/deceased-skopje-municipalities.csv', index_col='date')
    dfRegions.columns = [str(col) + '.cases.confirmed.todate' for col in dfRegions.columns]
    dfActive.columns = [str(col) + '.cases.active' for col in dfActive.columns]
    dfDeceased.columns = [str(col) + '.deceased.todate' for col in dfDeceased.columns]
    # merged = pd.concat([dfRegions, dfDeceased], axis=1, join='outer').sort_index(axis=1)
    merged = dfRegions.join(dfActive).join(dfDeceased).sort_index(axis=1)
    merged.to_csv(filename, float_format='%.0f', index_label='date')
    new_hash = sha1sum(filename)
    if old_hash != new_hash:
        with open("{}.timestamp".format(filename), "w") as f:
            f.write(str(update_time))

if __name__ == "__main__":
    update_time = int(time.time())
    import_sheet(update_time, SHEET_MAIN, RANGE_STATS, "csv/stats.csv")
    import_sheet(update_time, SHEET_MAIN, RANGE_STATS_WEEKLY, "csv/stats-weekly.csv")
    import_sheet(update_time, SHEET_MAIN, RANGE_PATIENTS, "csv/patients.csv")
    import_sheet(update_time, SHEET_MAIN, RANGE_HOSPITALS, "csv/hospitals.csv")
    import_sheet(update_time, SHEET_MAIN, RANGE_ICU, "csv/icu.csv")
    # import_sheet(update_time, SHEET_MAIN, RANGE_DSO, "csv/retirement_homes.csv") SLO-spec
    #import_sheet(update_time, SHEET_MAIN, RANGE_SCHOOLS, "csv/schools.csv") SLO-spec

    import_sheet(update_time, SHEET_MAIN, RANGE_REGIONS, "csv/regions.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    import_sheet(update_time, SHEET_MAIN, RANGE_ACTIVE_REGIONS, "csv/active-regions.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    import_sheet(update_time, SHEET_MAIN, RANGE_DECEASED_REGIONS, "csv/deceased-regions.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    computeMunicipalities(update_time)

    import_sheet(update_time, SHEET_MAIN, RANGE_SKOPJE_MUNICIPALITIES, "csv/skopje-municipalities.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    import_sheet(update_time, SHEET_MAIN, RANGE_DECEASED_SKOPJE_MUNICIPALITIES, "csv/deceased-skopje-municipalities.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    import_sheet(update_time, SHEET_MAIN, RANGE_ACTIVE_SKOPJE_MUNICIPALITIES, "csv/active-skopje-municipalities.csv", rotate=True, key_mapper=key_mapper_kraji, sort_keys=True)
    computeSkopjeMunicipalities(update_time)

    #import_sheet(update_time, SHEET_MEAS, RANGE_SAFETY_MEASURES, "csv/safety_measures.csv") SLO-spec
