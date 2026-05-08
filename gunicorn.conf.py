import os
import multiprocessing

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# 워커 설정
# 주의: Rate Limiter가 memory:// 스토리지를 사용하므로 멀티 워커 환경에서는
# 프로세스별로만 제한이 걸립니다. 엄격한 Rate Limiting이 필요하면:
# 1. WEB_CONCURRENCY=1 로 단일 워커 사용 (간단한 해결책)
# 2. Redis 사용: RATELIMIT_STORAGE_URI=redis://localhost:6379 설정
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "sync"  # 또는 "gthread" for async
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = 5

# 로깅
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# 성능 최적화
max_requests = 1000
max_requests_jitter = 100
preload_app = True  # 메모리 효율성 증가

# 보안
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
