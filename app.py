from flask import Flask, request, jsonify, send_file, render_template
from flask import Flask, request, jsonify, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

# 数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'address_book.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 模型 ---
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    methods = db.relationship('ContactMethod', backref='contact', lazy=True, cascade="all, delete-orphan")
    def to_dict(self):
        return {
            'id': self.id, 
            'name': self.name, 
            'is_favorite': self.is_favorite,
            'methods': [m.to_dict() for m in self.methods]
        }

class ContactMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    value = db.Column(db.String(200))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    def to_dict(self):
        return {'type': self.type, 'value': self.value}

with app.app_context():
    db.create_all()

# --- 路由 ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacts', methods=['GET'])
def get_contacts():
    only_fav = request.args.get('favorite')
    if only_fav == 'true':
        contacts = Contact.query.filter_by(is_favorite=True).all()
    else:
        contacts = Contact.query.all()
    return jsonify([c.to_dict() for c in contacts])

@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.json
    new_contact = Contact(name=data['name'])
    if 'methods' in data:
        for m in data['methods']:
            new_method = ContactMethod(type=m['type'], value=m['value'], contact=new_contact)
            db.session.add(new_method)
    db.session.add(new_contact)
    db.session.commit()
    return jsonify(new_contact.to_dict()), 201

@app.route('/contacts/<int:id>/favorite', methods=['PUT'])
def toggle_favorite(id):
    contact = Contact.query.get_or_404(id)
    contact.is_favorite = not contact.is_favorite 
    db.session.commit()
    return jsonify(contact.to_dict())

@app.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# --- 这里的代码就是你报错缺失的部分 ---
@app.route('/export', methods=['GET'])
def export_excel():
    contacts = Contact.query.all()
    data_list = []
    for c in contacts:
        methods_str = "; ".join([f"{m.type}:{m.value}" for m in c.methods])
        data_list.append({
            "Name": c.name,
            "Is Favorite": "Yes" if c.is_favorite else "No",
            "Contact Methods": methods_str
        })
    df = pd.DataFrame(data_list)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contacts')
    output.seek(0)
    return send_file(output, download_name="contacts.xlsx", as_attachment=True)

@app.route('/import', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    try:
        df = pd.read_excel(file)
        for index, row in df.iterrows():
            is_fav = True if row.get('Is Favorite') == 'Yes' else False
            new_contact = Contact(name=row['Name'], is_favorite=is_fav)
            db.session.add(new_contact)
            methods_raw = str(row.get('Contact Methods', ''))
            if methods_raw and methods_raw != 'nan':
                for part in methods_raw.split(';'):
                    if ':' in part:
                        t, v = part.strip().split(':', 1)
                        db.session.add(ContactMethod(type=t, value=v, contact=new_contact))
        db.session.commit()
        return jsonify({"message": "Import successful"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)