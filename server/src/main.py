if __package__ in (None, ""):
	import sys
	from pathlib import Path

	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os

from src import create_app

app = create_app()


if __name__ == "__main__":
	debug = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes"}
	app.run(debug=debug)
