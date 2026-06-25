import { Role } from './role';
import { Unite } from './unite';

export interface Utilisateur {
  id_utilisateur: number;
  email: string;
  mot_de_passe?: string;
  statut: string;
  cree: string | Date;
  cree_par?: string;
  modifier?: string | Date;
  modifier_par?: string;
  id_unite: number;
  id_role: number;

  unite?: Unite | null;
  role?: Role | null;

  // 🌟 زدنا هاد السطرين هنا باش الـ HTML يتعرف عليهم وميبقاش يعطي خطأ TS2339 🌟
  nom_role?: string;   // جاي من u.role.libelle فـ Flask
  nom_unite?: string;  // جاي من u.unite.libelle فـ Flask
}
