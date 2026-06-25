import { TestBed } from '@angular/core/testing';

import { MesEssais } from './mes-essais';

describe('MesEssais', () => {
  let service: MesEssais;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MesEssais);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
