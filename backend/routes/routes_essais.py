import json
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from models import Essai, EssaiNorme, EssaiUnite, EssaiGrandeur, Partie, Norme 
# استيراد نقي ومباشر من الـ extensions لتفادي الـ circular import
from extensions import db, socketio
from sqlalchemy.orm import joinedload
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

essais_bp = Blueprint('essais', __name__)


def clean_int_id(value):
    if value is None or str(value).strip() == "" or str(value).strip().lower() == "null":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def check_if_admin(claims):
    role = str(claims.get("role_code") or claims.get("role") or "").upper().strip()
    return "ADMIN" in role or role == "ADMINISTRATEUR" or claims.get("is_admin") is True

def serialize_parties(parties_data):
    if isinstance(parties_data, list):
        return ",".join(map(str, [p for p in parties_data if p is not None and str(p).strip() != ""]))
    if parties_data is not None and str(parties_data).strip() != "":
        return str(parties_data)
    return None

def deserialize_parties(id_partie_value):
    if not id_partie_value:
        return []
    if isinstance(id_partie_value, int):
        return [id_partie_value]
    if isinstance(id_partie_value, str):
        return [int(p) for p in id_partie_value.split(",") if p.strip().isdigit()]
    return []


@essais_bp.route('/api/unite/normes', methods=['GET'])
@jwt_required() 
def get_normes_with_parties():
    try:
        claims = get_jwt()
        id_unite_user = claims.get("id_unite")
        query = Norme.query.options(joinedload(Norme.parties))
        
        if not check_if_admin(claims):
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
                    {"id_partie": p.id_partie, "no_partie": p.no_partie, "titre": p.titre} 
                    for p in n.parties
                ] if hasattr(n, 'parties') and n.parties else []
            })
        return jsonify(result), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@essais_bp.route('/api/essais', methods=['GET'])
@jwt_required() 
def get_essais():
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None

        base_options = [
            joinedload(Essai.domaine), joinedload(Essai.famille),
            joinedload(Essai.sous_famille), joinedload(Essai.partie),
            joinedload(Essai.normes), joinedload(Essai.unites), joinedload(Essai.grandeurs)
        ]

        if check_if_admin(claims):
            essais = Essai.query.options(*base_options).all()
        else:
            essais = Essai.query.options(*base_options).filter(
                (Essai.id_utilisateur == current_user_id) | 
                (Essai.unites.any(id_unite=id_unite_int))
            ).all()

        result = []
        for e in essais:
            norme = e.normes[0] if e.normes else None
            unite = e.unites[0] if e.unites else None
            result.append({
                "id_essai": e.id_essai,
                "intitule": e.intitule,
                "type": e.type,
                "id_partie": deserialize_parties(e.id_partie),
                "nom_partie": e.partie.titre if (hasattr(e, 'partie') and e.partie) else None,
                "id_domaine": e.id_domaine,
                "nom_domaine": e.domaine.libelle if e.domaine else None,
                "id_famille": e.id_famille,
                "nom_famille": e.famille.nom_famille if e.famille else None,
                "id_sous_famille": e.id_sous_famille,
                "nom_sous_famille": e.sous_famille.libelle if e.sous_famille else None,
                "id_norme": norme.id_norme if norme else None,
                "nom_norme": norme.libelle if norme else None,
                "id_unite": unite.id_unite if unite else None,
                "nom_unite": unite.libelle if unite else None,
                "nom_ville": unite.ville.nom_ville if (unite and hasattr(unite, 'ville') and unite.ville) else None,
                "id_utilisateur": e.id_utilisateur,
                "cree": e.cree.isoformat() if hasattr(e, 'cree') and e.cree else None,
                "grandeurs": [g.id_grandeur for g in e.grandeurs] if e.grandeurs else []
            })
        return jsonify(result), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@essais_bp.route('/api/essais/<int:id>', methods=['GET'])
