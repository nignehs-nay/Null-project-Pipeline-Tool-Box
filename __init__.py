import bpy
import os
from bpy.types import Operator, Panel
from bpy.props import EnumProperty, FloatProperty, BoolProperty, StringProperty

bl_info = {
    "name": "Null Project Pipeline Toolbox",
    "author": "Null",
    "description": "Pipeline tools for Null Project workflow",
    "blender": (4, 2, 0),
    "version": (0, 0, 2),
    "location": "3D View > Sidebar > Pipeline Tools",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
}

#---------------------------------------------------------------
# 工具类定义
#---------------------------------------------------------------

class PIPELINE_OT_AddMetarig(Operator):
    """添加Metarig骨骼"""
    bl_idname = "pipeline.add_metarig"
    bl_label = "添加Metarig"
    bl_options = {'REGISTER', 'UNDO'}
    
    rig_type: EnumProperty(
        name="骨骼类型",
        items=[
            ('METARIG', "Human Metarig", "标准人体骨骼"),
            ('BASIC', "Basic Human", "简化人体骨骼")
        ],
        default='METARIG'
    )
    
    def execute(self, context):
        """执行添加Metarig操作"""
        if self.rig_type == 'METARIG':
            bpy.ops.object.armature_human_metarig_add()
        else:
            bpy.ops.object.armature_basic_human_metarig_add()
        return {'FINISHED'}

