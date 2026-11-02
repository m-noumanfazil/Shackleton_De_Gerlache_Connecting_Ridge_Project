# Gaussian Blur Sweep Report: C1 Safest Candidate DEM

## 1. Check Results
1. **Pixel Size**: 5.0000 m (X) x 5.0000 m (Y) (Expected: 5.0 m x 5.0 m). Status: **PASS**.
2. **NaN Count**: 0 in BIG DEM (2394 x 1900). Status: **PASS**.
3. **Window Statistics**:
   - Minimum: **1947.7814 m** (Expected: 1947.78 m, $|\Delta| = 0.0014$ m)
   - Maximum: **1959.4962 m** (Expected: 1959.50 m, $|\Delta| = 0.0038$ m)
   - Mean: **1955.3127 m** (Expected: 1955.31 m)
   - Standard Deviation: **2.0116 m** (Expected: 2.01 m)
   - Status: **PASS** (Deviation within $\pm 0.05$ m threshold; window col0=660, row0=360).
4. **Smallest Distance to Edge of BIG**: **360 pixels** (Top: 360 px, Bottom: 1480 px, Left: 660 px, Right: 1674 px). Status: **PASS**.

---

## 2. Sweep Table

| $\sigma_m$ (m) | Cutoff Wavelength (m) | std(low) (m) | std(high) (m) | min(high) (m) | max(high) (m) | std(high) / std(TILE) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 5 | 26.5 | 1.9960 | 0.0784 | -0.8885 | 0.7378 | 0.0390 |
| 10 | 53.0 | 1.9628 | 0.1700 | -1.3810 | 1.0658 | 0.0845 |
| 14 | 74.2 | 1.9312 | 0.2496 | -1.6704 | 1.3142 | 0.1241 |
| 20 | 106.0 | 1.8836 | 0.3700 | -1.9701 | 1.5980 | 0.1839 |
| 30 | 159.0 | 1.8130 | 0.5445 | -2.4359 | 1.9213 | 0.2707 |

---

## 3. High Component Morphological Observations

### $\sigma = 5$ m ($\sigma = 1.0$ px, Cutoff $\lambda_c = 26.5$ m)
The high component (std = 0.0784 m, ratio = 0.0390, range [-0.8885, 0.7378] m) appears predominantly as fine, uncorrelated pixel-scale speckle and sensor noise. Autocorrelation drops sharply within 1 to 2 pixels (5–10 m), exhibiting no discernible topographic mounds, crater forms, or directional striping.

### $\sigma = 10$ m ($\sigma = 2.0$ px, Cutoff $\lambda_c = 53.0$ m)
The high component (std = 0.1700 m, ratio = 0.0845, range [-1.3810, 1.0658] m) transitions from pure point speckle into subtle granular clusters and fine micro-relief spanning 2 to 3 pixels (10–15 m). Spatial coherence begins to emerge across small local patches, but features remain predominantly fine surface roughness without distinct macroscopic hills or directional banding.

### $\sigma = 14$ m ($\sigma = 2.8$ px, Cutoff $\lambda_c = 74.2$ m)
The high component (std = 0.2496 m, ratio = 0.1241, range [-1.6704, 1.3142] m) resolves into coherent, localized topographic mounds and gentle undulations spanning 3 to 4 pixels (15–20 m). The relief is spatially structured rather than noise-dominated, displaying isotropic undulations across the window without scan stripes or directional artifacts.

### $\sigma = 20$ m ($\sigma = 4.0$ px, Cutoff $\lambda_c = 106.0$ m)
The high component (std = 0.3700 m, ratio = 0.1839, range [-1.9701, 1.5980] m) contains prominent rolling mounds, shallow swales, and defined topographic features spanning 25 to 35 m. The spatial structure represents clear meso-topographic terrain relief rather than surface roughness, maintaining smooth contours with no preferential directional bias.

### $\sigma = 30$ m ($\sigma = 6.0$ px, Cutoff $\lambda_c = 159.0$ m)
The high component (std = 0.5445 m, ratio = 0.2707, range [-2.4359, 1.9213] m) is characterized by broad macroscopic hills, major slope variations, and substantial terrain swells spanning tens of metres. The residual captures substantial macro-topography (std reaches 27.1% of total tile variation) rather than localized surface roughness.

---

## 4. Files Written
- `/home/nightwing/Desktop/Dominus/data/C1_Candidates/C1_Safest_Candidate/enhanced/sweep/sweep_preview.png`
- `/home/nightwing/Desktop/Dominus/data/C1_Candidates/C1_Safest_Candidate/enhanced/sweep/sweep_spectrum.png`
- `/home/nightwing/Desktop/Dominus/data/C1_Candidates/C1_Safest_Candidate/enhanced/sweep/big_overview.png`
- `/home/nightwing/Desktop/Dominus/data/C1_Candidates/C1_Safest_Candidate/enhanced/sweep/blur_sweep_report.md`
