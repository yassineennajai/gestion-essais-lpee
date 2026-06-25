import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
// 🌟 استيراد الـ Interface لضمان الـ Type Safety عبر السيرفيس كامل
import { Famille } from '../interfaces/famille';

@Injectable({
  providedIn: 'root'
})
export class FamilleService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:5000/api/familles';

  
  private getHttpOptions() {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const currentUserString = localStorage.getItem('user');

    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    } else {
      console.warn("⚠️ Aucun Token trouvé dans le FamilleService !");
    }

    if (currentUserString) {
      try {
        const user = JSON.parse(currentUserString);
        if (user.role) {
          headers = headers.set('X-User-Role', user.role);
        }
        if (user.id_unite) {
          headers = headers.set('X-User-Unite', user.id_unite.toString());
        }
      } catch (e) {
        console.error("Erreur lors du parse de l'utilisateur dans FamilleService", e);
      }
    }

    return { headers: headers };
  }


  getAllFamilles(): Observable<Famille[]> {
    return this.http.get<Famille[]>(this.apiUrl, this.getHttpOptions());
  }


  getFamilleById(id: number): Observable<Famille> {
    return this.http.get<Famille>(`${this.apiUrl}/${id}`, this.getHttpOptions());
  }


  createFamille(familleData: any): Observable<any> {
    const listSousFamilles = familleData.sous_familles ||
                             familleData.sousFamilles ||
                             familleData.rawSousFamilles || [];

    const payload = {
      nom_famille: familleData.nom_famille || familleData.nom,

      sous_familles: listSousFamilles.map((sf: any) => ({
        libelle: sf.libelle || sf.nom_sous_famille || sf.nom || sf.nom_famille || ''
      }))
    };

    console.log('PAYLOAD FINAL CONVERTI ENVOYÉ AU FLASK:', payload);
    return this.http.post<any>(this.apiUrl, payload, this.getHttpOptions());
  }


  updateFamille(id: number, familleData: any): Observable<any> {
    const listSousFamilles = familleData.sous_familles ||
                             familleData.sousFamilles ||
                             familleData.rawSousFamilles || [];

    const payload = {
      nom_famille: familleData.nom_famille || familleData.nom,

      sous_familles: listSousFamilles.map((sf: any) => ({
        id_sous_famille: sf.id_sous_famille || 0,
        libelle: sf.libelle || sf.nom_sous_famille || sf.nom || sf.nom_famille || ''
      }))
    };

    console.log('PAYLOAD UPDATE CONVERTI ENVOYÉ AU FLASK:', payload);
    return this.http.put<any>(`${this.apiUrl}/${id}`, payload, this.getHttpOptions());
  }


  deleteFamille(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`, this.getHttpOptions());
  }
}
