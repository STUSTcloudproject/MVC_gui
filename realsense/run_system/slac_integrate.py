# ----------------------------------------------------------------------------
# -                        Open3D: www.open3d.org                            -
# ----------------------------------------------------------------------------
# Copyright (c) 2018-2023 www.open3d.org
# SPDX-License-Identifier: MIT
# ----------------------------------------------------------------------------

# examples/python/reconstruction_system/slac_integrate.py

import numpy as np
import open3d as o3d
import open3d.core as o3c
import os, sys

from open3d_example import join, get_rgbd_file_lists

def run(config, stop_event, message_queue):
    message_queue.put("slac non-rigid optimization.")
    o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)

    path_dataset = config["path_dataset"]
    slac_folder = join(path_dataset, config["subfolder_slac"])

    [color_files, depth_files] = get_rgbd_file_lists(config["path_dataset"])
    if len(color_files) != len(depth_files):
        raise ValueError(
            "The number of color images {} must equal to the number of depth images {}."
            .format(len(color_files), len(depth_files)))

    posegraph = o3d.io.read_pose_graph(
        join(slac_folder, config["template_optimized_posegraph_slac"]))

    if config["path_intrinsic"]:
        intrinsic = o3d.io.read_pinhole_camera_intrinsic(
            config["path_intrinsic"])
    else:
        intrinsic = o3d.camera.PinholeCameraIntrinsic(
            o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault)

    focal_length = intrinsic.get_focal_length()
    principal_point = intrinsic.get_principal_point()

    intrinsic_t = o3d.core.Tensor([[focal_length[0], 0, principal_point[0]],
                                   [0, focal_length[1], principal_point[1]],
                                   [0, 0, 1]])

    device = o3d.core.Device(
        'CUDA:0' if o3d.core.cuda.is_available() else 'CPU:0')
    voxel_grid = o3d.t.geometry.VoxelBlockGrid(
        attr_names=('tsdf', 'weight', 'color'),
        attr_dtypes=(o3c.float32, o3c.float32, o3c.float32),
        attr_channels=((1), (1), (3)),
        voxel_size=config['tsdf_cubic_size'] / 512,
        block_resolution=16,
        block_count=config['block_count'],
        device=device)

    ctr_grid_keys = o3d.core.Tensor.load(join(slac_folder, "ctr_grid_keys.npy"))
    ctr_grid_values = o3d.core.Tensor.load(join(slac_folder, "ctr_grid_values.npy"))

    ctr_grid = o3d.t.pipelines.slac.control_grid(3.0 / 8,
                                                 ctr_grid_keys.to(device),
                                                 ctr_grid_values.to(device),
                                                 device)

    fragment_folder = join(path_dataset, config["folder_fragment"])

    k = 0
    depth_scale = float(config['depth_scale'])
    depth_max = float(config['depth_max'])
    for i in range(len(posegraph.nodes)):
        if stop_event.is_set():
            message_queue.put("Stopping SLAC integration")
            return
        fragment_pose_graph = o3d.io.read_pose_graph(
            join(fragment_folder, "fragment_optimized_%03d.json" % i))
        for node in fragment_pose_graph.nodes:
            if stop_event.is_set():
                message_queue.put("Stopping SLAC integration")
                return
            pose_local = node.pose
            extrinsic_local_t = o3d.core.Tensor(np.linalg.inv(pose_local))

            pose = np.dot(posegraph.nodes[i].pose, node.pose)
            extrinsic_t = o3d.core.Tensor(np.linalg.inv(pose))

            depth = o3d.t.io.read_image(depth_files[k]).to(device)
            color = o3d.t.io.read_image(color_files[k]).to(device)
            rgbd = o3d.t.geometry.RGBDImage(color, depth)

            message_queue.put('Deforming and integrating Frame {:3d}'.format(k))
            rgbd_projected = ctr_grid.deform(rgbd, intrinsic_t,
                                             extrinsic_local_t, depth_scale,
                                             depth_max)

            frustum_block_coords = voxel_grid.compute_unique_block_coordinates(
                rgbd_projected.depth, intrinsic_t, extrinsic_t, depth_scale,
                depth_max)

            voxel_grid.integrate(frustum_block_coords, rgbd_projected.depth,
                                 rgbd_projected.color, intrinsic_t, extrinsic_t,
                                 depth_scale, depth_max)
            k = k + 1

    if (config["save_output_as"] == "pointcloud"):
        pcd = voxel_grid.extract_point_cloud().to(o3d.core.Device("CPU:0"))
        save_pcd_path = join(slac_folder, "output_slac_pointcloud.ply")
        o3d.t.io.write_point_cloud(save_pcd_path, pcd)
    else:
        mesh = voxel_grid.extract_triangle_mesh().to(o3d.core.Device("CPU:0"))
        mesh_legacy = mesh.to_legacy()
        save_mesh_path = join(slac_folder, "output_slac_mesh.ply")
        o3d.io.write_triangle_mesh(save_mesh_path, mesh_legacy)
