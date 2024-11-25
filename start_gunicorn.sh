#!/bin/bash

CUDA_VISIBLE_DEVICES=0 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn app:app -k uvicorn.workers.UvicornWorker -b 69.197.145.4:8000 -w 4 &
CUDA_VISIBLE_DEVICES=1 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn app:app -k uvicorn.workers.UvicornWorker -b 69.197.145.4:8001 -w 4 &
CUDA_VISIBLE_DEVICES=2 /sdb-disk/9D-Muslim-Ai/asr_live/.venv/bin/gunicorn app:app -k uvicorn.workers.UvicornWorker -b 69.197.145.4:8002 -w 4