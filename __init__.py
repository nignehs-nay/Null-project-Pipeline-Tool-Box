import bpy
import os
import math
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import EnumProperty, FloatProperty, BoolProperty, StringProperty, IntProperty
from mathutils import Matrix, Vector, Euler

#---------------------------------------------------------------
# 插件信息定义
#---------------------------------------------------------------
bl_info = {
    "name": "Null Project Pipeline Toolbox",
    "author": "Null",
    "description": "Pipeline tools for Null Project workflow",
    "blender": (4, 2, 0),
    "version": (0, 0, 3),  
    "location": "3D View > Sidebar > Pipeline Tools",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
}

#---------------------------------------------------------------
# 工具类定义 - 操作符(Operator)
#---------------------------------------------------------------
#   添加Metarig骨骼
class PIPELINE_OT_Addrigfy(Operator):
    """添加Metarig骨骼操作符"""
    bl_idname = "pipeline.add_metarig"
    bl_label = "添加rigfy骨骼"
    bl_options = {'REGISTER', 'UNDO'}   #   支持撤销

    #   选择骨骼类型
    rig_type: EnumProperty(
        name="骨骼类型",
        items=[
            ('METARIG', "Human Metarig", "标准人体骨骼"),
            ('BASIC', "Basic Human", "简化人体骨骼")
        ],
        default='METARIG'
    )
    
    def execute(self, context):
        if self.rig_type == 'METARIG':
            bpy.ops.object.armature_human_metarig_add()
        else:
            bpy.ops.object.armature_basic_human_metarig_add()
        return {'FINISHED'}

class PIPELINE_OT_GenerateRig(Operator):
    """生成Rigify绑定操作符"""
    bl_idname = "pipeline.generate_rig"
    bl_label = "生成绑定"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.pose.rigify_generate()
            self.report({'INFO'}, "Rigify绑定已生成")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "请先选择骨骼对象")
            return {'CANCELLED'}

class PIPELINE_OT_Playblast(Operator):
    """创建预览动画操作符"""
    bl_idname = "pipeline.playblast"
    bl_label = "预览动画"
    bl_options = {'REGISTER'}
    
    quality: EnumProperty(
        name="质量",
        items=[
            ('LOW', "低质量", "快速预览"),
            ('MEDIUM', "中等质量", "平衡速度和质量")
        ],
        default='MEDIUM'
    )
    
    format: EnumProperty(
        name="格式",
        items=[
            ('QUICKTIME', "QuickTime", "MOV格式"),
            ('MP4', "MP4/H.264", "MP4格式,H.264编码"),
        ],
        default='QUICKTIME'
    )
    
    show_file: BoolProperty(
        name="完成后显示文件",
        default=True
    )
    
    use_default_path: BoolProperty(
        name="使用默认路径",
        default=True,
        description="使用默认输出路径而不弹出对话框"
    )
    
    def execute(self, context):
        # 保存原始设置
        original_engine = context.scene.render.engine
        original_color_type = context.scene.display.shading.color_type
        original_file_format = context.scene.render.image_settings.file_format
        original_ffmpeg_format = context.scene.render.ffmpeg.format
        original_ffmpeg_preset = context.scene.render.ffmpeg.ffmpeg_preset
        original_crf = context.scene.render.ffmpeg.constant_rate_factor
        original_filepath = context.scene.render.filepath
        
        try:
            # 设置渲染引擎
            context.scene.render.engine = 'BLENDER_WORKBENCH'
            context.scene.display.shading.color_type = 'RANDOM'
            
            # 设置输出路径
            if self.use_default_path:
                # 使用默认路径
                blend_filepath = context.blend_data.filepath
                if blend_filepath:
                    blend_dir = os.path.dirname(blend_filepath)
                    filepath = os.path.join(blend_dir, "playblast")
                else:
                    filepath = os.path.join(os.path.expanduser("~"), "playblast")
            else:
                # 使用用户设置的路径
                filepath = context.scene.pipeline_playblast_filepath
            
            # 设置输出格式
            context.scene.render.image_settings.file_format = 'FFMPEG'
            
            # 添加文件扩展名
            if self.format == 'QUICKTIME':
                context.scene.render.ffmpeg.format = 'QUICKTIME'
                filepath += ".mov"            
            elif self.format == 'MP4':
                context.scene.render.ffmpeg.format = 'MPEG4'
                filepath += ".mp4"
            
            context.scene.render.filepath = filepath
            
            # 根据质量设置
            if self.quality == 'LOW':
                context.scene.render.ffmpeg.constant_rate_factor = 'LOW'
                context.scene.render.ffmpeg.ffmpeg_preset = 'REALTIME'
            else:  # MEDIUM
                context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
                context.scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
            
            # 确保输出目录存在
            output_dir = os.path.dirname(filepath)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 渲染动画
            bpy.ops.render.render(animation=True, use_viewport=True)
            
            # 播放动画
            bpy.ops.render.play_rendered_anim()
            
            # 显示文件
            if self.show_file:
                if os.path.exists(output_dir):
                    bpy.ops.wm.path_open(filepath=output_dir)
            
            # 保存渲染文件路径
            context.scene.pipeline_last_playblast = filepath
        finally:
            # 恢复原始设置
            context.scene.render.engine = original_engine
            context.scene.display.shading.color_type = original_color_type
            context.scene.render.image_settings.file_format = original_file_format
            context.scene.render.ffmpeg.format = original_ffmpeg_format
            context.scene.render.ffmpeg.ffmpeg_preset = original_ffmpeg_preset
            context.scene.render.ffmpeg.constant_rate_factor = original_crf
            context.scene.render.filepath = original_filepath
        
        return {'FINISHED'}

