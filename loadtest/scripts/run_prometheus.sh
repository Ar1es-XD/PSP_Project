#!/usr/bin/env bash
set -euo pipefail

prometheus --config.file=loadtest/prometheus/prometheus.yml
