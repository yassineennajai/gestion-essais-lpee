import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { UtilisateurService } from '../services/utilisateur';
import { NotificationService } from '../services/notification';
import { AlertService } from '../services/alert';
import Swal from 'sweetalert2';

interface AppNotification {
  id: number;
  user: string;
  unite: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  details: string;
  date: Date;
}

@Component({
  selector: 'app-dashboard-admin',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  templateUrl: './dashboard-admin.html',
  styleUrl: './dashboard-admin.css'
})
export class DashboardAdminComponent implements OnInit, OnDestroy {
  currentTitle: string = 'Dashboard';
  isSidebarOpen: boolean = false;
  isProfileMenuOpen: boolean = false;
  isNotifMenuOpen: boolean = false;
  unreadCount: number = 0;
  notifications: AppNotification[] = [];

  private notifSubscription!: Subscription;

  userEmail: string = '';
  userRole: string = '';
  userUnite: string = '';
  isAdmin: boolean = false;
  isLNM: boolean = false;
  isCEREP: boolean = false;
  constructor(
    private utilisateurService: UtilisateurService,
    private notificationService: NotificationService,
    private alertService: AlertService,
    public router: Router
  ) {}

  ngOnInit(): void {
    this.updateTitle(this.router.url);

    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.updateTitle(event.urlAfterRedirects || event.url);
      this.isSidebarOpen = false;
      this.isProfileMenuOpen = false;
      this.isNotifMenuOpen = false;
    });

    const currentUserString = localStorage.getItem('user');

    if (currentUserString) {
      try {
        const user = JSON.parse(currentUserString);
        this.userRole = user.role || 'USER';
        this.userEmail = user.email || 'user@lpee.ma';
        this.userUnite = user.unite || '';
        const fullUserText = JSON.stringify(user).toUpperCase();
        this.isLNM = fullUserText.includes('LNM');
        this.isCEREP = fullUserText.includes('CEREP');
      } catch (e) {
        this.isLNM = false;
        this.isCEREP = false;
      }
    } else {
      this.userRole = localStorage.getItem('role') || 'USER';
      this.userEmail = localStorage.getItem('email') || 'user@lpee.ma';
      this.userUnite = localStorage.getItem('unite') || '';
      const backupText = (this.userRole + this.userEmail + this.userUnite).toUpperCase();
      this.isLNM = backupText.includes('LNM');
      this.isCEREP = backupText.includes('CEREP');
    }

    const checkedRole = this.userRole.trim().toUpperCase();
    this.isAdmin = (checkedRole === 'ADMIN' || checkedRole === 'ADMINISTRATEUR');

    if (this.isAdmin) {
      this.isCEREP = false;
    }


    this.connectToRealTimeNotifications();
  }

  connectToRealTimeNotifications(): void {
    if (this.notifSubscription) {
      this.notifSubscription.unsubscribe();
    }

    this.notifSubscription = this.notificationService.onNewNotification().subscribe({
      next: (incomingNotif: AppNotification) => {
        try {
          incomingNotif.date = new Date(incomingNotif.date);


          this.triggerSweetAlert(incomingNotif);

          
          if (this.isAdmin) {
            this.notifications.unshift(incomingNotif);
            this.unreadCount++;
          }
        } catch (error) {
          console.error("Erreur de traitement de la notification :", error);
        }
      },
      error: (error) => {
        console.warn("Erreur de connexion WebSocket :", error);
      }
    });
  }

  triggerSweetAlert(notif: AppNotification): void {
    let iconType: 'success' | 'info' | 'error' = 'success';
    let actionLabel = 'créé';
    let alertColor = '#2ec4b6';

    if (notif.action === 'UPDATE') {
      iconType = 'info';
      actionLabel = 'modifié';
      alertColor = '#ff9f1c';
    } else if (notif.action === 'DELETE') {
      iconType = 'error';
      actionLabel = 'supprimé';
      alertColor = '#e71d36';
    }

    const Toast = Swal.mixin({
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 5000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
      }
    });

    Toast.fire({
      icon: iconType,
      title: `<span style="color: ${alertColor}; font-weight: bold;">[${notif.unite}] Activité détectée</span>`,
      html: `
        <div style="text-align: left; font-size: 13px;">
          👤 <b>${notif.user}</b> a ${actionLabel} l'essai : <br>
          <span style="font-style: italic; color: #555;">"${notif.details}"</span>
        </div>
      `,
      background: '#ffffff',
      iconColor: alertColor
    });
  }

  ngOnDestroy(): void {
    if (this.notifSubscription) {
      this.notifSubscription.unsubscribe();
    }
  }

  getInitials(): string {
    if (!this.userEmail) return 'US';
    return this.userEmail.substring(0, 2).toUpperCase();
  }

  private updateTitle(url: string): void {
    if (url.includes('ajouter-utilisateur')) this.currentTitle = 'Ajouter un utilisateur';
    else if (url.includes('utilisateur')) this.currentTitle = 'Gestion des Utilisateurs';
    else if (url.includes('ajouter-unite')) this.currentTitle = 'Ajouter une unité';
    else if (url.includes('unite')) this.currentTitle = 'Gestion des Unités';
    else if (url.includes('ajouter-essai')) this.currentTitle = 'Ajouter un essai';
    else if (url.includes('essais')) this.currentTitle = 'Gestion des Essais';
    else if (url.includes('normes')) this.currentTitle = 'Gestion des Normes';
    else if (url.includes('familles')) this.currentTitle = 'Gestion des Familles';
    else if (url.includes('domaines')) this.currentTitle = "Gestion des Domaines d'activité";
    else if (url.includes('grandeurs')) this.currentTitle = 'Gestion des Grandeurs de mesure';
    else if (url.includes('villes')) this.currentTitle = 'Gestion des Villes';
    else this.currentTitle = 'Dashboard';
  }

  toggleSidebar(): void {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  toggleProfileMenu(): void {
    this.isProfileMenuOpen = !this.isProfileMenuOpen;
    if (this.isProfileMenuOpen) this.isNotifMenuOpen = false;
  }

  toggleNotifMenu(): void {
    this.isNotifMenuOpen = !this.isNotifMenuOpen;
    if (this.isNotifMenuOpen) {
      this.isProfileMenuOpen = false;
      this.unreadCount = 0;
    }
  }

  clearNotifications(): void {
    this.notifications = [];
    this.unreadCount = 0;
    this.isNotifMenuOpen = false;
  }

  logout(): void {
    if (this.notifSubscription) {
      this.notifSubscription.unsubscribe();
    }
    localStorage.clear();
    this.router.navigate(['/']);
  }

  onSearch(event: any): void {
    const value = (event.target as HTMLInputElement).value;
    if (value !== undefined && value !== null) {
      this.utilisateurService.changeSearchTerm(value.trim());
    }
  }
}