class PIPELINE_OT_DeletePlayblast(Operator):
    """删除预览动画操作符"""
    bl_idname = "pipeline.delete_playblast"
    bl_label = "删除预览动画"
    
    def execute(self, context):
        filepath = context.scene.pipeline_last_playblast
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.report({'INFO'}, f"已删除预览文件: {filepath}")
                context.scene.pipeline_last_playblast = ""
            except Exception as e:
                self.report({'ERROR'}, f"删除失败: {str(e)}")
        else:
            self.report({'WARNING'}, "没有可删除的预览文件")
        return {'FINISHED'}

class PIPELINE_OT_PlayblastPathSelect(Operator):
    """选择预览动画输出路径操作符"""
    bl_idname = "pipeline.playblast_path_select"
    bl_label = "选择预览动画输出路径"
    
    filepath: StringProperty(
        subtype='FILE_PATH',
        description="选择预览动画的输出路径"
    )
    
    def execute(self, context):
        context.scene.pipeline_playblast_filepath = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if blend_filepath:
                blend_dir = os.path.dirname(blend_filepath)
                self.filepath = os.path.join(blend_dir, "playblast")
            else:
                self.filepath = os.path.join(os.path.expanduser("~"), "playblast")
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class PIPELINE_OT_AddEmpty(Operator):
    """添加空物体操作符"""
    bl_idname = "pipeline.add_empty"
    bl_label = "添加空物体"
    bl_options = {'REGISTER', 'UNDO'}
    
    empty_type: EnumProperty(
        name="类型",
        items=[
            ('PLAIN_AXES', "坐标轴", "简单坐标轴"),
            ('ARROWS', "箭头", "箭头指示器"),
            ('CUBE', "立方体", "立方体形状"),
            ('CIRCLE', "圆形", "圆形形状")
        ],
        default='PLAIN_AXES'
    )
    
    size: FloatProperty(
        name="大小",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    def execute(self, context):
        bpy.ops.object.empty_add(
            type=self.empty_type,
            align='WORLD',
            location=context.scene.cursor.location,
            scale=(self.size, self.size, self.size)
        )
        return {'FINISHED'}

class PIPELINE_OT_SetActiveCamera(Operator):
    """设置活动摄像机操作符"""
    bl_idname = "pipeline.set_active_camera"
    bl_label = "设为活动摄像机"
    
    def execute(self, context):
        if context.active_object and context.active_object.type == 'CAMERA':
            context.scene.camera = context.active_object
            self.report({'INFO'}, "活动摄像机已设置")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "请先选择摄像机")
            return {'CANCELLED'}

class PIPELINE_OT_KeyframeCharacter(Operator):
    """插入角色关键帧操作符"""
    bl_idname = "pipeline.keyframe_character"
    bl_label = "插入角色关键帧"
    
    key_type: EnumProperty(
        name="关键帧类型",
        items=[
            ('WHOLE', "完整角色", "所有骨骼"),
            ('SELECTED', "选中骨骼", "仅选中的骨骼")
        ],
        default='WHOLE'
    )
    
    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请在姿态模式下操作")
            return {'CANCELLED'}
        
        if self.key_type == 'WHOLE':
            bpy.ops.anim.keyframe_insert_by_name(type="WholeCharacter")
        else:
            bpy.ops.anim.keyframe_insert_by_name(type="WholeCharacterSelected")
        
        return {'FINISHED'}

class PIPELINE_OT_SwitchMode(Operator):
    """切换模式操作符"""
    bl_idname = "pipeline.switch_mode"
    bl_label = "切换模式"
    
    mode: EnumProperty(
        name="模式",
        items=[
            ('OBJECT', "物体模式", ""),
            ('POSE', "姿态模式", "")
        ],
        default='OBJECT'
    )
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode=self.mode)
        return {'FINISHED'}

class PIPELINE_OT_InstallExtensions(Operator):
    """安装扩展操作符"""
    bl_idname = "pipeline.install_extensions"
    bl_label = "安装扩展"
    
    def execute(self, context):
        install_commands = [
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='camera_shakify')",
            # ... 其他安装命令 ...
        ]
        
        for cmd in install_commands:
            try:
                exec(cmd)
                self.report({'INFO'}, f"已执行命令: {cmd}")
            except Exception as e:
                self.report({'ERROR'}, f"执行命令失败: {cmd} - {str(e)}")
        
        return {'FINISHED'}

class PIPELINE_OT_UpdateExtensions(Operator):
    """更新扩展操作符"""
    bl_idname = "pipeline.update_extensions"
    bl_label = "更新扩展"
    
    def execute(self, context):
        try:
            bpy.ops.extensions.package_upgrade_all()
            self.report({'INFO'}, "所有扩展已更新")
        except Exception as e:
            self.report({'ERROR'}, f"更新扩展失败: {str(e)}")
        return {'FINISHED'}

