import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';


export interface DashboardResponse {
  role: 'ADMIN' | 'USER';
  user_nom: string;
  nom_unite: string;
  user_email: string;
  ville_unite: string;
  user_date_creation: string;
  user_derniere_connexion: string;
  cards: any;
  chart_data: {
    unites_labels?: string[];
    unites_data?: number[];
    normes_unites_labels?: string[];
    normes_unites_data?: number[];
    villes_labels?: string[];
    villes_data?: number[];
    mensuels_labels?: string[];
    mensuels_data?: number[];
    type_labels?: string[];
    type_data?: number[];
  };
  recents_essais: any[];
  recents_normes: any[];
  recents_utilisateurs?: any[];
  recents_familles?: any[];
  activite_recente?: {
    dernier_essai: string;
    derniere_norme: string;
    derniere_famille: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {


  private readonly API_URL = 'http://localhost:5000/api/dashboard/stats';

  constructor(private http: HttpClient) { }

  getDashboardStats(): Observable<DashboardResponse> {

    const token = localStorage.getItem('token');


    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    return this.http.get<DashboardResponse>(this.API_URL, { headers });
  }
}
