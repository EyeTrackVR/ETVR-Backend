.DEFAULT_GOAL := run

install:
	poetry install

run:
	cd TrackingBackend/ && poetry run uvicorn main:app --reload

clean:
	rm -rf TrackingBackend/__pycache__/
	rm -rf TrackingBackend/app/__pycache__/
	rm -rf TrackingBackend/app/algorithms/__pycache__/
	rm -rf build/
	rm -rf dist/