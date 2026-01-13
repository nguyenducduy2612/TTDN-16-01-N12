# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MeetingRoom(models.Model):
    _name = 'meeting.room'
    _description = 'Quản lý phòng họp'
    _rec_name = 'name'

    name = fields.Char(string='Tên phòng', required=True)
    capacity = fields.Integer(string='Sức chứa', default=10)
    location = fields.Char(string='Vị trí')
    equipment_ids = fields.Many2many('tai_san', string='Thiết bị đi kèm')
    status = fields.Selection([
        ('free', 'Rảnh'),
        ('occupied', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì')
    ], string='Trạng thái', default='free', required=True)
