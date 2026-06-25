import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NormeService {

  private apiUrl = 'http://localhost:5000/api/normes';

  constructor(private http: HttpClient) {}

  // 🌟 دالة مساعدة لإنشاء الـ Headers بالـ Token الحالي
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('token'); // كنجيبو التوكن اللي تخزن عند الـ Login
    return new HttpHeaders({
      'Authorization': `Bearer ${token}` // ضروري كلمة Bearer متبوعة بمسافة والـ Token
    });
  }

  getAllNormes(): Observable<any> {
    // كنصيفطو الـ headers كـ خيار (Options) وسط الطلب
    return this.http.get(this.apiUrl, { headers: this.getAuthHeaders() });
  }

  createNorme(data: any): Observable<any> {
    return this.http.post(this.apiUrl, data, { headers: this.getAuthHeaders() });
  }

  updateNorme(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, data, { headers: this.getAuthHeaders() });
  }

  deleteNorme(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`, { headers: this.getAuthHeaders() });
  }
}
