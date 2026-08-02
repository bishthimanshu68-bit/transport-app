from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)
DB_NAME = "transport.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fleet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_no TEXT NOT NULL,
            driver TEXT NOT NULL,
            phone TEXT,
            status TEXT,
            location TEXT,
            unloading_date TEXT,
            next_program TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM fleet")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO fleet (truck_no, driver, phone, status, location, unloading_date, next_program)
            VALUES ('UP16 AB 2222', 'Ramesh Kumar', '9876543210', 'Available', 'Yard - Greater Noida', '2026-08-01', 'Ready for Dispatch')
        ''')
    conn.commit()
    conn.close()

init_db()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/fleet', methods=['GET'])
def get_fleet():
    rows = query_db("SELECT * FROM fleet ORDER BY id DESC")
    fleet_list = [dict(row) for row in rows]
    return jsonify(fleet_list)

@app.route('/api/fleet/add', methods=['POST'])
def add_fleet():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fleet (truck_no, driver, phone, status, location, unloading_date, next_program)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get("truck_no"),
        data.get("driver"),
        data.get("phone"),
        data.get("status", "Available"),
        data.get("location"),
        data.get("unloading_date"),
        data.get("next_program")
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vehicle added!"})

# UPDATE / EDIT API
@app.route('/api/fleet/update/<int:item_id>', methods=['POST'])
def update_fleet(item_id):
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE fleet 
        SET truck_no=?, driver=?, phone=?, status=?, location=?, unloading_date=?, next_program=?
        WHERE id=?
    ''', (
        data.get("truck_no"),
        data.get("driver"),
        data.get("phone"),
        data.get("status"),
        data.get("location"),
        data.get("unloading_date"),
        data.get("next_program"),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vehicle updated!"})

@app.route('/api/fleet/delete/<int:item_id>', methods=['DELETE'])
def delete_fleet(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fleet WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vehicle Deleted!"})

@app.route('/export/excel', methods=['GET'])
def export_excel():
    rows = query_db("SELECT * FROM fleet")
    fleet_list = [dict(row) for row in rows]
    
    output = io.BytesIO()
    df_fleet = pd.DataFrame(fleet_list)
    df_summary = pd.DataFrame([
        {"Metric": "Total Fleet", "Value": len(fleet_list)},
        {"Metric": "Available Trucks", "Value": sum(1 for x in fleet_list if x['status'] == 'Available')},
        {"Metric": "Report Date", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    ])
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary Dashboard', index=False)
        df_fleet.to_excel(writer, sheet_name='Fleet Master', index=False)
        
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'Transport_Fleet_Report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)