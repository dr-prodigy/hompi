#!/bin/bash
docker buildx build --build-arg TARGET=PI -t dr-prodigy/hompi .
