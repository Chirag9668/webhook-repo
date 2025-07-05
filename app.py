from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime,timezone
import os
import pytz

app = Flask(__name__)

# MongoDB setup 
client = MongoClient("mongodb+srv://parmchg5699523:z5Lao4ocLXQ2rBZf@webhook-cluster.tzlucgz.mongodb.net/?retryWrites=true&w=majority&appName=webhook-cluster")
db = client["webhook_db"]
collection = db["events"]

# Homepage - fetch events and display them
@app.route("/")
def home():
    events = list(collection.find().sort("timestamp", -1).limit(20))  # show recent 20 events
    for e in events:
        ts = e["timestamp"]
        
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone("Asia/Kolkata"))
    
        e["formatted_time"] = ts.strftime("%d %B %Y - %I:%M %p IST")

    return render_template("index.html", events=events)

# Webhook endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        ist = pytz.timezone("Asia/Kolkata")
        timestamp = datetime.now(ist)

        record = {
            "event_type": "push",
            "author": author,
            "to_branch": to_branch,
            "timestamp": timestamp
        }
        collection.insert_one(record)
        return jsonify({"msg": "Push event stored"}), 200

    elif event_type == "pull_request":
        action = data["action"]
        if action in ["opened", "closed"]:
            author = data["pull_request"]["user"]["login"]
            from_branch = data["pull_request"]["head"]["ref"]
            to_branch = data["pull_request"]["base"]["ref"]
            merged = data["pull_request"].get("merged", False)
            ist = pytz.timezone("Asia/Kolkata")
            timestamp = datetime.now(ist)

            if action == "opened":
                event_type_final = "pull_request"
            elif action == "closed" and merged:
                event_type_final = "merge"
            else:
                return jsonify({"msg": "PR closed but not merged"}), 200

            record = {
                "event_type": event_type_final,
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
            collection.insert_one(record)
            return jsonify({"msg": f"{event_type_final} event stored"}), 200

    return jsonify({"msg": "Event ignored"}), 200

if __name__ == "__main__":
    app.run(debug=True)