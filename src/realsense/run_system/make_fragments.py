import math
import multiprocessing
import os
import numpy as np
import open3d as o3d
from open3d_example import *
from optimize_posegraph import optimize_posegraph_for_fragment

# check opencv python package
with_opencv = initialize_opencv()
if with_opencv:
    from opencv_pose_estimation import pose_estimation

def register_one_rgbd_pair(s, t, color_files, depth_files, intrinsic, with_opencv, config):
    source_rgbd_image = read_rgbd_image(color_files[s], depth_files[s], True, config)
    target_rgbd_image = read_rgbd_image(color_files[t], depth_files[t], True, config)
    option = o3d.pipelines.odometry.OdometryOption()
    option.depth_diff_max = config["depth_diff_max"]
    if abs(s - t) != 1:
        if with_opencv:
            success_5pt, odo_init = pose_estimation(source_rgbd_image, target_rgbd_image, intrinsic, False)
            if success_5pt:
                [success, trans, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
                    source_rgbd_image, target_rgbd_image, intrinsic, odo_init,
                    o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), option)
                return [success, trans, info]
        return [False, np.identity(4), np.identity(6)]
    else:
        odo_init = np.identity(4)
        [success, trans, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
            source_rgbd_image, target_rgbd_image, intrinsic, odo_init,
            o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), option)
        return [success, trans, info]

def make_posegraph_for_fragment(path_dataset, sid, eid, color_files, depth_files, fragment_id, n_fragments, intrinsic, with_opencv, config, stop_event, message_queue):
    o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)
    pose_graph = o3d.pipelines.registration.PoseGraph()
    trans_odometry = np.identity(4)
    pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(trans_odometry))
    for s in range(sid, eid):
        for t in range(s + 1, eid):
            if stop_event.is_set():
                message_queue.put(f"Stopping posegraph creation for fragment {fragment_id}")
                return
            if t == s + 1:
                message_queue.put(f"Fragment {fragment_id:03d} / {n_fragments - 1:03d} :: RGBD matching between frame : {s} and {t}")
                [success, trans, info] = register_one_rgbd_pair(s, t, color_files, depth_files, intrinsic, with_opencv, config)
                trans_odometry = np.dot(trans, trans_odometry)
                trans_odometry_inv = np.linalg.inv(trans_odometry)
                pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(trans_odometry_inv))
                pose_graph.edges.append(o3d.pipelines.registration.PoseGraphEdge(s - sid, t - sid, trans, info, uncertain=False))
            if s % config['n_keyframes_per_n_frame'] == 0 and t % config['n_keyframes_per_n_frame'] == 0:
                message_queue.put(f"Fragment {fragment_id:03d} / {n_fragments - 1:03d} :: RGBD matching between frame : {s} and {t}")
                [success, trans, info] = register_one_rgbd_pair(s, t, color_files, depth_files, intrinsic, with_opencv, config)
                if success:
                    pose_graph.edges.append(o3d.pipelines.registration.PoseGraphEdge(s - sid, t - sid, trans, info, uncertain=True))
    o3d.io.write_pose_graph(join(path_dataset, config["template_fragment_posegraph"] % fragment_id), pose_graph)

def integrate_rgb_frames_for_fragment(color_files, depth_files, fragment_id, n_fragments, pose_graph_name, intrinsic, config, stop_event, message_queue):
    pose_graph = o3d.io.read_pose_graph(pose_graph_name)
    volume = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=config["tsdf_cubic_size"] / 512.0,
        sdf_trunc=0.04,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
    for i in range(len(pose_graph.nodes)):
        if stop_event.is_set():
            message_queue.put(f"Stopping integration for fragment {fragment_id}")
            return
        i_abs = fragment_id * config['n_frames_per_fragment'] + i
        message_queue.put(f"Fragment {fragment_id:03d} / {n_fragments - 1:03d} :: integrate rgbd frame {i_abs} ({i + 1} of {len(pose_graph.nodes)}).")
        rgbd = read_rgbd_image(color_files[i_abs], depth_files[i_abs], False, config)
        pose = pose_graph.nodes[i].pose
        volume.integrate(rgbd, intrinsic, np.linalg.inv(pose))
    mesh = volume.extract_triangle_mesh()
    mesh.compute_vertex_normals()
    return mesh

def make_pointcloud_for_fragment(path_dataset, color_files, depth_files, fragment_id, n_fragments, intrinsic, config, stop_event, message_queue):
    mesh = integrate_rgb_frames_for_fragment(color_files, depth_files, fragment_id, n_fragments, join(path_dataset, config["template_fragment_posegraph_optimized"] % fragment_id), intrinsic, config, stop_event, message_queue)
    pcd = o3d.geometry.PointCloud()
    pcd.points = mesh.vertices
    pcd.colors = mesh.vertex_colors
    pcd_name = join(path_dataset, config["template_fragment_pointcloud"] % fragment_id)
    o3d.io.write_point_cloud(pcd_name, pcd, format='auto', write_ascii=False, compressed=True)

def process_single_fragment(fragment_id, color_files, depth_files, n_files, n_fragments, config, stop_event, message_queue):
    if stop_event.is_set():
        message_queue.put(f"Skipping fragment {fragment_id} as stop event is set")
        return
    if config["path_intrinsic"]:
        intrinsic = o3d.io.read_pinhole_camera_intrinsic(config["path_intrinsic"])
    else:
        intrinsic = o3d.camera.PinholeCameraIntrinsic(o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault)
    sid = fragment_id * config['n_frames_per_fragment']
    eid = min(sid + config['n_frames_per_fragment'], n_files)

    make_posegraph_for_fragment(config["path_dataset"], sid, eid, color_files, depth_files, fragment_id, n_fragments, intrinsic, with_opencv, config, stop_event, message_queue)
    if stop_event.is_set():
        return
    optimize_posegraph_for_fragment(config["path_dataset"], fragment_id, config)
    if stop_event.is_set():
        return
    make_pointcloud_for_fragment(config["path_dataset"], color_files, depth_files, fragment_id, n_fragments, intrinsic, config, stop_event, message_queue)

def run(config, stop_event, message_queue):
    message_queue.put("making fragments from RGBD sequence.")
    make_clean_folder(join(config["path_dataset"], config["folder_fragment"]))

    [color_files, depth_files] = get_rgbd_file_lists(config["path_dataset"])
    n_files = len(color_files)
    n_fragments = int(math.ceil(float(n_files) / config['n_frames_per_fragment']))

    if config["python_multi_threading"] is True:
        max_workers = min(max(1, multiprocessing.cpu_count() - 1), n_fragments)
        os.environ['OMP_NUM_THREADS'] = '1'
        mp_context = multiprocessing.get_context('spawn')
        with mp_context.Pool(processes=max_workers) as pool:
            args = [(fragment_id, color_files, depth_files, n_files, n_fragments, config, stop_event, message_queue) for fragment_id in range(n_fragments)]
            pool.starmap(process_single_fragment, args)
    else:
        for fragment_id in range(n_fragments):
            process_single_fragment(fragment_id, color_files, depth_files, n_files, n_fragments, config, stop_event, message_queue)
