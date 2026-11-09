# Platform Checking Research Suite

**Comparative Neuroscience Laboratory · Towson University**  
*Kobe Anderson · M.A. Candidate · Advisor: Dr. Bryan Devan*

---

## 🏛️ The Two Core Pillars

The folder structure is organized around your two primary use cases:

### 1. Show-Off & In-Depth Presentation: "Return"
- **Purpose**: High-impact presentations, showing off to audiences, visual storytelling, and live interactive sensitivity demonstrations.
- **One-Click Launcher**: [`01_PRESENTATION_RETURN.html`](file:///c:/Users/kobeq/Documents/KAC%20database/analysis/01_PRESENTATION_RETURN.html)
- **Folder**: [`01_Presentation_Return/`](file:///c:/Users/kobeq/Documents/KAC%20database/analysis/01_Presentation_Return/Presentation_Return.html)
- **Key Features**:
  - Illustrated water ripple visual aesthetic & ambient sound
  - Native 30 Hz/10 Hz trajectory replay across Day 6 standard, Day 7 reminder, Day 8 raised, and SP1
  - Interactive definition sensitivity slider (real-time radius & dwell re-scoring)
  - AK1 30-animal 3-configuration measurement comparison
  - Neural hypothesis mapping (dorsomedial-striatal PV/WFA)

### 2. Academic, Advisory & Classroom Suite: "NeuroCheck"
- **Purpose**: Thesis advisors (Dr. Devan), advisory committee review, academic coursework, formal methodology, and journal evaluation.
- **One-Click Launcher**: [`02_ACADEMIC_RESEARCH_DASHBOARD.html`](file:///c:/Users/kobeq/Documents/KAC%20database/analysis/02_ACADEMIC_RESEARCH_DASHBOARD.html)
- **Folder**: [`02_Academic_Research_Dashboard/`](file:///c:/Users/kobeq/Documents/KAC%20database/analysis/02_Academic_Research_Dashboard/Academic_Research_Dashboard.html)
- **Key Features**:
  - Replicated hypothesis testing across 3 tests (Fisher's exact, Mann-Whitney U, Cox 10.6× hazard ratio)
  - DeepLabCut rotation-augmented tracking QC (<1% untracked time across 250,800 frames)
  - 10 publication-grade scientific art manifolds (300 DPI)
  - The 60 FPS DeepLabCut Motion Lab with 3D WebGL space-time cylinder and posture phase space
  - Integrated cross-experiment correlations (EPM, Open Field, NOR)

---

## 📂 Human-Centric Folder Navigation

```
analysis/
│
├── START_HERE.html                       ← Master visual navigation portal
│
├── 01_PRESENTATION_RETURN.html           ← Double-click to launch "Return" presentation
├── 02_ACADEMIC_RESEARCH_DASHBOARD.html   ← Double-click to launch Academic suite
├── 03_DEEPLABCUT_MOTION_LAB.html         ← Double-click to launch 60 FPS 3D Motion Lab
├── 04_CROSS_EXPERIMENT_CORRELATIONS.html ← Double-click to launch EPM/OF/NOR correlations
├── 05_INDIVIDUAL_ANIMAL_PROFILES.html    ← Double-click to view per-rat profiles
├── 06_BEHAVIOR_ATLAS.html                ← Double-click to view behavior atlas
│
├── 📁 01_Presentation_Return/            ← The "Return" presentation files & data
│   ├── Presentation_Return.html
│   ├── portal.css / portal.js / portal_math.js
│   └── portal_data/                      ← Native coordinate binaries
│
├── 📁 02_Academic_Research_Dashboard/     ← The Academic Suite for advisors & class
│   ├── Academic_Research_Dashboard.html
│   ├── DeepLabCut_Motion_Lab.html
│   ├── figures/                          ← All 10 publication art plates & plots
│   ├── demos_trimmed/                    ← Trimmed video clips
│   ├── js/                               ← Offline Three.js & OrbitControls bundles
│   └── site/                             ← Mirror profiles and explorer
│
├── 📁 03_Cross_Experiment_Correlations/   ← Multi-experiment behavioral integration
│   ├── Cross_Experiment_Correlations.html
│   ├── figures/                          ← Spearman correlation heatmaps & scatter plots
│   └── results/                          ← Merged per-rat tables and statistics
│
├── 📁 04_Individual_Animal_Profiles/     ← Detailed per-rat neurobehavioral dossiers
│   └── Individual_Animal_Profiles.html
│
├── 📁 05_Behavior_Atlas_Explorer/        ← Spatial trajectory maps & heatmaps
│   └── Behavior_Atlas_Explorer.html
│
├── 📁 06_Conference_Poster_Assets/       ← SfN conference poster files & SVGs
│
└── 📁 _archive_and_data_pipelines/       ← Background caches, models, and scripts (tucked away)
    ├── advanced/
    ├── dlc_measures/
    ├── kinematics/
    ├── scanning_accuracy/
    ├── thesis_integration/
    ├── tracking_pilot/
    ├── portal_planning/
    └── updated_anymaze/
```
