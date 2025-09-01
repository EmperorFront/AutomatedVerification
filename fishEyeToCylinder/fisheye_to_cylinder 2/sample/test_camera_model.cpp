//
// Created by chenghe on 8/3/22.
//
#include <iostream>
#include "camera_model_interface.h"
int main()
{
    haomo_cam::CameraParameters fisheye_camera_params;
    fisheye_camera_params.fx = 469.435394;
    fisheye_camera_params.fy = 469.852112;
    fisheye_camera_params.cx = 967.581665;
    fisheye_camera_params.cy = 538.946777;
    fisheye_camera_params.distortion_params =
            std::vector<float>{0.0640982, -0.0122619588, 0.00125413574, -0.000395158};
    fisheye_camera_params.camera_width = 1920;
    fisheye_camera_params.camera_height = 1080;
    fisheye_camera_params.q_body_cam =
            std::array<std::double_t, 4>{-0.0140862009, -0.0182368234, 0.821001172, -0.570461273};
    fisheye_camera_params.t_body_cam = std::array<std::double_t, 3>{2.14122534, -0.929897547, 0.640055537};

    haomo_cam::CylinderParameters cylinder_parameters;
    cylinder_parameters.camera_width  = 1024;
    cylinder_parameters.camera_height = 768;
    cylinder_parameters.horizontal_fov_deg = 180;
    cylinder_parameters.vertical_fov_upper = 32.0646;
    cylinder_parameters.vertical_fov_lower = 59.9672;
    cylinder_parameters.automatic_camera_height = false;

    auto fisheye_cam_ptr = haomo_cam::Camera::create(fisheye_camera_params);

    auto cylinder_cam_ptr = haomo_cam::Camera::create_cylinder_camera(fisheye_cam_ptr, cylinder_parameters);

    auto dewarper_ptr = haomo_cam::Dewarper::create(fisheye_cam_ptr, cylinder_cam_ptr);

    cv::Mat image = cv::imread("../../resource/V71C007/real/right_fisheye_camera_record_2022-08-16_19-55-52.475.jpg");

    auto dst = dewarper_ptr->dewarp(image);

    cv::namedWindow("dst", cv::WINDOW_NORMAL);
    cv::imshow("dst", dst);
    cv::waitKey(0);

    return 0;
}