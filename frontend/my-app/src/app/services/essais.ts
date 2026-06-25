import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class EssaiService {
  private http = inject(HttpClient);
  private apiUrl = 'http://127.0.0.1:5000/api'; // الرابط الأساسي للـ Flask

  /**
   * 🌟 دالة مساعدة لإنشاء الـ Headers الأمنية الحقيقية
   * كتقرا الـ JWT Token والبيانات وتصيفطهم للفلاسك بالطريقة المعيارية
   */
  private getAuthHeaders(): HttpHeaders {
    // 1. جلب الـ Token الحقيقي (تأكدي من الإسم باش مخبياه ف الـ Login: 'token' أو 'access_token')
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');

    // 2. جلب بيانات المستخدم للاحتياط
    const currentUserString = localStorage.getItem('user') || localStorage.getItem('currentUser');
    let role = 'Utilisateur';
    let idUnite = 'null';

    if (currentUserString) {
      try {
        const user = JSON.parse(currentUserString);
        role = user.role || 'Utilisateur';
        idUnite = user.id_unite ? user.id_unite.toString() : 'null';
      } catch (e) {
        console.error('Erreur lors du parsing de l\'utilisateur desde localStorage', e);
      }
    }

    // 3. بناء الـ Headers مع حقن الـ Bearer Token ليفكه الـ @jwt_required()
    let headers = new HttpHeaders({
      'X-User-Role': role,
      'X-User-Unite': idUnite
    });

    if (token) {
      // 🚀 حقن الـ Bearer Token لفتح حماية الـ Backend
      headers = headers.set('Authorization', `Bearer ${token}`);
    } else {
      console.warn("⚠️ Aucun Token JWT trouvé dans le localStorage !");
    }

    return headers;
  }

  // ==========================================
  // 📥 دالات جلب البيانات (GET)
  // ==========================================

  // 1. جلب كاع الـ Essais
  getEssais(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/essais`, { headers: this.getAuthHeaders() });
  }

  // 2. جلب المدن
  getVilles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/villes`, { headers: this.getAuthHeaders() });
  }

  // 3. جلب الوحدات
  getUnites(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/unites`, { headers: this.getAuthHeaders() });
  }

  // 4. جلب المجالات
  getDomaines(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/domaines`, { headers: this.getAuthHeaders() });
  }

  // 5. جلب العائلات (مفلترة دابا ف الباكيند تال الـ Unité)
  getFamilles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/familles`, { headers: this.getAuthHeaders() });
  }

  // 6. جلب العائلات الفرعية
  getSousFamillesByFamille(idFamille: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/sous-familles/${idFamille}`, { headers: this.getAuthHeaders() });
  }

  // 7. جلب المعايير مدمج معها الأجزاء
  getNormes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/unite/normes`, { headers: this.getAuthHeaders() });
  }

  // 🌟 8. الدالة المضافة والمصححة: جلب قائمة الـ Grandeurs مأمنة بالـ Token
  getGrandeurs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/grandeurs`, { headers: this.getAuthHeaders() });
  }

  // ==========================================
  // 📤 العمليات الأساسية (CRUD)
  // ==========================================

  createEssai(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/essais`, data, { headers: this.getAuthHeaders() });
  }

  updateEssai(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/essais/${id}`, data, { headers: this.getAuthHeaders() });
  }

  deleteEssai(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/essais/${id}`, { headers: this.getAuthHeaders() });
  }
}
