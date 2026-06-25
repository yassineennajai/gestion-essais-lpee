import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UtilisateurService {
  // 🎯 قمنا بجعل الروابط ديناميكية ونظيفة لتفادي تداخل الكلمات ف الـ URL
  private baseUrl = 'http://localhost:5000/api';
  private apiUrl = `${this.baseUrl}/utilisateurs`;

  // المتغير الخاص بالبحث (BehaviorSubject)
  private searchTermSource = new BehaviorSubject<string>('');

  // 🟢 نقوم بتصدير كِلا المتغيرين لضمان التوافق المطلق مع جميع المكونات بدون أخطاء
  searchTerm$ = this.searchTermSource.asObservable();
  currentSearchTerm = this.searchTerm$;

  constructor(private http: HttpClient) {}

  // الدالة الخاصة بتغيير كلمة البحث
  changeSearchTerm(term: string): void {
    this.searchTermSource.next(term);
  }

  // --- دوال الـ CRUD ---

  // تم تحويل نوع البيانات إلى <any> ليتوافق مع المصفوفة البسيطة أو المرجعة بصيغة Pagination من الباكند
  getUtilisateurs(): Observable<any> {
    return this.http.get<any>(this.apiUrl);
  }

  createUtilisateur(user: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, user);
  }

  updateUtilisateur(id: number, user: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}`, user);
  }

  deleteUtilisateur(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }

  getUnites(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/unites`);
  }
}

