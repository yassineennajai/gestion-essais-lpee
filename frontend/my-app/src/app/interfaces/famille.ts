
import { SousFamille } from './sous-famille';

export interface Famille {
  id_famille: number;
  nom_famille: string;
  id_unite?: number | null;


  sousFamilles?: SousFamille[];
}
