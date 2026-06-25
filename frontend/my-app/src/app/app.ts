import { Component, signal, ViewEncapsulation } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css', // <-- Singular 'styleUrl' وبلا brackets []
  encapsulation: ViewEncapsulation.None // <-- Zid(i) hada hna f l-root ga3 bach l-Bootstrap w styles l-kbar y-douzo 100%
})
export class App {
  protected readonly title = signal('my-app');
}
