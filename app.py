import os
import json
import sqlite3
import openai
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from hubspot import push_snapshot_to_hubspot

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
DB_PATH = 'scout.db'

def auto_tag(industry, size):
    tags = []
    industry = industry.lower()
    if "health" in industry or "med" in industry:
        tags.append("Compliance Risk")
    if "tech" in industry or "startup" in industry:
        tags.append("Rapid Tech Change")
    if size.isdigit() and int(size) > 1000:
        tags.append("Talent Pipeline Issues")
    if not tags:
        tags.append("General Training Need")
    return tags

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        industry = request.form['industry']
        size = request.form['size']
        region = request.form['region']
        nudge = ""

        tags = auto_tag(industry, size)
        tag_string = ', '.join(tags)

        prompt = f"""
You are helping a consultative AE plan for a conversation about AI readiness, upskilling, and workforce enablement.

Prospect:
- Name: {name}
- Industry: {industry}
- Size: {size}
- Region: {region}
- Likely Needs: {tag_string}

First, write a 3–5 sentence summary describing the account context and inferred priorities. Make it conversational, like you'd explain it to a teammate.

Then output:
1. Three openers or starter lines
2. Signals or objections to listen for
3. A one-line positioning statement aligned with Centriq’s mission
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            content = response.choices[0].message.content.strip()
            lines = content.splitlines()
            split_index = next((i for i, line in enumerate(lines) if line.strip().lower().startswith("1.")), None)

            if split_index is not None:
                summary = "\n".join(lines[:split_index]).strip()
                discovery = "\n".join(lines[split_index:]).strip()
            else:
                summary = ""
                discovery = content
        except Exception as e:
            summary = "Error generating summary."
            discovery = f"Error generating suggestions: {str(e)}"

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO snapshots (name, industry, size, region, tags, nudge, summary, discovery, pushed_to_hubspot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (name, industry, size, region, tag_string, nudge, summary, discovery))
        snapshot_id = c.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for('result', snapshot_id=snapshot_id))

    return render_template('index.html')

@app.route('/result/<int:snapshot_id>')
def result(snapshot_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
    snapshot = c.fetchone()
    conn.close()

    if not snapshot:
        return "Snapshot not found", 404

    return render_template('result.html', snapshot=snapshot)

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM snapshots ORDER BY created_at DESC')
    records = c.fetchall()
    conn.close()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('history.html', records=records, now=now)

@app.route('/nudge/<int:snapshot_id>', methods=['GET', 'POST'])
def nudge(snapshot_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
    snapshot = c.fetchone()

    if not snapshot:
        return "Snapshot not found", 404

    if request.method == 'POST':
        new_nudge = request.form['nudge']
        prompt = f"""
Update the AE's discovery planning with this new context:

Nudge: {new_nudge}

Original Snapshot:
- Prospect: {snapshot['name']}
- Industry: {snapshot['industry']}
- Size: {snapshot['size']}
- Region: {snapshot['region']}
- Likely Needs: {snapshot['tags']}

The AE is focused on:
- Capability gaps in AI readiness
- Org dynamics around training and tech adoption
- Conversational discovery, not scripted selling

Return:
1. Three new follow-up lines
2. Updated objection signals
3. A refined Centriq-style positioning statement
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            updated_discovery = response.choices[0].message.content.strip()
        except Exception as e:
            updated_discovery = f"Error generating new insights: {str(e)}"

        c.execute('UPDATE snapshots SET nudge = ?, discovery = ? WHERE id = ?',
                  (new_nudge, updated_discovery, snapshot_id))
        conn.commit()
        conn.close()

        return redirect(url_for('result', snapshot_id=snapshot_id))

    conn.close()
    return render_template('nudge.html', snapshot=snapshot)

@app.route('/autofill', methods=['POST'])
def autofill():
    name = request.json.get('name')
    if not name:
        return jsonify({'error': 'No name provided'}), 400

    prompt = f"""
Given the company name "{name}", estimate and return this JSON:
{{
  "industry": "...",
  "size": "...",
  "region": "..."
}}
Only return valid JSON.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        content = response.choices[0].message.content.strip()
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        json_text = content[json_start:json_end]
        data = json.loads(json_text)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/push/<int:snapshot_id>', methods=['POST'])
def push(snapshot_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
    snapshot = c.fetchone()

    if not snapshot:
        conn.close()
        return jsonify({'error': 'Snapshot not found'}), 404

    try:
        success, msg = push_snapshot_to_hubspot(
            snapshot['name'], snapshot['summary'], snapshot['discovery']
        )
        if success:
            c.execute('UPDATE snapshots SET pushed_to_hubspot = 1 WHERE id = ?', (snapshot_id,))
            conn.commit()
        else:
            print("❌ HubSpot push failed:", msg)
            return jsonify({'error': msg}), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
