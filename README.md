# Melodic Surprise Across Genres

**MUSIC 108 Final Project** — Computational Analysis of Musical Expectation and Stylistic Predictability

This project analyzes how melodic predictability varies across musical genres by computing information-theoretic surprise for each note transition. Using first-order Markov models trained on style-specific MIDI corpora, the pipeline quantifies which melodic moves are statistically unexpected within pop, classical, blues, rock, and country.

The analysis converts MIDI files into monophonic pitch sequences, builds transition probability matrices for each genre, computes per-note surprise values (−log₂ probability), and generates comparative visualizations.

---

## Project Structure
```
midi/
├── pop/
│   ├── track1.mid
│   ├── track2.mid
│   └── ...
├── classical/
│   └── ...
├── blues/
│   └── ...
├── rock/
│   └── ...
├── country/
│   └── ...
├── _txt/              # Auto-generated: human-readable MIDI dumps
│   ├── pop/
│   ├── classical/
│   └── ...
├── _surprise/         # Auto-generated: per-note surprise files
│   ├── pop/
│   └── ...
└── _plots/            # Auto-generated: histograms + example curves

pipeline/
├── midi_markov_pipeline.py     # Main processing script
├── analyze_surprise.py         # Statistical analysis + visualization
└── README.md
```

---

## Workflow

### 1. Prepare MIDI Datasets

Organize MIDI files into genre-specific subdirectories:
```
/path/to/midi/
├── pop/
├── classical/
├── blues/
├── rock/
└── country/
```

The pipeline preserves this structure for all outputs.

### 2. Run the Processing Pipeline

Generate human-readable MIDI dumps, train style-specific Markov models, and compute per-note surprise:
```bash
python midi_markov_pipeline.py
```

**Outputs:**
- `_txt/genre/...` → Readable MIDI event logs (`.mid.txt`)
- `_surprise/genre/...` → Per-note surprise files (format: `index, note, surprise_bits`)

### 3. Run Analysis & Visualization

Compute summary statistics and generate comparative plots:
```bash
python analyze_surprise.py
```

**Outputs:**
- `style_surprise_summary.csv` → Mean, variance, and note count per genre
- `_plots/` → Histograms of surprise distributions and example surprise curves

---

## What Surprise Means

Surprise quantifies how unexpected a melodic transition is within a given style:

**S = −log₂ P(next_note | current_note)**

Where **P(next | current)** is estimated from a genre-specific first-order Markov model.

- **Higher bits** = more unexpected transition (e.g., chromatic leap in country)
- **Lower bits** = more predictable continuation (e.g., stepwise motion in diatonic melody)

For example:
- A note with 50% probability → **1 bit** of surprise
- A note with 6.25% probability → **4 bits** of surprise

---

## Outputs & Interpretation

### Summary Statistics

For each genre, the pipeline computes:
- **Mean surprise** — average local unpredictability
- **Variance** — consistency of surprise across pieces
- **Total notes analyzed**

### Visualizations

1. **Histograms** — Distribution of surprise values per genre
2. **Surprise curves** — Example plots showing surprise spikes at structurally salient moments (e.g., large leaps, chromatic tones, phrase boundaries)

These plots support the argument that genres differ in their statistical grammars and that surprise peaks align with music-theoretic predictions about perceptual salience.

---

## Dependencies

Install required packages:
```bash
pip install mido pandas numpy matplotlib
```

**Library versions used:**
- `mido` — MIDI file parsing
- `pandas` — Data aggregation and CSV export
- `numpy` — Numerical computation
- `matplotlib` — Visualization

---

## Citation

Based on theoretical frameworks from:
- Pearce, M. T., & Wiggins, G. A. (2012). Auditory expectation: The information dynamics of music perception and cognition.
- Huron, D. (2006). *Sweet Anticipation: Music and the Psychology of Expectation*.
- Narmour, E. (1990). *The Analysis and Cognition of Basic Melodic Structures*.

---

## License

This project is for academic use. MIDI files are not included in this repository and must be sourced separately in compliance with copyright law.