class PIPELINE_OT_FilterIKFKInDopesheet(Operator):
    """在摄影表中过滤IK_FK属性操作符"""
    bl_idname = "pipeline.filter_ikfk_in_dopesheet"
    bl_label = "在摄影表中过滤IK_FK"
    
    def execute(self, context):
        # 创建新窗口
        bpy.ops.wm.window_new()
        
        # 获取新窗口的区域
        area = None
        for a in context.window_manager.windows[-1].screen.areas:
            if a.type == 'DOPESHEET_EDITOR':
                area = a
                break
        
        if not area:
            # 如果没有找到摄影表编辑器，则创建一个
            area = context.window_manager.windows[-1].screen.areas[0]
            area.ui_type = 'DOPESHEET'
        
        # 设置过滤条件
        space_data = area.spaces.active
        space_data.dopesheet.filter_text = "IK_FK"
        space_data.dopesheet.show_only_selected = False
        
        return {'FINISHED'}

class PIPELINE_OT_IKFKSwitch(Operator):
    """IK/FK切换操作符"""
    bl_idname = "pipeline.ikfk_switch"
    bl_label = "IK/FK切换"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 检查当前模式
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请在姿态模式下操作")
            return {'CANCELLED'}
        
        # 获取当前选中的骨骼对象
        rig = context.active_object
        if not rig or rig.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨骼对象")
            return {'CANCELLED'}
        
        # 获取选中的骨骼
        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "请先选择骨骼")
            return {'CANCELLED'}
        
        # 尝试识别肢体类型
        limb_type = None
        for bone in selected_bones:
            bone_name = bone.name.lower()
            
            # 检查左臂骨骼
            if ("hand_ik.l" in bone_name or "forearm_fk.l" in bone_name or 
                "upper_arm_fk.l" in bone_name or "hand_fk.l" in bone_name):
                limb_type = "ARM_L"
                break
            
            # 检查右臂骨骼
            elif ("hand_ik.r" in bone_name or "hand_fk.r" in bone_name or 
                  "forearm_fk.r" in bone_name or "upper_arm_fk.r" in bone_name):
                limb_type = "ARM_R"
                break
            
            # 检查左腿骨骼
            elif ("foot_ik.l" in bone_name or "foot_fk.l" in bone_name or 
                  "shin_fk.l" in bone_name or "thigh_fk.l" in bone_name or 
                  "thigh_ik.l" in bone_name):
                limb_type = "LEG_L"
                break
            
            # 检查右腿骨骼
            elif ("foot_ik.r" in bone_name or "foot_fk.r" in bone_name or 
                  "shin_fk.r" in bone_name or "thigh_fk.r" in bone_name or 
                  "thigh_ik.r" in bone_name):
                limb_type = "LEG_R"
                break
            
            # 检查手部骨骼
            elif ("hand_ik" in bone_name or "hand_fk" in bone_name):
                limb_type = "HAND"
                break
        
        # 如果无法识别肢体类型，报告错误
        if not limb_type:
            self.report({'ERROR'}, "无法识别肢体类型,请选择手臂、腿部或手部骨骼")
            return {'CANCELLED'}
        
        # 肢体映射到属性骨骼名称
        bone_map = {
            'ARM_L': "upper_arm_parent.L",
            'ARM_R': "upper_arm_parent.R",
            'LEG_L': "thigh_parent.L",
            'LEG_R': "thigh_parent.R",
            'HAND': "hand_ik"  # 手部使用不同的属性骨骼
        }
        
        # 获取属性骨骼名称
        prop_bone_name = bone_map[limb_type]
        
        # 检查属性骨骼是否存在
        if prop_bone_name not in rig.pose.bones:
            self.report({'ERROR'}, f"骨骼 {prop_bone_name} 不存在")
            return {'CANCELLED'}
        
        # 获取属性骨骼
        prop_bone = rig.pose.bones[prop_bone_name]
        
        # 获取当前IK/FK状态
        current_value = prop_bone.get("IK_FK", 0.0)
        
        # 自动切换状态
        new_value = 1.0 if current_value == 0.0 else 0.0
        
        # 设置新值
        prop_bone["IK_FK"] = new_value
        
        # 根据切换方向执行相应的操作
        if new_value == 1.0:  # IK切换到FK
            if limb_type in ['ARM_L', 'ARM_R']:
                # 左臂或右臂
                side = 'L' if limb_type == 'ARM_L' else 'R'
                
                # 获取骨骼
                upper_arm_ik = rig.pose.bones.get(f"upper_arm_ik.{side}")
                forearm_ik = rig.pose.bones.get(f"forearm_ik.{side}")
                hand_ik = rig.pose.bones.get(f"hand_ik.{side}")
                
                upper_arm_fk = rig.pose.bones.get(f"upper_arm_fk.{side}")
                forearm_fk = rig.pose.bones.get(f"forearm_fk.{side}")
                hand_fk = rig.pose.bones.get(f"hand_fk.{side}")
                
                # 执行IK到FK的切换操作
                if upper_arm_ik and forearm_ik and hand_ik and upper_arm_fk and forearm_fk and hand_fk:
                    # 确保FK骨骼使用四元数旋转
                    for bone in [upper_arm_fk, forearm_fk, hand_fk]:
                        if bone.rotation_mode != 'QUATERNION':
                            bone.rotation_mode = 'QUATERNION'
                    
                    # 复制位置和旋转
                    upper_arm_fk.location = upper_arm_ik.location.copy()
                    upper_arm_fk.rotation_quaternion = upper_arm_ik.rotation_quaternion.copy()
                    
                    forearm_fk.location = forearm_ik.location.copy()
                    forearm_fk.rotation_quaternion = forearm_ik.rotation_quaternion.copy()
                    
                    hand_fk.location = hand_ik.location.copy()
                    hand_fk.rotation_quaternion = hand_ik.rotation_quaternion.copy()
                    
                    # 更新视图
                    context.view_layer.update()
            elif limb_type in ['LEG_L', 'LEG_R']:
                # 左腿或右腿
                side = 'L' if limb_type == 'LEG_L' else 'R'
                
                # 获取骨骼
                thigh_ik = rig.pose.bones.get(f"thigh_ik.{side}")
                shin_ik = rig.pose.bones.get(f"shin_ik.{side}")
                foot_ik = rig.pose.bones.get(f"foot_ik.{side}")
                toe_ik = rig.pose.bones.get(f"toe_ik.{side}")
                
                thigh_fk = rig.pose.bones.get(f"thigh_fk.{side}")
                shin_fk = rig.pose.bones.get(f"shin_fk.{side}")
                foot_fk = rig.pose.bones.get(f"foot_fk.{side}")
                toe_fk = rig.pose.bones.get(f"toe_fk.{side}")
                
                # 执行IK到FK的切换操作
                if thigh_ik and shin_ik and foot_ik and toe_ik and thigh_fk and shin_fk and foot_fk and toe_fk:
                    # 确保FK骨骼使用四元数旋转
                    for bone in [thigh_fk, shin_fk, foot_fk, toe_fk]:
                        if bone.rotation_mode != 'QUATERNION':
                            bone.rotation_mode = 'QUATERNION'
                    
                    # 复制位置和旋转
                    thigh_fk.location = thigh_ik.location.copy()
                    thigh_fk.rotation_quaternion = thigh_ik.rotation_quaternion.copy()
                    
                    shin_fk.location = shin_ik.location.copy()
                    shin_fk.rotation_quaternion = shin_ik.rotation_quaternion.copy()
                    
                    foot_fk.location = foot_ik.location.copy()
                    foot_fk.rotation_quaternion = foot_ik.rotation_quaternion.copy()
                    
                    toe_fk.location = toe_ik.location.copy()
                    toe_fk.rotation_quaternion = toe_ik.rotation_quaternion.copy()
                    
                    # 更新视图
                    context.view_layer.update()
            elif limb_type == 'HAND':
                # 手部
                hand_ik = rig.pose.bones.get("hand_ik")
                hand_fk = rig.pose.bones.get("hand_fk")
                
                # 执行IK到FK的切换操作
                if hand_ik and hand_fk:
                    # 确保FK骨骼使用四元数旋转
                    if hand_fk.rotation_mode != 'QUATERNION':
                        hand_fk.rotation_mode = 'QUATERNION'
                    
                    # 复制位置和旋转
                    hand_fk.location = hand_ik.location.copy()
                    hand_fk.rotation_quaternion = hand_ik.rotation_quaternion.copy()
                    
                    # 更新视图
                    context.view_layer.update()
        else:  # FK切换到IK
            if limb_type in ['ARM_L', 'ARM_R']:
                # 左臂或右臂
                side = 'L' if limb_type == 'ARM_L' else 'R'
                
                # 获取骨骼
                upper_arm_fk = rig.pose.bones.get(f"upper_arm_fk.{side}")
                forearm_fk = rig.pose.bones.get(f"forearm_fk.{side}")
                hand_fk = rig.pose.bones.get(f"hand_fk.{side}")
                
                upper_arm_ik = rig.pose.bones.get(f"upper_arm_ik.{side}")
                forearm_ik = rig.pose.bones.get(f"forearm_ik.{side}")
                hand_ik = rig.pose.bones.get(f"hand_ik.{side}")
                pole_target = rig.pose.bones.get(f"upper_arm_ik_target.{side}")
                
                # 执行FK到IK的切换操作
                if upper_arm_fk and forearm_fk and hand_fk and upper_arm_ik and forearm_ik and hand_ik and pole_target:
                    # 复制位置和旋转
                    upper_arm_ik.location = upper_arm_fk.location.copy()
                    upper_arm_ik.rotation_quaternion = upper_arm_fk.rotation_quaternion.copy()
                    
                    forearm_ik.location = forearm_fk.location.copy()
                    forearm_ik.rotation_quaternion = forearm_fk.rotation_quaternion.copy()
                    
                    hand_ik.location = hand_fk.location.copy()
                    hand_ik.rotation_quaternion = hand_fk.rotation_quaternion.copy()
                    
                    # 匹配极目标
                    match_pole_target(
                        context.view_layer,
                        upper_arm_ik,
                        forearm_ik,
                        pole_target,
                        upper_arm_fk.matrix,
                        1.0  # 长度
                    )
                    
                    # 更新视图
                    context.view_layer.update()
            elif limb_type in ['LEG_L', 'LEG_R']:
                # 左腿或右腿
                side = 'L' if limb_type == 'LEG_L' else 'R'
                
                # 获取骨骼
                thigh_fk = rig.pose.bones.get(f"thigh_fk.{side}")
                shin_fk = rig.pose.bones.get(f"shin_fk.{side}")
                foot_fk = rig.pose.bones.get(f"foot_fk.{side}")
                toe_fk = rig.pose.bones.get(f"toe_fk.{side}")
                
                thigh_ik = rig.pose.bones.get(f"thigh_ik.{side}")
                shin_ik = rig.pose.bones.get(f"shin_ik.{side}")
                foot_ik = rig.pose.bones.get(f"foot_ik.{side}")
                toe_ik = rig.pose.bones.get(f"toe_ik.{side}")
                pole_target = rig.pose.bones.get(f"thigh_ik_target.{side}")
                
                # 执行FK到IK的切换操作
                if thigh_fk and shin_fk and foot_fk and toe_fk and thigh_ik and shin_ik and foot_ik and toe_ik and pole_target:
                    # 复制位置和旋转
                    thigh_ik.location = thigh_fk.location.copy()
                    thigh_ik.rotation_quaternion = thigh_fk.rotation_quaternion.copy()
                    
                    shin_ik.location = shin_fk.location.copy()
                    shin_ik.rotation_quaternion = shin_fk.rotation_quaternion.copy()
                    
                    foot_ik.location = foot_fk.location.copy()
                    foot_ik.rotation_quaternion = foot_fk.rotation_quaternion.copy()
                    
                    toe_ik.location = toe_fk.location.copy()
                    toe_ik.rotation_quaternion = toe_fk.rotation_quaternion.copy()
                    
                    # 匹配极目标
                    match_pole_target(
                        context.view_layer,
                        thigh_ik,
                        shin_ik,
                        pole_target,
                        thigh_fk.matrix,
                        1.0  # 长度
                    )
                    
                    # 更新视图
                    context.view_layer.update()
            elif limb_type == 'HAND':
                # 手部
                hand_fk = rig.pose.bones.get("hand_fk")
                hand_ik = rig.pose.bones.get("hand_ik")
                
                # 执行FK到IK的切换操作
                if hand_fk and hand_ik:
                    # 复制位置和旋转
                    hand_ik.location = hand_fk.location.copy()
                    hand_ik.rotation_quaternion = hand_fk.rotation_quaternion.copy()
                    
                    # 更新视图
                    context.view_layer.update()
        
        # 报告结果
        mode = "FK" if new_value == 1.0 else "IK"
        self.report({'INFO'}, f"已切换 {limb_type} 到 {mode} 模式,骨骼已正确跟随")
        
        return {'FINISHED'}

