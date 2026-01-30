import omni.usd
from pxr import Usd, UsdGeom, Gf, Sdf, UsdPhysics
import numpy as np
from PIL import Image

# ==========================================
# 해당 파일은 반드시 IsaacLab -> Window -> Script Editor 에서 실행해야 합니다.
# This script must be run in IsaacLab -> Window -> Script Editor.

# ==========================================
# [Configuration] Path and Parameters
# ==========================================
tiff_path = "/home/ash/projects/11_ICCAS2026_Mars_Logistics_Spot/assets/ESP_023247_1985.tif"

# ⚠️ Performance Trade-off: Increase 'step' to reduce polygon count (Recommended: 20~50)
step = 20  
# For Float32 (usually in meters), keep scale at 1.0.
vertical_scale = 1.0 
pixel_size_meters = 0.25 * step 

# ==========================================
# 1. Load Image & Clean "Garbage" Values
# ==========================================
Image.MAX_IMAGE_PIXELS = None 

try:
    print(f"🚀 Loading image from: {tiff_path}")
    img = Image.open(tiff_path)
    img_array = np.array(img)
    print(f"✅ Raw Data Shape: {img_array.shape}, Type: {img_array.dtype}")
except Exception as e:
    print(f"❌ Load Failed: {e}")
    raise e

# [Key Fix] Logic to handle NoData (Extreme values)
print("🧹 Cleaning NoData/Garbage values...")

# 1. Set valid range (Mars surface is typically between -8000m and 22000m)
# We treat anything outside -100,000 ~ 100,000 as garbage/NoData.
valid_mask = (img_array > -100000) & (img_array < 100000)

if np.any(valid_mask):
    # Find the lowest valid value (ground level)
    valid_min = np.min(img_array[valid_mask])
    print(f"👉 Valid Min Height detected: {valid_min}")
    
    # Overwrite garbage values with the 'valid min value' (flatten them)
    img_array[~valid_mask] = valid_min
else:
    print("⚠️ Warning: No valid height data found? Check the TIF file.")

# ==========================================
# 2. Downsample & Scale
# ==========================================
print(f"📉 Downsampling (Step: {step})...")
height_data = img_array[::step, ::step]

# If QGIS exported as Float32, the values are likely already in meters.
# So we DO NOT divide by 65535. Just apply vertical_scale.
height_data = height_data * vertical_scale

rows, cols = height_data.shape
print(f"👉 Final Grid: {rows} x {cols}, Max Height: {np.max(height_data):.2f}, Min Height: {np.min(height_data):.2f}")

# ==========================================
# 3. Generate Mesh
# ==========================================
print("⚙️ Building Mesh Vertices...")
x = np.linspace(0, cols * pixel_size_meters, cols)
y = np.linspace(0, rows * pixel_size_meters, rows)
xv, yv = np.meshgrid(x, y)

# Flatten arrays to list of (x, y, z) points
points = np.column_stack((xv.ravel(), yv.ravel(), height_data.ravel()))
points_vt = [Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])) for p in points]

# Generate Indices (Optimized for speed)
print("🔗 Connecting Triangles...")
r_idx = np.arange(rows - 1)
c_idx = np.arange(cols - 1)
R, C = np.meshgrid(r_idx, c_idx, indexing='ij')

p0 = R * cols + C
p1 = p0 + 1
p2 = p0 + cols
p3 = p2 + 1

indices = np.column_stack((p0.ravel(), p2.ravel(), p1.ravel(), p1.ravel(), p2.ravel(), p3.ravel())).ravel()
vertex_indices = indices.tolist()
vertex_counts = [3] * (len(vertex_indices) // 3)

# Apply to USD Stage
stage = omni.usd.get_context().get_stage()
mesh_path = "/World/Mars_Mesh"

if stage.GetPrimAtPath(mesh_path):
    stage.RemovePrim(mesh_path)

print(f"📦 Creating USD Mesh at: {mesh_path}")
mesh_geom = UsdGeom.Mesh.Define(stage, mesh_path)
mesh_geom.CreatePointsAttr(points_vt)
mesh_geom.CreateFaceVertexIndicesAttr(vertex_indices)
mesh_geom.CreateFaceVertexCountsAttr(vertex_counts)

# Set Normals and Extent (Bounding Box)
mesh_geom.CreateNormalsAttr()
extent = [
    Gf.Vec3f(float(np.min(x)), float(np.min(y)), float(np.min(height_data))),
    Gf.Vec3f(float(np.max(x)), float(np.max(y)), float(np.max(height_data)))
]
mesh_geom.CreateExtentAttr(extent)

# Apply Physics Collision
print("🛡️ Applying Physics Collision...")
prim = mesh_geom.GetPrim()
if not prim.HasAPI(UsdPhysics.CollisionAPI):
    UsdPhysics.CollisionAPI.Apply(prim)

print("🎉 Success! Terrain Generated.")
print("👉 Press 'F' to focus.")