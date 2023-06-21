# this is just here for convenience
.DEFAULT_GOAL := run

stream1:
	ffmpeg -stream_loop -1 -i TrackingBackend/assets/ETVR_SAMPLE.mp4 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8080

stream2:
	ffmpeg -stream_loop -1 -i TrackingBackend/assets/ETVR_SAMPLE.mp4 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://localhost:8081

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