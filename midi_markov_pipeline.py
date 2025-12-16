import os
from collections import defaultdict
import math
from mido import MidiFile

ROOT_DIR = r"/Users/skyla/Downloads/midi"

RECURSIVE = True

TEXT_ROOT = os.path.join(ROOT_DIR, "_txt")
SURPRISE_ROOT = os.path.join(ROOT_DIR, "_surprise")

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


def note_number_to_name(n: int) -> str:
    """Convert MIDI note number (0–127) to a name like C4, A#3, etc."""
    if not (0 <= n <= 127):
        return str(n)
    name = NOTE_NAMES[n % 12]
    octave = (n // 12) - 1
    return f"{name}{octave}"


def make_output_path(input_path: str, in_root: str, out_root: str, suffix: str) -> str:
    """
    Mirror folder structure from in_root under out_root, and change the file extension suffix.
    """
    rel = os.path.relpath(input_path, in_root)
    base, _ = os.path.splitext(rel)
    out_full = os.path.join(out_root, base + suffix)
    os.makedirs(os.path.dirname(out_full), exist_ok=True)
    return out_full


def midi_to_text_file(midi_path: str, out_path: str) -> None:
    """
    Load a MIDI file and write a human-readable text dump to out_path.
    """
    print(f"Processing (txt dump): {midi_path}")

    try:
        mid = MidiFile(midi_path)
    except Exception as e:
        # try forgiving load
        try:
            mid = MidiFile(midi_path, clip=True)
            print(f"  [warning] Loaded with clip=True due to error: {e}")
        except Exception as e2:
            print(f"  [unreadable] {midi_path}: {e} / {e2}")
            return

    lines = []
    lines.append(f"FILE: {os.path.basename(midi_path)}")
    lines.append(f"type = {mid.type}, ticks_per_beat = {mid.ticks_per_beat}")
    lines.append(f"tracks = {len(mid.tracks)}")
    lines.append("")

    for i, track in enumerate(mid.tracks):
        lines.append(f"=== Track {i}: {track.name!r} ===")
        abs_time = 0
        for msg in track:
            abs_time += msg.time  # accumulate delta-times

            if msg.is_meta:
                lines.append(f"  t={abs_time:>6}  META  {msg.type} {msg.dict()}")
            else:
                if msg.type in ("note_on", "note_off"):
                    note_name = note_number_to_name(msg.note)
                    lines.append(
                        f"  t={abs_time:>6}  {msg.type:<8} "
                        f"ch={msg.channel} note={msg.note}({note_name}) vel={msg.velocity}"
                    )
                else:
                    lines.append(f"  t={abs_time:>6}  {msg.type} {msg.dict()}")

        lines.append("")

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  [dumped] -> {out_path}")
    except Exception as e:
        print(f"  [error ] Could not write text file for {midi_path}: {e}")


def extract_note_sequence(midi_path: str):
    """
    Extract a simple monophonic note sequence from a MIDI file.

    Heuristic: take all NOTE_ON (velocity > 0) events from all tracks,
    sorted by their absolute times, and keep their .note numbers.
    """
    try:
        mid = MidiFile(midi_path)
    except Exception:
        try:
            mid = MidiFile(midi_path, clip=True)
        except Exception:
            print(f"[extract] unreadable, skipping: {midi_path}")
            return []

    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if not msg.is_meta and msg.type == "note_on" and msg.velocity > 0:
                events.append((abs_time, msg.note))

    events.sort(key=lambda x: x[0])
    sequence = [note for _, note in events]
    return sequence


def build_first_order_markov(midi_paths):
    """
    Build a first-order Markov transition model over MIDI notes for a set of files.
    """
    counts = defaultdict(lambda: defaultdict(int))

    for path in midi_paths:
        seq = extract_note_sequence(path)
        if len(seq) < 2:
            continue
        for x, y in zip(seq[:-1], seq[1:]):
            counts[x][y] += 1

    transition_probs = {}
    for x, next_counts in counts.items():
        total = sum(next_counts.values())
        if total == 0:
            continue
        transition_probs[x] = {y: c / total for y, c in next_counts.items()}

    return transition_probs, counts


def compute_surprise_sequence(sequence, transition_probs):
    """
    For a given sequence of notes [n0, n1, n2, ...], compute surprise
    for each transition using the Markov model:
    """
    surprises = []
    for prev_note, next_note in zip(sequence[:-1], sequence[1:]):
        p_dict = transition_probs.get(prev_note, {})
        p = p_dict.get(next_note, 1e-6)  # tiny probability for unseen transitions
        s = -math.log2(p)
        surprises.append(s)
    return surprises


def write_surprise_file(sequence, surprises, out_path: str):
    """
    Save surprise per note to a tab-separated text file
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("index\tnote\tsurprise_bits\n")
            for i, (note, s) in enumerate(zip(sequence[1:], surprises), start=1):
                f.write(f"{i}\t{note}\t{s:.6f}\n")
        print(f"  [surprise] -> {out_path}")
    except Exception as e:
        print(f"  [error ] Could not write surprise file {out_path}: {e}")


def find_midi_files(root_dir: str, recursive: bool = True):
    """Return a list of .mid/.midi files under root_dir."""
    exts = {".mid", ".midi"}
    midi_files = []

    if recursive:
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in exts:
                    midi_files.append(os.path.join(dirpath, fn))
    else:
        for fn in os.listdir(root_dir):
            full = os.path.join(root_dir, fn)
            if os.path.isfile(full) and os.path.splitext(fn)[1].lower() in exts:
                midi_files.append(full)

    return midi_files


def main():
    if not os.path.isdir(ROOT_DIR):
        print(f"[error] ROOT_DIR does not exist: {ROOT_DIR}")
        return

    midi_files = find_midi_files(ROOT_DIR, recursive=RECURSIVE)
    print(f"Found {len(midi_files)} MIDI files under {ROOT_DIR}\n")
    if not midi_files:
        return

    # 1) Dump human-readable txt files, mirroring style subfolders
    print("=== Step 1: Text dumps ===")
    for path in midi_files:
        out_txt_path = make_output_path(
            input_path=path,
            in_root=ROOT_DIR,
            out_root=TEXT_ROOT,
            suffix=".mid.txt",
        )
        midi_to_text_file(path, out_txt_path)

    # 2) Group files by style = top-level subfolder
    print("\n=== Step 2: Build style-specific Markov models ===")
    style_to_files = defaultdict(list)
    for path in midi_files:
        rel = os.path.relpath(path, ROOT_DIR)
        style = rel.split(os.sep)[0] if os.sep in rel else "ROOT"
        style_to_files[style].append(path)

    style_models = {}
    for style, files in style_to_files.items():
        print(f"  Building Markov model for style '{style}' ({len(files)} files)...")
        model, counts = build_first_order_markov(files)
        style_models[style] = model
        print(f"    -> states: {len(model)}")

    # 3) For each file, compute surprise curve using its style's model
    print("\n=== Step 3: Compute surprise curves per file ===")
    for path in midi_files:
        rel = os.path.relpath(path, ROOT_DIR)
        style = rel.split(os.sep)[0] if os.sep in rel else "ROOT"
        model = style_models.get(style, {})
        if not model:
            print(f"  [skip ] No model for style '{style}' (or empty). {path}")
            continue

        seq = extract_note_sequence(path)
        if len(seq) < 2:
            print(f"  [skip ] Too few notes in {path}")
            continue

        surprises = compute_surprise_sequence(seq, model)
        out_surprise_path = make_output_path(
            input_path=path,
            in_root=ROOT_DIR,
            out_root=SURPRISE_ROOT,
            suffix=".surprise.txt",
        )
        write_surprise_file(seq, surprises, out_surprise_path)

    print("\nAll done.")


if __name__ == "__main__":
    main()
