import { Norme } from './norme';

export interface Partie {
  id_partie: number;
  no_partie: string;
  titre: string;
  id_norme: number;


  norme?: Norme | null;
}
