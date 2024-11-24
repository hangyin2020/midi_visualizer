import pretty_midi

# Function to convert MIDI pitch to key index (starting from 0)
def midi_pitch_to_key_index(pitch):
    return pitch - 21  # MIDI pitch 21 corresponds to A0 (key 0)

# Load the MIDI file
midi_file = 'Steinway Grand Piano test1.mid'
midi_data = pretty_midi.PrettyMIDI(midi_file)

# Generate mock data for Blender
midi_mock_data = []

for instrument in midi_data.instruments:
    for note in instrument.notes:
        key_index = midi_pitch_to_key_index(note.pitch)
        start_time = round(note.start, 2)  # Round to 2 decimal places
        duration = round(note.end - note.start, 2)  # Round to 2 decimal places
        midi_mock_data.append((key_index, start_time, duration))

# Print the generated data for Blender
print("midi_mock_data = [")
for entry in midi_mock_data:
    print(f"    {entry},")
print("]")
