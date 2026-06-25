import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private socket: Socket;
  private readonly SERVER_URL = 'http://localhost:5000';

  constructor() {
    this.socket = io(this.SERVER_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000
    });

    this.socket.on('connect', () => {
      console.log('🟢 Socket.IO connecté avec succès au serveur Flask ! (ID:', this.socket.id, ')');
    });

    this.socket.on('disconnect', (reason) => {
      console.warn('🟡 Socket.IO déconnecté du serveur. Raison:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('🔴 Erreur de connexion Socket.IO détectée:', error);
    });
  }

  onNewNotification(): Observable<any> {
    return new Observable((observer) => {
      this.socket.on('notification_essai', (data) => {
        console.log('📥 Notification reçue en direct via WebSocket:', data);
        observer.next(data);
      });

      return () => {
        this.socket.off('notification_essai');
      };
    });
  }
}
