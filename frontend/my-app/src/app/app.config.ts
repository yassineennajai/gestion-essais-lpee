import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http'; // 🌟 زدت هنا withInterceptors

import { routes } from './app.routes';
import { authInterceptor } from './auth.interceptor'; // 🌟 تأكدي من مسار ملف الـ interceptor لي صاوبنا

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),

    // 🌟 التعديل هنا: تفعيل الـ Interceptor وسط الـ HttpClient
    provideHttpClient(
      withInterceptors([authInterceptor])
    )
  ]
};