class PIPELINE_OT_ExecuteInstruction(Operator):
    """执行指令操作符"""
    bl_idname = "pipeline.execute_instruction"
    bl_label = "执行指令"
    bl_options = {'REGISTER', 'UNDO'}
    
    instruction_type: EnumProperty(
        name="指令类型",
        items=[
            ('ARM_IK_TO_FK', "手臂IK切换到FK", "执行手臂IK切换到FK的指令"),
            ('ARM_FK_TO_IK', "手臂FK切换到IK", "执行手臂FK切换到IK的指令"),
            ('LEG_IK_TO_FK', "腿部IK切换到FK", "执行腿部IK切换到FK的指令"),
            ('LEG_FK_TO_IK', "腿部FK切换到IK", "执行腿部FK切换到IK的指令")
        ],
        default='ARM_IK_TO_FK'
    )
    
    def execute(self, context):
        # 获取指令
        if self.instruction_type == 'ARM_IK_TO_FK':
            instruction = context.scene.pipeline_arm_ik_to_fk_instruction
        elif self.instruction_type == 'ARM_FK_TO_IK':
            instruction = context.scene.pipeline_arm_fk_to_ik_instruction
        elif self.instruction_type == 'LEG_IK_TO_FK':
            instruction = context.scene.pipeline_leg_ik_to_fk_instruction
        else:  # LEG_FK_TO_IK
            instruction = context.scene.pipeline_leg_fk_to_ik_instruction
        
        # 执行指令
        if instruction:
            try:
                exec(instruction)
                self.report({'INFO'}, f"已执行指令: {instruction}")
            except Exception as e:
                self.report({'ERROR'}, f"执行指令失败: {str(e)}")
        else:
            self.report({'WARNING'}, "指令为空")
        
        return {'FINISHED'}

