#!/usr/bin/env python3
"""
Simple web server for Railway health checks
"""
from flask import Flask, jsonify
import os
import threading
import time

app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot",
        "database": "MySQL",
        "timestamp": time.time()
    })

def run_web_server():
    """Run the web server"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    run_web_server() 