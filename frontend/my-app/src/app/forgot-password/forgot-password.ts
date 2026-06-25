import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './forgot-password.html',
  styleUrls: ['./forgot-password.css']
})
export class ForgotPassword {

  email = '';

  constructor(private http: HttpClient) {}

  envoyer() {

    this.http.post(
      'http://127.0.0.1:5000/api/forgot-password',
      { email: this.email }
    ).subscribe({
      next: (response: any) => {
        console.log(response); // مهم للتأكد
        alert(response.message);
      },
      error: (error) => {
        console.log(error);
        alert(error.error?.message || 'Erreur serveur');
      }
    });

  }
}
