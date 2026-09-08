import sys
import os
import shutil
from pathlib import Path

import dairy_app


if sys.platform == "android":
    private_folder = Path(
        os.environ.get("ANDROID_PRIVATE", os.getcwd())
    )

    private_folder.mkdir(parents=True, exist_ok=True)

    android_db = private_folder / "dairy_farm.db"

    bundled_db = Path(__file__).resolve().parent / "dairy_farm.db"

    if not android_db.exists() and bundled_db.exists():
        shutil.copy2(bundled_db, android_db)

    dairy_app.DATABASE = str(android_db)

else:
    dairy_app.DATABASE = str(
        Path(__file__).resolve().parent / "dairy_farm.db"
    )


dairy_app.init_database()

app = dairy_app.QApplication(sys.argv)

window = dairy_app.DairyAppBuilder()

window.show()

sys.exit(app.exec())
