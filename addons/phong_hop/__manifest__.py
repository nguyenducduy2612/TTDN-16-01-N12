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
        - Trạng thái phòng: Rảnh, Đang sử dụng, Bảo trì
        - Đăng ký lịch sử dụng phòng họp
        - Kiểm tra trùng lịch
    """,
    'author': "User",
    'category': 'Administration',
    'version': '0.1',
    'depends': ['base', 'nhan_su', 'quan_ly_tai_san'],
    'data': [
        'security/ir.model.access.csv',
        'views/meeting_room_views.xml',
        'views/meeting_booking_views.xml',
        'views/menu_views.xml',
    ],
    'application': True,
}
