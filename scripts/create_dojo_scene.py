"""
create_dojo_scene.py — Blender script to create a Traditional Dojo scene.

Run with:
    blender --background --python create_dojo_scene.py

Creates a warm, traditional Japanese dojo interior for the Neurodivergent Ninja
avatar video pipeline. Outputs background and foreground layers for compositing.
"""

import bpy
import math
import os
import json

# Output settings
OUTPUT_DIR = r"C:\Users\Steam\Documents\NeurodivergentNinja\dojo_scene"
RENDER_WIDTH = 1080
RENDER_HEIGHT = 1920  # 9:16 vertical

# Colors (RGB normalized 0-1)
COLORS = {
    "wood_dark": (0.15, 0.08, 0.04),
    "wood_light": (0.35, 0.22, 0.12),
    "wood_warm": (0.45, 0.28, 0.15),
    "paper_shoji": (0.95, 0.92, 0.85),
    "paper_glow": (1.0, 0.98, 0.9),
    "wall_dark": (0.12, 0.10, 0.08),
    "tatami_green": (0.45, 0.50, 0.35),
    "tatami_edge": (0.2, 0.15, 0.08),
    "lantern_warm": (1.0, 0.7, 0.3),
    "scroll_paper": (0.9, 0.88, 0.82),
    "ink_black": (0.05, 0.05, 0.05),
    "gold_accent": (0.8, 0.6, 0.2),
}


