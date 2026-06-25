from flask import Blueprint, request, jsonify
from models import Norme, Partie
from extensions import db
from sqlalchemy.orm import joinedload
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

normes_bp = Blueprint('normes', __name__)


@normes_bp.route('/api/normes', methods=['GET'])
@jwt_required() 
def get_normes():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite_user = claims.get("id_unite")

        
        query = Norme.query.options(joinedload(Norme.parties))

        if role_code != "ADMIN":
            if id_unite_user is not None:
                query = query.filter(Norme.id_unite == int(id_unite_user))
            else:
                return jsonify([]), 200

        normes = query.all()

        result = []
        for n in normes:
            result.append({
                "id_norme": n.id_norme,
                "libelle": n.libelle,
                "id_utilisateur": n.id_utilisateur,
                "id_unite": n.id_unite,
                "parties": [
                    {
                        "id_partie": p.id_partie,
                        "no_partie": p.no_partie,
                        "titre": p.titre
                    }
                    for p in n.parties
                ] if n.parties else []
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@normes_bp.route('/api/normes', methods=['POST'])
@jwt_required()
def create_norme():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        id_unite_user = claims.get("id_unite")

        data = request.get_json()

        if not data or not data.get("libelle"):
            return jsonify({"message": "Le libellé de la norme est obligatoire"}), 400

        resolved_unite_id = int(id_unite_user) if id_unite_user is not None else None

        norme = Norme(
            libelle=data.get("libelle"),
            id_utilisateur=int(current_user_id), 
            id_unite=resolved_unite_id
        )

        db.session.add(norme)
        db.session.flush()

        for p in data.get("parties", []):
            if p.get("titre"):
                partie = Partie(
                    no_partie=p.get("no_partie"),
                    titre=p.get("titre"),
                    id_norme=norme.id_norme
                )
                db.session.add(partie)

        db.session.commit()
        return jsonify({"message": "Norme créée avec succès"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@normes_bp.route('/api/normes/<int:id>', methods=['PUT'])
@jwt_required()
def update_norme(id):
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role_code = claims.get("role_code")

     
        norme = Norme.query.options(joinedload(Norme.parties)).get(id)
        if not norme:
            return jsonify({"message": "Norme introuvable"}), 404

        if role_code != "ADMIN" and str(norme.id_utilisateur) != str(current_user_id):
            return jsonify({"message": "Modification non autorisée"}), 403

        data = request.get_json()
        if not data or not data.get("libelle"):
            return jsonify({"message": "Le libellé de la norme est obligatoire"}), 400
            
    
        norme.libelle = data.get("libelle", norme.libelle)

      
        norme.parties.clear()

      
        for p in data.get("parties", []):
            if p.get("titre"):
                nouvelle_partie = Partie(
                    no_partie=p.get("no_partie"),
                    titre=p.get("titre")
                    
                )
                norme.parties.append(nouvelle_partie)

        db.session.commit()
        return jsonify({"message": "Norme modifiée avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@normes_bp.route('/api/normes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_norme(id):
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role_code = claims.get("role_code")

        norme = Norme.query.get(id)
        if not norme:
            return jsonify({"message": "Norme introuvable"}), 404

        if role_code != "ADMIN" and str(norme.id_utilisateur) != str(current_user_id):
            return jsonify({"message": "Suppression non autorisée"}), 403

        db.session.delete(norme)
        db.session.commit()

        return jsonify({"message": "Norme supprimée avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500