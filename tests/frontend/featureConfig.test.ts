import { describe, it, expect } from 'vitest';
import { FEATURES, FEATURE_KEYS, emptyApplicantForm } from '../../frontend/src/utils/featureConfig';

describe('featureConfig', () => {
  it('has a definition for every feature key', () => {
    for (const key of FEATURE_KEYS) {
      expect(FEATURES[key]).toBeDefined();
      expect(FEATURES[key].label.length).toBeGreaterThan(0);
    }
  });

  it('marks protected/identity attributes as immutable', () => {
    expect(FEATURES.age.mutable).toBe(false);
    expect(FEATURES.personal_status_sex.mutable).toBe(false);
    expect(FEATURES.foreign_worker.mutable).toBe(false);
  });

  it('gives numeric features a min/max range', () => {
    for (const key of FEATURE_KEYS) {
      if (FEATURES[key].category === 'numeric') {
        expect(FEATURES[key].min).toBeDefined();
        expect(FEATURES[key].max).toBeDefined();
      }
    }
  });

  it('emptyApplicantForm returns an entry for every feature', () => {
    const form = emptyApplicantForm();
    expect(Object.keys(form).sort()).toEqual([...FEATURE_KEYS].sort());
  });
});
