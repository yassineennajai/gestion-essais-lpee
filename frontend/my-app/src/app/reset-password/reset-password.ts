import { Component } from '@angular/core';

import { FormsModule } from '@angular/forms';

import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-reset-password',

  imports: [FormsModule],

  templateUrl: './reset-password.html',

  styleUrl: './reset-password.css'
})

export class ResetPassword {

  email = '';

  nouveau_password = '';

  constructor(
    private http: HttpClient
  ) {}

  resetPassword() {

    this.http.post(

      'http://127.0.0.1:5000/api/reset-password',

      {

        email: this.email,

        mot_de_passe: this.nouveau_password

      }

    ).subscribe({

      next: (response: any) => {

        alert(response.message);

      },

      error: (error) => {

        alert(error.error.message);

      }

    });

  }

}
