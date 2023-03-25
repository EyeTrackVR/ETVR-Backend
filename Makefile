.DEFAULT_GOAL := run

install:
	poetry install

run:
	cd TrackingBackend/ && poetry run uvicorn main:app --reload

pyinstaller:
	poetry run pyinstaller ETVR.spec TrackingBackend/main.py

clean:
	rm tarcker-config.json
	rm TrackingBackend/tacker-config.json
	rm -rf TrackingBackend/__pycache__/
	rm -rf TrackingBackend/app/__pycache__/
	rm -rf TrackingBackend/app/algorithms/__pycache__/
	rm -rf build/
	rm -rf dist/