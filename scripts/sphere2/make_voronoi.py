"""Precomputes the spherical Voronoi cells used to fracture the black sphere (scripts/sphere2/voronoi.npz).
Blender's bundled Python has no scipy, so the cells are computed once here. usage: python make_voronoi.py out.npz"""
import sys
import numpy as np
from scipy.spatial import SphericalVoronoi

rng = np.random.default_rng(17)
O = np.array([-0.35, -0.85, 0.4]); O /= np.linalg.norm(O)            # smaller pieces where the first crack starts
dirs = rng.normal(0, 1, (6000, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
pacc = 0.25 + 0.75 * np.clip((dirs @ O + 0.2) / 1.2, 0, 1) ** 2
S = dirs[rng.random(6000) < pacc][:230]
sv = SphericalVoronoi(S, radius=1.0, center=np.zeros(3)); sv.sort_vertices_of_regions()
np.savez(sys.argv[1], seeds=S, verts=sv.vertices, idx=np.concatenate(sv.regions), lens=np.array([len(r) for r in sv.regions]))
