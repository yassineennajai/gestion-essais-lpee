import { Routes } from '@angular/router';

import { Login } from './login/login';
import { ForgotPassword } from './forgot-password/forgot-password';


import { DashboardAdminComponent } from './dashboard-admin/dashboard-admin';
import { UnitesComponent  } from './unite/unite';
import { AjouterUniteComponent } from './unite/ajouter-unite/ajouter-unite';


import { UtilisateursComponent  } from './utilisateurs/utilisateurs';
import { DashboardComponent } from './dashboard/dashboard';
import { AjouterUtilisateur } from './utilisateurs/ajouter-utilisateur/ajouter-utilisateur';
import { EssaisComponent } from './essais/essais';
import { AjouterEssaiComponent } from './essais/ajouter-essai/ajouter-essai';

import { Normes } from './normes/normes';
import { AjouterNormeComponent } from './normes/ajouter-norme/ajouter-norme';
import { Familles } from './familles/familles';
import { AjouterFamilleComponent } from './familles/ajouter-famille/ajouter-famille';


import { GrandeursComponent } from './grandeurs/grandeurs';
import { DomainesComponent } from './domaines/domaines';
import { VillesComponent } from './villes/villes';

import { Parametres } from './parametres/parametres';

export const routes: Routes = [
  { path: '', component: Login },
  { path: 'forgot-password', component: ForgotPassword },


  {
    path: 'dashboard-admin',
    component: DashboardAdminComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },


      { path: 'utilisateur', component:UtilisateursComponent  },
      { path: 'ajouter-utilisateur', component: AjouterUtilisateur },
      { path: 'modifier-utilisateur/:id', component: AjouterUtilisateur },
      { path: 'unite', component: UnitesComponent  },
      { path: 'ajouter-unite', component: AjouterUniteComponent },


      { path: 'essais', component: EssaisComponent },
      { path: 'ajouter-essai', component: AjouterEssaiComponent },


      { path: 'normes', component: Normes },
      { path: 'ajouter-norme', component: AjouterNormeComponent },
      { path: 'familles', component: Familles },
      { path: 'ajouter-famille', component: AjouterFamilleComponent },

      { path: 'grandeurs', component: GrandeursComponent },


      { path: 'domaines', component: DomainesComponent },


      { path: 'villes', component: VillesComponent },




      { path: 'parametres', component: Parametres }
    ]
  },

  { path: '**', redirectTo: '' }
];
