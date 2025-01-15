# this is just here for convenience
.DEFAULT_GOAL := run

stream1:
	ffmpeg -stream_loop "-1" -i eyetrackvr_backend/assets/ETVR_SAMPLE.mp4 -attempt_recovery 1 -http_persistent 1 -http_seekable 0 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8080

stream2:
	ffmpeg -stream_loop "-1" -i eyetrackvr_backend/assets/ETVR_SAMPLE.mp4 -attempt_recovery 1 -http_persistent 1 -http_seekable 0 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8081

install:
	poetry install

run:
	poetry run uvicorn --factory eyetrackvr_backend:setup_app --reload --port 8000

black:
	poetry run black eyetrackvr_backend/

ruff:
	poetry run ruff eyetrackvr_backend/

mypy:
	poetry run mypy --ignore-missing-imports --check-untyped-defs eyetrackvr_backend/

pyinstaller:
	poetry run pyinstaller ETVR.spec

nuitka:
	poetry run python -m nuitka --standalone --include-module=cv2 eyetrackvr_backend/__main__.py

clean:
	rm -rf eyetrackvr_backend/__pycache__/
	rm -rf eyetrackvr_backend/app/__pycache__/
	rm -rf eyetrackvr_backend/app/algorithms/__pycache__/
	rm -rf build/
	rm -rf dist/