class PIPELINE_OT_GenerateRig(Operator):
    """生成Rigify绑定"""
    bl_idname = "pipeline.generate_rig"
    bl_label = "生成绑定"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行生成绑定操作"""
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.pose.rigify_generate()
            self.report({'INFO'}, "Rigify绑定已生成")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "请先选择骨骼对象")
            return {'CANCELLED'}

class PIPELINE_OT_Playblast(Operator):
    """创建预览动画"""
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
            ('MP4', "MP4/H.264", "MP4格式，H.264编码"),
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
        """执行预览动画渲染"""
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
    """删除预览动画"""
    bl_idname = "pipeline.delete_playblast"
    bl_label = "删除预览动画"
    
    def execute(self, context):
        """执行删除预览文件操作"""
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
    """选择预览动画输出路径"""
    bl_idname = "pipeline.playblast_path_select"
    bl_label = "选择预览动画输出路径"
    
    filepath: StringProperty(
        subtype='FILE_PATH',
        description="选择预览动画的输出路径"
    )
    
    def execute(self, context):
        """设置预览动画输出路径"""
        context.scene.pipeline_playblast_filepath = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """打开文件浏览器选择路径"""
        # 设置默认输出路径
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if blend_filepath:
                blend_dir = os.path.dirname(blend_filepath)
                self.filepath = os.path.join(blend_dir, "playblast")
            else:
                self.filepath = os.path.join(os.path.expanduser("~"), "playblast")
        
        # 打开文件浏览器
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class PIPELINE_OT_AddEmpty(Operator):
    """添加空物体"""
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
        """执行添加空物体操作"""
        bpy.ops.object.empty_add(
            type=self.empty_type,
            align='WORLD',
            location=context.scene.cursor.location,
            scale=(self.size, self.size, self.size)
        )
        return {'FINISHED'}

class PIPELINE_OT_SetActiveCamera(Operator):
    """设置活动摄像机"""
    bl_idname = "pipeline.set_active_camera"
    bl_label = "设为活动摄像机"
    
    def execute(self, context):
        """设置活动摄像机"""
        if context.active_object and context.active_object.type == 'CAMERA':
            context.scene.camera = context.active_object
            self.report({'INFO'}, "活动摄像机已设置")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "请先选择摄像机")
            return {'CANCELLED'}

class PIPELINE_OT_KeyframeCharacter(Operator):
    """插入角色关键帧"""
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
        """执行关键帧插入操作"""
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请在姿态模式下操作")
            return {'CANCELLED'}
        
        if self.key_type == 'WHOLE':
            bpy.ops.anim.keyframe_insert_by_name(type="WholeCharacter")
        else:
            bpy.ops.anim.keyframe_insert_by_name(type="WholeCharacterSelected")
        
        return {'FINISHED'}

class PIPELINE_OT_IKFKSwitch(Operator):
    """IK/FK切换"""
    bl_idname = "pipeline.ikfk_switch"
    bl_label = "IK/FK切换"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """
        执行IK/FK切换操作
        1. 检查当前是否在姿态模式
        2. 检查是否选择了骨骼对象
        3. 尝试识别肢体类型（左臂/右臂/左腿/右腿）
        4. 获取对应的属性骨骼
        5. 切换IK/FK状态
        6. 报告操作结果
        """
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
            bone_name = bone.name.lower()  # 转换为小写以进行不区分大小写的匹配
            
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
        
        # 如果无法识别肢体类型，报告错误
        if not limb_type:
            self.report({'ERROR'}, "无法识别肢体类型，请选择手臂或腿部骨骼")
            return {'CANCELLED'}
        
        # 肢体映射到属性骨骼名称
        bone_map = {
            'ARM_L': "upper_arm_parent.L",
            'ARM_R': "upper_arm_parent.R",
            'LEG_L': "thigh_parent.L",
            'LEG_R': "thigh_parent.R"
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
        # 如果当前是IK模式(0.0)，则切换到FK模式(1.0)
        # 如果当前是FK模式(1.0)，则切换到IK模式(0.0)
        new_value = 1.0 if current_value == 0.0 else 0.0
        
        # 设置新值
        prop_bone["IK_FK"] = new_value
        
        # 报告结果
        mode = "FK" if new_value == 1.0 else "IK"
        self.report({'INFO'}, f"已切换 {limb_type} 到 {mode} 模式")
        
        return {'FINISHED'}

class PIPELINE_OT_SwitchMode(Operator):
    """切换模式"""
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
        """执行模式切换操作"""
        bpy.ops.object.mode_set(mode=self.mode)
        return {'FINISHED'}

class PIPELINE_OT_InstallExtensions(Operator):
    """安装扩展"""
    bl_idname = "pipeline.install_extensions"
    bl_label = "安装扩展"
    
    def execute(self, context):
        """执行安装扩展操作"""
        # 扩展安装命令列表
        install_commands = [
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='camera_shakify')",                # camera shakify
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='add_camera_rigs')",             # add camera rigs
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='f2')",                            # f2
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='auto_mirror')",                   # auto mirror
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='EdgeFlow')",                       # EdgeFlow
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='Half_Knife')",                   # Half Knife
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='copy_object_name_to_data')",     # copy object name to data
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='cell_fracture')",                # cell fracture
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='icon_viewer')",                   # icon viewer
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='hot_node')",                     # hot node
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='material_library')",              # material library
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='mmd_tools')",                     # mmd tools
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='vrm')",                            # VRM format
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='mio3_uv')",                        # mio3 uv
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='named_attribute_list')",           # named attribute list
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='node_align')",                   # node align
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='node_group_presets')",           # node group presets
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='screencast_keys')",               # screencast keys
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='render_preset')",                 # render preset
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='quick_groups')",                  # quick groups
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='time_tracker')",                   # time tracker
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='toggle_language')",               # toggle language
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='ucupaint')",                      # Ucupaint
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='ZenUVChecker')",                   # Zen UV Checker
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='you_are_autosave')",               # you are autosave
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='Modifier_List_Fork')",            # Modifier 
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='right_mouse_navigation')",         # Right Mouse Navigation
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='simple_deform_helper')",            # simple deform helper
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='PlaceHelper')",                    # PlaceHelper
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='popoti_align_helper')",             # popoti align helper
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='Colorista')",                       # Colorista
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='proceduraltiles')",                 # procedural tiles
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='noise_nodes')",                    # noise nodes
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='MustardUI')",                        # MustardUI
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='polychase')",                       # polychase
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='sakura_poselib')",                  # sakura poselib
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='Sakura_Rig_GUI')",                 # Sakura Rig GUI
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='easy_clouds')",                    # easy clouds
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='sapling_tree_gen')",               # sapling tree gen
            "bpy.ops.extensions.package_install(repo_index=0, pkg_id='jiggle_physics')",                 # jiggle physics
        ]
        
        # 执行所有安装命令
        for cmd in install_commands:
            try:
                # 执行命令
                exec(cmd)
                self.report({'INFO'}, f"已执行命令: {cmd}")
            except Exception as e:
                self.report({'ERROR'}, f"执行命令失败: {cmd} - {str(e)}")
        
        return {'FINISHED'}

class PIPELINE_OT_UpdateExtensions(Operator):
    """更新扩展"""
    bl_idname = "pipeline.update_extensions"
    bl_label = "更新扩展"
    
    def execute(self, context):
        """执行更新所有扩展操作"""
        try:
            # 使用指定的命令更新所有扩展
            bpy.ops.extensions.package_upgrade_all()
            self.report({'INFO'}, "所有扩展已更新")
        except Exception as e:
            self.report({'ERROR'}, f"更新扩展失败: {str(e)}")
        return {'FINISHED'}

class PIPELINE_OT_PROXY_GEO_RIGFY(Operator):
    bl_idname = "pipeline.proxy_geometry_to_rigfy"
    bl_label = "proxy_geometry_to_rigfy"

def execute(self, context):
        """
        执行为Rigfy创建代理几何体操作
        1. 检查当前是否在姿态模式
        2. 检查是否选择了骨骼对象

        """
        # 检查当前模式
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请在姿态模式下操作")
            return {'CANCELLED'}

        # 

#---------------------------------------------------------------
# 面板类定义
#---------------------------------------------------------------

class PIPELINE_PT_MainPanel(Panel):
    """主面板类,显示在3D视图的侧边栏"""
    bl_label = "Null Project Pipeline Box"
    bl_space_type = 'VIEW_3D'  # 只在3D视图中显示
    bl_region_type = 'UI'      # 侧边栏
    bl_category = "Pipeline Tool"   # 标签名称
    
    def draw(self, context):
        """绘制面板UI"""
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
        else:  # SETTINGS
            self.draw_settings_section(layout, context)
    
    def draw_default_section(self, layout, context):
        """绘制默认分区"""
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
        """绘制动画分区"""
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
        """绘制骨骼分区"""
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_rig_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_rig_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="骨骼工具")
        
        if context.scene.pipeline_show_rig_tools:
            row = box.row()
            row.operator("pipeline.add_metarig", text="Human Metarig").rig_type = 'METARIG'
            row.operator("pipeline.add_metarig", text="Basic Human").rig_type = 'BASIC'
            
            # 生成绑定按钮
            row = box.row()
            row.operator("pipeline.generate_rig", text="生成绑定")
    
    def draw_settings_section(self, layout, context):
        """绘制设置分区"""
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "pipeline_show_extension_tools", 
                 icon='TRIA_DOWN' if context.scene.pipeline_show_extension_tools else 'TRIA_RIGHT',
                 icon_only=True, emboss=False
        )
        row.label(text="扩展")
        
        if context.scene.pipeline_show_extension_tools:
            row = box.row()
            row.operator("pipeline.install_extensions", text="在线安装需要的扩展")
            row.operator("pipeline.update_extensions", text="在线更新已安装的扩展")

#---------------------------------------------------------------
# 属性注册
#---------------------------------------------------------------

def register_properties():
    """注册插件属性"""
    # 预览动画属性
    bpy.types.Scene.pipeline_playblast_quality = EnumProperty(
        name="预览质量",
        items=[
            ('LOW', "低质量", "快速预览"),
            ('MEDIUM', "中等质量", "平衡速度和质量")
        ],
        default='MEDIUM'
    )
    
    bpy.types.Scene.pipeline_playblast_format = EnumProperty(
        name="预览格式",
        items=[
            ('QUICKTIME', "QuickTime", "MOV格式"),
            ('MP4', "MP4/H.264", "MP4格式，H.264编码"),
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

def unregister_properties():
    """注销插件属性"""
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

#---------------------------------------------------------------
# 注册与注销
#---------------------------------------------------------------

# 所有类的列表
classes = (
    PIPELINE_OT_AddMetarig,
    PIPELINE_OT_GenerateRig,
    PIPELINE_OT_Playblast,
    PIPELINE_OT_DeletePlayblast,
    PIPELINE_OT_PlayblastPathSelect,
    PIPELINE_OT_AddEmpty,
    PIPELINE_OT_SetActiveCamera,
    PIPELINE_OT_KeyframeCharacter,
    PIPELINE_OT_IKFKSwitch,
    PIPELINE_OT_SwitchMode,
    PIPELINE_OT_InstallExtensions,
    PIPELINE_OT_UpdateExtensions,
    PIPELINE_PT_MainPanel
)

def register():
    """注册插件"""
    # 注册所有类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册属性
    register_properties()
    print("Null Project Pipeline Tool Box 已注册")

def unregister():
    """注销插件"""
    # 注销所有类
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # 注销属性
    unregister_properties()
    print("Null Project Pipeline Tool Box 已注销")

# 当脚本直接运行时注册插件
if __name__ == "__main__":
    register()