from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import io
from flask import send_file
app = Flask(__name__)

# 配置 SQLite 数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'address_book.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 模型定义 (Models) ---

# 主联系人表
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # 作业 1.1: 收藏功能 (
    is_favorite = db.Column(db.Boolean, default=False) 
    
    # 建立关系：一个联系人对应多个联系方式
    methods = db.relationship('ContactMethod', backref='contact', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_favorite': self.is_favorite,
            'methods': [m.to_dict() for m in self.methods] # 嵌套返回联系方式
        }

# 联系方式表 
class ContactMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50)) # 例如: "phone", "email", "wechat"
    value = db.Column(db.String(200)) # 具体号码或账号
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)

    def to_dict(self):
        return {'type': self.type, 'value': self.value}

# 初始化数据库
with app.app_context():
    db.create_all()

@app.route('/')
def hello():
    return "Backend is running!"

# 1. 获取所有联系人 (支持按是否收藏筛选)
@app.route('/contacts', methods=['GET'])
def get_contacts():
    # 如果前端传了 ?favorite=true，就只查收藏的
    only_fav = request.args.get('favorite')
    
    if only_fav == 'true':
        contacts = Contact.query.filter_by(is_favorite=True).all()
    else:
        contacts = Contact.query.all()
        
    return jsonify([c.to_dict() for c in contacts])

# 2. 添加联系人 (支持同时添加多个联系方式)
@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.json
    # data 格式示例: {"name": "Alice", "methods": [{"type": "phone", "value": "12345"}, {"type": "email", "value": "a@a.com"}]}
    
    new_contact = Contact(name=data['name'])
    
    # 处理多种联系方式
    if 'methods' in data:
        for m in data['methods']:
            new_method = ContactMethod(type=m['type'], value=m['value'], contact=new_contact)
            db.session.add(new_method)
            
    db.session.add(new_contact)
    db.session.commit()
    return jsonify(new_contact.to_dict()), 201

# 3. 收藏/取消收藏联系人 
@app.route('/contacts/<int:id>/favorite', methods=['PUT'])
def toggle_favorite(id):
    contact = Contact.query.get_or_404(id)
    # 切换状态：如果是True变False，反之亦然
    contact.is_favorite = not contact.is_favorite 
    db.session.commit()
    return jsonify(contact.to_dict())

# 4. 删除联系人
@app.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'message': 'Deleted'})
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)

    # 5. 导出为 Excel 
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
    
    # 保存到内存流中，而不是存到硬盘
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contacts')
    output.seek(0)
    
    return send_file(output, download_name="contacts.xlsx", as_attachment=True)

# 6. 从 Excel 导入 
@app.route('/import', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    
    try:
        df = pd.read_excel(file)
        # 假设 Excel 列名是: Name, Is Favorite, Contact Methods (格式: type:value; type:value)
        
        for index, row in df.iterrows():
            # 创建联系人
            is_fav = True if row.get('Is Favorite') == 'Yes' else False
            new_contact = Contact(name=row['Name'], is_favorite=is_fav)
            db.session.add(new_contact)
            
            # 解析联系方式字符串
            methods_raw = str(row.get('Contact Methods', ''))
            if methods_raw and methods_raw != 'nan':
                method_parts = methods_raw.split(';')
                for part in method_parts:
                    if ':' in part:
                        m_type, m_value = part.strip().split(':', 1)
                        new_method = ContactMethod(type=m_type, value=m_value, contact=new_contact)
                        db.session.add(new_method)
                        
        db.session.commit()
        return jsonify({"message": "Import successful"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500