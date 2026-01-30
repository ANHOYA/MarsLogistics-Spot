import omni.kit.commands
import omni.usd
from pxr import UsdGeom, Gf, Sdf, UsdPhysics

# ==========================================
# [User Configuration] Modify this section only!
# ==========================================
# Enter the absolute path of the .tif file saved from QGIS
# (Recommended: Use forward slash '/' instead of backslash '\')
tiff_path = "/home/ash/projects/11_ICCAS2026_Mars_Logistics_Spot/assets/ESP_023247_1985.tif"

# Mars Terrain Scale Settings (Aspect ratio must match)
# Usually, HiRISE DTM resolution is about 0.25m ~ 0.5m per pixel.
# If the terrain appears too small, adjust this value to 1.0 or 100.0.
horizontal_scale = 1.0  
vertical_scale = 1.0    # Height scale (1.0 is original if saved as Float32)

# ==========================================
# 1. Create HeightField (Terrain)
# ==========================================
stage = omni.usd.get_context().get_stage()
terrain_path = "/World/Mars_Terrain"

# Delete if existing prim name exists (Prevent duplication)
if stage.GetPrimAtPath(terrain_path):
    omni.kit.commands.execute("DeletePrims", paths=[terrain_path])

print(f"🚀 Loading Mars Terrain... Path: {tiff_path}")

# Execute terrain creation command
omni.kit.commands.execute(
    "CreateHeightField",
    path=terrain_path,
    parent_path="/World",
    filename=tiff_path,
    horizontal_scale=horizontal_scale,
    vertical_scale=vertical_scale
)

# ==========================================
# 2. Apply Physics Material (Mars Regolith Properties)
# ==========================================
# Mars soil is slippery but soft. Setting friction coefficient to 0.6~0.7
material_path = "/World/Physics_Materials/Regolith"
omni.kit.commands.execute(
    "AddPhysicsMaterial",
    stage=stage,
    path=material_path,
    static_friction=0.7,  # Static friction (High due to sand)
    dynamic_friction=0.6, # Dynamic friction
    restitution=0.1       # Restitution (Shock absorption, low bounce due to sand)
)

# Bind physics material to the terrain
prim = stage.GetPrimAtPath(terrain_path)
utils = UsdPhysics.CollisionAPI.Apply(prim)
binding = UsdPhysics.MaterialBindingAPI.Apply(prim)
material = stage.GetPrimAtPath(material_path)
rel = binding.CreatePhysicsMaterialBindingRel()
rel.AddTarget(material.GetPath())

print("✅ Mars Terrain Creation and Physics Application Complete!")
print("👉 If you don't see anything, press 'F' key to focus.")
