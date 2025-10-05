# tools/make_pus.py — generate PU skeletons quickly
from pathlib import Path

root = Path(__file__).resolve().parents[1]  # project_root/src
pu_dir = root / "src" / "core" / "pu"
pu_dir.mkdir(parents=True, exist_ok=True)

# ցանկդ՝ իրական անուններով պահի
pu_list = [
    "pu00_menu_router","pu01_start","pu02_main_menu","pu03_catalog_ui",
    "pu04_cart","pu05_cart_ui","pu06_checkout_fsm","pu08_checkout_address",
    "pu09_payment","pu10_checkout","pu12_loyalty","pu13_delivery",
    "pu18_admin_import","pu20_notifications","pu31_confirm","pu44_delivery_eta",
    "pu47_wizard",
    # … այստեղ ավելացրու մնացածդ՝ մինչև 50
]

skel = """# -*- coding: utf-8 -*-
# {name}.py — skeleton
def register(bot, ctx):
    # TODO: implement
    pass

def healthcheck(ctx):
    return True
"""

for nm in pu_list:
    f = pu_dir / f"{nm}.py"
    if not f.exists():
        f.write_text(skel.format(name=nm), encoding="utf-8")
        print("created", f)
    else:
        print("exists ", f)
