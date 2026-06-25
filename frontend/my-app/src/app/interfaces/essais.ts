export interface Essai {
  id_essai?: number;
  id?: number; // للامان في حالة استعمال id
  intitule: string;
  type: string;
  id_domaine?: number;
  nom_domaine?: string;
  id_famille?: number;
  nom_famille?: string;
  id_sous_famille?: number;
  nom_sous_famille?: string;
  id_partie?: number;
  nom_partie?: string;
  id_norme?: number;
  nom_norme?: string;
  id_unite?: number;
  nom_unite?: string;
  nom_ville?: string;
  cree?: string;
}
