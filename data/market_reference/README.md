# Market reference data

Drop HelloData (or similar) market-analysis CSV exports here. The backend
(`backend/app/services/market_reference.py`) loads every `*.csv` in this folder and
builds a street-address → market-rent lookup used by the importer to attach real
market rents to owned properties (driving rent-gap, basis-gap, and 721 scoring).

Expected columns (case/spacing-insensitive): an address column (e.g. `Address`) and
a rent column (e.g. `Rent`). Extra columns are ignored.

The CSV/XLSX files themselves are gitignored (licensed data) — only this README is
tracked. You can also point `MARKET_REFERENCE_CSV` at a file path instead.
