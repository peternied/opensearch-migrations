#!/usr/bin/env bash
trap 'cd ~/git/opensearch-migrations' EXIT

flake8 $(git ls-files '*.py') || true
./gradlew frontend:build || true
cd TrafficCapture/dockerSolution/src/main/docker/migrationConsole/lib/console_link/ || true
pipenv run test -m "not slow" || true