def cleanup_scene():
    """Remove all default objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def create_material(name, base_color, roughness=0.5, emission=None):
    """Create a principled BSDF material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 2.0
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_wood_material(name, base_color, grain_scale=20):
    """Create wood material with procedural grain."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Texture coordinate
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Mapping for grain direction
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-600, 0)
    mapping.inputs['Scale'].default_value = (grain_scale, 1, 1)
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    
    # Wave texture for wood grain
    wave = nodes.new('ShaderNodeTexWave')
    wave.location = (-400, 0)
    wave.wave_type = 'RINGS'
    wave.inputs['Scale'].default_value = 3.0
    wave.inputs['Distortion'].default_value = 8.0
    wave.inputs['Detail'].default_value = 2.0
    links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
    
    # Color ramp for grain coloring
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-200, 0)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (*base_color, 1.0)
    ramp.color_ramp.elements[1].position = 0.6
    darker = tuple(c * 0.7 for c in base_color)
    ramp.color_ramp.elements[1].color = (*darker, 1.0)
    links.new(wave.outputs['Color'], ramp.inputs['Fac'])
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (100, 0)
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_shoji_material():
    """Create translucent shoji paper material."""
    mat = bpy.data.materials.new(name="Shoji_Paper")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Principled BSDF with subsurface for paper translucency
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*COLORS['paper_shoji'], 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Subsurface Weight'].default_value = 0.3
    bsdf.inputs['Subsurface Radius'].default_value = (0.5, 0.5, 0.5)
    
    # Add slight emission for backlit effect
    bsdf.inputs['Emission Color'].default_value = (*COLORS['paper_glow'], 1.0)
    bsdf.inputs['Emission Strength'].default_value = 0.5
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_floor():
    """Create polished wooden floor with planks."""
    # Base floor plane
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    
    # Add wood material
    mat = create_wood_material("Floor_Wood", COLORS['wood_warm'], grain_scale=30)
    floor.data.materials.append(mat)
    
    return floor


def create_back_wall():
    """Create the back wall of the dojo."""
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 4, 3))
    wall = bpy.context.active_object
    wall.name = "Back_Wall"
    wall.rotation_euler = (math.radians(90), 0, 0)
    wall.scale = (1, 1, 1.2)
    
    mat = create_material("Wall_Dark", COLORS['wall_dark'], roughness=0.8)
    wall.data.materials.append(mat)
    
    return wall


def create_shoji_screen(location, rotation_z=0, panels=3):
    """Create a shoji screen (sliding door) with wooden frame."""
    screen_width = 2.5
    screen_height = 4.0
    frame_thickness = 0.05
    
    # Create parent empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    parent = bpy.context.active_object
    parent.name = f"Shoji_Screen_{location[0]:.1f}"
    parent.rotation_euler = (0, 0, math.radians(rotation_z))
    
    # Frame material
    frame_mat = create_wood_material("Shoji_Frame", COLORS['wood_dark'], grain_scale=50)
    
    # Paper material
    paper_mat = create_shoji_material()
    
    for panel_idx in range(panels):
        panel_width = screen_width / panels
        panel_x = (panel_idx - (panels - 1) / 2) * panel_width
        
        # Vertical frame pieces
        for side in [-1, 1]:
            x_offset = panel_x + side * panel_width / 2
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(x_offset, 0, screen_height / 2)
            )
            frame = bpy.context.active_object
            frame.scale = (frame_thickness, frame_thickness, screen_height / 2)
            frame.data.materials.append(frame_mat)
            frame.parent = parent
        
        # Horizontal frame pieces
        for z_pos in [0.1, screen_height - 0.1, screen_height / 3, 2 * screen_height / 3]:
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(panel_x, 0, z_pos)
            )
            frame = bpy.context.active_object
            frame.scale = (panel_width / 2, frame_thickness, frame_thickness)
            frame.data.materials.append(frame_mat)
            frame.parent = parent
        
        # Paper panels (2 per panel - upper and lower halves)
        for z_idx, z_pos in enumerate([screen_height / 6 + 0.1, screen_height / 2 + 0.2]):
            bpy.ops.mesh.primitive_plane_add(
                size=1,
                location=(panel_x, 0.02, z_pos + screen_height / 6)
            )
            paper = bpy.context.active_object
            paper.scale = (panel_width / 2 - frame_thickness, 1, screen_height / 6 - frame_thickness)
            paper.rotation_euler = (math.radians(90), 0, 0)
            paper.data.materials.append(paper_mat)
            paper.parent = parent
    
    return parent


def create_lantern(location, name="Lantern"):
    """Create a warm Japanese paper lantern."""
    # Lantern body (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.15,
        depth=0.4,
        location=location
    )
    lantern = bpy.context.active_object
    lantern.name = name
    
    # Lantern material with emission
    mat = create_material(
        f"{name}_Mat",
        COLORS['paper_shoji'],
        roughness=0.9,
        emission=COLORS['lantern_warm']
    )
    lantern.data.materials.append(mat)
    
    # Add actual light inside
    light_loc = (location[0], location[1], location[2])
    bpy.ops.object.light_add(type='POINT', location=light_loc)
    light = bpy.context.active_object
    light.name = f"{name}_Light"
    light.data.energy = 50
    light.data.color = COLORS['lantern_warm']
    light.data.shadow_soft_size = 0.3
    light.parent = lantern
    
    # Top cap
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08,
        depth=0.05,
        location=(location[0], location[1], location[2] + 0.22)
    )
    cap = bpy.context.active_object
    cap.data.materials.append(create_material("Lantern_Cap", COLORS['wood_dark'], roughness=0.6))
    cap.parent = lantern
    
    return lantern


def create_scroll(location, text_lines=None):
    """Create a decorative wall scroll with kanji."""
    # Scroll backing
    bpy.ops.mesh.primitive_plane_add(
        size=1,
        location=location
    )
    scroll = bpy.context.active_object
    scroll.name = "Wall_Scroll"
    scroll.scale = (0.4, 1, 1.2)
    scroll.rotation_euler = (math.radians(90), 0, 0)
    
    mat = create_material("Scroll_Paper", COLORS['scroll_paper'], roughness=0.85)
    scroll.data.materials.append(mat)
    
    # Scroll rollers (top and bottom)
    roller_mat = create_wood_material("Scroll_Roller", COLORS['wood_dark'], grain_scale=100)
    for z_offset in [-1.25, 1.25]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.04,
            depth=0.5,
            location=(location[0], location[1] - 0.02, location[2] + z_offset)
        )
        roller = bpy.context.active_object
        roller.rotation_euler = (0, math.radians(90), 0)
        roller.data.materials.append(roller_mat)
        roller.parent = scroll
    
    return scroll


def create_low_table():
    """Create a low Japanese table (chabudai) for foreground depth."""
    table_height = 0.35
    table_width = 1.2
    table_depth = 0.8
    
    # Table top
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, -1.5, table_height / 2 + 0.15)
    )
    table_top = bpy.context.active_object
    table_top.name = "Table_Top"
    table_top.scale = (table_width / 2, table_depth / 2, 0.03)
    
    mat = create_wood_material("Table_Wood", COLORS['wood_light'], grain_scale=40)
    table_top.data.materials.append(mat)
    
    # Table legs
    leg_positions = [
        (-table_width/2 + 0.1, -table_depth/2 + 0.1),
        (table_width/2 - 0.1, -table_depth/2 + 0.1),
        (-table_width/2 + 0.1, table_depth/2 - 0.1),
        (table_width/2 - 0.1, table_depth/2 - 0.1),
    ]
    
    for i, (x, y) in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(x, -1.5 + y, table_height / 2)
        )
        leg = bpy.context.active_object
        leg.name = f"Table_Leg_{i}"
        leg.scale = (0.03, 0.03, table_height / 2)
        leg.data.materials.append(mat)
        leg.parent = table_top
    
    return table_top


def create_holographic_display(location):
    """Create a subtle holographic display for modern touch."""
    # Floating frame
    bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    display = bpy.context.active_object
    display.name = "Holo_Display"
    display.scale = (0.5, 1, 0.35)
    display.rotation_euler = (math.radians(80), 0, 0)
    
    # Create emissive holographic material
    mat = bpy.data.materials.new(name="Holo_Mat")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Emission with cyan tint
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0.2, 0.8, 1.0, 1.0)  # Subtle cyan
    emission.inputs['Strength'].default_value = 1.5
    
    # Transparent for alpha
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    
    # Mix for semi-transparency
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.3  # 30% visible
    
    links.new(transparent.outputs['BSDF'], mix.inputs[1])
    links.new(emission.outputs['Emission'], mix.inputs[2])
    
    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    display.data.materials.append(mat)
    
    return display


def setup_camera():
    """Set up camera with slight upward angle."""
    # Camera looking slightly up at the avatar
    bpy.ops.object.camera_add(
        location=(0, -4.5, 1.5)  # Position in front, at chest height
    )
    camera = bpy.context.active_object
    camera.name = "Dojo_Camera"
    
    # Point camera slightly upward (as if looking up at presenter)
    camera.rotation_euler = (math.radians(85), 0, 0)  # Near vertical but tilted up
    
    # Set camera properties for vertical format
    camera.data.type = 'PERSP'
    camera.data.lens = 35  # Wide-ish lens for immersive feel
    
    bpy.context.scene.camera = camera
    
    return camera


def setup_lighting():
    """Set up warm, soft dojo lighting."""
    # Main key light (warm, from above-left)
    bpy.ops.object.light_add(type='AREA', location=(-3, 2, 5))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = 200
    key_light.data.color = (1.0, 0.95, 0.85)  # Warm white
    key_light.data.size = 4
    key_light.rotation_euler = (math.radians(45), math.radians(-20), 0)
    
    # Fill light (cooler, from right)
    bpy.ops.object.light_add(type='AREA', location=(3, 0, 3))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 80
    fill_light.data.color = (0.9, 0.95, 1.0)  # Slightly cool
    fill_light.data.size = 3
    fill_light.rotation_euler = (math.radians(60), math.radians(30), 0)
    
    # Back light from shoji screens (simulating exterior light)
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
    back_light = bpy.context.active_object
    back_light.name = "Shoji_Backlight"
    back_light.data.energy = 150
    back_light.data.color = (1.0, 0.98, 0.92)  # Warm daylight
    back_light.data.size = 8
    back_light.rotation_euler = (math.radians(120), 0, 0)
    
    # Ambient/world lighting
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("Dojo_World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    bg_node = nodes.get('Background')
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.02, 0.018, 0.015, 1.0)  # Very dark warm
        bg_node.inputs['Strength'].default_value = 0.5


def setup_render_settings():
    """Configure render settings for high-quality output."""
    scene = bpy.context.scene
    
    # Resolution
    scene.render.resolution_x = RENDER_WIDTH
    scene.render.resolution_y = RENDER_HEIGHT
    scene.render.resolution_percentage = 100
    
    # Use Eevee for faster rendering (good for stylized look)
    scene.render.engine = 'BLENDER_EEVEE'
    
    # Eevee settings - Blender 5.0 compatible
    eevee = scene.eevee
    eevee.taa_render_samples = 64
    
    # Try to set optional settings (API changes between versions)
    try:
        eevee.use_gtao = True  # Ambient occlusion
        eevee.gtao_distance = 1.0
    except AttributeError:
        pass  # Not available in this version
    
    try:
        eevee.use_bloom = True
        eevee.bloom_threshold = 0.8
        eevee.bloom_intensity = 0.3
    except AttributeError:
        pass  # Not available in this version
    
    # Film settings
    scene.render.film_transparent = True  # For alpha channel
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'


def build_dojo_scene():
    """Main function to build the complete dojo scene."""
    print("Building Traditional Dojo Scene...")
    
    # Clear existing scene
    cleanup_scene()
    
    # Create scene elements
    print("  Creating floor...")
    create_floor()
    
    print("  Creating back wall...")
    create_back_wall()
    
    print("  Creating shoji screens...")
    # Left shoji screen (angled inward)
    create_shoji_screen(location=(-3, 3, 0), rotation_z=-15, panels=3)
    # Right shoji screen (angled inward)  
    create_shoji_screen(location=(3, 3, 0), rotation_z=15, panels=3)
    # Back center shoji (behind where avatar will be)
    create_shoji_screen(location=(0, 4.5, 0), rotation_z=0, panels=4)
    
    print("  Creating lanterns...")
    create_lantern(location=(-2, 2, 3.5), name="Lantern_Left")
    create_lantern(location=(2, 2, 3.5), name="Lantern_Right")
    
    print("  Creating wall scroll...")
    create_scroll(location=(2.8, 3.8, 3))
    
    print("  Creating low table (foreground)...")
    create_low_table()
    
    print("  Creating holographic display...")
    create_holographic_display(location=(-2.2, 2.5, 2.8))
    
    print("  Setting up camera...")
    setup_camera()
    
    print("  Setting up lighting...")
    setup_lighting()
    
    print("  Configuring render settings...")
    setup_render_settings()
    
    print("Dojo scene complete!")


def render_scene():
    """Render the scene and save outputs."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    scene = bpy.context.scene
    
    # Render full scene (background)
    print(f"Rendering background to {OUTPUT_DIR}...")
    scene.render.filepath = os.path.join(OUTPUT_DIR, "dojo_background.png")
    bpy.ops.render.render(write_still=True)
    
    # For foreground, hide everything except the table and render with alpha
    print("Rendering foreground layer...")
    
    # Hide all objects except foreground elements
    foreground_objects = ['Table_Top']
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE']:
            if obj.name in foreground_objects or any(obj.name.startswith(fg) for fg in foreground_objects):
                obj.hide_render = False
            elif 'Table_Leg' in obj.name:
                obj.hide_render = False
            else:
                obj.hide_render = True
        elif obj.type == 'LIGHT':
            obj.hide_render = False  # Keep lights
    
    scene.render.filepath = os.path.join(OUTPUT_DIR, "dojo_foreground.png")
    bpy.ops.render.render(write_still=True)
    
    # Restore visibility
    for obj in bpy.data.objects:
        obj.hide_render = False
    
    # Save blend file
    blend_path = os.path.join(OUTPUT_DIR, "dojo_scene.blend")
    print(f"Saving blend file to {blend_path}...")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    
    # Create scene config JSON
    config = {
        "name": "Traditional Dojo",
        "version": "1.0",
        "resolution": {
            "width": RENDER_WIDTH,
            "height": RENDER_HEIGHT
        },
        "avatar_zone": {
            "description": "Center area for upper-body avatar compositing",
            "x_center": 0.5,  # Normalized (0-1)
            "y_center": 0.45,  # Slightly above center
            "scale": 0.6,  # Avatar should take up 60% of height
            "safe_area": {
                "left": 0.2,
                "right": 0.8,
                "top": 0.1,
                "bottom": 0.85
            }
        },
        "layers": {
            "background": "dojo_background.png",
            "foreground": "dojo_foreground.png",
            "blend_file": "dojo_scene.blend"
        },
        "style": {
            "theme": "traditional_japanese",
            "mood": "warm, calm, focused",
            "lighting": "soft warm lantern light with daylight from shoji",
            "colors": ["wood_brown", "paper_cream", "warm_orange"]
        },
        "compositing_hints": {
            "avatar_layer_order": 1,  # Between background (0) and foreground (2)
            "foreground_purpose": "Table edge creates depth in front of avatar",
            "edge_blend": "soft vignette recommended",
            "color_correction": "warm tint to match scene"
        }
    }
    
    config_path = os.path.join(OUTPUT_DIR, "scene_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Saved scene config to {config_path}")
    
    print("\n=== Render Complete ===")
    print(f"Background: {os.path.join(OUTPUT_DIR, 'dojo_background.png')}")
    print(f"Foreground: {os.path.join(OUTPUT_DIR, 'dojo_foreground.png')}")
    print(f"Blend file: {blend_path}")
    print(f"Config: {config_path}")


if __name__ == "__main__":
    build_dojo_scene()
    render_scene()
