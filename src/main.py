from flask import Flask
from datetime import datetime, timezone

app = Flask(__name__)


start_time = datetime.now(timezone.utc)

@app.route("/health")
def health_check():
    now = datetime.now(timezone.utc)
    
    totalSecs = int((now - start_time).total_seconds())
    
    hr = totalSecs // 3600
    result = totalSecs % 3600
    min = result // 60
    sec = result % 60
    
    uptime_format = f"{hr:02d}:{min:02d}:{sec:02d}"
    
    timeNow = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "nama": "Puspita Wijayanti Kusuma",
        "nrp": "5025241059", 
        "status": "UP",
        "timestamp": timeNow,
        "uptime": uptime_format
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)