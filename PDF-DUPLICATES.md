# Duplicate PDFs: what is left to do in Google Drive

Written 2026-10-20. **Delete this file once the Drive side is done.**

Locally, the clean-up is finished. 117 presumed duplicates were moved from `pdfs/` into
`pdfs/duplicates/`, not deleted. `pdfs/duplicates/README.md` lists every file moved, the
copy kept for each paper, and the rules used to choose it. `content/pdf-map.json` now names
only kept files, and every publication page's figure-and-cover source is byte-identical to
what it was before the move.

The shared Drive folder `pdfs` is the curated copy but not an exact mirror, so it can't
simply be synced from here.

## 1. Rename eight linked files in Drive (optional, keeps names consistent)

A `Copy` link in `PAYWALL-STATUS.md` points at each of these files. The local copy kept for
each paper is byte-identical but better named. Renaming a file in Drive keeps its link
working, so nothing on the site changes.

| Rename in Drive | To |
| --- | --- |
| `Caldeira_AJS1995.pdf` | `Caldeira_AJS1995_seafloor-basalt.pdf` |
| `Caldeira_Rau_GRL_2000.pdf` | `Caldeira-Rau_GRL2000_accel_weathering_carbonate.pdf` |
| `Cao_et_al_PNAS2010.pdf` | `Cao_et_al_PNAS2010_CO2-physiological-forcing.pdf` |
| `Davis-et-al_Science2010_CO2-emissions-existing-infrastructure - Copy.pdf` | `Davis-et-al_Science2010_CO2-emissions-existing-infrastructure.pdf` |
| `Duffy_Caldeira_GRL1997.pdf` | `Duffy_Caldeira_GRL1997_salinity-sea-ice.pdf` |
| `Govindasamy_etal_2003.pdf` | `Govindasamy_etal_GPC2003.pdf` |
| `Hoffert_etal_Science2002.pdf` | `Hoffert-et-al_Science2002_AdvTechPaths.pdf` |
| `Pagani_et_al_Nature2009.pdf` | `Pagani-et-al_Nature2009_terrestrial-plants-CO2-decline.pdf` |

If a file with the target name already exists in Drive, move that one into `duplicates`
first. **Don't delete the linked file instead**, because that breaks its `Copy` link.

## 2. Mirror the `duplicates` sub-folder in Drive (optional)

Make a `duplicates` sub-folder in the Drive `pdfs` folder. Move into it any file listed in
the "Moved here" column of `pdfs/duplicates/README.md` that is actually in Drive. Some are
not, because the Drive folder was already partly cleaned. None of the moved files is the
target of a `Copy` link.
