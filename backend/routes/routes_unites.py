from flask import Blueprint, request, jsonify
from models import Unite, DomaineActivite, Famille, Norme, Ville, Utilisateur, EssaiUnite
from extensions import db
from sqlalchemy import func

unites_bp = Blueprint('unites', __name__)

@unites_bp.route('/api/domaines', methods=['GET'])
def get_domaines():
    domaines = DomaineActivite.query.all()
    return jsonify([{"id_domaine": d.id_domaine, "libelle": d.libelle} for d in domaines]), 200

@unites_bp.route('/api/unites/familles', methods=['GET'])
def get_familles():
    familles = Famille.query.all()
    return jsonify([{"id_famille": f.id_famille, "nom_famille": f.nom_famille} for f in familles]), 200

@unites_bp.route('/api/unite/normes', methods=['GET'])
def get_normes():
    normes = Norme.query.all()
    return jsonify([{"id_norme": n.id_norme, "libelle": n.libelle} for n in normes]), 200

@unites_bp.route('/api/villes', methods=['GET'])
def get_villes():
    villes = Ville.query.all()
    return jsonify([{"id_ville": v.id_ville, "nom_ville": v.nom_ville} for v in villes]), 200

@unites_bp.route('/api/unites', methods=['GET'])
def get_unites():
    try:
        unites = Unite.query.all()
        result = []
        for u in unites:
       
            id_ville_val = getattr(u, 'id_ville', None)
            nom_ville = "Ville Inconnue"
            
      
            if id_ville_val:
                ville_obj = Ville.query.filter_by(id_ville=id_ville_val).first()
                if ville_obj:
                    nom_ville = ville_obj.nom_ville
            elif hasattr(u, 'ville') and u.ville:
                nom_ville = u.ville.nom_ville
                id_ville_val = u.ville.id_ville
            
            result.append({
                "id_unite": u.id_unite,
                "libelle": u.libelle or getattr(u, 'nom_unite', ''),
                "nom_unite": u.libelle,
                "contact": u.contact,
                "id_ville": id_ville_val,
                "nom_ville": nom_ville, 
                "type": u.type
            })
        return jsonify(result), 200
    except Exception as err:
        return jsonify({"message": "Erreur lors de la récupération", "error": str(err)}), 500

@unites_bp.route('/api/unites/<int:id>', methods=['GET'])
def get_unite(id):
    try:
        u = Unite.query.filter_by(id_unite=id).first()
        if not u:
            return jsonify({"message": "Unité non trouvée"}), 404
            
        id_ville_val = getattr(u, 'id_ville', None)
        nom_ville = "Ville Inconnue"
        
        if id_ville_val:
            ville_obj = Ville.query.filter_by(id_ville=id_ville_val).first()
            if ville_obj:
                nom_ville = ville_obj.nom_ville
        elif hasattr(u, 'ville') and u.ville:
            nom_ville = u.ville.nom_ville
            id_ville_val = u.ville.id_ville

        return jsonify({
            "id_unite": u.id_unite,
            "libelle": u.libelle,
            "contact": u.contact,
            "id_ville": id_ville_val,
            "nom_ville": nom_ville,
            "type": u.type
        }), 200
    except Exception as err:
        return jsonify({"message": "Erreur", "error": str(err)}), 500

def extraire_id_ville(ville_data):
    if not ville_data:
        return None
    
    if isinstance(ville_data, dict):
        return ville_data.get('id_ville')
        
    if isinstance(ville_data, int):
        return ville_data
        
    if isinstance(ville_data, str):
        if ville_data.isdigit():
            return int(ville_data)
        else:
            v = Ville.query.filter_by(nom_ville=ville_data).first()
            if v:
                return v.id_ville
    return None

@unites_bp.route('/api/unites', methods=['POST'])
def create_unite():
    try:
        data = request.json
        if not data or 'libelle' not in data:
            return jsonify({"message": "Champs obligatoires manquants"}), 400

        max_id = db.session.query(func.max(Unite.id_unite)).scalar() or 0
        next_id = max_id + 1

        raw_ville = data.get('id_ville') or data.get('la_ville')
        id_ville_val = extraire_id_ville(raw_ville)

        new_unite = Unite(
            id_unite=next_id,
            libelle=data.get('libelle'),
            contact=data.get('contact'),
            id_ville=id_ville_val, 
            type=data.get('type', 'Public')
        )
        db.session.add(new_unite)
        db.session.commit()
        return jsonify({"message": "Unité créée avec succès!", "id_unite": next_id}), 201
    except Exception as err:
        db.session.rollback()
        return jsonify({"message": "Erreur interne", "details": str(err)}), 500

@unites_bp.route('/api/unites/<int:id>', methods=['PUT'])
def update_unite(id):
    try:
        u = Unite.query.filter_by(id_unite=id).first()
        if not u:
            return jsonify({"message": "Unité non trouvée"}), 404
        
        data = request.json
        u.libelle = data.get('libelle', u.libelle)
        u.contact = data.get('contact', u.contact)
        u.type = data.get('type', u.type)
        
        raw_ville = data.get('id_ville') or data.get('la_ville')
        if raw_ville:
            id_ville_val = extraire_id_ville(raw_ville)
            if id_ville_val:
                u.id_ville = id_ville_val

        db.session.commit()
        return jsonify({"message": "Unité modified avec succès"}), 200
    except Exception as err:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la modification", "details": str(err)}), 500

@unites_bp.route('/api/unites/<int:id>', methods=['DELETE'])
def delete_unite(id):
    try:
        u = Unite.query.filter_by(id_unite=id).first()
        if not u:
            return jsonify({"message": "Unité non trouvée"}), 404
            
        Utilisateur.query.filter_by(id_unite=id).update({Utilisateur.id_unite: None})
        db.session.query(EssaiUnite).filter_by(id_unite=id).delete(synchronize_session=False)

        db.session.delete(u)
        db.session.commit()
        return jsonify({"message": "Unité supprimée avec succès"}), 200
    except Exception as err:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "error": str(err)}), 500