# 辅助函数
def perpendicular_vector(v):
    """返回一个垂直于给定向量的向量"""
    if v.length < 1e-6:
        return Vector((1, 0, 0))
    
    # 尝试使用(1, 0, 0)叉乘
    cross = v.cross(Vector((1, 0, 0)))
    if cross.length > 1e-6:
        return cross.normalized()
    
    # 如果叉乘结果太小，尝试使用(0, 1, 0)
    cross = v.cross(Vector((0, 1, 0)))
    return cross.normalized()

def rotation_difference(mat1, mat2):
    """计算两个矩阵之间的旋转差异"""
    q1 = mat1.to_quaternion()
    q2 = mat2.to_quaternion()
    return q1.rotation_difference(q2).angle

def match_pole_target(view_layer, ik_first, ik_last, pole, match_bone_matrix, length):
    """匹配极目标位置"""
    a = ik_first.matrix.to_translation()
    b = ik_last.matrix.to_translation() + ik_last.vector
    ikv = b - a
    pv = perpendicular_vector(ikv).normalized() * length

    def set_pole(pvi):
        """设置极目标位置"""
        pole_loc = a + (ikv/2) + pvi
        pole.location = pole_loc
        view_layer.update()

    set_pole(pv)
    angle = rotation_difference(ik_first.matrix, match_bone_matrix)

    pv1 = Matrix.Rotation(angle, 4, ikv) @ pv
    set_pole(pv1)
    ang1 = rotation_difference(ik_first.matrix, match_bone_matrix)

    pv2 = Matrix.Rotation(-angle, 4, ikv) @ pv
    set_pole(pv2)
    ang2 = rotation_difference(ik_first.matrix, match_bone_matrix)

    if ang1 < ang2:
        set_pole(pv1)

