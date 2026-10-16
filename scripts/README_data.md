# Getting the data

Data is not stored in the repo (see `.gitignore`). Create `data/` and fill it yourself.

## Turbofan run-to-failure data (C-MAPSS)

Options, in the order I would try them:

1. Hugging Face mirror: `SoyVitou/NASA-C-MAPSS-Turbofan-Engine` (subsets FD001 to FD004).
2. NASA Prognostics Data Repository (search "Turbofan Engine Degradation Simulation Data Set").

NASA's data.gov listing for the C-MAPSS simulator said it was unavailable for download in October 2026.
Check each source's licence and cite NASA (Saxena and Goebel, 2008) in the README.

Put the files in `data/cmapss/`.

## SECOM

UCI Machine Learning Repository, "SECOM". Put the files in `data/secom/`.

## Documents for RAG

Collect 20 or more public technical PDFs (datasheets, standards, papers). Put them in `data/docs/`.
Check each licence before using it.
