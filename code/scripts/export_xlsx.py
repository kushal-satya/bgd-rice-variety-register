"""Write the pilot (or full) output tables into one workbook with frozen headers and filters."""
import sys, pandas as pd
suf = "_pilot" if (len(sys.argv) < 2 or sys.argv[1] == "pilot") else ""
sheets = {"rice_varieties": f"rice_varieties{suf}", "local_names": f"local_names{suf}",
          "fish_strains": f"fish_strains{suf}", "fish_events": f"fish_events{suf}",
          "rice_not_approved": f"rice_not_approved_or_unresolved{suf}", "conflicts": f"conflicts{suf}", "sources": f"sources{suf}",
          "failures": f"failures{suf}"}
out = f"05_output/bgd_variety_archive{suf}.xlsx"
with pd.ExcelWriter(out, engine="openpyxl") as xw:
    for name, f in sheets.items():
        import os
        if not os.path.exists(f"05_output/{f}.csv"):
            continue
        df = pd.read_csv(f"05_output/{f}.csv", dtype=str).fillna("")
        df.to_excel(xw, sheet_name=name, index=False)
        ws = xw.sheets[name]; ws.freeze_panes = "B2"; ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(45, max(10, max(len(str(c.value or "")) for c in col[:50]) * 0.9))
    sc = pd.read_csv("06_validation/spot_checks_pilot.csv" if suf else "06_validation/spot_checks.csv", dtype=str).fillna("")
    sc.to_excel(xw, sheet_name="spot_checks", index=False)
print(out)
