# ScrapeBench Overleaf package

Upload the contents of this archive as one Overleaf project and set `main.tex`
as the main document. It uses the standard `acmart` class and
`ACM-Reference-Format`, both available in Overleaf's TeX Live installation.

This is the 2026-10-17 four-identity feasibility snapshot. The included
`web4_final_summary.csv`, `web4_by_scenario.csv`, and
`web4_protection_quality.csv` are the auditable data behind the paper tables.
All five branches, including MetaCloak, are complete. No legacy
cumulative-funnel result is used.

The paper now includes three publication figures: a vector research-motivation
diagram in the introduction, a vector system/optimization framework in the
method section, and a real four-scenario qualitative comparison under T1 JPEG
Q70.  The large scenario table reports FDFR, conditional ISM, end-to-end ISM,
and paired gap; no unavailable BRISQUE or SER-FIQ value is imputed.

Compile with pdfLaTeX and BibTeX. Local compilation on the cluster could not be
completed because that host does not have `acmart.cls`; this does not normally
affect Overleaf.
