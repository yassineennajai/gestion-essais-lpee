import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Unite } from '../interfaces/unite';

@Injectable({
  providedIn: 'root'
})
export class UniteService {
  private apiUrl = 'http://127.0.0.1:5000/api/unites';

  constructor(private http: HttpClient) {}

 
  getUnetes(): Observable<Unite[]> {
    return this.http.get<Unite[]>(this.apiUrl);
  }


  CreateUnite(unite: any): Observable<any> {
    return this.http.post(this.apiUrl, unite);
  }

  updateUnite(unite: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${unite.id_unite}`, unite);
  }


  deleteUnite(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`);
  }
}
