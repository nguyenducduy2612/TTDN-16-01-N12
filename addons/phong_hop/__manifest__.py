# -*- coding: utf-8 -*-
{
    'name': "Quản lý phòng họp",
    'license': 'LGPL-3',
    'summary': """
        Module quản lý phòng họp, thiết bị và đặt phòng.
    """,
    'description': """
        Module Phòng họp:
        - Quản lý danh sách phòng họp
        - Quản lý sức chứa, vị trí
        - Quản lý thiết bị đi kèm (kết hợp module tài sản)
        - Trạng thái phòng real-time: Rảnh, Đang sử dụng, Bảo trì
        - Đăng ký lịch sử dụng phòng họp với phê duyệt
        - Quản lý danh sách người tham gia cuộc họp
        - Validate sức chứa phòng theo số người tham gia
        - Trạng thái booking: Chờ duyệt, Đã duyệt, Từ chối, Đã hủy, Đang diễn ra
        - Kiểm tra trùng lịch
        - Cập nhật trạng thái phòng theo lịch real-time (computed field)
        - Thống kê sử dụng phòng và khung giờ cao điểm
        - Phân quyền linh hoạt theo user/phòng ban/chức vụ
    """,
    'author': "User",
    'category': 'Administration',
    'version': '0.5',
    'depends': ['base', 'nhan_su', 'quan_ly_tai_san'],
    'data': [
        'security/ir.model.access.csv',
        'views/meeting_booking_views.xml',
        'views/meeting_room_views.xml',
        'views/meeting_statistics_views.xml',
        'views/phong_hop_permission_views.xml',
        'views/menu_views.xml',
    ],
    'application': True,
}
