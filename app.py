from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///domestic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo baseado nas colunas do CSV (ajuste os campos conforme necessário)
class DomesticPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Exemplo de campos - adapte conforme as colunas reais do seu CSV:
    field1 = db.Column(db.String)
    field2 = db.Column(db.String)
    field3 = db.Column(db.String)
    # Adicione todos os campos que o CSV possuir

    def to_dict(self):
        return {
            "id": self.id,
            "field1": self.field1,
            "field2": self.field2,
            "field3": self.field3,
            # Coloque aqui todos os campos para retorno JSON
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/permissions', methods=['GET'])
def get_permissions():
    permissions = DomesticPermission.query.all()
    return jsonify([p.to_dict() for p in permissions])

def import_csv():
    if DomesticPermission.query.first():
        print("Dados já importados.")
        return

    if not os.path.exists('domestic-residence-Permissions.csv.csv'):
        print("Arquivo CSV não encontrado.")
        return

    df = pd.read_csv('domestic-residence-Permissions.csv.csv', encoding='latin1')
    for idx, row in df.iterrows():
        permission = DomesticPermission(
            # Substitua 'field1', 'field2' etc pelos nomes reais das colunas do CSV:
            field1=row['NomeColuna1'],
            field2=row['NomeColuna2'],
            field3=row['NomeColuna3'],
            # Adapte para todas as colunas necessárias
        )
        db.session.add(permission)
    db.session.commit()
    print("Importação concluída.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_csv()
    app.run(debug=True)
