from flask import Blueprint, request, jsonify
from models import Utilisateur 
from extensions import db 
from sqlalchemy.orm import joinedload 

from werkzeug.security import generate_password_hash

utilisateurs_bp = Blueprint('utilisateurs', __name__)


@utilisateurs_bp.route('/api/utilisateurs', methods=['GET'])
def get_users():
    try:
        users = Utilisateur.query.options(
            joinedload(Utilisateur.unite),
            joinedload(Utilisateur.role)
        ).all()
        
        result = []
        for u in users:
            result.append({
                "id_utilisateur": u.id_utilisateur,
                "email": u.email,
                "id_role": u.id_role,
                "nom_role": u.role.libelle if u.role else 'Utilisateur', 
                "id_unite": u.id_unite,
                "nom_unite": u.unite.libelle if u.unite else '--' 
            })
            
        return jsonify(result), 200
        
    except Exception as err:
        return jsonify({"message": "Erreur", "error": str(err)}), 500


@utilisateurs_bp.route('/api/utilisateurs/<int:id>', methods=['GET'])
def get_user(id):
    try:
        u = Utilisateur.query.filter_by(id_utilisateur=id).first()
        if not u:
            return jsonify({"message": "User not found"}), 404
            
        return jsonify({
            "id_utilisateur": u.id_utilisateur,
            "email": u.email,
            "id_role": u.id_role,
            "nom_role": u.role.libelle if u.role else 'Utilisateur',
            "id_unite": u.id_unite,
            "nom_unite": u.unite.libelle if u.unite else '--'
        }), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@utilisateurs_bp.route('/api/utilisateurs', methods=['POST'])
def create_user():
    try:
        data = request.json 
        if not data or 'email' not in data or 'mot_de_passe' not in data:
            return jsonify({"message": "Email et mot de passe requis"}), 400

        
        mot_de_passe_secure = generate_password_hash(data['mot_de_passe'])

        new_user = Utilisateur(
            email=data['email'],
            mot_de_passe=mot_de_passe_secure,
            id_role=data.get('id_role'),
            id_unite=data.get('id_unite')
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la création", "error": str(e)}), 500


@utilisateurs_bp.route('/api/utilisateurs/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        u = Utilisateur.query.filter_by(id_utilisateur=id).first()
        if not u:
            return jsonify({"message": "User not found"}), 404

        data = request.json 
        u.email = data.get('email', u.email)
        u.id_role = data.get('id_role', u.id_role)
        u.id_unite = data.get('id_unite', u.id_unite)
        
      
        if data.get('mot_de_passe') and data['mot_de_passe'].strip() != '':
            u.mot_de_passe = generate_password_hash(data['mot_de_passe'])
            
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur modification", "error": str(e)}), 500


@utilisateurs_bp.route('/api/utilisateurs/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        u = Utilisateur.query.filter_by(id_utilisateur=id).first()
        if not u:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
            
        try:
            db.session.delete(u)
            db.session.commit()
            return jsonify({"message": "Utilisateur supprimé définitivement"}), 200
        except Exception:
            db.session.rollback()
            u.statut = 'Inactif'
            db.session.commit()
            return jsonify({"message": "Utilisateur désactivé (Soft Delete)"}), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "error": str(e)}), 500