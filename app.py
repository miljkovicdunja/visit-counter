import redis
import logging
import os
import socket
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger=logging.getLogger(__name__)

app=Flask(__name__)

def get_redis():
    return redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        socket_connect_timeout=2,
        decode_response=True,
    )

@app.after_request
def log_request(response):
    logger.info("%s %s -> %s", request.method, request.path, response.status_code)
    return response

@app.get("/")
def index():
    return jsonify(message="Hello DevOps", host=socket.gethostname())

@app.get("/visits")
def visits():
    count=get_redis().incr("visits")
    return jsonify(visits=count)

@app.get("/health")
def health():
    try:
        get_redis().ping()
    except redis.exceptions.RedisError:
        return jsonify(status="error"), 503
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ["APP_PORT"]))