#---------------------------------------------------------------
# 面板类定义 - 用户界面(Panel)
#---------------------------------------------------------------

class PIPELINE_PT_MainPanel(Panel):
    """主面板类"""
    bl_label = "Null Project Pipeline ToolBox"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Pipeline ToolBox"
    
    def draw(self, context):
        layout = self.layout
        
        # 功能分区选择
        box = layout.box()
        row = box.row()
        row.label(text="功能分区")
        row.prop(context.scene, "pipeline_active_section", expand=True)
        
        # 根据选择的分区显示不同的工具
        if context.scene.pipeline_active_section == 'DEFAULT':
            self.draw_default_section(layout, context)
        elif context.scene.pipeline_active_section == 'ANIMATION':
            self.draw_animation_section(layout, context)
        elif context.scene.pipeline_active_section == 'RIGGING':
            self.draw_rigging_section(layout, context)
        else:  # SETTINGS   #
            self.draw_settings_section(layout, context)

    def draw_default_section(self, layout, context):            
        # 模式切换
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_mode_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_mode_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="模式切换")
        
        if context.scene.pipeline_show_mode_tools:
            row = box.row()
            row.operator("pipeline.switch_mode", text="物体模式").mode = 'OBJECT'
    
        # 空物体工具
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_empty_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_empty_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="空物体工具")
        
        if context.scene.pipeline_show_empty_tools:
            row = box.row()
            row.prop(context.scene, "pipeline_empty_type", text="类型")
            row.prop(context.scene, "pipeline_empty_size", text="大小")
            box.operator("pipeline.add_empty", text="添加空物体")
        
        # 摄像机工具
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_camera_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_camera_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="摄像机工具")
        
        if context.scene.pipeline_show_camera_tools:
            box.operator("pipeline.set_active_camera", text="设为活动摄像机")
    
    def draw_animation_section(self, layout, context):
        # 模式切换
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_mode_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_mode_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="模式切换")
        
        if context.scene.pipeline_show_mode_tools:
            row = box.row()
            row.operator("pipeline.switch_mode", text="物体模式").mode = 'OBJECT'
            row.operator("pipeline.switch_mode", text="姿态模式").mode = 'POSE'
        
        # 关键帧工具
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_keyframe_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_keyframe_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="关键帧工具")
        
        if context.scene.pipeline_show_keyframe_tools:
            row = box.row()
            row.operator("pipeline.keyframe_character", text="完整角色关键帧").key_type = 'WHOLE'
            row.operator("pipeline.keyframe_character", text="选中骨骼关键帧").key_type = 'SELECTED'
        
        # IK/FK切换(rigfy)
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_ikfk_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_ikfk_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="Rigfy骨骼IK/FK工具")
        
        if context.scene.pipeline_show_ikfk_tools:
            box.operator("pipeline.ikfk_switch", text="切换IK/FK")
            box.operator("pipeline.filter_ikfk_in_dopesheet", text="在摄影表中过滤IK_FK")
            
            # IK/FK指令工具
            row = box.row()
            row.prop(context.scene, "pipeline_show_ikfk_instructions", 
                     icon='TRIA_DOWN' if context.scene.pipeline_show_ikfk_instructions else 'TRIA_RIGHT',
                     icon_only=True, emboss=False
            )
            row.label(text="IK/FK指令工具")
            
            if context.scene.pipeline_show_ikfk_instructions:
                # 预设指令
                box.label(text="预设指令（直接执行）", icon='SCRIPT')
                
                # 手臂IK切换到FK指令
                row = box.row()
                row.prop(context.scene, "pipeline_arm_ik_to_fk_instruction", text="手臂IK->FK")
                op = row.operator("pipeline.execute_instruction", text="IK->FK", icon='PLAY')
                op.instruction_type = 'ARM_IK_TO_FK'
                
                # 手臂FK切换到IK指令
                row = box.row()
                row.prop(context.scene, "pipeline_arm_fk_to_ik_instruction", text="手臂FK->IK")
                op = row.operator("pipeline.execute_instruction", text="FK->IK", icon='PLAY')
                op.instruction_type = 'ARM_FK_TO_IK'
                
                # 腿部IK切换到FK指令
                row = box.row()
                row.prop(context.scene, "pipeline_leg_ik_to_fk_instruction", text="腿部IK->FK")
                op = row.operator("pipeline.execute_instruction", text="IK->FK", icon='PLAY')
                op.instruction_type = 'LEG_IK_TO_FK'
                
                # 腿部FK切换到IK指令
                row = box.row()
                row.prop(context.scene, "pipeline_leg_fk_to_ik_instruction", text="腿部FK->IK")
                op = row.operator("pipeline.execute_instruction", text="FK->IK", icon='PLAY')
                op.instruction_type = 'LEG_FK_TO_IK'
                
                # 提示
                box.label(text="指令格式: bpy.ops.pose.rigify_...", icon='INFO')
                box.label(text="例如: bpy.ops.pose.rigify_limb_ik2fk_unu81nec92ae7d86(...)")
        
        # 预览工具
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_playblast_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_playblast_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="预览动画")
        
        if context.scene.pipeline_show_playblast_tools:
            # 质量设置
            row = box.row()
            row.prop(context.scene, "pipeline_playblast_quality", text="质量")
            
            # 格式设置
            row = box.row()
            row.prop(context.scene, "pipeline_playblast_format", text="格式")
            
            # 文件选项
            row = box.row()
            row.prop(context.scene, "pipeline_playblast_show_file", text="完成后显示文件")
            
            # 使用默认路径选项
            row = box.row()
            row.prop(context.scene, "pipeline_playblast_use_default_path", text="使用默认路径")

            # 渲染按钮
            row = box.row()
            op = row.operator("pipeline.playblast", text="创建预览动画")
            op.quality = context.scene.pipeline_playblast_quality
            op.format = context.scene.pipeline_playblast_format
            op.show_file = context.scene.pipeline_playblast_show_file
            op.use_default_path = context.scene.pipeline_playblast_use_default_path

            # 路径选择按钮
            if not context.scene.pipeline_playblast_use_default_path:
                row = box.row()
                row.operator("pipeline.playblast_path_select", text="选择输出路径")
                if context.scene.pipeline_playblast_filepath:
                    row = box.row()
                    row.label(text=f"路径: {context.scene.pipeline_playblast_filepath}")
           
            # 删除按钮
            if context.scene.pipeline_last_playblast:
                row = box.row()
                row.operator("pipeline.delete_playblast", text="删除预览动画", icon='TRASH')
    
    def draw_rigging_section(self, layout, context):
        # 模式切换子分区
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_mode_tools_rigging", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_mode_tools_rigging else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="模式切换")
        
        if context.scene.pipeline_show_mode_tools_rigging:
            # 模式切换按钮
            row = box.row()
            row.operator("pipeline.switch_mode", text="物体模式").mode = 'OBJECT'
            row.operator("pipeline.switch_mode", text="姿态模式").mode = 'POSE'

        # 骨骼工具子分区
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_rig_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_rig_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False  
        )
        row.label(text="骨骼工具")
        if context.scene.pipeline_show_rig_tools:
            # 添加骨骼按钮
            row = box.row()
            row.operator("pipeline.add_metarig", text="Human Metarig").rig_type = 'METARIG'
            row.operator("pipeline.add_metarig", text="Basic Human").rig_type = 'BASIC'
            
            # 生成绑定按钮
            row = box.row()
            row.operator("pipeline.generate_rig", text="生成绑定")
    
    def draw_settings_section(self, layout, context):
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_extension_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_extension_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="安装我需要使用的扩展")
        
        if context.scene.pipeline_show_extension_tools:
            row = box.row()
            row.operator("pipeline.update_extensions", text="在线更新已安装的扩展")
            row.operator("pipeline.install_extensions", text="在线安装需要的扩展")

            # 提示
            box.label(text="提示: 不建议使用安装扩展的功能", icon='INFO')
            box.label(text="提示: 下载安装扩展的时候会需要很长时间", icon='INFO')
            box.label(text="提示: 在安装时不要乱动blender,请保证有充足的时间情况下在下载和安装扩展.", icon='INFO')
            box.label(text="提示: 请保证有充足的时间情况下在下载和安装扩展.", icon='INFO')
            box.label(text="提示: 更新扩展可能需要重新启动Blender", icon='INFO')

