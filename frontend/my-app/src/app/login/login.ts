import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    FormsModule,
    RouterModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  email = '';
  mot_de_passe = '';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  onLogin() {
    const data = {
      email: this.email,
      mot_de_passe: this.mot_de_passe
    };

    this.authService.login(data).subscribe({
      next: (response: any) => {

        localStorage.clear();


        localStorage.setItem('token', response.token);


        const currentRole = response.role === 'Administrateur' || response.role === 'ADMIN' ? 'ADMIN' : 'USER';

        const userSessionData = {
          role: currentRole,
          id_unite: response.id_unite,
          email: this.email,
          nom_unite: response.nom_unite || ''
        };


        localStorage.setItem('user', JSON.stringify(userSessionData));
        localStorage.setItem('role', currentRole);
        localStorage.setItem('nom_unite', response.nom_unite || '');
        localStorage.setItem('unite', response.id_unite);

        console.log("Connexion réussie ! Le rôle actuel est :", currentRole);


        this.router.navigate(['/dashboard-admin/dashboard']);
      },
      error: (error) => {

        alert(error.error?.message || 'Identifiants incorrects ou erreur serveur.');
      }
    });
  }
}
