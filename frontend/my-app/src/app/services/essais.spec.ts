import { TestBed } from '@angular/core/testing';

import { Essais } from './essais';

describe('Essais', () => {
  let service: Essais;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Essais);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
