import os
from mido import MidiFile

# --------- CONFIG: CHANGE THIS -------------
ROOT_DIR = r"/Users/skyla/Downloads/midi"  # <- set this to your MIDI folder
RECURSIVE = True                         # include subfolders or not
# ------------------------------------------


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


def note_number_to_name(n):
    """Convert MIDI note number (0–127) to e.g. C4, A#3, etc."""
    if not (0 <= n <= 127):
        return str(n)
    name = NOTE_NAMES[n % 12]
    octave = (n // 12) - 1
    return f"{name}{octave}"


def midi_to_text_file(midi_path):
    """
    Load a MIDI file and write a human-readable text dump next to it.

    e.g. /folder/song.mid -> /folder/song.mid.txt
    """
    try:
        mid = MidiFile(midi_path)
    except Exception as e:
        # try forgiving load
        try:
            mid = MidiFile(midi_path, clip=True)
        except Exception as e2:
            print(f"[unreadable] {midi_path}: {e} / {e2}")
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
                # meta events
                lines.append(f"  t={abs_time:>6}  META  {msg.type} {msg.dict()}")
            else:
                # regular MIDI events
                if msg.type in ("note_on", "note_off"):
                    note_name = note_number_to_name(msg.note)
                    lines.append(
                        f"  t={abs_time:>6}  {msg.type:<8} "
                        f"ch={msg.channel} note={msg.note}({note_name}) vel={msg.velocity}"
                    )
                else:
                    # other MIDI messages (control_change, program_change, etc.)
                    lines.append(f"  t={abs_time:>6}  {msg.type} {msg.dict()}")

        lines.append("")

    # output path: add ".txt" after the .mid extension
    out_path = midi_path + ".txt"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[dumped] {midi_path}  ->  {out_path}")
    except Exception as e:
        print(f"[error ] Could not write text file for {midi_path}: {e}")


def find_midi_files(root_dir, recursive=True):
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
    midi_files = find_midi_files(ROOT_DIR, recursive=RECURSIVE)
    print(f"Found {len(midi_files)} MIDI files under {ROOT_DIR}\n")

    for path in midi_files:
        midi_to_text_file(path)

    print("\nDone.")


if __name__ == "__main__":
    main()
