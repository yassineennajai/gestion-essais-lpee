import { Injectable } from '@angular/core';
import Swal from 'sweetalert2';

@Injectable({
  providedIn: 'root'
})
export class AlertService {

  constructor() { }

  /**
   * 🟢 تنبيه النجاح (Success Toast)
   * يظهر في الأعلى على اليمين ويختفي تلقائياً بعد 3 ثوانٍ
   */
  success(message: string): void {
    const Toast = Swal.mixin({
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
      }
    });

    Toast.fire({
      icon: 'success',
      title: message,
      background: '#ffffff',
      iconColor: '#2ec4b6'
    });
  }

  /**
   * 🔴 تنبيه الخطأ (Error Toast)
   * يظهر عند فشل الاتصال بالسيرفر أو وجود حقول غير صالحة
   */
  error(message: string): void {
    const Toast = Swal.mixin({
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 4000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
      }
    });

    Toast.fire({
      icon: 'error',
      title: message,
      background: '#ffffff',
      iconColor: '#e71d36'
    });
  }

  /**
   * 🟡 نافذة التأكيد قبل الحذف (Confirmation Dialog)
   * تسأل المستخدم وتنتظر إجابته بالموافقة أو الإلغاء
   */
  confirm(
    titre: string,
    description: string,
    boutonConfirmer: string = 'Oui, supprimer',
    boutonAnnuler: string = 'Annuler'
  ): Promise<boolean> {
    return Swal.fire({
      title: titre,
      text: description,
      icon: 'warning',
      iconColor: '#ffb703',
      showCancelButton: true,
      confirmButtonColor: '#e71d36',
      cancelButtonColor: '#6c757d',
      confirmButtonText: boutonConfirmer,
      cancelButtonText: boutonAnnuler,
      reverseButtons: true,
      heightAuto: false,
      customClass: {
        popup: 'rounded-4 shadow border-0 p-4',
        title: 'fw-bold text-dark fs-4',
        htmlContainer: 'text-secondary fs-6 py-2',
        confirmButton: 'btn btn-danger btn-lg px-4 py-2 rounded-3 fw-semibold mx-2',
        cancelButton: 'btn btn-secondary btn-lg px-4 py-2 rounded-3 fw-semibold mx-2'
      }
    }).then((result) => {
      return result.isConfirmed;
    });
  }
}