@jwt_required()
def get_essai(id):
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None

        query = Essai.query.options(
            joinedload(Essai.domaine), joinedload(Essai.famille),
            joinedload(Essai.sous_famille), joinedload(Essai.partie),
            joinedload(Essai.normes), joinedload(Essai.unites), joinedload(Essai.grandeurs)
        ).filter(Essai.id_essai == id)

        if not check_if_admin(claims):
            query = query.filter(
                (Essai.id_utilisateur == current_user_id) | 
                (Essai.unites.any(id_unite=id_unite_int))
            )

        e = query.first()
        if not e:
            return jsonify({"message": "Essai non trouvé"}), 404

        norme = e.normes[0] if e.normes else None
        unite = e.unites[0] if e.unites else None

        return jsonify({
            "id_essai": e.id_essai, 
            "intitule": e.intitule, 
            "type": e.type,
            "id_domaine": e.id_domaine, 
            "id_famille": e.id_famille, 
            "id_sous_famille": e.id_sous_famille,
            "id_partie": deserialize_parties(e.id_partie), 
            "id_utilisateur": e.id_utilisateur,
            "nom_partie": e.partie.titre if (hasattr(e, 'partie') and e.partie) else None,
            "id_norme": norme.id_norme if norme else None, 
            "id_unite": unite.id_unite if unite else None,
            "grandeurs": [g.id_grandeur for g in e.grandeurs] if e.grandeurs else []
        }), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@essais_bp.route('/api/essais', methods=['POST'])
@jwt_required()
def create_essai():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.json
        if not data or 'intitule' not in data or 'type' not in data:
            return jsonify({"message": "Données invalides : 'intitule' et 'type' requis"}), 400

        id_domaine_clean = clean_int_id(data.get('id_domaine'))
        id_famille_clean = clean_int_id(data.get('id_famille'))
        id_sous_famille_clean = clean_int_id(data.get('id_sous_famille'))
        serialized_partie_value = serialize_parties(data.get('id_partie'))

        new_essai = Essai(
            intitule=str(data['intitule']).strip(),
            type=str(data['type']).strip(),
            id_domaine=id_domaine_clean,
            id_famille=id_famille_clean,
            id_sous_famille=id_sous_famille_clean,
            id_partie=serialized_partie_value,
            id_utilisateur=current_user_id 
        )

        db.session.add(new_essai)
        db.session.flush()

        id_norme_clean = clean_int_id(data.get('id_norme'))
        if id_norme_clean is not None:
            db.session.add(EssaiNorme(id_essai=new_essai.id_essai, id_norme=id_norme_clean))

        id_unite_clean = clean_int_id(data.get('id_unite'))
        unite_name = "LPEE"
        if id_unite_clean is not None:
            db.session.add(EssaiUnite(id_essai=new_essai.id_essai, id_unite=id_unite_clean))
            try:
                from models import Unite
                unite_obj = db.session.get(Unite, id_unite_clean)
                if unite_obj:
                    unite_name = unite_obj.libelle
            except:
                pass

        grandeurs_list = data.get('grandeurs', []) or []
        if isinstance(grandeurs_list, list):
            for g_id in grandeurs_list:
                g_id_clean = clean_int_id(g_id)
                if g_id_clean is not None:
                    db.session.add(EssaiGrandeur(id_essai=new_essai.id_essai, id_grandeur=g_id_clean))

        db.session.commit()

        user_email = f"Opérateur {current_user_id}"
        try:
            from models import Utilisateur
            user_obj = db.session.get(Utilisateur, current_user_id)
            if user_obj:
                user_email = user_obj.email
        except:
            pass

        # إرسال الإشعار اللحظي للجميع تلقائياً
        try:
            socketio.emit('notification_essai', {
                "id": int(time.time()),
                "user": user_email,
                "unite": unite_name,
                "action": "CREATE",
                "details": new_essai.intitule,
                "date": datetime.utcnow().isoformat()
            })
            print("🟢 [SUCCESS] Notification émise avec succès via WebSocket (extensions.socketio)")
        except Exception as socket_err:
            print(f"⚠️ Erreur SocketIO lors de la création: {str(socket_err)}")

        return jsonify({"message": "Essai créé avec succès", "id_essai": new_essai.id_essai}), 201
    except Exception as err:
        db.session.rollback()
        print(f"❌ [CRITICAL 500] Erreur lors de la création: {str(err)}")
        return jsonify({"error": "Internal Server Error", "details": str(err)}), 500


