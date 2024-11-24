import bpy
import os
import json

# Get Blender's working directory
file_dir = bpy.path.abspath("/Users/hangyin/Desktop/Learn_blender/")  # Directory where the .blend file is saved
json_file_path = os.path.join(file_dir, "midi_data.json")

# Load the JSON file
if os.path.exists(json_file_path):
    with open(json_file_path, 'r') as f:
        midi_data = json.load(f)
        print("Loaded MIDI Data:", midi_data)
else:
    print(f"File not found: {json_file_path}")

# Define piano dimensions
white_key_width = 1.0
black_key_width = 0.6
white_key_depth = 5.0
black_key_depth = 2.5
key_height = 0.2

# Key pattern for one octave
extra_key_left = [1, 2, 1]
extra_key_right = [1]
key_pattern = [1, 2, 1, 2, 1, 1, 2, 1, 2, 1, 2, 1]  # White (1) and black (2) keys in an octave
num_octaves = 7  # 7 full octaves

# Extend the key pattern for 88 keys
full_key_pattern = extra_key_left + key_pattern * num_octaves + extra_key_right

# Parameters
keyboard_z = 0  # Z-coordinate of the keyboard
speed = 1       # Movement speed (units per second)
fps = 24        # Frames per second


# Dictionary to store x_offset for each MIDI key
key_offsets = {}

# Create piano keys and assign types
def create_piano_keys():
    global key_offsets  # Ensure we update the global dictionary
    key_objects = []
    x_offset = 0

    for i, key_type in enumerate(full_key_pattern):
        if key_type == 1:  # White key
            width = white_key_width
            depth = white_key_depth
            y_pos = 0
        elif key_type == 2:  # Black key
            width = black_key_width
            depth = black_key_depth
            y_pos = -0.5
            x_offset -= white_key_width / 2  # Offset for black keys
        
        # Create the key
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_offset, y_pos, -depth / 2))
        key = bpy.context.object
        key.scale.x = width / 1.1
        key.scale.y = key_height
        key.scale.z = depth
        key.name = f"Key_{i}"

        # Add a custom property to store the key type
        key["key_type"] = key_type  # Store 1 for white or 2 for black

        # Assign a material to the key
        mat = bpy.data.materials.new(name=f"Material_Key_{i}")
        mat.diffuse_color = (1, 1, 1, 1) if key_type == 1 else (0, 0, 0, 1)
        key.data.materials.append(mat)

        # Store the x_offset for this key in the dictionary
        midi_key = i  # Assuming MIDI starts at 21
        key_offsets[midi_key] = x_offset

        key_objects.append(key)

        # Adjust offsets
        if key_type == 2:  # Black key
            x_offset += white_key_width / 2
        if key_type == 1:  # White key
            x_offset += white_key_width

    return key_objects

# create cubes for particles
def create_cubes():
    """
    Create cubes for each MIDI event at the correct initial positions,
    and ensure they continue moving past the keyboard.
    """
    extra_distance = 1.0  # Additional distance cubes move beyond the keyboard
    for i, midi_event in enumerate(midi_data):
        key, start_time, end_time = midi_event
        duration = end_time - start_time  # Calculate duration

        # Calculate initial Z position
        start_distance = speed * start_time  # Distance above the keyboard
        initial_y = 3
        initial_z = keyboard_z + start_distance

        # Get the X position based on the MIDI key from the dictionary
        x_position = key_offsets.get(key, 0)  # Default to 0 if key not found

        # Create a cube
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, initial_y, initial_z))
        cube = bpy.context.object
        cube.scale.x = 0.9
        cube.scale.z = 0.3
        cube.name = f"MIDI_Cube_{i}"

        # Animate the cube moving down
        start_frame = 0  # All cubes start moving together at frame 0
        end_frame = start_frame + int((start_time + extra_distance / speed) * fps)  # When it moves off-screen

        # Insert keyframes
        cube.location = (x_position, initial_y, initial_z)  # Initial position
        cube.keyframe_insert(data_path="location", frame=start_frame)

        cube.location = (x_position, initial_y, keyboard_z - extra_distance)  # Final position (below the keyboard)
        cube.keyframe_insert(data_path="location", frame=end_frame)

        # Set keyframe interpolation to Linear
        action = cube.animation_data.action
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'
                
        # Optionally color the cube to represent the key or duration
        mat = bpy.data.materials.new(name=f"Material_{key}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Example: Use the key index to vary the color
            bsdf.inputs['Base Color'].default_value = ((key - 21) * 0.01, 0.5, 0.7, 1)
        cube.data.materials.append(mat)
        
        # Retrieve the key object
        key_object = bpy.data.objects.get(f"Key_{key}")
        if key_object:
            key_material = ensure_material_with_nodes(key_object)  # Ensure material is created and assigned
            if key_material.use_nodes:
                key_bsdf = key_material.node_tree.nodes.get("Principled BSDF")
                if key_bsdf:
                    # Get the key's type from the custom property
                    key_type = key_object.get("key_type", 1)  # Default to 1 (white) if no property exists

                    # Default color: white for key_type 1 (white keys), black for key_type 2 (black keys)
                    if key_type == 1:  # White key
                        default_color = (1, 1, 1, 1)  # White color
                    elif key_type == 2:  # Black key
                        default_color = (0, 0, 0, 1)  # Black color

                    press_color = (0, 1, 0, 1)  # Red when pressed

                    hit_frame = int(start_time * fps)

                    # Set the initial color to default (white or black)
                    key_bsdf.inputs['Base Color'].default_value = default_color
                    key_bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=hit_frame - 3)

                    # Change to press color when the key is pressed (hit_frame)
                    key_bsdf.inputs['Base Color'].default_value = press_color
                    key_bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=hit_frame)

                    # Revert to default color after a few frames (hit_frame + 2)
                    key_bsdf.inputs['Base Color'].default_value = default_color
                    key_bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=hit_frame + 5)
                else:
                    print(f"Principled BSDF node not found in material {key_material.name}.")
            else:
                print(f"Material {key_material.name} does not use nodes.")
        else:
            print(f"Key object for Key_{key} not found.")

            
            
# Ensure the material has nodes and is properly named
def ensure_material_with_nodes(key_object):
    # Get or create the material for the key
    material_name = f"Material_{key_object.name}"  # Create a unique material name based on the key's name
    key_material = bpy.data.materials.get(material_name)
    
    if not key_material:  # If the material does not exist, create a new one
        key_material = bpy.data.materials.new(name=material_name)
    
    # Ensure the material uses nodes
    if not key_material.use_nodes:
        key_material.use_nodes = True  # Set to use nodes if it's not already

    # Assign the material to the key object
    if key_object.data.materials:
        key_object.data.materials[0] = key_material  # Replace the first material slot
    else:
        key_object.data.materials.append(key_material)  # Add the material to the object
    
    return key_material
            
# Main function
def main():
    # Clear the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create and animate cubes
    create_piano_keys()  # Create keys and store their offsets
    create_cubes()       # Create MIDI cubes using stored offsets

# Run the script
main()
