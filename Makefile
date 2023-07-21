# this is just here for convenience
.DEFAULT_GOAL := run

stream1:
	ffmpeg -stream_loop "-1" -i TrackingBackend/assets/ETVR_SAMPLE.mp4 -attempt_recovery 1 -http_persistent 1 -http_seekable 0 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8080

stream2:
	ffmpeg -stream_loop "-1" -i TrackingBackend/assets/ETVR_SAMPLE.mp4 -attempt_recovery 1 -http_persistent 1 -http_seekable 0 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8081

install:
	poetry install

run:
	cd TrackingBackend/ && poetry run uvicorn --factory main:setup_app --reload --port 8000

black:
	poetry run black TrackingBackend/

ruff:
	poetry run ruff TrackingBackend/

mypy:
	poetry run mypy --ignore-missing-imports --check-untyped-defs TrackingBackend/

pyinstaller:
	poetry run pyinstaller ETVR.spec TrackingBackend/main.py

nuitka:
	poetry run python -m nuitka --standalone --include-module=cv2 TrackingBackend/main.py

clean:
	rm tarcker-config.json
	rm TrackingBackend/tacker-config.json
	rm -rf TrackingBackend/__pycache__/
	rm -rf TrackingBackend/app/__pycache__/
	rm -rf TrackingBackend/app/algorithms/__pycache__/
	rm -rf build/
	rm -rf dist/