@essais_bp.route('/api/essais/<int:id>', methods=['PUT'])
@jwt_required()
def update_essai(id):
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        id_unite_user = claims.get("id_unite")
        id_unite_user_int = int(id_unite_user) if id_unite_user is not None else None

        e = db.session.query(Essai).options(joinedload(Essai.unites)).filter_by(id_essai=id).first()
        if not e:
            return jsonify({"message": "Essai non trouvé"}), 404

        has_unit_access = any(u.id_unite == id_unite_user_int for u in e.unites) if e.unites else False
        if not check_if_admin(claims) and e.id_utilisateur != current_user_id and not has_unit_access:
            return jsonify({"message": "Modification non autorisée"}), 403

        data = request.json

        if 'intitule' in data: e.intitule = str(data['intitule']).strip()
        if 'type' in data: e.type = str(data['type']).strip()
        if 'id_domaine' in data: e.id_domaine = clean_int_id(data['id_domaine'])
        if 'id_famille' in data: e.id_famille = clean_int_id(data['id_famille'])
        if 'id_sous_famille' in data: e.id_sous_famille = clean_int_id(data['id_sous_famille'])
        if 'id_partie' in data: e.id_partie = serialize_parties(data['id_partie'])

        unite_name = "LPEE"
        if 'id_unite' in data:
            db.session.query(EssaiUnite).filter_by(id_essai=id).delete()
            id_unite_clean = clean_int_id(data['id_unite'])
            if id_unite_clean is not None:
                db.session.add(EssaiUnite(id_essai=id, id_unite=id_unite_clean))
                try:
                    from models import Unite
                    unite_obj = db.session.get(Unite, id_unite_clean)
                    if unite_obj:
                        unite_name = unite_obj.libelle
                except:
                    pass
        else:
            if e.unites:
                unite_name = e.unites[0].libelle

        if 'grandeurs' in data:
            db.session.query(EssaiGrandeur).filter_by(id_essai=id).delete()
            grandeurs_list = data.get('grandeurs', []) or []
            if isinstance(grandeurs_list, list):
                for g_id in grandeurs_list:
                    g_id_clean = clean_int_id(g_id)
                    if g_id_clean is not None:
                        db.session.add(EssaiGrandeur(id_essai=id, id_grandeur=g_id_clean))

        db.session.commit()

        user_email = f"Opérateur {current_user_id}"
        try:
            from models import Utilisateur
            user_obj = db.session.get(Utilisateur, current_user_id)
            if user_obj:
                user_email = user_obj.email
        except:
            pass

        try:
            socketio.emit('notification_essai', {
                "id": int(time.time()),
                "user": user_email,
                "unite": unite_name,
                "action": "UPDATE",
                "details": e.intitule,
                "date": datetime.utcnow().isoformat()
            })
            print("🟢 [SUCCESS] Notification émise avec succès via WebSocket (extensions.socketio)")
        except Exception as socket_err:
            print(f"⚠️ Erreur SocketIO lors de la modification: {str(socket_err)}")

        return jsonify({"message": "Essai modifié avec succès"}), 200
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": str(err)}), 500


@essais_bp.route('/api/essais/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_essai(id):
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        id_unite_user = claims.get("id_unite")
        id_unite_user_int = int(id_unite_user) if id_unite_user is not None else None

        e = db.session.query(Essai).options(
            joinedload(Essai.normes),
            joinedload(Essai.unites),
            joinedload(Essai.grandeurs)
        ).filter_by(id_essai=id).first()
        
        if not e:
            return jsonify({"message": "Essai non trouvé"}), 404

        has_unit_access = any(u.id_unite == id_unite_user_int for u in e.unites) if e.unites else False
        if not check_if_admin(claims) and e.id_utilisateur != current_user_id and not has_unit_access:
            return jsonify({"message": "Suppression non autorisée"}), 403

        nom_essai_supprime = e.intitule
        unite_name = e.unites[0].libelle if e.unites else "LPEE"

        if hasattr(e, 'normes'): e.normes.clear()
        if hasattr(e, 'unites'): e.unites.clear()
        if hasattr(e, 'grandeurs'): e.grandeurs.clear()

        db.session.delete(e)
        db.session.commit()

        user_email = f"Opérateur {current_user_id}"
        try:
            from models import Utilisateur
            user_obj = db.session.get(Utilisateur, current_user_id)
            if user_obj:
                user_email = user_obj.email
        except:
            pass

        try:
            socketio.emit('notification_essai', {
                "id": int(time.time()),
                "user": user_email,
                "unite": unite_name,
                "action": "DELETE",
                "details": nom_essai_supprime,
                "date": datetime.utcnow().isoformat()
            })
            print("🟢 [SUCCESS] Notification émise avec succès via WebSocket (extensions.socketio)")
        except Exception as socket_err:
            print(f"⚠️ Erreur SocketIO lors de la suppression: {str(socket_err)}")

        return jsonify({"message": "Essai supprimé avec succès"}), 200
    except Exception as err:
        db.session.rollback()
        print(f"❌ Erreur lors de la suppression de l'essai {id}: {str(err)}")
        return jsonify({"error": str(err)}), 500