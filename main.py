from pathlib import Path
import sys
import os
import shutil

import dairy_app


# ==============================
# DATABASE LOCATION
# ==============================

if sys.platform == "android":

    private_folder = Path(
        os.environ.get(
            "ANDROID_PRIVATE",
            os.getcwd()
        )
    )

    private_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    android_db = private_folder / "dairy_farm.db"

    bundled_db = (
        Path(__file__).resolve().parent
        / "dairy_farm.db"
    )

    if not android_db.exists() and bundled_db.exists():
        shutil.copy2(
            bundled_db,
            android_db
        )

    dairy_app.DATABASE = str(android_db)

else:

    dairy_app.DATABASE = str(
        Path(__file__).resolve().parent
        / "dairy_farm.db"
    )


# ==============================
# DATABASE INITIALIZATION
# ==============================

dairy_app.init_database()


# ==============================
# CREATE APPLICATION
# ==============================

app = dairy_app.QApplication(sys.argv)


# ==============================
# LOGIN
# ==============================

login = dairy_app.LoginDialog()

if login.exec() != dairy_app.QDialog.DialogCode.Accepted:
    sys.exit(0)


# ==============================
# MAIN DAIRY FARM APP
# ==============================

window = dairy_app.DairyAppBuilder()

window.show()


# ==============================
# START APPLICATION
# ==============================

sys.exit(app.exec())
