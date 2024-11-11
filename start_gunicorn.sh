#!/bin/bash

CUDA_VISIBLE_DEVICES=0 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn -w 4 -b 69.197.145.4:8000 app:app &
CUDA_VISIBLE_DEVICES=1 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn -w 4 -b 69.197.145.4:8001 app:app &
CUDA_VISIBLE_DEVICES=2 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn -w 4 -b 69.197.145.4:8002 app:app