#---------------------------------------------------------------
# 属性注册 - 自定义场景属性
#---------------------------------------------------------------

def register_properties():
    # 预览动画属性
    bpy.types.Scene.pipeline_playblast_quality = EnumProperty(
        name="预览质量",
        items=[
            ('LOW', "低质量", "快速预览"),
            ('MEDIUM', "中等质量", "平衡速度和质量")
        ],
        default='LOW'
    )
    
    bpy.types.Scene.pipeline_playblast_format = EnumProperty(
        name="预览格式",
        items=[
            ('QUICKTIME', "QuickTime", "MOV格式"),
            ('MP4', "MP4/H.264", "MP4格式,H.264编码"),
        ],
        default='QUICKTIME'
    )
    
    bpy.types.Scene.pipeline_playblast_show_file = BoolProperty(
        name="完成后显示文件",
        default=True
    )
    
    bpy.types.Scene.pipeline_playblast_use_default_path = BoolProperty(
        name="使用默认路径",
        default=True,
        description="使用默认输出路径而不弹出对话框"
    )
    
    bpy.types.Scene.pipeline_playblast_filepath = StringProperty(
        name="输出路径",
        subtype='FILE_PATH',
        default="",
        description="预览动画的输出路径"
    )
    
    bpy.types.Scene.pipeline_last_playblast = StringProperty(
        name="最后预览路径",
        default="",
        description="最后创建的预览动画路径"
    )
    
    # 空物体属性
    bpy.types.Scene.pipeline_empty_type = EnumProperty(
        name="空物体类型",
        items=[
            ('PLAIN_AXES', "坐标轴", "简单坐标轴"),
            ('ARROWS', "箭头", "箭头指示器"),
            ('CUBE', "立方体", "立方体形状"),
            ('CIRCLE', "圆形", "圆形形状")
        ],
        default='PLAIN_AXES'
    )
    
    bpy.types.Scene.pipeline_empty_size = FloatProperty(
        name="空物体大小",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    # 分区选择
    bpy.types.Scene.pipeline_active_section = EnumProperty(
        name="活动分区",
        items=[
            ('DEFAULT', "默认", "默认工具"),
            ('ANIMATION', "动画", "动画工具"),
            ('RIGGING', "骨骼", "骨骼工具"),
            ('SETTINGS', "设置", "设置工具")
        ],
        default='DEFAULT'
    )
    
    # 折叠面板显示状态
    bpy.types.Scene.pipeline_show_empty_tools = BoolProperty(
        name="显示空物体工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_camera_tools = BoolProperty(
        name="显示摄像机工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_mode_tools = BoolProperty(
        name="显示模式工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_keyframe_tools = BoolProperty(
        name="显示关键帧工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_ikfk_tools = BoolProperty(
        name="显示IK/FK工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_playblast_tools = BoolProperty(
        name="显示预览工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_rig_tools = BoolProperty(
        name="显示骨骼工具",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_extension_tools = BoolProperty(
        name="显示扩展工具",
        default=True
    )        
    bpy.types.Scene.pipeline_show_mode_tools_rigging = BoolProperty(
        name="显示模式工具（骨骼分区）",
        default=True
    )
    
    bpy.types.Scene.pipeline_show_ikfk_instructions = BoolProperty(
        name="显示IK/FK指令工具",
        default=True
    )
    
    # 预设指令属性
    bpy.types.Scene.pipeline_arm_ik_to_fk_instruction = StringProperty(
        name="手臂IK切换到FK指令",
        default="",
        description="输入bpy.ops指令,用于手臂IK切换到FK"
    )
    
    bpy.types.Scene.pipeline_arm_fk_to_ik_instruction = StringProperty(
        name="手臂FK切换到IK指令",
        default="",
        description="输入bpy.ops指令,用于手臂FK切换到IK"
    )
    
    bpy.types.Scene.pipeline_leg_ik_to_fk_instruction = StringProperty(
        name="腿部IK切换到FK指令",
        default="",
        description="输入bpy.ops指令,用于腿部IK切换到FK"
    )
    
    bpy.types.Scene.pipeline_leg_fk_to_ik_instruction = StringProperty(
        name="腿部FK切换到IK指令",
        default="",
        description="输入bpy.ops指令,用于腿部FK切换到IK"
    )

def unregister_properties():
    # 预览动画属性
    del bpy.types.Scene.pipeline_playblast_quality
    del bpy.types.Scene.pipeline_playblast_format
    del bpy.types.Scene.pipeline_playblast_show_file
    del bpy.types.Scene.pipeline_playblast_use_default_path
    del bpy.types.Scene.pipeline_playblast_filepath
    del bpy.types.Scene.pipeline_last_playblast
    
    # 空物体属性
    del bpy.types.Scene.pipeline_empty_type
    del bpy.types.Scene.pipeline_empty_size
    
    # 分区选择
    del bpy.types.Scene.pipeline_active_section
    
    # 折叠面板显示状态
    del bpy.types.Scene.pipeline_show_empty_tools
    del bpy.types.Scene.pipeline_show_camera_tools
    del bpy.types.Scene.pipeline_show_mode_tools
    del bpy.types.Scene.pipeline_show_keyframe_tools
    del bpy.types.Scene.pipeline_show_ikfk_tools
    del bpy.types.Scene.pipeline_show_playblast_tools
    del bpy.types.Scene.pipeline_show_rig_tools
    del bpy.types.Scene.pipeline_show_extension_tools
    del bpy.types.Scene.pipeline_show_mode_tools_rigging
    del bpy.types.Scene.pipeline_show_ikfk_instructions
    
    # 预设指令属性
    del bpy.types.Scene.pipeline_arm_ik_to_fk_instruction
    del bpy.types.Scene.pipeline_arm_fk_to_ik_instruction
    del bpy.types.Scene.pipeline_leg_ik_to_fk_instruction
    del bpy.types.Scene.pipeline_leg_fk_to_ik_instruction

#---------------------------------------------------------------
# 注册与注销 - 插件生命周期管理
#---------------------------------------------------------------

# 所有类的列表
classes = (
    PIPELINE_OT_Addrigfy,
    PIPELINE_OT_GenerateRig,
    PIPELINE_OT_Playblast,
    PIPELINE_OT_DeletePlayblast,
    PIPELINE_OT_PlayblastPathSelect,
    PIPELINE_OT_AddEmpty,
    PIPELINE_OT_SetActiveCamera,
    PIPELINE_OT_KeyframeCharacter,
    PIPELINE_OT_SwitchMode,
    PIPELINE_OT_InstallExtensions,
    PIPELINE_OT_UpdateExtensions,
    PIPELINE_OT_FilterIKFKInDopesheet,
    PIPELINE_OT_IKFKSwitch,
    PIPELINE_OT_ExecuteInstruction,
    PIPELINE_PT_MainPanel
)

def register():
    # 注册所有类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册属性
    register_properties()
    print("Null Project Pipeline Tool Box 已注册")

def unregister():
    # 注销所有类
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # 注销属性
    unregister_properties()
    print("Null Project Pipeline Tool Box 已注销")

# 当脚本直接运行时注册插件
if __name__ == "__main__":
    register()