# Data Preparation

This document covers downloading and processing Japanese statistical data from e-Stat.

## Overview

We collect data from three main sources:
1. **Census Data** - Population, households, demographics
2. **Income & Economy** - National survey of family income and wealth
3. **Labor & Wages** - Wage structure statistics

## Step 1: Download Census Data

### Script: `docs/download_census_modal.py`

Downloads all 2020 Population Census datasets from e-Stat.

```bash
modal run docs/download_census_modal.py
```

**What it does:**
- Scrapes e-Stat website for census file links
- Downloads 6,839 Excel files in parallel (500 concurrent workers)
- Saves to `census-data` Modal volume
- Runtime: ~15 minutes

**Output:**
```
Total files: 6839
Successfully downloaded: 6838
Errors: 1
```

### Script: `docs/download_economy_labor_modal.py`

Downloads economy and labor statistics.

```bash
modal run docs/download_economy_labor_modal.py
```

**Categories:**
- Income & Economy (`toukei=00200564`)
- Labor & Wages (`toukei=00450091`)

**Output:** ~50 Excel files in `economy-labor-data` volume

## Step 2: Convert Excel to CSV

### Script: `docs/convert_census_to_csv.py`

Converts Excel files to CSV with human-readable filenames.

```bash
modal run --detach docs/convert_census_to_csv.py
```

**Process:**
1. Scans `census-data` volume for `.xls` and `.xlsx` files
2. Reads each Excel file with pandas
3. Extracts title from first few rows
4. Saves as `{ID}_{Title}.csv` in `/data/csv/` subfolder
5. Uses 100 parallel workers

**Example transformation:**
```
Before: 00200521_12345.xlsx
After:  00200521_2020_Population_Census_Preliminary_Counts.csv
```

**Runtime:** ~10 minutes for 6,838 files

### Script: `docs/convert_economy_labor_to_csv.py`

Same process for economy/labor data.

```bash
modal run docs/convert_economy_labor_to_csv.py
```

## Step 3: Clean Filenames

### Script: `docs/fix_csv_filenames.py`

Removes URL-encoded garbage from filenames.

```bash
modal run docs/fix_csv_filenames.py
```

**Fixes:**
```
Before: attachment%3B%20filename*%3DUTF-8%27%27a01e_2020_Population_Census.csv
After:  a01e_2020_Population_Census.csv
```

**Results:**
- Census: 6,838 files renamed
- Economy: 50 files renamed

## Step 4: Clean Up (Optional)

### Remove Excel Files

After CSV conversion, delete original Excel files to save space:

```bash
modal run docs/cleanup_data.py
```

**What it removes:**
- All `.xls` and `.xlsx` files
- Duplicate CSVs (e.g., `ID.csv` if `ID_Title.csv` exists)

### Remove Duplicate CSVs

Remove exact content duplicates:

```bash
modal run docs/remove_duplicate_csvs.py
```

Uses content hashing to identify duplicates.

## Data Statistics

### Census Data
- **Files**: 6,838 CSVs
- **Size**: ~2GB
- **Categories**: Population, households, labor force, industry, etc.
- **Geographic levels**: National, prefectural, municipal

### Economy & Labor Data
- **Files**: 50 CSVs
- **Size**: ~100MB
- **Topics**: Income, consumption, wealth, wages

## File Naming Convention

All CSV files follow this pattern:
```
{dataset_id}_{human_readable_title}.csv
```

Examples:
- `a01e_2020_Population_Census_Preliminary_Counts.csv`
- `00200564_National_Survey_Family_Income.csv`

## Volume Structure

```
census-data/
├── csv/
│   ├── a01e_2020_Population_Census.csv
│   ├── b01_Households_by_Type.csv
│   └── ... (6,838 files)

economy-labor-data/
├── income_economy/
│   └── ... (25 files)
└── labor_wages/
    └── ... (25 files)
```

## Troubleshooting

### Download Failures
- **Issue**: Some files fail to download (timeout)
- **Solution**: Re-run the download script - it skips existing files

### CSV Conversion Errors
- **Issue**: Some Excel files have complex formatting
- **Solution**: Script handles errors gracefully, skips problematic files

### Filename Encoding
- **Issue**: Special characters in filenames
- **Solution**: `fix_csv_filenames.py` handles URL decoding

## Next Steps

Once data is prepared, proceed to [Dataset Generation](02-dataset-generation.md) to create training examples.
